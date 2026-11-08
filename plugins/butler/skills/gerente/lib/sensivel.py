"""Detecção de dado sensível: senha, cartão, CPF, RG e tokens de acesso.

Roda antes de qualquer arquivo entrar no histórico, porque o histórico não esquece. Nunca devolve o valor achado:
só o tipo, a linha e uma impressão digital (`digital`), os 12 primeiros caracteres do SHA-256 de `<tipo>:<valor>`. A
impressão digital não depende do arquivo nem da linha, então uma liberação (`## Liberações de dado sensível` nas
regras) continua valendo quando a nota muda ou é movida.

O que casa:
- `cpf`: `000.000.000-00` com dígitos verificadores válidos, ou 11 dígitos válidos com a palavra CPF antes, na linha;
- `cartao`: 13 a 19 dígitos em grupos de 4 (`0000 0000 0000 0000`), ou seguidos, logo depois de uma palavra de
  cartão (`cartão`, `crédito`, `débito`, `card`), sempre com o Luhn válido; `cartão SD`, `SIM` ou `de memória` não
  contam;
- `senha`: `senha`, `password`, `senha do wi-fi` e afins seguidos de `:`, `=`, `|` (tabela) ou de `é`, e de um valor;
- `pin`: `PIN:` seguido de 4 a 8 dígitos (`PIN: 24`, de pinos, não casa);
- `rg`: a sigla RG seguida de um número no formato de RG;
- `token`: chaves com prefixo conhecido (GitHub, Anthropic, OpenAI, AWS, Slack, Google).

Fica de fora de propósito: número de série, MAC, placa de carro, IMEI sem palavra de cartão e valor em reais.
"""
import hashlib
import re


def _so_digitos(valor):
    return re.sub(r"\D", "", valor)


def luhn(digitos):
    total, dobro = 0, False
    for c in reversed(digitos):
        n = int(c)
        if dobro:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        dobro = not dobro
    return total % 10 == 0


def cpf_valido(digitos):
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10 % 11) % 10 != int(digitos[tamanho]):
            return False
    return True


_PALAVRA_CARTAO = r"(?:cart[aã]o|cr[eé]dito|d[eé]bito|credit\s*card|debit\s*card|card(?:\s*number)?)"
_NAO_CARTAO = r"(?!\s*(?:sd|micro\s*sd|sim|de\s+mem[oó]ria|de\s+visita|postal|do\s+sus))"
PADROES = [
    ("cpf", re.compile(r"(?<![\d.])(\d{3}\.\d{3}\.\d{3}-\d{2})(?![\d-])")),
    ("cpf", re.compile(r"(?i)\bcpf\b[^\d\n]{0,15}(\d{11}|\d{3}\.?\d{3}\.?\d{3}-?\d{2})(?!\d)")),
    ("cartao", re.compile(r"(?<![\d-])((?:\d{4}[ -]){3}\d{1,7})(?![\d-])")),
    ("cartao", re.compile(r"(?i)\b" + _PALAVRA_CARTAO + _NAO_CARTAO + r"[^\d\n]{0,25}(\d{13,19})(?!\d)")),
    ("senha", re.compile(r"(?i)\b(?:senha|password|passwd|pwd|passphrase|chave\s+do\s+wi-?fi)(?:\s+do\s+wi-?fi)?\b"
                         r"[\"']?\s*(?::|=|\|)\s*[\"']?(?!\s*(?:\||n[aã]o\s+informad|-+\s*(?:\||$)|—|$))"
                         r"([^\s|\"']{3,})")),
    ("senha", re.compile(r"(?i)\b(?:a\s+)?senha(?:\s+do\s+wi-?fi)?\s+(?:é|e)\s*:?\s*[\"“']?([^\s\"”']{3,})")),
    ("pin", re.compile(r"(?i)\bpin\b\s*[:=]\s*(\d{4,8})(?!\d)")),
    ("rg", re.compile(r"(?i)\brg\b\s*(?:n[ºo°.]*\s*)?[:=]?\s*(\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX])(?![\d])")),
    ("token", re.compile(r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|sk-ant-[A-Za-z0-9_-]{20,}|"
                         r"sk-(?:proj-)?[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|"
                         r"AIza[0-9A-Za-z_-]{35})")),
]


def _valido(tipo, valor):
    if tipo == "cpf":
        return cpf_valido(_so_digitos(valor))
    if tipo == "cartao":
        digitos = _so_digitos(valor)
        return 13 <= len(digitos) <= 19 and luhn(digitos)
    return True


def digital(tipo, valor):
    normal = _so_digitos(valor) if tipo in ("cpf", "cartao", "pin", "rg") else valor
    return hashlib.sha256(f"{tipo}:{normal}".encode("utf-8")).hexdigest()[:12]


def achar(texto, liberadas=()):
    """Lista de achados `{"tipo", "linha", "digital"}`, sem o valor. Ignora as impressões digitais liberadas."""
    achados, vistos = [], set()
    liberadas = {d.lower() for d in liberadas}
    for numero, linha in enumerate(texto.splitlines(), start=1):
        for tipo, padrao in PADROES:
            for casado in padrao.finditer(linha):
                valor = casado.group(1)
                if not _valido(tipo, valor):
                    continue
                marca = digital(tipo, valor)
                if marca in liberadas or (numero, marca) in vistos:
                    continue
                vistos.add((numero, marca))
                achados.append({"tipo": tipo, "linha": numero, "digital": marca})
    return achados


def digital_de_arquivo(conteudo):
    return hashlib.sha256(conteudo).hexdigest()[:12]


def binario(conteudo):
    return b"\0" in conteudo[:8192]


def no_arquivo(caminho, liberadas=()):
    """(achados, binario, digital do arquivo). Arquivo binário não é lido como texto: quem chama decide. O texto é
    lido inteiro, porque o histórico grava o arquivo inteiro."""
    with open(caminho, "rb") as arquivo:
        conteudo = arquivo.read()
    if binario(conteudo):
        return [], True, digital_de_arquivo(conteudo)
    return achar(conteudo.decode("utf-8", "replace"), liberadas), False, None
