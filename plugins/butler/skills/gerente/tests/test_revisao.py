"""Casos que a revisão da primeira versão achou: cada teste reproduz um defeito conferido antes da correção."""
import datetime
import os
import sys

from apoio import Ambiente, nota, rodar_testes

SENHA = "senha: " + "Xq7!" + "pLm2#"
AMANHA = (datetime.date.today() + datetime.timedelta(days=1)).isoformat() + " 00:00"


def test_desfazer_renomeacao_so_de_maiusculas_nao_apaga_a_nota():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/nota.md", nota("nota"))
        amb.preparar()
        inicio = amb.inicio("renomeia")
        amb.rodar("renomear", "--token", inicio["token"], "Inbox/nota.md", "Inbox/Nota.md")
        amb.rodar("fim", "--token", inicio["token"])
        token = amb.inicio("desfaz")["token"]
        amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--aplicar")
        nomes = os.listdir(amb.caminho("Inbox"))
        assert nomes == ["nota.md"], nomes
    finally:
        amb.fechar()


def test_desfazer_nao_leva_edicao_de_fora_gravada_na_retomada():
    amb = Ambiente()
    try:
        amb.escrever("Casa/A.md", nota("A", "linha 1"))
        amb.escrever("Casa/B.md", nota("B", "linha 1"))
        amb.preparar()
        inicio = amb.inicio("pedido", sessao="s1")
        amb.escrever("Casa/A.md", nota("A", "linha 1 do pedido"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "pedido: A", "Casa/A.md")
        amb.escrever("Casa/A.md", nota("A", "linha 1 do pedido\n\nedição no Obsidian"))
        retomada = amb.inicio("pedido", sessao="s1")
        assert retomada["retomada"]
        amb.escrever("Casa/B.md", nota("B", "linha 1 do pedido"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "pedido: B", "Casa/B.md")
        amb.rodar("fim", "--token", inicio["token"])
        token = amb.inicio("desfaz")["token"]
        plano = amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"])["plano"]
        itens = {i["arquivo"]: i for i in plano["itens"]}
        assert itens["Casa/A.md"]["conflito"], itens
        amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--aplicar")
        assert "edição no Obsidian" in amb.ler("Casa/A.md")
    finally:
        amb.fechar()


def test_foto_inicial_confere_a_pasta_do_obsidian():
    amb = Ambiente()
    try:
        amb.escrever(".obsidian/plugins/x/data.json", '{"' + SENHA.replace(": ", '": "') + '"}')
        resposta = amb.preparar()
        fora = [i["arquivo"] for i in resposta["fora_do_historico"]]
        assert ".obsidian/plugins/x/data.json" in fora, resposta
        assert ".obsidian/plugins/x/data.json" not in amb.git("ls-files")
        assert resposta["arquivos_na_foto"] == len(amb.git("ls-files").splitlines())
    finally:
        amb.fechar()


def test_ponto_recusa_pasta_e_renomear_nao_grava_dado_sensivel():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Inbox/Segredo.md", nota("Segredo", SENHA, links=("Outra",)))
        amb.escrever("Inbox/Outra.md", nota("Outra"))
        token = amb.inicio("pedido")["token"]
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "pasta", "Inbox")
        assert resposta["gravados"] == [] and resposta["recusados"][0]["motivo"] == "pasta", resposta
        resposta = amb.rodar("renomear", "--token", token, "Inbox/Outra.md", "Inbox/Outra nova.md")
        assert "Inbox/Segredo.md" in [r["arquivo"] for r in resposta["recusados"]], resposta
        assert "Inbox/Segredo.md" not in amb.git("ls-files")
    finally:
        amb.fechar()


def test_sensivel_depois_de_dois_megabytes():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("pedido")["token"]
        amb.escrever("Inbox/Grande.md", nota("Grande", ("x" * 100 + "\n") * 30000 + SENHA))
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "grande", "Inbox/Grande.md")
        assert [r["arquivo"] for r in resposta["recusados"]] == ["Inbox/Grande.md"], resposta
        assert "Inbox/Grande.md" not in amb.git("ls-files")
    finally:
        amb.fechar()


