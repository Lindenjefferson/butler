"""Revisão: árvore de pastas, sugestão para link quebrado, alvo citado por várias notas, possíveis duplicatas,
links em Markdown e binários liberados por pasta."""
from apoio import REGRAS, Ambiente, nota, rodar_testes


def _achados(resposta, arquivo):
    for item in resposta["notas"]:
        if item["arquivo"] == arquivo:
            return item["achados"]
    return []


def test_arvore_conta_as_notas_de_cada_pasta():
    amb = Ambiente()
    try:
        amb.escrever("Casa/Cozinha/Fogão.md", nota("Fogão"))
        resposta = amb.rodar("revisar")
        arvore = {item["pasta"]: item["notas"] for item in resposta["arvore"]}
        assert arvore[""] == 2  # Início.md e CLAUDE.md
        assert arvore["Inbox"] == 0 and arvore["Casa"] == 0 and arvore["Casa/Cozinha"] == 1
        assert arvore["Inventários"] == 1 and ".obsidian" not in arvore
    finally:
        amb.fechar()


def test_link_quebrado_sugere_a_nota_parecida():
    amb = Ambiente()
    try:
        amb.escrever("Casa/Cozinha.md", nota("Cozinha", "Ver [[Geladera]] e [[Nada Parecido Aqui]]"))
        achados = [a for a in _achados(amb.rodar("revisar"), "Casa/Cozinha.md") if a["codigo"] == "link_quebrado"]
        por_alvo = {a["alvo"]: a for a in achados}
        assert por_alvo["Geladera"]["sugestao"] == "Geladeira"
        assert "Geladeira" in por_alvo["Geladera"]["mensagem"]
        assert por_alvo["Nada Parecido Aqui"].get("sugestao") is None
    finally:
        amb.fechar()


def test_alvo_citado_por_tres_notas_vira_candidato_a_nota():
    amb = Ambiente()
    try:
        for nome in ("A", "B", "C"):
            amb.escrever(f"Casa/{nome}.md", nota(nome, "Ver [[Fogão a Lenha]]"))
        amb.escrever("Casa/D.md", nota("D", "Ver [[Só Uma Vez]]"))
        recorrentes = amb.rodar("revisar")["links_quebrados_recorrentes"]
        assert recorrentes == [{"alvo": "Fogão a Lenha", "notas": ["Casa/A.md", "Casa/B.md", "Casa/C.md"]}]
    finally:
        amb.fechar()


def test_possiveis_duplicatas_por_titulo_e_por_source():
    amb = Ambiente()
    try:
        amb.escrever("Casa/Geladeira.md", nota("Geladeira"))
        url = 'source: "https://exemplo.com/artigo"\n'
        amb.escrever("Recursos/Artigo um.md", nota("Artigo um").replace("source: teste\n", url))
        amb.escrever("Recursos/Artigo dois.md", nota("Artigo dois").replace("source: teste\n", url))
        duplicatas = amb.rodar("revisar")["possiveis_duplicatas"]
        assert {"motivo": "mesmo título", "notas": ["Casa/Geladeira.md", "Inventários/Geladeira.md"]} in duplicatas
        assert {"motivo": "mesmo source", "notas": ["Recursos/Artigo dois.md", "Recursos/Artigo um.md"]} \
            in duplicatas
        assert len(duplicatas) == 2  # `source: teste` das outras notas não é link
    finally:
        amb.fechar()


def test_vault_com_links_em_markdown_avisa_na_revisao_e_no_renomear():
    amb = Ambiente()
    try:
        assert amb.rodar("revisar")["links_markdown"] is False
        amb.escrever(".obsidian/app.json", '{"useMarkdownLinks": true}')
        amb.preparar()
        assert amb.rodar("revisar")["links_markdown"] is True
        token = amb.inicio("renomeia", sessao="s")["token"]
        resposta = amb.rodar("renomear", "--token", token, "Inventários/Geladeira.md", "Inventários/Geladeira 2.md")
        assert resposta["links_markdown"] is True
    finally:
        amb.fechar()


