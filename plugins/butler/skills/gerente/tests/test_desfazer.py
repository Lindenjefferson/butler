"""Desfazer por pedido (mescla de três vias), voltar uma nota a uma data e renomear com os links."""
import datetime
import time

from apoio import Ambiente, nota, rodar_testes


def _triagem(amb):
    """Um pedido que move uma nota do Inbox, cria outra, apaga uma terceira e mexe no Início."""
    amb.escrever("Inbox/Mover.md", nota("Mover"))
    amb.escrever("Inbox/Apagar.md", nota("Apagar"))
    amb.preparar()
    inicio = amb.inicio("triagem do Inbox")
    token = inicio["token"]
    amb.escrever("Casa/Mover.md", amb.ler("Inbox/Mover.md"))
    amb.apagar("Inbox/Mover.md")
    amb.rodar("ponto", "--token", token, "--rotulo", "triagem: Mover", "Inbox/Mover.md", "Casa/Mover.md")
    amb.escrever("Casa/Criada.md", nota("Criada"))
    amb.apagar("Inbox/Apagar.md")
    amb.escrever("Início.md", amb.ler("Início.md") + "- [[Mover]]\n- [[Criada]]\n")
    amb.rodar("ponto", "--token", token, "--rotulo", "triagem: Criada", "Casa/Criada.md", "Inbox/Apagar.md",
              "Início.md")
    amb.rodar("fim", "--token", token)
    return inicio["pedido"]


def test_desfazer_um_pedido_volta_tudo():
    amb = Ambiente()
    try:
        pedido = _triagem(amb)
        listados = amb.rodar("pedidos")["pedidos"]
        assert listados[0]["pedido"] == pedido and listados[0]["pontos"] == 2
        token = amb.inicio("desfaz")["token"]
        plano = amb.rodar("desfazer", "--token", token, "--pedido", pedido)["plano"]
        acoes = {i["arquivo"]: i["acao"] for i in plano["itens"]}
        assert acoes == {"Inbox/Mover.md": "recriar", "Casa/Mover.md": "apagar", "Casa/Criada.md": "apagar",
                         "Inbox/Apagar.md": "recriar", "Início.md": "restaurar"}, acoes
        assert amb.existe("Casa/Criada.md")
        feito = amb.rodar("desfazer", "--token", token, "--pedido", pedido, "--aplicar")
        assert feito["pulados_por_conflito"] == [] and feito["ponto"]
        assert amb.existe("Inbox/Mover.md") and amb.existe("Inbox/Apagar.md")
        assert not amb.existe("Casa/Mover.md") and not amb.existe("Casa")
        assert "[[Criada]]" not in amb.ler("Início.md")
        assert "[desfaz]" in amb.git("log", "-1", "--format=%s")
    finally:
        amb.fechar()


def test_mudanca_posterior_em_outro_trecho_fica():
    amb = Ambiente()
    try:
        pedido = _triagem(amb)
        amb.escrever("Início.md", "- [[Topo novo]]\n" + amb.ler("Início.md"))
        token = amb.inicio("desfaz")["token"]
        plano = amb.rodar("desfazer", "--token", token, "--pedido", pedido)["plano"]
        inicio = [i for i in plano["itens"] if i["arquivo"] == "Início.md"][0]
        assert inicio["conflito"] is False
        amb.rodar("desfazer", "--token", token, "--pedido", pedido, "--aplicar")
        texto = amb.ler("Início.md")
        assert "[[Topo novo]]" in texto and "[[Criada]]" not in texto
    finally:
        amb.fechar()


def test_mudanca_posterior_no_mesmo_trecho_e_conflito():
    amb = Ambiente()
    try:
        pedido = _triagem(amb)
        amb.escrever("Início.md", amb.ler("Início.md").replace("- [[Criada]]", "- [[Criada]] (revisada)"))
        amb.escrever("Casa/Criada.md", amb.ler("Casa/Criada.md") + "\nmais texto\n")
        token = amb.inicio("desfaz")["token"]
        feito = amb.rodar("desfazer", "--token", token, "--pedido", pedido, "--aplicar")
        assert sorted(feito["pulados_por_conflito"]) == ["Casa/Criada.md", "Início.md"]
        assert "(revisada)" in amb.ler("Início.md") and amb.existe("Casa/Criada.md")
        assert amb.existe("Inbox/Mover.md")
        aceito = amb.rodar("desfazer", "--token", token, "--pedido", pedido, "--aplicar", "--aceitar", "Início.md")
        assert aceito["aplicados"] == ["Início.md"] and "[[Criada]]" not in amb.ler("Início.md")
    finally:
        amb.fechar()


