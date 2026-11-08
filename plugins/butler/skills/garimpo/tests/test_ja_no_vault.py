"""ja_no_vault.py: repetidos pelo frontmatter e pelo registro de links."""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "ja_no_vault.py")

REGISTRO = """# Registro

| Código | Status | Destino (nota) | Registrado em |
|---|---|---|---|
| DeSo2rNMgBr | triado | Painel da Vida | 2026-11-04 |
| Codigo | Status | cabeçalho sem acento | x |
"""


def rodar(vault, *args):
    saida = subprocess.run([sys.executable, "-I", SCRIPT, vault, *args], capture_output=True, check=True)
    return json.loads(saida.stdout.decode("utf-8"))


def test_registro_e_frontmatter():
    with tempfile.TemporaryDirectory() as vault:
        os.makedirs(os.path.join(vault, "Sistema"))
        with open(os.path.join(vault, "Sistema", "Registro.md"), "w", encoding="utf-8") as arquivo:
            arquivo.write(REGISTRO)
        with open(os.path.join(vault, "Nota.md"), "w", encoding="utf-8") as arquivo:
            arquivo.write("---\nsource: \"https://youtu.be/abc123\"\n---\n# Nota\n")
        resultado = rodar(vault, "--registro", "Sistema/Registro.md", "https://www.instagram.com/reels/DeSo2rNMgBr/?igsh=1",
                          "https://www.youtube.com/watch?v=abc123", "https://www.instagram.com/p/desO2rnmgbr/")
        assert resultado[0]["registro"] == {"status": "triado", "destino": "Painel da Vida"}
        assert resultado[1]["notas"] == ["Nota.md"] and "registro" not in resultado[1]
        assert "registro" not in resultado[2], "maiúsculas contam no código"
        sem = rodar(vault, "https://www.instagram.com/reel/DeSo2rNMgBr/")
        assert "registro" not in sem[0]


def test_nota_com_bom():
    with tempfile.TemporaryDirectory() as vault:
        with open(os.path.join(vault, "Nota.md"), "w", encoding="utf-8") as arquivo:
            arquivo.write(chr(0xFEFF) + "---\nsource: \"https://youtu.be/abc123\"\n---\n# Nota\n")
        assert rodar(vault, "https://www.youtube.com/watch?v=abc123")[0]["notas"] == ["Nota.md"]


def test_url_no_corpo_de_uma_lista_da_colheita():
    with tempfile.TemporaryDirectory() as vault:
        os.makedirs(os.path.join(vault, "Lazer"))
        with open(os.path.join(vault, "Lazer", "Filmes.md"), "w", encoding="utf-8") as arquivo:
            arquivo.write("---\ntitle: Filmes\n---\n# Filmes\n\n- **Filme B**: indicado. [canal](https://youtu.be/xyz789)\n")
        with open(os.path.join(vault, "Outra.md"), "w", encoding="utf-8") as arquivo:
            arquivo.write("# Outra\n\nCitei https://youtu.be/xyz789 no texto.\n")
        com = rodar(vault, "--lista", "Lazer/Filmes.md", "--lista", "Viagens/<destino>.md",
                    "https://www.youtube.com/watch?v=xyz789")
        assert com[0]["notas"] == ["Lazer/Filmes.md"], com
        assert rodar(vault, "https://www.youtube.com/watch?v=xyz789")[0]["notas"] == []


if __name__ == "__main__":
    test_registro_e_frontmatter()
    test_nota_com_bom()
    test_url_no_corpo_de_uma_lista_da_colheita()
    print("ALL PASS")
