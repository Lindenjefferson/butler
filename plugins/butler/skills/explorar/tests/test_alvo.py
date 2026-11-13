"""alvo.py: monta grupos de até dez notas, separa o que fica fora e aponta fontes de vídeo a reassistir."""
import json
import os
import subprocess
import sys
import tempfile
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SCRIPT = os.path.join(RAIZ, "scripts", "alvo.py")
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import alvo  # noqa: E402

REGRAS = """# Regras do Butler

## Notas protegidas

- `Viagens/Protegida.md` — protegida

## Formato rígido

- `Viagens/Rigida.md` — rígida
"""


def escrever(vault, caminho, texto="# x\n"):
    destino = os.path.join(vault, *caminho.split("/"))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def rodar(vault, *args):
    saida = subprocess.run([sys.executable, "-I", SCRIPT, vault, "montar", *args], capture_output=True)
    return saida.returncode, json.loads(saida.stdout.decode("utf-8") or "{}")


def test_pasta_agrupa_por_subpasta_ate_dez():
    with tempfile.TemporaryDirectory() as vault:
        for i in range(23):
            escrever(vault, f"X/N{i:02d}.md")
        for i in range(4):
            escrever(vault, f"X/Sub/S{i}.md")
        codigo, r = rodar(vault, "--pasta", "X")
        assert codigo == 0, r
        tamanhos = [(g["pasta"], len(g["notas"])) for g in r["grupos"]]
        assert tamanhos == [("X", 8), ("X", 8), ("X", 7), ("X/Sub", 4)], tamanhos
        assert r["grupos"][0]["notas"][0] == "X/N00.md" and r["grupos"][0]["id"] == "g1"
        assert r["grupos"][0]["notas"] == sorted(r["grupos"][0]["notas"])


def test_subpasta_pequena_junta_com_a_vizinha():
    with tempfile.TemporaryDirectory() as vault:
        for i in range(5):
            escrever(vault, f"Y/N{i}.md")
        for i in range(2):
            escrever(vault, f"Y/Sub/S{i}.md")
        codigo, r = rodar(vault, "--pasta", "Y")
        assert [len(g["notas"]) for g in r["grupos"]] == [7], r["grupos"]


def test_fora_inbox_ideia_protegida_rigida_nfd():
    with tempfile.TemporaryDirectory() as vault:
        escrever(vault, "Sistema/Regras do Butler.md", REGRAS)
        escrever(vault, "Inbox/A.md")
        escrever(vault, "Viagens/Ideia.md", "---\ntype: ideia\n---\n# x\n")
        escrever(vault, "Viagens/Protegida.md")
        escrever(vault, "Viagens/Rigida.md")
        escrever(vault, "Viagens/" + unicodedata.normalize("NFD", "Ação") + ".md")
        notas = ["Inbox/A.md", "Viagens/Ideia.md", "Viagens/Protegida.md", "Viagens/Rigida.md",
                 "Viagens/" + unicodedata.normalize("NFD", "Ação") + ".md"]
        codigo, r = rodar(vault, "--notas", *notas, "--excluir-campo", "type", "--excluir-valor", "ideia")
        motivos = {f["nota"]: f["motivo"] for f in r["fora"]}
        assert [motivos[n] for n in notas] == ["inbox", "ideia", "protegida", "rigida", "nfd"], motivos
        assert r["grupos"] == [], r
        assert codigo == 1, codigo


def test_reassistir_so_video_com_sinal_de_lista():
    with tempfile.TemporaryDirectory() as vault:
        escrever(vault, "Lazer/Jogos.md", "---\ntitle: Jogos\n---\n# Jogos\n\n"
                 "- **AER** — de uma lista de \"5 jogos\" (os outros 4 não ficaram visíveis). "
                 "[Fonte](https://www.instagram.com/reel/X/)\n"
                 "- **Celeste** — bom. [Fonte](https://www.instagram.com/reel/Y/)\n"
                 "- **Outro** — de uma lista de \"5 jogos\". [Fonte](https://exemplo.com/artigo)\n")
        codigo, r = rodar(vault, "--pasta", "Lazer")
        assert r["reassistir"] == [{"nota": "Lazer/Jogos.md", "url": "https://www.instagram.com/reel/X/",
                                    "sinais": ["numero_no_titulo", "os_outros"]}], r["reassistir"]


def test_sinais_de_lista_cobre_todos():
    assert alvo.sinais_de_lista("Top 7 filmes", "") == ["numero_no_titulo"]
    assert alvo.sinais_de_lista("x", "Uma LISTA DE filmes") == ["lista_de"]
    assert alvo.sinais_de_lista("x", "Não Identificado e não confirmado, provavelmente") == [
        "nao_identificado", "nao_confirmado", "provavelmente"]
    assert alvo.sinais_de_lista("x", "**A** **B** **C**") == ["varios_nomes"]
    assert alvo.sinais_de_lista("x", "**A** **B**") == []
    assert alvo.sinais_de_lista("Receita", "texto simples") == []


def test_fontes_em_video_reconhece_instagram_youtube_tiktok():
    texto = ("https://www.instagram.com/reel/A/ e [x](https://instagram.com/p/B/) "
             "https://www.youtube.com/watch?v=1 https://youtu.be/2 https://www.tiktok.com/@u/video/3 "
             "https://www.gov.br/pagina")
    assert alvo.fontes_em_video(texto) == [
        "https://www.instagram.com/reel/A/", "https://instagram.com/p/B/", "https://www.youtube.com/watch?v=1",
        "https://youtu.be/2", "https://www.tiktok.com/@u/video/3"]
    assert alvo.fontes_em_video("https://www.gov.br/x") == []


def test_notas_lista_explicita_mantem_so_existentes():
    with tempfile.TemporaryDirectory() as vault:
        escrever(vault, "A/Existe.md")
        codigo, r = rodar(vault, "--notas", "A/Existe.md", "A/Falta.md")
        assert r["fora"] == [{"nota": "A/Falta.md", "motivo": "nao_existe"}], r["fora"]
        assert r["grupos"][0]["notas"] == ["A/Existe.md"]
        assert r["alvo"]["tipo"] == "notas"


def test_alvo_invalido_sai_com_2():
    with tempfile.TemporaryDirectory() as vault:
        codigo, _ = rodar(vault, "--pasta", "Nao existe")
        assert codigo == 2, codigo


if __name__ == "__main__":
    for nome, funcao in sorted(globals().items()):
        if nome.startswith("test_") and callable(funcao):
            funcao()
            print("ok", nome)
    print("ALL PASS")
