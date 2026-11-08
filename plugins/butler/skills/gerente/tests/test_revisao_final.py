"""Casos da revisão final da primeira versão: cada teste reproduz um defeito conferido antes da correção."""
import datetime
import json
import os
import shutil

from apoio import Ambiente, nota, rodar_testes

SENHA = "senha: " + "Xq7!" + "pLm2#"


def test_aviso_no_meio_do_pedido_nao_solta_a_trava():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("triagem", sessao="S1")
        amb.rodar("aviso", "--sessao", "S1")
        amb.escrever("Casa/A.md", nota("A"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "triagem: A", "Casa/A.md")
    finally:
        amb.fechar()


def test_trava_de_aviso_que_morreu_nao_vira_o_pedido_da_sessao():
    amb = Ambiente()
    try:
        amb.preparar()
        trava = {"pedido": "x", "token": "t", "rotulo": "aviso do início da sessão", "sessao": "aviso:S1",
                 "inicio": "2026-01-01T00:00:00-03:00", "atualizado": "2026-01-01T00:00:00-03:00"}
        with open(os.path.join(amb.historico, "trava.json"), "w", encoding="utf-8") as arquivo:
            json.dump(trava, arquivo)
        inicio = amb.inicio("triagem", sessao="S1")
        assert not inicio["retomada"] and inicio["pedido"] != "x", inicio
    finally:
        amb.fechar()


def test_preparar_grava_a_nota_de_regras_no_proprio_pedido():
    amb = Ambiente(regras=False)
    try:
        amb.preparar()
        inicio = amb.inicio("preparar o vault")
        assert not inicio["historico_ok"]
        amb2 = Ambiente()
        amb.escrever("Sistema/Regras do Butler.md", amb2.ler("Sistema/Regras do Butler.md"))
        amb2.fechar()
        resposta = amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "preparar: regras",
                             "Sistema/Regras do Butler.md")
        assert resposta["gravados"] == ["Sistema/Regras do Butler.md"], resposta
        amb.rodar("fim", "--token", inicio["token"])
        assert amb.rodar("pedidos")["pedidos"][0]["pedido"] == inicio["pedido"]
    finally:
        amb.fechar()


def test_vault_movido_reaproveita_o_historico():
    amb = Ambiente()
    try:
        amb.preparar()
        novo = os.path.join(amb.raiz, "Vault Novo")
        shutil.move(amb.vault, novo)
        resposta = amb.rodar("preparar-historico", "--vault", novo, "--historico", amb.historico, cwd=amb.raiz)
        assert resposta["ok"] and resposta["ja_existia"], resposta
    finally:
        amb.fechar()


