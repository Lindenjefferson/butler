"""Diário de pedidos: o que não virou nota (trava ocupada, abandonada por prazo, fim recusado) fica registrado."""
from apoio import Ambiente, nota, rodar_testes


def test_inicio_e_fim_registram_no_diario():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("triagem", sessao="s")["token"]
        amb.escrever("Inbox/X.md", nota("X"))
        amb.rodar("ponto", "--token", token, "--rotulo", "triagem: X", "Inbox/X.md")
        amb.rodar("fim", "--token", token)
        eventos = [e["evento"] for e in amb.rodar("diario")["eventos"]]
        assert eventos == ["inicio", "fim"], eventos
    finally:
        amb.fechar()


def test_retomada_nao_registra_outro_inicio():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="s")
        amb.inicio("triagem", sessao="s")  # retomada
        eventos = [e["evento"] for e in amb.rodar("diario")["eventos"]]
        assert eventos == ["inicio"], eventos
    finally:
        amb.fechar()


def test_trava_ocupada_registra_no_diario():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="a")
        amb.inicio("garimpo", sessao="b", esperado=3)
        eventos = amb.rodar("diario")["eventos"]
        ocupadas = [e for e in eventos if e["evento"] == "trava_ocupada"]
        assert len(ocupadas) == 1 and ocupadas[0]["rotulo"] == "garimpo"
    finally:
        amb.fechar()


def test_fim_recusado_sem_ponto_registra_no_diario():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("triagem", sessao="s")["token"]
        amb.escrever("Casa/X.md", nota("X"))
        amb.rodar("fim", "--token", token, esperado=6)
        eventos = [e["evento"] for e in amb.rodar("diario")["eventos"]]
        assert eventos == ["inicio", "fim_recusado_sem_ponto"], eventos
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
