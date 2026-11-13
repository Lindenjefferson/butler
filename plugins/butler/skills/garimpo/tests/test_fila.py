"""fila.py: próximo lote de uma fila declarada, comparada contra o registro de links."""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "fila.py")

FILA = """# Fila

### Receitas (3 itens)
AAA111\thttps://www.instagram.com/reel/AAA111/
BBB222\thttps://www.instagram.com/reel/BBB222/
CCC333\thttps://www.instagram.com/reel/CCC333/

### Viagens (1 itens)
DDD444\thttps://www.instagram.com/reel/DDD444/

### Política (2 itens)
EEE555\thttps://www.instagram.com/reel/EEE555/
FFF666\thttps://www.instagram.com/reel/FFF666/
"""

REGISTRO = """# Registro

| Código | Status | Destino | Data |
|---|---|---|---|
| AAA111 | triado | Receita X | 2026-11-12 |
| EEE555 | descartado | sem conteúdo | 2026-11-12 |
"""


def rodar(vault, *args):
    saida = subprocess.run([sys.executable, "-I", SCRIPT, vault, *args], capture_output=True, check=True)
    return json.loads(saida.stdout.decode("utf-8"))


def _vault_padrao(tmp):
    os.makedirs(os.path.join(tmp, "Sistema"), exist_ok=True)
    with open(os.path.join(tmp, "Fila.md"), "w", encoding="utf-8") as f:
        f.write(FILA)
    with open(os.path.join(tmp, "Sistema", "Registro.md"), "w", encoding="utf-8") as f:
        f.write(REGISTRO)


def test_escolhe_o_bloco_com_menos_pendente_primeiro():
    with tempfile.TemporaryDirectory() as vault:
        _vault_padrao(vault)
        r = rodar(vault, "--fila", "Fila.md", "--registro", "Sistema/Registro.md")
        # Viagens tem 1 pendente, Receitas tem 2 (AAA111 já está no registro) — Viagens vence.
        assert r["bloco"] == "Viagens", r
        assert r["urls"] == ["https://www.instagram.com/reel/DDD444/"], r


def test_item_ja_no_registro_nao_entra_no_lote():
    with tempfile.TemporaryDirectory() as vault:
        _vault_padrao(vault)
        r = rodar(vault, "--fila", "Fila.md", "--registro", "Sistema/Registro.md", "--pular", "Viagens",
                  "--pular", "Política")
        assert r["bloco"] == "Receitas", r
        urls = r["urls"]
        assert "https://www.instagram.com/reel/AAA111/" not in urls, "já está triado no registro"
        assert urls == ["https://www.instagram.com/reel/BBB222/", "https://www.instagram.com/reel/CCC333/"]


def test_pular_tira_bloco_mas_aparece_em_pulados_se_tinha_pendente():
    with tempfile.TemporaryDirectory() as vault:
        _vault_padrao(vault)
        r = rodar(vault, "--fila", "Fila.md", "--registro", "Sistema/Registro.md", "--pular", "Viagens", "--pular", "Política")
        assert r["bloco"] == "Receitas", r
        # Política tem FFF666 pendente (EEE555 já descartado, mas descartado ainda conta como "visto")
        assert "Política" in r["pulados"], r
        assert "Viagens" in r["pulados"], r


def test_tamanho_lote_corta_a_lista():
    with tempfile.TemporaryDirectory() as vault:
        _vault_padrao(vault)
        r = rodar(vault, "--fila", "Fila.md", "--registro", "Sistema/Registro.md", "--pular", "Viagens",
                  "--pular", "Política", "--tamanho-lote", "1")
        assert r["bloco"] == "Receitas"
        assert r["urls"] == ["https://www.instagram.com/reel/BBB222/"]


def test_sem_registro_nada_conta_como_visto():
    with tempfile.TemporaryDirectory() as vault:
        _vault_padrao(vault)
        r = rodar(vault, "--fila", "Fila.md")
        assert r["bloco"] == "Viagens"
        assert r["progresso"]["total_pendente"] == 6


def test_sem_pendente_nenhum_devolve_bloco_nulo():
    with tempfile.TemporaryDirectory() as vault:
        os.makedirs(os.path.join(vault, "Sistema"), exist_ok=True)
        with open(os.path.join(vault, "Fila.md"), "w", encoding="utf-8") as f:
            f.write("### Receitas (1 itens)\nAAA111\thttps://www.instagram.com/reel/AAA111/\n")
        with open(os.path.join(vault, "Sistema", "Registro.md"), "w", encoding="utf-8") as f:
            f.write("| Código | Status | Destino | Data |\n|---|---|---|---|\n| AAA111 | triado | X | 2026-11-12 |\n")
        r = rodar(vault, "--fila", "Fila.md", "--registro", "Sistema/Registro.md")
        assert r["bloco"] is None and r["urls"] == [], r


def test_ordem_arquivo_mantem_a_ordem_declarada():
    with tempfile.TemporaryDirectory() as vault:
        _vault_padrao(vault)
        r = rodar(vault, "--fila", "Fila.md", "--registro", "Sistema/Registro.md", "--ordem", "arquivo")
        # Na ordem do arquivo, Receitas vem antes de Viagens (mesmo tendo mais pendentes).
        assert r["bloco"] == "Receitas", r


def test_progresso_traz_totais_por_bloco():
    with tempfile.TemporaryDirectory() as vault:
        _vault_padrao(vault)
        r = rodar(vault, "--fila", "Fila.md", "--registro", "Sistema/Registro.md")
        nomes = {b["nome"]: b for b in r["progresso"]["blocos"]}
        assert nomes["Receitas"] == {"nome": "Receitas", "total": 3, "pendente": 2}
        assert nomes["Viagens"] == {"nome": "Viagens", "total": 1, "pendente": 1}
        assert r["progresso"]["total_fila"] == 6
        assert r["progresso"]["total_registrado"] == 2


if __name__ == "__main__":
    test_escolhe_o_bloco_com_menos_pendente_primeiro()
    test_item_ja_no_registro_nao_entra_no_lote()
    test_pular_tira_bloco_mas_aparece_em_pulados_se_tinha_pendente()
    test_tamanho_lote_corta_a_lista()
    test_sem_registro_nada_conta_como_visto()
    test_sem_pendente_nenhum_devolve_bloco_nulo()
    test_ordem_arquivo_mantem_a_ordem_declarada()
    test_progresso_traz_totais_por_bloco()
    print("ALL PASS")