def test_mostrar_nao_mistura_mudanca_de_fora():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("pedido", sessao="S1")
        amb.escrever("Casa/A.md", nota("A"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "pedido: A", "Casa/A.md")
        amb.escrever("Casa/Obsidian.md", nota("Obsidian"))
        amb.inicio("pedido", sessao="S1")
        amb.escrever("Casa/B.md", nota("B"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "pedido: B", "Casa/B.md")
        diff = amb.rodar("mostrar", "--pedido", inicio["pedido"])["diff"]
        assert "Casa/A.md" in diff and "Casa/B.md" in diff and "Casa/Obsidian.md" not in diff, diff
    finally:
        amb.fechar()


def test_aceitar_so_o_nome_antigo_nao_sobrescreve_o_novo():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/nota.md", nota("nota"))
        amb.preparar()
        inicio = amb.inicio("renomeia")
        amb.rodar("renomear", "--token", inicio["token"], "Inbox/nota.md", "Inbox/Nota.md")
        amb.rodar("fim", "--token", inicio["token"])
        amb.escrever("Inbox/Nota.md", nota("Nota", "edição depois"))
        token = amb.inicio("desfaz")["token"]
        feito = amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--aplicar", "--aceitar",
                          "Inbox/nota.md")
        assert "edição depois" in amb.ler("Inbox/Nota.md"), feito
        assert "Inbox/nota.md" in [i["arquivo"] for i in feito["nome_ocupado"]] or os.path.normcase("A") != "a", feito
    finally:
        amb.fechar()


def test_renomear_e_desfazer_nao_apagam_o_inbox():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Unica.md", nota("Unica"))
        amb.preparar()
        inicio = amb.inicio("triagem")
        amb.rodar("renomear", "--token", inicio["token"], "Inbox/Unica.md", "Casa/Unica.md")
        assert os.path.isdir(amb.caminho("Inbox"))
        amb.rodar("fim", "--token", inicio["token"])
        inicio = amb.inicio("anota")
        amb.escrever("Inbox/Anotada.md", nota("Anotada"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "anota", "Inbox/Anotada.md")
        amb.rodar("fim", "--token", inicio["token"])
        token = amb.inicio("desfaz")["token"]
        amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--aplicar")
        assert os.path.isdir(amb.caminho("Inbox"))
    finally:
        amb.fechar()


def test_desfazer_apaga_a_pasta_que_o_pedido_criou():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("cria")
        amb.escrever("Nova Pasta/Sub/X.md", nota("X"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "cria", "Nova Pasta/Sub/X.md")
        amb.rodar("fim", "--token", inicio["token"])
        token = amb.inicio("desfaz")["token"]
        amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--aplicar")
        assert not amb.existe("Nova Pasta")
    finally:
        amb.fechar()


def test_ponto_com_outra_grafia_e_recusado():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("pedido")["token"]
        amb.escrever("Inventários/Geladeira.md", nota("Geladeira", "- Voltagem: 220V"))
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "x", "inventários/geladeira.md")
        if os.path.normcase("A") == "a":  # só no Windows o disco acha o arquivo com outra grafia
            assert resposta["recusados"] and "Inventários/Geladeira.md" in resposta["recusados"][0]["motivo"], \
                resposta
    finally:
        amb.fechar()


def test_renomear_para_nota_recusada_nao_grava_meio_movimento():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Wifi.md", nota("Wifi", "rede da casa"))
        amb.preparar()
        token = amb.inicio("renomeia")["token"]
        amb.escrever("Inbox/Wifi.md", nota("Wifi", SENHA))
        amb.rodar("renomear", "--token", token, "Inbox/Wifi.md", "Casa/Wifi.md")
        assert "Inbox/Wifi.md" in amb.git("ls-files")
    finally:
        amb.fechar()


def test_ate_com_minuto_inclui_o_proprio_minuto():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("pedido")
        amb.escrever("Casa/A.md", nota("A", "versão 1"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "a", "Casa/A.md")
        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        plano = amb.rodar("desfazer", "--token", inicio["token"], "--nota", "Casa/A.md", "--ate", agora)["plano"]
        assert plano["itens"], plano
    finally:
        amb.fechar()


def test_desfazer_mostra_a_versao_que_deixaria():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("pedido")
        amb.escrever("Casa/A.md", nota("A", "versão do pedido"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "a", "Casa/A.md")
        amb.rodar("fim", "--token", inicio["token"])
        amb.escrever("Casa/A.md", nota("A", "versão de fora"))
        token = amb.inicio("desfaz")["token"]
        plano = amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--conteudo",
                          "Casa/A.md")["plano"]
        assert plano["conteudo"]["Casa/A.md"] is None, plano  # o pedido criou a nota: desfazer a apagaria
    finally:
        amb.fechar()


def test_conteudo_de_item_sem_mudanca_e_o_arquivo_atual():
    amb = Ambiente()
    try:
        amb.escrever("Casa/A.md", nota("A", "original"))
        amb.preparar()
        inicio = amb.inicio("pedido")
        amb.escrever("Casa/A.md", nota("A", "do pedido"))
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "a", "Casa/A.md")
        amb.rodar("fim", "--token", inicio["token"])
        amb.escrever("Casa/A.md", nota("A", "original"))
        token = amb.inicio("desfaz")["token"]
        plano = amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--conteudo",
                          "Casa/A.md")["plano"]
        assert plano["itens"][0]["acao"] == "nada", plano
        assert plano["conteudo"]["Casa/A.md"] == nota("A", "original"), plano
    finally:
        amb.fechar()


def test_nome_ocupado_aparece_a_parte_e_aceitar_nao_resolve():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Livros.md", nota("Livros"))
        amb.preparar()
        inicio = amb.inicio("apaga")
        amb.apagar("Inbox/Livros.md")
        amb.rodar("ponto", "--token", inicio["token"], "--rotulo", "apaga", "Inbox/Livros.md")
        amb.rodar("fim", "--token", inicio["token"])
        amb.escrever("Inbox/livros.md", nota("livros"))
        token = amb.inicio("desfaz")["token"]
        feito = amb.rodar("desfazer", "--token", token, "--pedido", inicio["pedido"], "--aplicar", "--aceitar",
                          "Inbox/Livros.md")
        if os.path.normcase("A") == "a":
            assert feito["nome_ocupado"] == [{"arquivo": "Inbox/Livros.md", "ocupado_por": "Inbox/livros.md"}], feito
            assert "Inbox/Livros.md" not in feito["pulados_por_conflito"], feito
    finally:
        amb.fechar()


def test_aviso_que_perdeu_a_trava_responde_json():
    import subprocess, sys
    amb = Ambiente()
    try:
        amb.preparar()
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from lib import trava
        atual = trava.pegar(amb.historico, "aviso do início da sessão", "aviso:S9")
        trava.forcar(amb.historico)
        trava.pegar(amb.historico, "outro", "S9")
        try:
            trava.soltar(amb.historico, atual["token"])
        except trava.TokenInvalido:
            pass
        resposta = amb.rodar("aviso", "--sessao", "S9")
        assert "pedido desta sessão" in resposta["linha"], resposta
    finally:
        amb.fechar()


def test_pedidos_por_nota_lista_so_a_nota():
    amb = Ambiente()
    try:
        amb.preparar()
        pedidos = amb.rodar("pedidos", "--nota", "Início.md", "--todos")["pedidos"]
        assert pedidos and all(p["arquivos"] == ["Início.md"] for p in pedidos), pedidos
    finally:
        amb.fechar()


def test_situacao_aponta_historico_de_vault_que_sumiu():
    amb = Ambiente()
    try:
        amb.preparar()
        novo = os.path.join(amb.raiz, "Vault Novo")
        shutil.move(amb.vault, novo)
        resposta = amb.rodar("situacao", "--vault", novo, cwd=amb.raiz)
        assert resposta["historicos_de_vaults_que_sumiram"] == [
            {"vault": amb.vault, "historico": amb.historico}], resposta
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
