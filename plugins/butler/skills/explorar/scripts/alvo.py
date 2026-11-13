#!/usr/bin/env python3
"""Monta o alvo de uma exploração: grupos de notas, o que fica fora e as fontes de vídeo a reassistir.

Subcomando `montar`: recebe o alvo (`--pasta` ou `--notas`; `--tema` é da tarefa seguinte e por ora sai com 2),
separa em `fora` as notas que não entram e agrupa as demais em grupos de até `--tamanho` (padrão 10).

Fora, com o `motivo`: `nao_existe` (nota da lista que não existe), `nfd` (nome com acento decomposto),
`inbox` (pasta de entrada, das regras do vault), `protegida` e `rigida` (da nota de regras do Butler) e `ideia`
(frontmatter com `--excluir-campo` igual a `--excluir-valor`).

Grupos: por pasta, em ordem alfabética. Pasta com mais de `--tamanho` notas divide-se em ceil(n/tamanho) grupos
equilibrados; subpasta com menos de 3 notas junta-se à pasta-mãe se o total couber em `--tamanho`.

Reassistir: toda fonte de vídeo (instagram reel/p, youtube, youtu.be, tiktok) vinda do frontmatter `source` ou de
links no corpo cujo item (a linha, nas listas de um item por linha; senão título + corpo) tem sinal de lista
incompleta: `numero_no_titulo`, `lista_de`, `os_outros`, `nao_identificado`, `nao_confirmado`, `provavelmente`,
`varios_nomes` (3 ou mais nomes em negrito na mesma linha). Sem acento nem maiúsculas.

Imprime JSON: alvo, grupos, fora, reassistir, tema_candidatos. Só lê o vault.
Saída: 0 ok, 1 alvo vazio (nenhum grupo), 2 alvo inválido.

Uso: python alvo.py <vault> montar (--pasta P | --notas N [N ...] | --tema T)
                     [--excluir-campo type --excluir-valor ideia] [--tamanho 10]
"""
import argparse
import json
import math
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "gerente"))
from lib import regras as regras_lib  # noqa: E402

URL = re.compile(r"https?://[^\s<>\]]+")
VIDEO = re.compile(
    r"https?://(?:www\.|m\.)?(?:instagram\.com/(?:reel|reels|p|tv)/|youtube\.com/(?:watch|shorts)|youtu\.be/|"
    r"tiktok\.com/)", re.IGNORECASE)
NEGRITO = re.compile(r"\*\*[^*\n]+\*\*")
SINAIS = [
    ("numero_no_titulo", re.compile(r"\b(?:[2-9]|[1-9]\d)\s+[a-z]{3,}")),
    ("lista_de", re.compile(r"\blista de\b(?!\s*[\"'“]?\d)")),
    ("os_outros", re.compile(r"\bos outros\b")),
    ("nao_identificado", re.compile(r"\bnao identificad[oa]s?\b")),
    ("nao_confirmado", re.compile(r"\bnao confirmad[oa]s?\b")),
    ("provavelmente", re.compile(r"\bprovavelmente\b")),
]


def agrupar(notas, tamanho):
    """Grupos `{"id", "pasta", "notas"}` de até `tamanho` notas, por pasta, em ordem alfabética."""
    baldes = {}
    for nota in sorted(notas):
        baldes.setdefault(os.path.dirname(nota), []).append(nota)
    for pasta in sorted(baldes, key=lambda p: -p.count("/")):
        itens = baldes.get(pasta)
        if itens is None or len(itens) >= 3 or not pasta:
            continue
        mae = pasta
        while "/" in mae:
            mae = mae.rsplit("/", 1)[0]
            if mae in baldes and len(baldes[mae]) + len(itens) <= tamanho:
                baldes[mae] = sorted(baldes[mae] + itens)
                del baldes[pasta]
                break
    grupos = []
    for pasta in sorted(baldes):
        itens = baldes[pasta]
        k = max(1, math.ceil(len(itens) / tamanho))
        base, resto = divmod(len(itens), k)
        inicio = 0
        for i in range(k):
            n = base + (1 if i < resto else 0)
            grupos.append({"id": f"g{len(grupos) + 1}", "pasta": pasta, "notas": itens[inicio:inicio + n]})
            inicio += n
    return grupos


def sinais_de_lista(titulo, texto):
    """Ids dos sinais de lista incompleta no título e no texto, na ordem fixa."""
    negrito = max((len(NEGRITO.findall(l)) for l in texto.splitlines()), default=0)
    limpo = regras_lib.sem_acento(URL.sub(" ", f"{titulo}\n{texto}"))
    achados = [nome for nome, padrao in SINAIS if padrao.search(limpo)]
    if negrito >= 3:
        achados.append("varios_nomes")
    return achados