def test_voltar_nota_a_uma_data_lista_as_mudancas_posteriores():
    amb = Ambiente()
    try:
        amb.preparar()
        original = amb.ler("Inventários/Geladeira.md")
        time.sleep(1.1)
        marco = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        time.sleep(1.1)
        token = amb.inicio("altera")["token"]
        amb.escrever("Inventários/Geladeira.md", original.replace("127V", "220V"))
        amb.rodar("ponto", "--token", token, "--rotulo", "voltagem", "Inventários/Geladeira.md")
        plano = amb.rodar("desfazer", "--token", token, "--nota", "Inventários/Geladeira.md", "--ate", marco)["plano"]
        assert len(plano["mudancas_posteriores"]) == 1 and plano["itens"][0]["acao"] == "restaurar"
        amb.rodar("desfazer", "--token", token, "--nota", "Inventários/Geladeira.md", "--ate", marco, "--aplicar",
                  "--aceitar", "Inventários/Geladeira.md")
        assert amb.ler("Inventários/Geladeira.md") == original
        antes_de_tudo = amb.rodar("desfazer", "--token", token, "--nota", "Inventários/Geladeira.md", "--ate",
                                  "2000-01-01", esperado=2)
        assert "não há ponto" in antes_de_tudo["erro"]
    finally:
        amb.fechar()


def test_renomear_atualiza_links_com_apelido_e_secao():
    amb = Ambiente()
    try:
        amb.escrever("Casa/Usa.md", nota("Usa", "Ver [[Geladeira|a geladeira]], [[Geladeira#Voltagem]] e "
                                               "![[Inventários/Geladeira]]", links=("Geladeira",)))
        amb.preparar()
        token = amb.inicio("renomeia")["token"]
        resposta = amb.rodar("renomear", "--token", token, "Inventários/Geladeira.md", "Inventários/Refrigerador.md")
        assert sorted(resposta["links_atualizados"]) == ["Casa/Usa.md", "Início.md"]
        texto = amb.ler("Casa/Usa.md")
        assert "[[Refrigerador|a geladeira]]" in texto and "[[Refrigerador#Voltagem]]" in texto
        assert "![[Refrigerador]]" in texto and "- [[Refrigerador]]" in texto
        assert amb.git("status", "--porcelain").strip() == ""
        assert amb.rodar("renomear", "--token", token, "Casa/Usa.md", "Início.md", esperado=2)
    finally:
        amb.fechar()


def test_renomear_nao_mexe_em_link_dentro_de_codigo():
    amb = Ambiente()
    try:
        corpo = "Sintaxe: `[[Geladeira]]`\n\n```\n[[Geladeira]]\n```\n\nDe verdade: [[Geladeira]]"
        amb.escrever("Casa/Guia.md", nota("Guia", corpo))
        amb.preparar()
        token = amb.inicio("renomeia")["token"]
        amb.rodar("renomear", "--token", token, "Inventários/Geladeira.md", "Inventários/Refrigerador.md")
        texto = amb.ler("Casa/Guia.md")
        assert "Sintaxe: `[[Geladeira]]`" in texto and "```\n[[Geladeira]]\n```" in texto
        assert "De verdade: [[Refrigerador]]" in texto
    finally:
        amb.fechar()


def test_renomear_nao_toma_link_solto_de_nota_homonima():
    amb = Ambiente()
    try:
        amb.escrever("Doces/Bolo.md", nota("Bolo"))
        amb.escrever("Salgados/Bolo.md", nota("Bolo"))
        amb.escrever("Casa/Cardápio.md", nota("Cardápio", "Solto: [[Bolo]]. Com caminho: [[Doces/Bolo]] e [[Salgados/Bolo]]."))
        amb.preparar()
        token = amb.inicio("renomeia")["token"]
        resposta = amb.rodar("renomear", "--token", token, "Doces/Bolo.md", "Doces/Torta.md")
        texto = amb.ler("Casa/Cardápio.md")
        # o solto pode ser de qualquer um dos dois: fica como está e a nota sai na lista para a pessoa conferir
        assert "Solto: [[Bolo]]." in texto and "[[Torta]] e [[Salgados/Bolo]]" in texto
        assert resposta["links_ambiguos"] == ["Casa/Cardápio.md"]
    finally:
        amb.fechar()


def test_renomear_nao_regrava_nota_que_nao_e_utf8():
    amb = Ambiente()
    try:
        latin = "café com [[Geladeira]]\n".encode("latin-1")
        amb.escrever("Casa/Latin.md", latin, binario=True)
        amb.preparar()
        token = amb.inicio("renomeia")["token"]
        resposta = amb.rodar("renomear", "--token", token, "Inventários/Geladeira.md", "Inventários/Refrigerador.md")
        with open(amb.caminho("Casa/Latin.md"), "rb") as arquivo:
            assert arquivo.read() == latin
        assert resposta["links_nao_conferidos"] == ["Casa/Latin.md"]
        assert "Casa/Latin.md" not in resposta["links_atualizados"]
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
