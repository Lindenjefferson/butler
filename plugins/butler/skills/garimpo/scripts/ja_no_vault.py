"""Confere se links já estão no vault, olhando as URLs do frontmatter de todas as notas e o registro de links.

Uso: python ja_no_vault.py <pasta do vault> [--registro <nota do registro>] [--lista <lista> ...] URL1 [URL2 ...]

Compara pela identidade do conteúdo, não pela URL inteira:
- Instagram: o código do post (/p/<id>/, /reel/<id>/ e /reels/<id>/ são o mesmo);
- YouTube: o id do vídeo (watch?v=, youtu.be/, /shorts/, /embed/);
- o resto: a URL sem esquema, sem www, sem query, sem âncora e sem barra no fim.

Com `--registro` (o caminho, relativo ao vault, da nota de registro de links que as regras do Butler declaram em
`## Caminhos`), confere também a tabela dela: a primeira coluna de cada linha é o código do post do Instagram (o
trecho depois de `/p/`, `/reel/` ou `/reels/`, com maiúsculas e minúsculas contando). Um link registrado aparece
mesmo que a nota de destino tenha sido apagada, movida ou renomeada.

Cada `--lista` (um caminho de `## Listas da colheita`, com `<destino>` valendo qualquer nome) faz a busca ler também o
corpo daquelas notas, onde a colheita guarda a URL de cada item: assim um link de fora do Instagram, que não tem linha
no registro, também aparece como repetido.

Imprime um JSON com, para cada URL pedida, a lista de notas (caminho relativo ao vault) que já têm o mesmo
conteúdo no frontmatter e, se o registro tiver o link, `registro` com `status` e `destino`. Só lê: não altera nenhuma
nota. Sai com 0 mesmo quando acha repetidos.
"""
import json
import os
import re
import sys
from urllib.parse import parse_qs, urlsplit

URL = re.compile(r"https?://[^\s\"'<>\]\)]+")
IGNORAR = {".obsidian", ".trash", ".git"}


def chave(url):
    url = url.strip().rstrip(".,;")
    partes = urlsplit(url)
    host = partes.netloc.lower().removeprefix("www.").removeprefix("m.")
    caminho = partes.path.rstrip("/")
    if host.endswith("instagram.com"):
        achado = re.match(r"/(?:[^/]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", caminho)
        if achado:
            return "instagram:" + achado.group(1)
    if host in ("youtube.com", "music.youtube.com"):
        if caminho == "/watch":
            video = parse_qs(partes.query).get("v", [""])[0]
            if video:
                return "youtube:" + video
        achado = re.match(r"/(?:shorts|embed|live)/([A-Za-z0-9_-]+)", caminho)
        if achado:
            return "youtube:" + achado.group(1)
    if host == "youtu.be" and caminho:
        return "youtube:" + caminho.lstrip("/").split("/")[0]
    return host + caminho.lower() if host.endswith("github.com") else host + caminho


def frontmatter(texto):
    if not texto.startswith("---"):
        return ""
    fim = texto.find("\n---", 3)
    return texto[3:fim] if fim != -1 else ""


def indice(vault, listas=()):
    """Mapa de chave → notas. O frontmatter de toda nota conta; o corpo, só nas listas da colheita (`listas`: caminhos
    relativos ao vault, com `<destino>` valendo qualquer nome), que guardam a URL na linha do item."""
    padroes = [re.compile("^" + re.escape(l.replace("\\", "/")).replace(re.escape("<destino>"), "[^/]+") + "$",
                          re.IGNORECASE) for l in listas]
    mapa = {}
    for raiz, pastas, arquivos in os.walk(vault):
        pastas[:] = [p for p in pastas if p not in IGNORAR]
        for nome in arquivos:
            if not nome.endswith(".md"):
                continue
            caminho = os.path.join(raiz, nome)
            relativo = os.path.relpath(caminho, vault).replace("\\", "/")
            lista = any(p.match(relativo) for p in padroes)
            try:
                with open(caminho, encoding="utf-8-sig", errors="replace") as arquivo:
                    texto = arquivo.read() if lista else frontmatter(arquivo.read(20000))
            except OSError:
                continue
            for url in URL.findall(texto):
                mapa.setdefault(chave(url), set()).add(relativo)
    return mapa


def registro(vault, relativo):
    """Mapa de chave → {"status", "destino"} a partir das linhas da tabela do registro de links."""
    caminho = os.path.join(vault, *relativo.replace("\\", "/").split("/"))
    try:
        with open(caminho, encoding="utf-8-sig") as arquivo:
            linhas = arquivo.read().splitlines()
    except OSError:
        return {}
    mapa = {}
    for linha in linhas:
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) < 3 or celulas[1].lower() == "status" or not re.fullmatch(r"[A-Za-z0-9_-]{5,}", celulas[0]):
            continue
        mapa["instagram:" + celulas[0]] = {"status": celulas[1], "destino": celulas[2]}
    return mapa


def main():
    args = sys.argv[1:]
    nota_registro = None
    if "--registro" in args:
        posicao = args.index("--registro")
        nota_registro = args[posicao + 1] if posicao + 1 < len(args) else None
        del args[posicao:posicao + 2]
    listas = []
    while "--lista" in args:
        posicao = args.index("--lista")
        if posicao + 1 < len(args):
            listas.append(args[posicao + 1])
        del args[posicao:posicao + 2]
    if len(args) < 2:
        sys.exit("uso: python ja_no_vault.py <pasta do vault> [--registro <nota>] [--lista <lista> ...] URL1 [URL2 ...]")
    vault, urls = args[0], args[1:]
    if not os.path.isdir(vault):
        sys.exit(f"pasta do vault não encontrada: {vault}")
    mapa = indice(vault, listas)
    registrados = registro(vault, nota_registro) if nota_registro else {}
    saida = []
    for url in urls:
        item = {"url": url, "chave": chave(url), "notas": sorted(mapa.get(chave(url), set()))}
        if item["chave"] in registrados:
            item["registro"] = registrados[item["chave"]]
        saida.append(item)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(saida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
