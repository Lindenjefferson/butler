"""Nuvem conectada: o caminho declarado em `## Caminhos` e as pastas fora da varredura em `## Nuvem: pastas fora
da varredura`, ambos lidos pela nota de regras e expostos por `situacao`."""
from apoio import REGRAS, Ambiente

SECAO = """## Nuvem: pastas fora da varredura

- `G:\\Meu Drive\\Exames médicos` — dado de saúde
- `G:\\Meu Drive\\Documentos\\Lindemberg` — documento pessoal
- sem código, só texto

"""


def _com_nuvem():
    amb = Ambiente()
    texto = REGRAS.replace("- indice: `Início.md`", "- indice: `Início.md`\n- nuvem: `G:\\Meu Drive`")
    texto = texto.replace("## Caminhos", SECAO + "## Caminhos")
    amb.escrever("Sistema/Regras do Butler.md", texto)
    return amb


def test_situacao_traz_o_caminho_e_as_pastas_fora_da_varredura():
    amb = _com_nuvem()
    try:
        amb.preparar()
        regras = amb.rodar("situacao")["regras"]
        assert regras["caminhos"]["nuvem"] == "G:\\Meu Drive", regras["caminhos"]
        assert regras["nuvem_ignorada"] == ["G:\\Meu Drive\\Exames médicos", "G:\\Meu Drive\\Documentos\\Lindemberg"], \
            regras["nuvem_ignorada"]
    finally:
        amb.fechar()


def test_sem_a_secao_fica_vazia():
    amb = Ambiente()
    try:
        amb.preparar()
        regras = amb.rodar("situacao")["regras"]
        assert regras["nuvem_ignorada"] == []
        assert "nuvem" not in regras["caminhos"]
    finally:
        amb.fechar()


if __name__ == "__main__":
    test_situacao_traz_o_caminho_e_as_pastas_fora_da_varredura()
    test_sem_a_secao_fica_vazia()
    print("ALL PASS")
