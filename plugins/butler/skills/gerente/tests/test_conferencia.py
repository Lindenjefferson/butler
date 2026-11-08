"""Conferência do toque, avisos das mudanças de fora e revisão do vault."""
import os
import unicodedata

from apoio import Ambiente, nota, rodar_testes


def achados(amb, caminho):
    return [a["codigo"] for a in amb.rodar("conferir", caminho)["notas"][0]["achados"]]


def test_nota_certa_nao_tem_achado_e_bom_nao_atrapalha():
    amb = Ambiente()
    try:
        assert achados(amb, "Veículo/Histórico de Manutenção.md") == []
        assert achados(amb, "Início.md") == []
        resposta = amb.rodar("conferir", "Veículo/Histórico de Manutenção.md")["notas"][0]
        assert resposta["protegida"] is True and resposta["rigida"] is False
        assert amb.rodar("conferir", "Inventários/Geladeira.md")["notas"][0]["rigida"] is True
    finally:
        amb.fechar()


def test_achados_da_conferencia():
    amb = Ambiente()
    try:
        amb.escrever("Inbox/Sem frontmatter.md", "# Solta\n\ntexto\n")
        assert set(achados(amb, "Inbox/Sem frontmatter.md")) == {"sem_frontmatter", "sem_veja_tambem"}
        amb.escrever("Inbox/Nome.md", nota("Outro título"))
        assert achados(amb, "Inbox/Nome.md") == ["titulo_diferente"]
        amb.escrever("Inbox/Dois pontos.md", nota("Dois: pontos"))
        assert achados(amb, "Inbox/Dois pontos.md") == []
        amb.escrever("Inbox/Links.md", nota("Links", "[[Geladeira|a geladeira]] [[Geladeira#Voltagem]] "
                                                  "`[[No código]]` [[Inventários/Geladeira]]", links=("Sumiu",)))
        resposta = amb.rodar("conferir", "Inbox/Links.md")["notas"][0]["achados"]
        assert [(a["codigo"], a.get("alvo")) for a in resposta] == [("link_quebrado", "Sumiu")]
        amb.escrever("Inbox/Aberto.md", "---\ntitle: Aberto\n\n# sem fechar\n")
        assert "frontmatter_invalido" in achados(amb, "Inbox/Aberto.md")
    finally:
        amb.fechar()


def test_excecao_aprendida_cala_o_achado():
    amb = Ambiente()
    try:
        amb.escrever("Início.md", "---\ntitle: Início\n---\n\n# Início\n")
        assert achados(amb, "Início.md") == []
        amb.escrever("Outra.md", "---\ntitle: Outra\n---\n\n# Outra\n")
        assert achados(amb, "Outra.md") == ["sem_veja_tambem"]
    finally:
        amb.fechar()


def test_avisos_das_mudancas_de_fora():
    amb = Ambiente()
    try:
        amb.preparar()
        historico = amb.ler("Veículo/Histórico de Manutenção.md")
        amb.escrever("Veículo/Histórico de Manutenção.md", historico.replace("- 2026-03-02 pneus\n", ""))
        amb.escrever("Inventários/Geladeira.md", amb.ler("Inventários/Geladeira.md") + "\n- Cor: branca\n")
        amb.escrever("Inbox/Ideia (1).md", nota("Ideia (1)"))
        amb.escrever("CLAUDE.md", amb.ler("CLAUDE.md") + "\nRegra nova.\n")
        fora = amb.inicio()["mudancas_de_fora"]
        assert fora["protegidas_com_remocao"] == ["Veículo/Histórico de Manutenção.md"], fora
        assert fora["copias_conflito"] == ["Inbox/Ideia (1).md"]
        assert fora["regras_mudaram"] == ["CLAUDE.md"]
        estado = amb.estado()
        assert estado["avisos"]["protegidas_com_remocao"] == ["Veículo/Histórico de Manutenção.md"]
    finally:
        amb.fechar()


def test_protegida_apagada_por_fora_avisa():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.apagar("Inventários/Geladeira.md")
        fora = amb.inicio()["mudancas_de_fora"]
        assert fora["protegidas_com_remocao"] == ["Inventários/Geladeira.md"]
    finally:
        amb.fechar()


def test_aviso_do_inicio_da_sessao():
    amb = Ambiente()
    try:
        assert amb.rodar("aviso", cwd=amb.raiz, BUTLER_CONFIG=amb.config)["vault_do_butler"] is False
        amb.preparar()
        amb.escrever("Inbox/A.md", nota("A"))
        resposta = amb.rodar("aviso")
        linha = resposta["linha"]
        assert linha.startswith("Butler: Inbox com 1 nota") and "1 pendência" in linha and "histórico ok" in linha
        assert "Inbox/A.md" in amb.git("ls-files")
        so_leitura = amb.rodar("aviso", BUTLER_SO_LEITURA="1")
        assert so_leitura["mudancas_de_fora"] is None
    finally:
        amb.fechar()


def test_revisar_relata_sem_corrigir():
    amb = Ambiente()
    try:
        os.makedirs(amb.caminho("Vazia/Sub"))
        amb.escrever("Casa/Solta.md", nota("Solta", links=("Inexistente",)))
        nfd = unicodedata.normalize("NFD", "Casa/Decomposição.md")
        amb.escrever(nfd, nota(unicodedata.normalize("NFD", "Decomposição")))
        amb.escrever("Casa/Solta (1).md", nota("Solta (1)"))
        antes = sorted(os.listdir(amb.vault))
        relatorio = amb.rodar("revisar")
        assert sorted(os.listdir(amb.vault)) == antes
        assert "Vazia" in relatorio["pastas_vazias"] and "Inbox" not in relatorio["pastas_vazias"]
        assert relatorio["copias_conflito"] == ["Casa/Solta (1).md"]
        assert relatorio["nomes_nfd"] == [nfd]
        assert "Casa/Solta.md" in relatorio["fora_do_indice"]
        assert "Veículo/Histórico de Manutenção.md" not in relatorio["fora_do_indice"]
        com_link = [n for n in relatorio["notas"] if n["arquivo"] == "Casa/Solta.md"][0]
        assert [a["codigo"] for a in com_link["achados"]] == ["link_quebrado"]
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
