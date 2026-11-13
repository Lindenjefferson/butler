#!/usr/bin/env python3
"""Compara uma fila declarada de links contra o registro de links e devolve o próximo lote.

A fila é uma nota do vault com um ou mais blocos `### <nome> (<N> itens)`, cada um seguido de uma
linha por item: `<código>\t<url>` (código e URL separados por tab) ou só `<url>`. É o formato que a
exportação dos "Salvos" do Instagram já usa, lido por fora deste script e colado numa nota; este
script não baixa nem lê nenhuma exportação, só compara o que já está declarado contra o que já foi
processado.

Pendente é todo item cujo código (ou, sem código, a URL inteira) não aparece em nenhuma linha do
registro de links (`--registro`, o caminho da nota de registro; qualquer status conta como "já visto",
inclusive `falhou` e `descartado` — este script não decide retentativa, só o que nunca entrou). Sem
`--registro`, nada conta como já visto e a fila inteira é pendente.

Escolhe o próximo bloco com pendente (por padrão, o de menos itens pendentes primeiro — "menor
primeiro" foi a ordem usada manualmente neste vault e evita que um bloco gigante trave a fila),
pulando os nomes de `--pular`, e devolve até `--tamanho-lote` URLs pendentes dele.

Imprime um JSON com `bloco` (nome do bloco escolhido, ou null se não sobrar nenhum pendente),
`urls` (lista de URLs do lote, na ordem do bloco), `progresso` (totais gerais e por bloco) e
`pulados` (nomes de `--pular` que tinham pendente). Só lê: não altera nenhuma nota.

Uso: python fila.py <vault> --fila "<nota da fila>" [--registro "<nota do registro>"]
                     [--tamanho-lote 20] [--pular "Política" --pular "Direção"]
                     [--ordem menor-primeiro|arquivo]
"""
import argparse
import json
import os
import re
import sys

CODIGO_URL = re.compile(
    r"(?:/p/|/reel/|/reels/)([A-Za-z0-9_-]+)", re.IGNORECASE
)


def chave_do_item(codigo, url):
    """Identidade do item: o código do post, se achar um; senão a URL limpa (sem querystring/barra final)."""
    if codigo:
        return codigo
    m = CODIGO_URL.search(url)
    if m:
        return m.group(1)
    sem_query = url.split("?", 1)[0].rstrip("/")
    return sem_query


def ler_fila(texto):
    """Lê os blocos `### <nome> (<N> itens)` da nota da fila, cada um com uma lista de (código, url)."""
    blocos = []
    bloco_atual = None
    for linha in texto.splitlines():
        titulo = re.match(r"^###\s+(.+?)\s*\(\d+\s+itens?\)\s*$", linha)
        if titulo:
            bloco_atual = {"nome": titulo.group(1).strip(), "itens": []}
            blocos.append(bloco_atual)
            continue
        titulo_sem_contagem = re.match(r"^###\s+(.+?)\s*$", linha)
        if titulo_sem_contagem and not linha.strip().startswith("####"):
            bloco_atual = {"nome": titulo_sem_contagem.group(1).strip(), "itens": []}
            blocos.append(bloco_atual)
            continue
        if bloco_atual is None:
            continue
        partes = linha.split("\t")
        if len(partes) >= 2 and partes[1].strip():
            bloco_atual["itens"].append((partes[0].strip(), partes[1].strip()))
        elif len(partes) == 1 and re.match(r"^https?://", partes[0].strip()):
            bloco_atual["itens"].append((None, partes[0].strip()))
    return blocos


def ler_chaves_do_registro(texto):
    """Chaves (códigos) de toda linha da tabela do registro, qualquer status."""
    chaves = set()
    for linha in texto.splitlines():
        m = re.match(r"^\|\s*([A-Za-z0-9_-]+)\s*\|", linha)
        if m and m.group(1).lower() not in ("código", "codigo"):
            chaves.add(m.group(1))
    return chaves


def montar_progresso(blocos, vistos):
    progresso_blocos = []
    total, total_pendente = 0, 0
    for bloco in blocos:
        pendentes = [item for item in bloco["itens"] if chave_do_item(*item) not in vistos]
        progresso_blocos.append({"nome": bloco["nome"], "total": len(bloco["itens"]), "pendente": len(pendentes)})
        total += len(bloco["itens"])
        total_pendente += len(pendentes)
    return {"total_fila": total, "total_registrado": total - total_pendente,
            "total_pendente": total_pendente, "blocos": progresso_blocos}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--fila", required=True)
    ap.add_argument("--registro")
    ap.add_argument("--tamanho-lote", type=int, default=20)
    ap.add_argument("--pular", action="append", default=[])
    ap.add_argument("--ordem", choices=["menor-primeiro", "arquivo"], default="menor-primeiro")
    args = ap.parse_args()

    caminho_fila = os.path.join(args.vault, args.fila)
    if not os.path.isfile(caminho_fila):
        sys.exit(f"Nota da fila não encontrada: {args.fila}")
    with open(caminho_fila, encoding="utf-8") as f:
        blocos = ler_fila(f.read())

    vistos = set()
    if args.registro:
        caminho_registro = os.path.join(args.vault, args.registro)
        if os.path.isfile(caminho_registro):
            with open(caminho_registro, encoding="utf-8") as f:
                vistos = ler_chaves_do_registro(f.read())

    pulados_nomes = set(args.pular)
    pulados_com_pendente = []
    candidatos = []
    for bloco in blocos:
        pendentes = [item for item in bloco["itens"] if chave_do_item(*item) not in vistos]
        if not pendentes:
            continue
        if bloco["nome"] in pulados_nomes:
            pulados_com_pendente.append(bloco["nome"])
            continue
        candidatos.append((bloco["nome"], pendentes))

    resultado = {"bloco": None, "urls": [], "progresso": montar_progresso(blocos, vistos),
                 "pulados": sorted(pulados_com_pendente)}

    if candidatos:
        if args.ordem == "menor-primeiro":
            candidatos.sort(key=lambda c: len(c[1]))
        nome, pendentes = candidatos[0]
        resultado["bloco"] = nome
        resultado["urls"] = [url for _, url in pendentes[: args.tamanho_lote]]

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