def fontes_em_video(texto):
    """URLs de vídeo (Instagram, YouTube, TikTok) do texto, sem repetir, na ordem."""
    vistas = []
    for url in URL.findall(texto):
        url = url.rstrip(").,;>")
        if VIDEO.match(url) and url not in vistas:
            vistas.append(url)
    return vistas


def separar_frontmatter(texto):
    texto = texto.lstrip(chr(0xFEFF))
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", texto, re.DOTALL)
    if not m:
        return {}, texto
    campos = {}
    for linha in m.group(1).splitlines():
        par = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", linha)
        if par:
            campos[par.group(1)] = par.group(2).strip("\"'")
    return campos, texto[m.end():]


def reassistir_da_nota(nota, texto):
    campos, corpo = separar_frontmatter(texto)
    titulo = campos.get("title") or os.path.splitext(os.path.basename(nota))[0]
    achados, restante = [], []
    for linha in corpo.splitlines():
        urls = fontes_em_video(linha)
        if urls and re.match(r"^\s*(?:[-*+]|\d+\.)\s", linha):
            sinais = sinais_de_lista("", linha)
            achados += [{"nota": nota, "url": u, "sinais": sinais} for u in urls if sinais]
        else:
            restante.append(linha)
    corpo_resto = "\n".join(restante)
    sinais = sinais_de_lista(titulo, corpo_resto)
    if sinais:
        for url in fontes_em_video(campos.get("source", "") + "\n" + corpo_resto):
            achados.append({"nota": nota, "url": url, "sinais": sinais})
    return achados


def ler_texto(caminho):
    with open(caminho, encoding="utf-8-sig") as f:
        return f.read()


def motivo_fora(vault, nota, regras, inbox, excluir):
    if unicodedata.normalize("NFC", nota) != nota:
        return "nfd"
    if regras_lib.casa(nota, [inbox]):
        return "inbox"
    if regras and regras.protegida(nota):
        return "protegida"
    if regras and regras.rigida(nota):
        return "rigida"
    if excluir:
        campos, _ = separar_frontmatter(ler_texto(os.path.join(vault, *nota.split("/"))))
        if campos.get(excluir[0]) == excluir[1]:
            return "ideia"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("subcomando", choices=["montar"])
    alvo = ap.add_mutually_exclusive_group(required=True)
    alvo.add_argument("--pasta")
    alvo.add_argument("--notas", nargs="+")
    alvo.add_argument("--tema")
    ap.add_argument("--excluir-campo")
    ap.add_argument("--excluir-valor")
    ap.add_argument("--tamanho", type=int, default=10)
    args = ap.parse_args()
    if args.tamanho < 1:
        print("--tamanho deve ser 1 ou mais", file=sys.stderr)
        return 2
    if args.tema:
        print("--tema ainda não foi implementado", file=sys.stderr)
        return 2

    if args.pasta:
        raiz = os.path.join(args.vault, *args.pasta.strip("/").split("/"))
        if not os.path.isdir(raiz):
            print(f"Pasta não encontrada: {args.pasta}", file=sys.stderr)
            return 2
        candidatas = []
        for dirpath, _, nomes in os.walk(raiz):
            for nome in nomes:
                if nome.lower().endswith(".md"):
                    rel = os.path.relpath(os.path.join(dirpath, nome), args.vault).replace(os.sep, "/")
                    candidatas.append(rel)
        candidatas.sort()
        descricao = {"tipo": "pasta", "valor": args.pasta}
    else:
        candidatas = [n.replace("\\", "/") for n in args.notas]
        descricao = {"tipo": "notas", "valor": candidatas}

    regras = regras_lib.ler(args.vault)
    inbox = regras.caminhos["inbox"] if regras else "Inbox"
    excluir = (args.excluir_campo, args.excluir_valor) if args.excluir_campo and args.excluir_valor else None
    fora, mantidas = [], []
    for nota in candidatas:
        if not os.path.isfile(os.path.join(args.vault, *nota.split("/"))):
            fora.append({"nota": nota, "motivo": "nao_existe"})
            continue
        motivo = motivo_fora(args.vault, nota, regras, inbox, excluir)
        if motivo:
            fora.append({"nota": nota, "motivo": motivo})
        else:
            mantidas.append(nota)

    grupos = agrupar(mantidas, args.tamanho)
    reassistir = []
    for nota in mantidas:
        reassistir += reassistir_da_nota(nota, ler_texto(os.path.join(args.vault, *nota.split("/"))))
    print(json.dumps({"alvo": descricao, "grupos": grupos, "fora": fora, "reassistir": reassistir,
                      "tema_candidatos": []}, ensure_ascii=False, indent=2))
    return 0 if grupos else 1


if __name__ == "__main__":
    sys.exit(main())
