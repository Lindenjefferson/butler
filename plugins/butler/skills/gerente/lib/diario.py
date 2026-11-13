"""Diário de pedidos, só de acréscimo, fora do vault.

O histórico git (`B pedidos`, `B mostrar`) registra o que virou nota. O que NÃO virou nota — a trava achada
ocupada, uma trava abandonada por prazo, um `fim` recusado por `sem_ponto` — não deixa rastro em lugar nenhum:
numa conversa sem ninguém olhando a resposta na hora (um serviço de pé), isso se perde. `diario.jsonl`, na pasta
de estado (fora do vault, nunca sincronizado), guarda uma linha JSON por evento, só de acréscimo:

    {"quando": "2026-11-13T10:00:00-03:00", "evento": "inicio" | "trava_ocupada" | "trava_abandonada_por_prazo" |
     "fim" | "fim_recusado_sem_ponto", "pedido", "rotulo", "sessao", ...os campos que fizerem sentido no evento}

Não é um histórico para desfazer (isso é o `historico.py`); é só para alguém, ou um painel, conferir depois o que
aconteceu sem estar olhando. Gravar uma linha nunca derruba o pedido: um erro de disco aqui só é ignorado.
"""
import json
import os

ARQUIVO = "diario.jsonl"


def registrar(pasta, **campos):
    try:
        os.makedirs(pasta, exist_ok=True)
        with open(os.path.join(pasta, ARQUIVO), "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(json.dumps(campos, ensure_ascii=False) + "\n")
    except OSError:
        pass


def ler(pasta, limite=50):
    """Os últimos `limite` eventos, do mais velho ao mais novo. Linha ilegível é pulada, não derruba a leitura."""
    try:
        with open(os.path.join(pasta, ARQUIVO), encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
    except OSError:
        return []
    eventos = []
    for linha in linhas[-limite:]:
        try:
            eventos.append(json.loads(linha))
        except ValueError:
            continue
    return eventos