def test_binario_liberado_por_pasta_entra_no_historico():
    amb = Ambiente()
    try:
        regras = REGRAS.replace("## Liberações de dado sensível\n",
                                "## Liberações de dado sensível\n\n- `Anexos/**` — prints e PDFs\n")
        amb.escrever("Sistema/Regras do Butler.md", regras)
        amb.preparar()
        token = amb.inicio("anexa", sessao="s")["token"]
        amb.escrever("Anexos/2026/print.png", b"\x89PNG\x00\x01", binario=True)
        amb.escrever("Outra/foto.png", b"\x89PNG\x00\x02", binario=True)
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "anexa", "Anexos/2026/print.png",
                             "Outra/foto.png")
        assert resposta["gravados"] == ["Anexos/2026/print.png"]
        assert [r["arquivo"] for r in resposta["recusados"]] == ["Outra/foto.png"]
    finally:
        amb.fechar()


def test_binario_liberado_por_pasta_entra_pelas_mudancas_de_fora():
    amb = Ambiente()
    try:
        regras = REGRAS.replace("## Liberações de dado sensível\n",
                                "## Liberações de dado sensível\n\n- `Anexos/**` — prints e PDFs\n")
        amb.escrever("Sistema/Regras do Butler.md", regras)
        amb.preparar()
        amb.escrever("Anexos/colado.png", b"\x89PNG\x00\x03", binario=True)
        amb.escrever("Outra/foto.png", b"\x89PNG\x00\x04", binario=True)
        fora = amb.inicio("anexa", sessao="s")["mudancas_de_fora"]["fora_do_historico"]
        assert [item["arquivo"] for item in fora] == ["Outra/foto.png"]
        assert "Anexos/colado.png" in amb.git("ls-files")
    finally:
        amb.fechar()


def test_liberacao_por_pasta_nao_libera_dado_sensivel_em_texto():
    amb = Ambiente()
    try:
        regras = REGRAS.replace("## Liberações de dado sensível\n",
                                "## Liberações de dado sensível\n\n- `Anexos/**` — prints e PDFs\n")
        amb.escrever("Sistema/Regras do Butler.md", regras)
        amb.preparar()
        token = amb.inicio("anexa", sessao="s")["token"]
        amb.escrever("Anexos/senha.md", nota("senha", "cartão 4111 1111 1111 1111"))
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "anexa", "Anexos/senha.md")
        assert resposta["gravados"] == [] and resposta["recusados"][0]["motivo"] == "dado sensível"
    finally:
        amb.fechar()


def test_link_quebrado_nunca_sugere_o_claude_md():
    amb = Ambiente()
    try:
        amb.escrever("Casa/Cozinha.md", nota("Cozinha", "Ver [[Claud]]"))
        achados = [a for a in _achados(amb.rodar("revisar"), "Casa/Cozinha.md") if a["codigo"] == "link_quebrado"]
        assert achados and achados[0].get("sugestao") is None
    finally:
        amb.fechar()


def test_excecao_aprendida_cala_o_link_recorrente():
    amb = Ambiente()
    try:
        regras = REGRAS.replace("## Exceções aprendidas\n", "## Exceções aprendidas\n\n"
                                "- `Casa/**` `link_quebrado_recorrente` — o alvo ainda vai virar nota\n")
        amb.escrever("Sistema/Regras do Butler.md", regras)
        for nome in ("A", "B", "C"):
            amb.escrever(f"Casa/{nome}.md", nota(nome, "Ver [[Fogão a Lenha]]"))
        assert amb.rodar("revisar")["links_quebrados_recorrentes"] == []
    finally:
        amb.fechar()


def test_pasta_de_nome_hexadecimal_libera_os_binarios():
    amb = Ambiente()
    try:
        regras = REGRAS.replace("## Liberações de dado sensível\n", "## Liberações de dado sensível\n\n"
                                "- `a1b2c3d4e5f6a7b8` — export do app\n- `a1b2c3d4e5f6` — outro export\n")
        amb.escrever("Sistema/Regras do Butler.md", regras)
        amb.preparar()
        token = amb.inicio("anexa", sessao="s")["token"]
        amb.escrever("a1b2c3d4e5f6a7b8/print.png", b"\x89PNG\x00\x05", binario=True)
        amb.escrever("a1b2c3d4e5f6/foto.png", b"\x89PNG\x00\x06", binario=True)
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "anexa", "a1b2c3d4e5f6a7b8/print.png",
                             "a1b2c3d4e5f6/foto.png")
        assert sorted(resposta["gravados"]) == ["a1b2c3d4e5f6/foto.png", "a1b2c3d4e5f6a7b8/print.png"], resposta
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
