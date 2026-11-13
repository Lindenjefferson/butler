"""Confere se uma proposta de reescrita guarda os dados da nota: o que sumiu e o que apareceu.

Uso: conferir_dados.py "<nota>" "<proposta>"

Compara o corpo dos dois arquivos (o frontmatter fica de fora) e imprime um JSON:

    {"ok": false, "sumiu": {"links": [], "wikilinks": [], "numeros": [], "codigo": []}, "novo": {...}}

- `links`: as URLs; `wikilinks`: o destino de cada `[[nota]]`, sem apelido nem seção;
- `numeros`: cada número do texto ("45", "1.299,90", "3.15"), fora das URLs, do código e da numeração das listas;
- `codigo`: o texto entre crases.

`sumiu` é o que a nota tem e a proposta não; `novo`, o contrário. Saída 0 quando os dois vêm vazios, 1 quando não,
2 quando um arquivo não abre. O script só enxerga esses quatro tipos de dado: nome, frase e sentido continuam
sendo conferidos por quem lê. Só lê os dois arquivos.
"""
import json
import re
import sys

FRONTMATTER = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.S)
LINK = re.compile(r"https?://[^\s)\]>\"]+")
WIKILINK = re.compile(r"\[\[([^\]|#]+)")
CODIGO = re.compile(r"`([^`\n]+)`")
MARCADOR = re.compile(r"^\s*\d+[.)]\s", re.M)
NUMERO = re.compile(r"\d+(?:[.,]\d+)*")
TIPOS = ("links", "wikilinks", "numeros", "codigo")


def dados(texto):
    corpo = FRONTMATTER.sub("", texto, count=1)
    links = {link.rstrip(".,;:") for link in LINK.findall(corpo)}
    codigo = {trecho.strip() for trecho in CODIGO.findall(corpo)}
    resto = MARCADOR.sub("", CODIGO.sub(" ", LINK.sub(" ", corpo)))
    return {"links": sorted(links),
            "wikilinks": sorted({destino.strip() for destino in WIKILINK.findall(corpo)}),
            "numeros": sorted(set(NUMERO.findall(resto))),
            "codigo": sorted(codigo)}


def comparar(antes, depois):
    a, d = dados(antes), dados(depois)
    sumiu = {tipo: [item for item in a[tipo] if item not in d[tipo]] for tipo in TIPOS}
    novo = {tipo: [item for item in d[tipo] if item not in a[tipo]] for tipo in TIPOS}
    return {"ok": not any(sumiu.values()) and not any(novo.values()), "sumiu": sumiu, "novo": novo}


def _ler(caminho):
    with open(caminho, encoding="utf-8-sig") as arquivo:
        return arquivo.read()


def main(argumentos):
    if len(argumentos) != 2:
        print(json.dumps({"erro": "uso: conferir_dados.py <nota> <proposta>"}, ensure_ascii=False))
        return 2
    try:
        resultado = comparar(_ler(argumentos[0]), _ler(argumentos[1]))
    except OSError as erro:
        print(json.dumps({"erro": str(erro)}, ensure_ascii=False))
        return 2
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