def test_restaurar_a_nota_de_regras_sem_ela():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.apagar("Sistema/Regras do Butler.md")
        inicio = amb.inicio("preparar")
        assert not inicio["historico_ok"]
        pedidos = amb.rodar("pedidos", "--nota", "Sistema/Regras do Butler.md", "--todos")["pedidos"]
        assert pedidos, pedidos
        plano = amb.rodar("desfazer", "--token", inicio["token"], "--nota", "Sistema/Regras do Butler.md", "--ate",
                          AMANHA)["plano"]
        assert plano["itens"][0]["acao"] == "recriar", plano
        amb.rodar("desfazer", "--token", inicio["token"], "--nota", "Sistema/Regras do Butler.md", "--ate",
                  AMANHA, "--aplicar", "--aceitar", "Sistema/Regras do Butler.md")
        assert amb.existe("Sistema/Regras do Butler.md")
    finally:
        amb.fechar()


def test_inicio_mantem_os_avisos_que_o_aviso_gravou():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Veículo/Histórico de Manutenção.md", nota("Histórico de Manutenção", "- 2026-01-10 troca"))
        aviso = amb.rodar("aviso")
        assert aviso["mudancas_de_fora"]["protegidas_com_remocao"], aviso
        inicio = amb.inicio("pedido")
        assert inicio["mudancas_de_fora"]["protegidas_com_remocao"] == ["Veículo/Histórico de Manutenção.md"], inicio
        assert amb.estado()["avisos"]["protegidas_com_remocao"]
        amb.rodar("fim", "--token", inicio["token"])
        assert not amb.estado()["avisos"].get("protegidas_com_remocao")
    finally:
        amb.fechar()


def test_rotulo_do_pedido_e_contagem_de_pontos():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("triagem do Inbox", sessao="s1")
        amb.escrever("Casa/A.md", nota("A"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "triagem: A", "Casa/A.md")
        amb.escrever("Casa/Fora.md", nota("Fora"))
        amb.inicio("triagem do Inbox", sessao="s1")
        amb.escrever("Casa/B.md", nota("B"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "triagem: B", "Casa/B.md")
        fim = amb.rodar("fim", "--token", inicio["token"])
        pedido = amb.rodar("pedidos")["pedidos"][0]
        assert fim["pontos"] == pedido["pontos"] == 2, (fim, pedido)
        assert pedido["rotulo"] == "triagem do Inbox", pedido
        token = amb.inicio("desfaz")["token"]
        plano = amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"])["plano"]
        assert plano["rotulo"] == "triagem do Inbox", plano
    finally:
        amb.fechar()


def test_titulo_de_arquivo_de_atualizacao_e_de_modelo():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Geladeira - atualização.md",
                     nota("Geladeira", extra='atualiza: "[[Geladeira]]"\n'))
        amb.escrever("Sistema/Modelos/Modelo de Nota.md", nota("{{title}}"))
        notas = amb.rodar("conferir", "Inbox/Geladeira - atualização.md", "Sistema/Modelos/Modelo de Nota.md")["notas"]
        for item in notas:
            assert "titulo_diferente" not in [a["codigo"] for a in item["achados"]], item
    finally:
        amb.fechar()


def test_vaults_com_o_mesmo_nome_nao_dividem_historico():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from lib import config
    um = config.historico_padrao(os.path.join("a", "Vault"))
    outro = config.historico_padrao(os.path.join("b", "Vault"))
    assert um != outro and os.path.basename(um).startswith("Vault")


def test_erro_vira_json():
    amb = Ambiente()
    try:
        resposta = amb.rodar("sensivel", "Nao existe.md", esperado=2)
        assert resposta["ok"] is False and resposta["erro"], resposta
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
