"""Apagar nota pelo script: só com o pedido, com ponto, e fora do Inbox só a pedido."""
from apoio import Ambiente, nota, rodar_testes


def test_apagar_nota_do_inbox_grava_ponto_e_o_desfazer_devolve():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Filme.md", nota("Filme"))
        amb.preparar()
        inicio = amb.inicio("triagem do Inbox")
        resposta = amb.rodar("apagar", "--token", inicio["token"], "--rotulo", "triagem: Filme", "Inbox/Filme.md")
        assert resposta["apagados"] == ["Inbox/Filme.md"] and resposta["ponto"]
        assert not amb.existe("Inbox/Filme.md") and amb.existe("Inbox")
        assert amb.git("status", "--porcelain").strip() == ""
        amb.rodar("fim", "--token", inicio["token"])
        token = amb.inicio("desfaz")["token"]
        amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--aplicar")
        assert amb.existe("Inbox/Filme.md")
    finally:
        amb.fechar()


def test_apagar_fora_do_inbox_so_com_a_opcao():
    amb = Ambiente()
    try:
        amb.escrever("Casa/Velha.md", nota("Velha"))
        amb.escrever("Inbox/Fica.md", nota("Fica"))
        amb.preparar()
        token = amb.inicio("remove")["token"]
        recusa = amb.rodar("apagar", "--token", token, "--rotulo", "remove", "Inbox/Fica.md", "Casa/Velha.md",
                           esperado=2)
        assert "Casa/Velha.md" in recusa["erro"]
        assert amb.existe("Casa/Velha.md") and amb.existe("Inbox/Fica.md")  # um recusado: nenhum sai
        resposta = amb.rodar("apagar", "--token", token, "--rotulo", "remove", "--fora-do-inbox", "Casa/Velha.md")
        assert resposta["apagados"] == ["Casa/Velha.md"] and not amb.existe("Casa/Velha.md")
    finally:
        amb.fechar()


def test_apagar_recusa_o_que_nao_e_nota_do_pedido():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Nota.md", nota("Nota"))
        amb.preparar()
        token = amb.inicio("triagem")["token"]
        amb.rodar("apagar", "--token", "errado", "--rotulo", "x", "Inbox/Nota.md", esperado=5)
        amb.rodar("apagar", "--token", token, "--rotulo", "x", "Inbox/Não existe.md", esperado=2)
        amb.rodar("apagar", "--token", token, "--rotulo", "x", "Inbox", esperado=2)
        amb.rodar("apagar", "--token", token, "--rotulo", "x", "--fora-do-inbox", "../fora.md", esperado=2)
        amb.escrever("Inbox/Sem ponto.md", nota("Sem ponto"))  # o histórico não a tem: o desfazer não a devolveria
        amb.rodar("apagar", "--token", token, "--rotulo", "x", "Inbox/Sem ponto.md", esperado=2)
        assert amb.existe("Inbox/Nota.md") and amb.existe("Inbox/Sem ponto.md")
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
