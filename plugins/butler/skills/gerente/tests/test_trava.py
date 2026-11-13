"""Um pedido por vez: trava atômica, retomada pela mesma sessão, token, fim e estado.json."""
import datetime
import json
import os
import subprocess
import sys
import threading

from apoio import BUTLER, REGRAS, Ambiente, rodar_testes


def _envelhecer_trava(amb, minutos):
    caminho = os.path.join(amb.historico, "trava.json")
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    dados["atualizado"] = (datetime.datetime.now().astimezone() - datetime.timedelta(minutes=minutos)).isoformat()
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo)


def test_segunda_sessao_acha_a_trava_e_nao_forca():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="sessao-a")
        resposta = amb.inicio("garimpo", sessao="sessao-b", esperado=3)
        trava = resposta["trava_ocupada"]
        assert trava["rotulo"] == "triagem" and "token" not in trava and trava["minutos_parada"] == 0
    finally:
        amb.fechar()


def test_mesma_sessao_retoma_a_trava_com_o_mesmo_pedido():
    amb = Ambiente()
    try:
        amb.preparar()
        primeiro = amb.inicio("triagem", sessao="sessao-a")
        segundo = amb.inicio("triagem", sessao="sessao-a")
        assert segundo["retomada"] and segundo["pedido"] == primeiro["pedido"]
        assert segundo["token"] == primeiro["token"]
    finally:
        amb.fechar()


def test_dois_inicios_em_paralelo_so_um_pega():
    amb = Ambiente()
    try:
        amb.preparar()
        codigos = []

        def rodar(nome):
            processo = subprocess.run([sys.executable, BUTLER, "inicio", "--rotulo", nome, "--sessao", nome],
                                      capture_output=True, cwd=amb.vault, env=amb.ambiente())
            codigos.append(processo.returncode)

        linhas = [threading.Thread(target=rodar, args=(f"s{i}",)) for i in range(4)]
        for linha in linhas:
            linha.start()
        for linha in linhas:
            linha.join()
        assert sorted(codigos) == [0, 3, 3, 3], codigos
    finally:
        amb.fechar()


def test_trava_abandonada_por_prazo_libera_sozinha_com_o_modo_declarado():
    amb = Ambiente()
    try:
        amb.escrever("Sistema/Regras do Butler.md", REGRAS.replace(
            "## Caminhos", "## Modo sem supervisão\n\n- trava abandonada depois de: `30 min`\n\n## Caminhos"))
        amb.preparar()
        amb.inicio("triagem", sessao="a")
        _envelhecer_trava(amb, 31)
        resposta = amb.inicio("garimpo", sessao="b")
        assert resposta["ok"] and resposta["trava_abandonada_por_prazo"]["rotulo"] == "triagem"
    finally:
        amb.fechar()


def test_trava_ainda_dentro_do_prazo_nao_libera_sozinha():
    amb = Ambiente()
    try:
        amb.escrever("Sistema/Regras do Butler.md", REGRAS.replace(
            "## Caminhos", "## Modo sem supervisão\n\n- trava abandonada depois de: `30 min`\n\n## Caminhos"))
        amb.preparar()
        amb.inicio("triagem", sessao="a")
        _envelhecer_trava(amb, 10)
        resposta = amb.inicio("garimpo", sessao="b", esperado=3)
        assert resposta["trava_ocupada"]["rotulo"] == "triagem"
    finally:
        amb.fechar()


def test_trava_abandonada_sem_o_modo_declarado_continua_exigindo_forcar():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="a")
        _envelhecer_trava(amb, 300)
        resposta = amb.inicio("garimpo", sessao="b", esperado=3)
        assert resposta["trava_ocupada"]["rotulo"] == "triagem"
    finally:
        amb.fechar()


def test_trava_corrompida_nao_entra_na_conta_do_prazo():
    amb = Ambiente()
    try:
        amb.escrever("Sistema/Regras do Butler.md", REGRAS.replace(
            "## Caminhos", "## Modo sem supervisão\n\n- trava abandonada depois de: `30 min`\n\n## Caminhos"))
        amb.preparar()
        with open(os.path.join(amb.historico, "trava.json"), "w") as arquivo:
            arquivo.write("{meio")
        resposta = amb.inicio("garimpo", sessao="b", esperado=3)
        assert resposta["trava_ocupada"]["corrompida"] is True
    finally:
        amb.fechar()


def test_token_errado_e_recusado():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio()
        resposta = amb.rodar("ponto", "--token", "errado", "--rotulo", "x", "Início.md", esperado=5)
        assert "token" in resposta["erro"]
    finally:
        amb.fechar()


def test_fim_solta_a_trava_e_grava_o_resumo_no_estado():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("garimpo")
        resumo = {"notas": [{"acao": "criada", "para": "Inbox/X.md"}],
                  "garimpo": [{"url": "https://example.com/a", "nota": "Inbox/X.md", "veredito": "✅",
                               "classificacao": "ideia de projeto", "destino_sugerido": "Ideias de Projetos"}],
                  "perguntas": [{"pergunta": "de quem é?", "proposta": "casal", "nota": "Inbox/X.md"}]}
        amb.rodar("fim", "--token", inicio["token"], "--resumo", "-", entrada=json.dumps(resumo).encode("utf-8"))
        estado = amb.estado()
        assert estado["trava"] is None and estado["versao"] == 1
        assert estado["ultimo_pedido"]["garimpo"][0]["veredito"] == "✅"
        assert estado["ultimo_pedido"]["rotulo"] == "garimpo"
        assert estado["perguntas"][0]["proposta"] == "casal"
        assert not os.path.exists(os.path.join(amb.historico, "trava.json"))
        amb.inicio("outro")
    finally:
        amb.fechar()


def test_estado_mostra_a_trava_sem_o_token():
    amb = Ambiente()
    try:
        amb.preparar()
        inicio = amb.inicio("triagem")
        texto = open(os.path.join(amb.historico, "estado.json"), encoding="utf-8").read()
        assert inicio["token"] not in texto
        assert json.loads(texto)["trava"]["rotulo"] == "triagem"
    finally:
        amb.fechar()


def test_liberar_trava_so_com_forcar_e_soltar_sessao_so_a_propria():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="a")
        assert amb.rodar("soltar-sessao", "--sessao", "b")["soltou"] is False
        amb.rodar("liberar-trava", esperado=2)
        assert amb.rodar("liberar-trava", "--forcar")["liberada"]["rotulo"] == "triagem"
        amb.inicio("garimpo", sessao="b")
        assert amb.rodar("soltar-sessao", "--sessao", "b")["soltou"] is True
    finally:
        amb.fechar()


def test_trava_corrompida_conta_como_ocupada():
    amb = Ambiente()
    try:
        amb.preparar()
        with open(os.path.join(amb.historico, "trava.json"), "w") as arquivo:
            arquivo.write("{meio")
        resposta = amb.inicio(esperado=3)
        assert resposta["trava_ocupada"]["corrompida"] is True
    finally:
        amb.fechar()


def test_aviso_nao_grava_com_pedido_em_andamento():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="a")
        amb.escrever("Inbox/Nova.md", "x")
        resposta = amb.rodar("aviso")
        assert "pedido em andamento: triagem" in resposta["linha"]
        assert "Inbox/Nova.md" not in amb.git("ls-files")
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
