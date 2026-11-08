"""Leitura do vault: arquivos, frontmatter e wikilinks. Só lê."""
import json
import os
import re
import unicodedata

IGNORAR_PASTAS = {".obsidian", ".trash", ".git", ".tmp.drivedownload", ".tmp.driveupload"}
IGNORAR_ARQUIVOS = {"desktop.ini", "thumbs.db", ".ds_store"}
COPIA_CONFLITO = re.compile(r" \(\d+\)$")
_LINK = re.compile(r"!?\[\[([^\]\n]+?)\]\]")
_CERCA = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)
_CODIGO_INLINE = re.compile(r"`[^`\n]*`")
_CHAVE = re.compile(r"^[A-Za-z_][\w-]*\s*:")


def rel(vault, caminho):
    return os.path.relpath(caminho, vault).replace("\\", "/")


def absoluto(vault, relativo):
    return os.path.join(vault, *relativo.split("/"))


def arquivos(vault, com_obsidian=False):
    """Os arquivos do vault. `com_obsidian` inclui a configuração do Obsidian, que entra no histórico (menos o
    estado das janelas) e por isso passa pela detecção de dado sensível: um plugin pode guardar uma chave ali."""
    lista = []
    ignorar = IGNORAR_PASTAS - {".obsidian"} if com_obsidian else IGNORAR_PASTAS
    for raiz, pastas, nomes in os.walk(vault):
        pastas[:] = sorted(p for p in pastas if p not in ignorar)
        for nome in sorted(nomes):
            if nome.lower() in IGNORAR_ARQUIVOS:
                continue
            if com_obsidian and rel(vault, raiz) == ".obsidian" and nome.startswith("workspace"):
                continue
            lista.append(rel(vault, os.path.join(raiz, nome)))
    return lista


def grafia_no_disco(vault, relativo):
    """O caminho como o disco o grafa (`casa/x.md` vira `Casa/X.md` no Windows), ou None se não existe."""
    atual, partes = vault, []
    for parte in relativo.split("/"):
        try:
            nomes = os.listdir(atual)
        except OSError:
            return None
        achado = parte if parte in nomes else next((n for n in nomes if n.lower() == parte.lower()), None)
        if achado is None:
            return None
        partes.append(achado)
        atual = os.path.join(atual, achado)
    return "/".join(partes)


def pastas_vazias(vault, manter=()):
    """Pastas sem nenhum arquivo dentro, em qualquer profundidade, menos as de `manter`."""
    manter = {m.lower().strip("/") for m in manter if m}
    vazias = []
    for raiz, pastas, nomes in os.walk(vault, topdown=False):
        pastas[:] = [p for p in pastas if p not in IGNORAR_PASTAS]
        relativo = rel(vault, raiz)
        if relativo == "." or any(parte in IGNORAR_PASTAS for parte in relativo.split("/")):
            continue
        tem = False
        for atual, subpastas, subnomes in os.walk(raiz):
            subpastas[:] = [p for p in subpastas if p not in IGNORAR_PASTAS]
            if any(n.lower() not in IGNORAR_ARQUIVOS for n in subnomes):
                tem = True
                break
        if not tem and relativo.lower() not in manter:
            vazias.append(relativo)
    return sorted(vazias)


def ler_texto(vault, relativo):
    """(texto sem BOM, tinha_bom)."""
    with open(absoluto(vault, relativo), "rb") as arquivo:
        dados = arquivo.read()
    bom = dados.startswith(b"\xef\xbb\xbf")
    return dados[3:].decode("utf-8", "replace") if bom else dados.decode("utf-8", "replace"), bom


def frontmatter(texto):
    """(dict de chave → valor cru, erro). Sem frontmatter: (None, None). Lê só o nível de cima, que é o que a
    conferência usa; listas e valores aninhados ficam como texto."""
    if not texto.startswith("---"):
        return None, None
    linhas = texto.splitlines()
    if linhas[0].strip() != "---":
        return None, None
    campos = {}
    for numero, linha in enumerate(linhas[1:], start=2):
        if linha.strip() == "---":
            return campos, None
        if not linha.strip() or linha.startswith((" ", "\t", "-", "#")):
            continue
        if not _CHAVE.match(linha):
            return campos, f"linha {numero} do frontmatter não é `chave: valor`"
        chave, _, valor = linha.partition(":")
        campos[chave.strip()] = valor.strip().strip("\"'")
    return campos, "o frontmatter não fecha com `---`"


def sem_codigo(texto):
    return _CODIGO_INLINE.sub("", _CERCA.sub("", texto))


def wikilinks(texto):
    """Alvos dos wikilinks fora de código, sem `|apelido` nem `#seção`."""
    alvos = []
    for casado in _LINK.finditer(sem_codigo(texto)):
        alvo = casado.group(1).split("|", 1)[0].split("#", 1)[0].split("^", 1)[0].strip()
        if alvo:
            alvos.append(alvo)
    return alvos


def _nfc(texto):
    return unicodedata.normalize("NFC", texto).lower()


def indice(lista):
    """Tudo o que um wikilink pode nomear: o nome sem `.md`, o caminho com e sem `.md` e o nome com extensão."""
    nomes = set()
    for caminho in lista:
        base = caminho.rsplit("/", 1)[-1]
        nomes.update({_nfc(caminho), _nfc(base)})
        if caminho.lower().endswith(".md"):
            nomes.update({_nfc(caminho[:-3]), _nfc(base[:-3])})
    return nomes


def link_existe(alvo, nomes):
    alvo = _nfc(alvo.strip().lstrip("/"))
    return alvo in nomes or alvo + ".md" in nomes


def secao(texto, titulo):
    """Corpo da seção `## <titulo>` (qualquer nível), ou None."""
    padrao = re.compile(r"^(#{1,6})\s+" + re.escape(titulo) + r"\s*$", re.I | re.M)
    casado = padrao.search(texto)
    if not casado:
        return None
    nivel = len(casado.group(1))
    resto = texto[casado.end():]
    fim = re.search(r"^#{1," + str(nivel) + r"}\s", resto, re.M)
    return resto[:fim.start()] if fim else resto


def copia_conflito(relativo):
    base = relativo.rsplit("/", 1)[-1]
    raiz = base.rsplit(".", 1)[0] if "." in base else base
    return bool(COPIA_CONFLITO.search(raiz))


def nome_nfd(relativo):
    return unicodedata.normalize("NFC", relativo) != relativo


def usa_links_markdown(vault):
    """O Obsidian do vault cria links em Markdown (`[x](Nota.md)`) em vez de wikilinks: o `renomear` e a conferência
    só leem wikilinks."""
    try:
        with open(os.path.join(vault, ".obsidian", "app.json"), encoding="utf-8-sig") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return False
    return isinstance(dados, dict) and dados.get("useMarkdownLinks") is True


def arvore(vault):
    """Cada pasta do vault (a raiz é `""`), com as notas `.md` que ficam direto nela, inclusive as pastas vazias."""
    lista = []
    for raiz, pastas, nomes in os.walk(vault):
        pastas[:] = sorted(p for p in pastas if p not in IGNORAR_PASTAS)
        relativo = rel(vault, raiz)
        lista.append({"pasta": "" if relativo == "." else relativo,
                      "notas": sum(1 for n in nomes if n.lower().endswith(".md"))})
    return lista
