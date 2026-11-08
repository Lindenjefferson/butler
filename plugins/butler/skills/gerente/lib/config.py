"""Configuração da máquina: onde fica o histórico de cada vault.

O arquivo é `~/.butler/maquina.json` (ou o caminho em `BUTLER_CONFIG`), fora de qualquer vault, porque o caminho do
histórico só vale nesta máquina e um apontador dentro do vault seria sincronizado para as outras:

    {"versao": 1, "vaults": {"<caminho do vault>": {"historico": "<pasta do histórico>"}}}

O Wingman lê este mesmo arquivo para achar o `estado.json` de cada vault (`<historico>/estado.json`).

A pasta do histórico não pode ficar dentro do vault, numa pasta sincronizada (OneDrive, Google Drive, Dropbox,
iCloud) nem numa pasta temporária ou de cache, que uma limpeza de disco apaga. `BUTLER_PERMITIR_TEMP=1` libera a
pasta temporária, só para os testes.
"""
import hashlib
import json
import os
import re
import tempfile
import unicodedata

VERSAO = 1
SINCRONIZADAS = ("onedrive", "google drive", "googledrive", "my drive", "meu drive", "drivefs", "dropbox",
                 "icloud", "icloud drive", "mega", "pcloud", "box sync")
LIMPEZA = ("temp", "tmp", "cache", "caches")


def caminho_config():
    return os.environ.get("BUTLER_CONFIG") or os.path.join(os.path.expanduser("~"), ".butler", "maquina.json")


def chave(caminho):
    """Forma comparável de um caminho: absoluto, sem `..`, sem diferença de maiúsculas no Windows e em NFC."""
    return unicodedata.normalize("NFC", os.path.normcase(os.path.abspath(caminho)))


def ler():
    try:
        with open(caminho_config(), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return {"versao": VERSAO, "vaults": {}}
    if not isinstance(dados, dict) or not isinstance(dados.get("vaults"), dict):
        return {"versao": VERSAO, "vaults": {}}
    return dados


def gravar(dados):
    destino = caminho_config()
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporario = destino + ".novo"
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    os.replace(temporario, destino)


def historico_de(vault):
    """Pasta do histórico configurada para o vault, ou None."""
    alvo = chave(vault)
    for caminho, dados in ler()["vaults"].items():
        if chave(caminho) == alvo and isinstance(dados, dict) and dados.get("historico"):
            return dados["historico"]
    return None


def registrar(vault, historico):
    dados = ler()
    alvo = chave(vault)
    for caminho, antigo in list(dados["vaults"].items()):
        mesmo_historico = isinstance(antigo, dict) and antigo.get("historico") \
            and chave(antigo["historico"]) == chave(historico)
        if chave(caminho) == alvo or mesmo_historico:
            del dados["vaults"][caminho]
    dados["versao"] = VERSAO
    dados["vaults"][os.path.abspath(vault)] = {"historico": os.path.abspath(historico)}
    gravar(dados)


def achar_vault(inicio):
    """Sobe de `inicio` até achar um vault configurado nesta máquina ou, sem nenhum, uma pasta com a nota de regras
    (um vault ainda não preparado aqui). Devolve o caminho ou None. O `butler.py` e a guarda das escritas usam esta
    mesma busca, para chegarem à mesma trava de qualquer subpasta."""
    from .regras import ARQUIVO

    configurados = {chave(caminho) for caminho in ler()["vaults"]}
    com_regras = None
    atual = os.path.abspath(inicio)
    while True:
        if chave(atual) in configurados:
            return atual
        if com_regras is None and os.path.isfile(os.path.join(atual, *ARQUIVO.split("/"))):
            com_regras = atual
        pai = os.path.dirname(atual)
        if pai == atual:
            return com_regras
        atual = pai


def slug(vault):
    """O nome da pasta do vault e um pedaço do hash do caminho: dois vaults com o mesmo nome em lugares diferentes
    não dividem histórico nem trava."""
    nome = os.path.basename(os.path.abspath(vault).rstrip("\\/")) or "vault"
    marca = hashlib.sha1(chave(vault).encode("utf-8")).hexdigest()[:6]
    return re.sub(r'[<>:"/\\|?*]', "_", nome) + "-" + marca


def sumidos():
    """Os vaults registrados nesta máquina cuja pasta não existe mais, com o histórico de cada um: um vault movido ou
    renomeado reaproveita o dele (`preparar-historico --historico <pasta>`)."""
    return [{"vault": caminho, "historico": dados["historico"]} for caminho, dados in ler()["vaults"].items()
            if isinstance(dados, dict) and dados.get("historico") and not os.path.isdir(caminho)]


def dono_do_historico(historico, vault):
    """O outro vault, que ainda existe, já registrado com esta pasta de histórico, ou None. Um registro cuja pasta
    sumiu é o mesmo vault movido ou renomeado, que reaproveita o histórico."""
    alvo, proprio = chave(historico), chave(vault)
    for caminho, dados in ler()["vaults"].items():
        if isinstance(dados, dict) and dados.get("historico") and chave(dados["historico"]) == alvo \
                and chave(caminho) != proprio and os.path.isdir(caminho):
            return caminho
    return None


def historico_padrao(vault):
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return os.path.join(base, "Butler", slug(vault))
    return os.path.join(os.path.expanduser("~"), ".local", "share", "butler", slug(vault))


def pasta_de_estado(vault):
    """Onde ficam o `estado.json` e a trava: a pasta do histórico, ou, sem histórico configurado, uma pasta da
    máquina por vault (a trava precisa existir mesmo sem histórico)."""
    return historico_de(vault) or os.path.join(os.path.dirname(caminho_config()), "sem-historico", slug(vault))


def _partes(caminho):
    return [parte.lower() for parte in re.split(r"[\\/]+", os.path.abspath(caminho)) if parte]


def _dentro(filho, pai):
    filho, pai = chave(filho), chave(pai)
    try:
        return os.path.commonpath([filho, pai]) == pai
    except ValueError:
        return False


def motivo_pasta_proibida(historico, vault):
    """Por que a pasta não serve para o histórico, ou None se serve."""
    if _dentro(historico, vault) or _dentro(vault, historico):
        return "a pasta do histórico não pode ficar dentro do vault nem conter o vault"
    partes = _partes(historico)
    for parte in partes:
        for nome in SINCRONIZADAS:
            if parte == nome or parte.startswith(nome + " -") or parte.startswith(nome + "-"):
                return f"a pasta fica dentro de uma pasta sincronizada ({parte})"
    for marca in ("ONEDRIVE", "ONEDRIVECONSUMER", "ONEDRIVECOMMERCIAL"):
        raiz = os.environ.get(marca)
        if raiz and _dentro(historico, raiz):
            return "a pasta fica dentro do OneDrive"
    if os.environ.get("BUTLER_PERMITIR_TEMP") != "1":
        if _dentro(historico, tempfile.gettempdir()):
            return "a pasta fica numa pasta temporária, que uma limpeza de disco apaga"
        for parte in partes:
            if parte in LIMPEZA:
                return f"a pasta fica numa pasta temporária ou de cache ({parte})"
    return None
