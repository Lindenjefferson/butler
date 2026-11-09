"""Leitura de `Sistema/Regras do Butler.md`, a nota do vault que diz o que o Butler protege.

O plugin não traz nenhuma regra de um vault: elas moram nesta nota, que a pessoa lê e edita no Obsidian. O script lê
só as seções que dá para conferir sem um modelo; o resto da nota (as exceções escritas em prosa, por exemplo) é lido
pela skill. Títulos de seção, comparados sem acento e sem maiúsculas:

- `## Notas protegidas` e `## Formato rígido`: cada item é `- \\`<caminho ou glob>\\` — <explicação>`. Glob com `*`
  (dentro de uma pasta) e `**` (em qualquer profundidade), relativo ao vault, com `/`.
- `## Escritas toleradas do Wingman`: lida pela skill; o script só a repassa.
- `## Exceções aprendidas`: um item com dois trechos em código, `- \\`<glob>\\` \\`<código de achado>\\` — <por quê>`,
  cala aquele achado da conferência naquelas notas. Item sem o segundo trecho é só texto para a skill.
- `## Liberações de dado sensível`: `- \\`<impressão digital>\\` — <arquivo e motivo>`, para um alarme falso ou um
  binário que a pessoa liberou. Um item com um caminho ou glob no lugar da digital (`- \\`Anexos/**\\` — prints`)
  libera os binários daquela pasta, nunca um dado sensível num texto. Um valor com cara de digital (hexadecimal)
  vale também como caminho, para uma pasta de nome hexadecimal não ser liberada calada pela metade.
- `## Caminhos`: `- <nome>: \\`<caminho>\\``, com os nomes `inbox` (padrão `Inbox`), `indice` (a nota índice, sem
  padrão), `pendencias` (sem padrão), `registro de links` (sem padrão), `veja tambem` (o título da seção de links
  no fim das notas, padrão `Veja também`) e `nuvem` (a raiz da nuvem sincronizada onde o vault está, sem padrão; um
  caminho absoluto do sistema operacional, não relativo ao vault).
- `## Nuvem: pastas fora da varredura`: cada item é `- \\`<caminho ou glob>\\` — <explicação>`, igual a `Notas
  protegidas`, mas os caminhos são absolutos (fora do vault) e dizem o que a preparação e qualquer rotina que olhe a
  nuvem nunca devem varrer, por privacidade.
- `## Listas da colheita`: `- <classificação>: \\`<caminho>\\` — <explicação>`, a lista em que a skill `colheita`
  grava cada classificação do garimpo (`filme`, `viagem`, `receita`). `<destino>` no caminho quer dizer uma nota por
  destino (a nota de cada viagem). Classificação sem linha aqui vira nota no Inbox, como todo link.

O `CLAUDE.md` da raiz e a própria nota de regras são sempre protegidos, estejam ou não na lista.
"""
import os
import re
import unicodedata

ARQUIVO = "Sistema/Regras do Butler.md"
SEMPRE_PROTEGIDAS = ("CLAUDE.md", ARQUIVO)
PADROES = {"inbox": "Inbox", "veja tambem": "Veja também"}
_CODIGO = re.compile(r"`([^`]+)`")
_DIGITAL = re.compile(r"[0-9a-f]{12,64}")


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower().strip()


class Regras:
    def __init__(self, texto=""):
        self.protegidas, self.rigidas, self.toleradas = [], [], []
        self.excecoes, self.liberacoes, self.caminhos = [], set(), dict(PADROES)
        self.binarios_liberados = []
        self.colheita = {}
        self.nuvem_ignorada = []
        secao = None
        for linha in texto.splitlines():
            titulo = re.match(r"^##\s+(.+?)\s*$", linha)
            if titulo:
                secao = sem_acento(titulo.group(1))
                continue
            item = re.match(r"^\s*[-*]\s+(.*)$", linha)
            if not item or secao is None:
                continue
            corpo = item.group(1)
            codigos = _CODIGO.findall(corpo)
            if secao in ("caminhos", "listas da colheita"):
                par = re.match(r"^([^:`]+):\s*`([^`]+)`", corpo)
                if par:
                    destino = self.caminhos if secao == "caminhos" else self.colheita
                    destino[sem_acento(par.group(1))] = par.group(2).strip().strip("/")
                continue
            if not codigos:
                continue
            if secao == "notas protegidas":
                self.protegidas.append(codigos[0].strip())
            elif secao == "nuvem: pastas fora da varredura":
                self.nuvem_ignorada.append(codigos[0].strip())
            elif secao == "formato rigido":
                self.rigidas.append(codigos[0].strip())
            elif secao == "escritas toleradas do wingman":
                self.toleradas.append(corpo.strip())
            elif secao == "excecoes aprendidas" and len(codigos) >= 2:
                self.excecoes.append((codigos[0].strip(), codigos[1].strip()))
            elif secao.startswith("liberacoes"):
                valor = codigos[0].strip()
                # Um nome de pasta pode ter cara de digital (um export com hash): o valor vale pelos dois jeitos.
                if _DIGITAL.fullmatch(valor.lower()):
                    self.liberacoes.add(valor.lower())
                self.binarios_liberados.append(valor)

    def protegida(self, caminho):
        return caminho in SEMPRE_PROTEGIDAS or casa(caminho, self.protegidas)

    def rigida(self, caminho):
        return casa(caminho, self.rigidas)

    def calado(self, caminho, codigo):
        return any(cod == codigo and casa(caminho, [glob]) for glob, cod in self.excecoes)

    def libera_binario(self, caminho, marca):
        """O binário pode entrar no histórico: liberado pela digital ou pela pasta."""
        return marca in self.liberacoes or casa(caminho, self.binarios_liberados)

    def caminho(self, nome):
        return self.caminhos.get(nome)

    def como_dict(self):
        return {"protegidas": self.protegidas, "rigidas": self.rigidas, "toleradas": self.toleradas,
                "excecoes": [{"glob": g, "codigo": c} for g, c in self.excecoes],
                "liberacoes": sorted(self.liberacoes),
                "binarios_liberados": self.binarios_liberados, "caminhos": self.caminhos, "colheita": self.colheita,
                "nuvem_ignorada": self.nuvem_ignorada}


def _glob_para_regex(glob):
    partes, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            partes.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            partes.append(".*")
            i += 2
        elif glob[i] == "*":
            partes.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            partes.append("[^/]")
            i += 1
        else:
            partes.append(re.escape(glob[i]))
            i += 1
    return re.compile("^" + "".join(partes) + "$", re.IGNORECASE)


def casa(caminho, globs):
    caminho = unicodedata.normalize("NFC", caminho.replace("\\", "/"))
    for glob in globs:
        glob = unicodedata.normalize("NFC", glob.replace("\\", "/").strip("/"))
        if _glob_para_regex(glob).match(caminho) or (not any(c in glob for c in "*?") and
                                                      caminho.lower().startswith(glob.lower() + "/")):
            return True
    return False


def ler(vault):
    """As regras do vault, ou None se a nota não existe ou não dá para ler (o Butler trabalha sem histórico)."""
    try:
        with open(os.path.join(vault, *ARQUIVO.split("/")), encoding="utf-8-sig") as arquivo:
            return Regras(arquivo.read())
    except (OSError, UnicodeDecodeError):
        return None

