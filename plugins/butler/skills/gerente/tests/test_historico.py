"""Histórico fora do vault, mudanças de fora e pontos de retorno."""
import os
import subprocess

from apoio import Ambiente, nota, rodar_testes


def test_preparar_cria_historico_fora_do_vault_sem_arquivo_no_vault():
    amb = Ambiente()
    try:
        antes = sorted(os.listdir(amb.vault))
        resposta = amb.preparar()
        assert resposta["historico_ok"], resposta
        assert sorted(os.listdir(amb.vault)) == antes
        for raiz, pastas, nomes in os.walk(amb.vault):
            assert ".git" not in pastas and ".gitignore" not in nomes
        assert "Veículo/Histórico de Manutenção.md" in amb.git("ls-files")
        assert amb.estado()["historico"]["ok"] is True
    finally:
        amb.fechar()


def test_preparar_de_novo_so_confere():
    amb = Ambiente()
    try:
        amb.preparar()
        de_novo = amb.preparar()
        assert de_novo["ja_existia"] and de_novo["foto_inicial"] is None
        assert amb.git("rev-list", "--count", "HEAD").strip() == "1"
    finally:
        amb.fechar()


def test_pasta_proibida_dentro_do_vault_ou_sincronizada():
    amb = Ambiente()
    try:
        dentro = amb.rodar("preparar-historico", "--vault", amb.vault, "--historico",
                           os.path.join(amb.vault, "hist"), esperado=2)
        assert "dentro do vault" in dentro["erro"]
        drive = amb.rodar("preparar-historico", "--vault", amb.vault, "--historico",
                          os.path.join(amb.raiz, "Google Drive", "hist"), esperado=2)
        assert "sincronizada" in drive["erro"]
        temp = amb.rodar("preparar-historico", "--vault", amb.vault, "--historico",
                         os.path.join(amb.raiz, "hist"), esperado=2, BUTLER_PERMITIR_TEMP="0")
        assert "temporária" in temp["erro"]
    finally:
        amb.fechar()


def test_sem_preparar_e_sem_historico_e_diz_o_motivo():
    amb = Ambiente()
    try:
        resposta = amb.inicio()
        assert resposta["historico_ok"] is False and "preparar" in resposta["motivo"]
        assert amb.rodar("pedidos", esperado=4)["historico_ok"] is False
    finally:
        amb.fechar()


def test_regras_ausentes_derrubam_o_historico():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.apagar("Sistema/Regras do Butler.md")
        resposta = amb.inicio()
        assert resposta["historico_ok"] is False and "Regras do Butler" in resposta["motivo"]
    finally:
        amb.fechar()


def test_mudanca_de_fora_vira_ponto_proprio_antes_do_pedido():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Inbox/Nova ideia.md", nota("Nova ideia"))
        resposta = amb.inicio("triagem")
        fora = resposta["mudancas_de_fora"]
        assert fora["ponto"] and {"estado": "novo", "arquivo": "Inbox/Nova ideia.md"} in fora["arquivos"]
        assert "[fora]" in amb.git("log", "-1", "--format=%s")
        assert amb.git("status", "--porcelain").strip() == ""
    finally:
        amb.fechar()


def test_ponto_grava_so_os_arquivos_listados():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio("triagem")["token"]
        amb.escrever("Inbox/A.md", nota("A"))
        amb.escrever("Inbox/B.md", nota("B"))
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "triagem: A", "Inbox/A.md")
        assert resposta["gravados"] == ["Inbox/A.md"]
        assert "Inbox/A.md" in amb.git("ls-files") and "Inbox/B.md" not in amb.git("ls-files")
    finally:
        amb.fechar()


def test_ponto_grava_movimento_pelos_dois_caminhos():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Mover.md", nota("Mover"))
        amb.preparar()
        token = amb.inicio("triagem")["token"]
        os.makedirs(amb.caminho("Casa"))
        os.replace(amb.caminho("Inbox/Mover.md"), amb.caminho("Casa/Mover.md"))
        amb.rodar("ponto", "--token", token, "--rotulo", "move", "Inbox/Mover.md", "Casa/Mover.md")
        arquivos = amb.git("ls-files")
        assert "Casa/Mover.md" in arquivos and "Inbox/Mover.md" not in arquivos
    finally:
        amb.fechar()


def test_crlf_bom_e_acentos_ficam_identicos():
    amb = Ambiente()
    try:
        conteudo = (chr(0xFEFF) + "---\r\ntitle: Ação\r\n---\r\n\r\nLinha com CRLF e ç\r\n").encode("utf-8")
        amb.escrever("Notas/Ação Çedilha.md", conteudo, binario=True)
        amb.preparar()
        guardado = subprocess.run(["git", f"--git-dir={os.path.join(amb.historico, 'git')}", "cat-file", "blob",
                                   "HEAD:Notas/Ação Çedilha.md"], capture_output=True, check=True).stdout
        assert guardado == conteudo
    finally:
        amb.fechar()


def test_remoto_configurado_derruba_o_historico():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.git("remote", "add", "origin", "https://example.invalid/x.git")
        resposta = amb.rodar("situacao")
        assert resposta["historico_ok"] is False and "remoto" in resposta["motivo"]
    finally:
        amb.fechar()


def test_vault_achado_com_outra_grafia_e_de_subpasta():
    amb = Ambiente()
    try:
        amb.preparar()
        resposta = amb.rodar("situacao", cwd=amb.caminho("Veículo"))
        assert resposta["historico_ok"], resposta
        if os.name == "nt":
            outra = amb.rodar("situacao", "--vault", amb.vault.upper().replace("\\", "/"))
            assert outra["historico_ok"], outra
    finally:
        amb.fechar()


def test_index_lock_orfao_nao_trava_o_pedido():
    amb = Ambiente()
    try:
        amb.preparar()
        trava = os.path.join(amb.historico, "git", "index.lock")
        open(trava, "w").close()
        velho = os.path.getmtime(trava) - 3600
        os.utime(trava, (velho, velho))
        amb.escrever("Inbox/X.md", nota("X"))
        resposta = amb.inicio()
        assert resposta["historico_ok"] and resposta["mudancas_de_fora"]["ponto"], resposta
    finally:
        amb.fechar()


def test_renomeacao_so_de_maiusculas_aparece():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/nota baixa.md", nota("nota baixa"))
        amb.preparar()
        os.replace(amb.caminho("Inbox/nota baixa.md"), amb.caminho("Inbox/Nota Baixa.md"))
        fora = amb.inicio()["mudancas_de_fora"]
        estados = {(i["estado"], i["arquivo"]) for i in fora["arquivos"]}
        assert ("novo", "Inbox/Nota Baixa.md") in estados, estados
        assert ("apagado", "Inbox/nota baixa.md") in estados, estados
        assert "Inbox/Nota Baixa.md" in amb.git("ls-files") and "Inbox/nota baixa.md" not in amb.git("ls-files")
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
