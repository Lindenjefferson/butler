"""O fim confere o que ficou sem ponto, e as dúvidas de um Lote sobrevivem à compactação."""
import json
import os

from apoio import Ambiente, nota, rodar_testes


def test_fim_recusa_arquivo_mudado_sem_ponto():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("triagem", sessao="s")["token"]
        amb.escrever("Casa/Nova.md", nota("Nova"))
        amb.rodar("ponto", "--token", token, "--rotulo", "triagem: Nova", "Casa/Nova.md")
        amb.escrever("Início.md", amb.ler("Início.md") + "- [[Nova]]\n")  # o índice esquecido
        resposta = amb.rodar("fim", "--token", token, esperado=6)
        assert resposta["sem_ponto"] == [{"estado": "alterado", "arquivo": "Início.md"}]
        assert os.path.exists(os.path.join(amb.historico, "trava.json"))  # a trava continua com o pedido
        amb.rodar("ponto", "--token", token, "--rotulo", "triagem: índice", "Início.md")
        assert amb.rodar("fim", "--token", token)["ok"]
    finally:
        amb.fechar()


def test_fim_com_sem_ponto_ok_solta_mesmo_assim():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("triagem", sessao="s")["token"]
        amb.escrever("Casa/Do usuário.md", nota("Do usuário"))  # o usuário escreveu no Obsidian no meio
        resposta = amb.rodar("fim", "--token", token, "--sem-ponto-ok")
        assert resposta["ok"] and resposta["sem_ponto"][0]["arquivo"] == "Casa/Do usuário.md"
        assert amb.inicio("outro", sessao="t")["retomada"] is False
    finally:
        amb.fechar()


def test_fim_ignora_a_pasta_do_obsidian():
    amb = Ambiente()
    try:
        amb.escrever(".obsidian/app.json", "{}")
        amb.preparar()
        token = amb.inicio("triagem", sessao="s")["token"]
        amb.escrever(".obsidian/app.json", '{"x": 1}')
        assert amb.rodar("fim", "--token", token)["ok"]
    finally:
        amb.fechar()


def test_fim_sem_historico_nao_confere():
    amb = Ambiente()
    try:
        token = amb.inicio("anota", sessao="s")["token"]
        amb.escrever("Inbox/X.md", nota("X"))
        assert amb.rodar("fim", "--token", token)["ok"]
    finally:
        amb.fechar()


def test_duvida_gravada_volta_na_retomada_e_no_fim():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("triagem", sessao="s")["token"]
        amb.rodar("duvida", "--token", token, "--pergunta", "De quem é a nota X?", "--proposta", "compartilhada",
                  "--nota", "Inbox/X.md")
        amb.rodar("duvida", "--token", token, "--pergunta", "De quem é a nota X?", "--proposta", "compartilhada",
                  "--nota", "Inbox/X.md")  # repetida não duplica
        retomada = amb.inicio("triagem", sessao="s")
        assert retomada["retomada"]
        assert retomada["duvidas"] == [{"pergunta": "De quem é a nota X?", "proposta": "compartilhada",
                                        "nota": "Inbox/X.md"}]
        resumo = json.dumps({"perguntas": [{"pergunta": "Descarto Y?", "proposta": "sim", "nota": "Inbox/Y.md"}]})
        fim = amb.rodar("fim", "--token", token, "--resumo", "-", entrada=resumo.encode("utf-8"))
        assert fim["ok"]
        perguntas = amb.estado()["perguntas"]
        assert [p["pergunta"] for p in perguntas] == ["De quem é a nota X?", "Descarto Y?"]
    finally:
        amb.fechar()


def test_duvida_com_token_errado_e_recusada():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="s")
        amb.rodar("duvida", "--token", "errado", "--pergunta", "?", esperado=5)
    finally:
        amb.fechar()


def test_mesma_duvida_reescrita_no_resumo_nao_duplica():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("triagem", sessao="s")["token"]
        amb.rodar("duvida", "--token", token, "--pergunta", "De quem é a nota X?", "--proposta", "compartilhada",
                  "--nota", "Inbox/X.md")
        resumo = json.dumps({"perguntas": [{"pergunta": "de quem e a nota  X", "proposta": "minha",
                                            "nota": "Inbox/X.md"},
                                           {"pergunta": "De quem é a nota X?", "nota": "Inbox/Z.md"}]})
        assert amb.rodar("fim", "--token", token, "--resumo", "-", entrada=resumo.encode("utf-8"))["ok"]
        perguntas = amb.estado()["perguntas"]
        assert [(p["pergunta"], p.get("nota")) for p in perguntas] == [("De quem é a nota X?", "Inbox/X.md"),
                                                                     ("De quem é a nota X?", "Inbox/Z.md")]
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
