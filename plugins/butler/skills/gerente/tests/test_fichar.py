"""Fichar: as listas de destino declaradas na nota de regras e o ciclo dentro do pedido da triagem."""
import json

from apoio import REGRAS, Ambiente, nota, rodar_testes

LISTAS = """## Listas para fichar

- filme: `Lazer/Filmes para Assistir.md` — um item por filme
- viagem: `Viagens/<destino>.md` — a nota da viagem com o mesmo destino
- Receita: `Casa/Receitas.md`
- sem código, só texto

"""
LISTAS_TITULO_ANTIGO = LISTAS.replace("## Listas para fichar", "## Listas da colheita")
REGISTRO = nota("Registro de Links", "| Código | Status | Destino (nota) | Registrado em |\n|---|---|---|---|\n")


def _com_listas(texto=LISTAS):
    amb = Ambiente()
    amb.escrever("Sistema/Regras do Butler.md", REGRAS.replace("## Caminhos", texto + "## Caminhos"))
    return amb


def test_situacao_traz_as_listas_para_fichar():
    amb = _com_listas()
    try:
        amb.preparar()
        regras = amb.rodar("situacao")["regras"]
        assert regras["colheita"] == {"filme": "Lazer/Filmes para Assistir.md", "viagem": "Viagens/<destino>.md",
                                      "receita": "Casa/Receitas.md"}, regras["colheita"]
    finally:
        amb.fechar()


def test_titulo_antigo_listas_da_colheita_ainda_e_lido():
    amb = _com_listas(LISTAS_TITULO_ANTIGO)
    try:
        amb.preparar()
        regras = amb.rodar("situacao")["regras"]
        assert regras["colheita"] == {"filme": "Lazer/Filmes para Assistir.md", "viagem": "Viagens/<destino>.md",
                                      "receita": "Casa/Receitas.md"}, regras["colheita"]
    finally:
        amb.fechar()


def test_sem_a_secao_a_colheita_fica_vazia():
    amb = Ambiente()
    try:
        amb.preparar()
        assert amb.rodar("situacao")["regras"]["colheita"] == {}
    finally:
        amb.fechar()


def test_pedido_que_mexe_numa_lista_guarda_colhidos_e_o_desfazer_mantem_edicao_posterior():
    """O contrato que a skill usa: a lista entra no ponto da triagem, `colhidos` vai para o estado.json e o desfazer
    do pedido tira só o item, mantendo o que o usuário escreveu depois. A releitura da lista antes de gravar (edição
    durante o pedido) é da skill e não tem como ser testada aqui."""
    amb = _com_listas()
    try:
        amb.escrever("Lazer/Filmes para Assistir.md", nota("Filmes para Assistir", "- Filme A (2001)"))
        amb.escrever("Sistema/Registro de Links.md", REGISTRO)
        amb.preparar()
        inicio = amb.inicio("triagem do Inbox")
        token = inicio["token"]
        lista = amb.ler("Lazer/Filmes para Assistir.md")
        amb.escrever("Lazer/Filmes para Assistir.md", lista.replace("- Filme A (2001)",
                                                                    "- Filme A (2001)\n- Filme B (2010)"))
        amb.escrever("Sistema/Registro de Links.md",
                     amb.ler("Sistema/Registro de Links.md").replace(
                         "|---|---|---|---|\n", "|---|---|---|---|\n| ABCDE12 | colhido | Filmes para Assistir | "
                                                "2026-01-02 |\n"))
        amb.rodar("ponto", "--token", token, "--rotulo", "triagem: Filmes para Assistir", "Lazer/Filmes para Assistir.md",
                  "Sistema/Registro de Links.md")
        colhido = {"url": "https://www.instagram.com/reel/ABCDE12/", "classificacao": "filme",
                   "nota": "Lazer/Filmes para Assistir.md"}
        amb.rodar("fim", "--token", token, "--resumo", "-",
                  entrada=json.dumps({"notas": [{"acao": "alterada", "para": "Lazer/Filmes para Assistir.md"}],
                                      "colhidos": [colhido]}).encode("utf-8"))
        assert amb.estado()["ultimo_pedido"]["colhidos"] == [colhido]

        # Depois, o usuário acrescenta outro filme no topo da lista, pelo Obsidian.
        texto = amb.ler("Lazer/Filmes para Assistir.md")
        amb.escrever("Lazer/Filmes para Assistir.md", texto.replace("- Filme A (2001)", "- Filme Z (1999)\n\n"
                                                                    "- Filme A (2001)"))
        desfaz = amb.inicio("desfaz a última triagem")["token"]
        feito = amb.rodar("desfazer", "--token", desfaz, "--pedido", inicio["pedido"], "--aplicar")
        assert feito["pulados_por_conflito"] == [], feito
        texto = amb.ler("Lazer/Filmes para Assistir.md")
        assert "Filme B" not in texto and "Filme Z (1999)" in texto and "Filme A (2001)" in texto
        assert "ABCDE12" not in amb.ler("Sistema/Registro de Links.md")
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
