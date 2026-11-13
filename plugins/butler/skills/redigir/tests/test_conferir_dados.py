"""conferir_dados.py: o que sumiu e o que apareceu entre a nota e a proposta (links, wikilinks, números, código)."""
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))

from conferir_dados import comparar, dados  # noqa: E402

ANTES = """---
title: Mala
updated: 2026-01-02
---

# Mala

A mochila da LATAM mede 45×35×20 cm e a tarifa Basic inclui só ela, veja [[Direitos do Passageiro|direitos]]
e a [fonte](https://exemplo.com/mala?x=1). Rodar `pip install mala` antes.

**Confiança geral:** média
"""

DEPOIS = """---
title: Mala
updated: 2026-03-04
---

# Mala

1. **Item pessoal** — a mochila que vai embaixo do banco. [Fonte](https://exemplo.com/mala?x=1)
   - **LATAM:** 45×35×20 cm; a tarifa Basic inclui só ela.
2. **Antes:** `pip install mala`.

## Veja também
- [[Direitos do Passageiro]]
"""


def test_reorganizar_sem_perder_nem_inventar():
    resultado = comparar(ANTES, DEPOIS)
    assert resultado["ok"] is True
    assert not any(resultado["sumiu"].values()) and not any(resultado["novo"].values())


def test_frontmatter_e_numeracao_de_lista_ficam_de_fora():
    achados = dados(DEPOIS)
    assert achados["numeros"] == ["20", "35", "45"]
    assert achados["wikilinks"] == ["Direitos do Passageiro"]
    assert achados["links"] == ["https://exemplo.com/mala?x=1"]
    assert achados["codigo"] == ["pip install mala"]


def test_aponta_o_que_sumiu():
    proposta = DEPOIS.replace("45×35×20 cm", "45×35 cm").replace("- [[Direitos do Passageiro]]\n", "")
    proposta = proposta.replace(" [Fonte](https://exemplo.com/mala?x=1)", "").replace("`pip install mala`", "o pip")
    resultado = comparar(ANTES, proposta)
    assert resultado["ok"] is False
    assert resultado["sumiu"] == {"links": ["https://exemplo.com/mala?x=1"], "wikilinks": ["Direitos do Passageiro"],
                                  "numeros": ["20"], "codigo": ["pip install mala"]}


def test_aponta_o_que_apareceu():
    proposta = DEPOIS.replace("só ela.", "só ela, até 10 kg, veja [[Bagagem]] e https://outro.com/x.")
    resultado = comparar(ANTES, proposta)
    assert resultado["ok"] is False
    assert resultado["novo"] == {"links": ["https://outro.com/x"], "wikilinks": ["Bagagem"], "numeros": ["10"],
                                 "codigo": []}


def test_numero_com_separador_e_o_mesmo_dado():
    assert dados("Custa R$ 1.299,90 em 12x; versão 3.15.")["numeros"] == ["1.299,90", "12", "3.15"]
    assert comparar("São 1.299,90.", "- **Preço:** 1.299,90")["ok"] is True


def test_linha_de_comando():
    with tempfile.TemporaryDirectory() as pasta:
        nota, proposta = os.path.join(pasta, "nota.md"), os.path.join(pasta, "proposta.md")
        for caminho, texto in ((nota, ANTES), (proposta, DEPOIS.replace("45×", "46×"))):
            with open(caminho, "w", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(texto)
        script = os.path.join(os.path.dirname(AQUI), "conferir_dados.py")
        saida = subprocess.run([sys.executable, script, nota, proposta], capture_output=True, text=True,
                               encoding="utf-8")
        assert saida.returncode == 1, saida.stderr
        assert '"sumiu"' in saida.stdout and '"45"' in saida.stdout and '"46"' in saida.stdout
        igual = subprocess.run([sys.executable, script, nota, nota], capture_output=True, text=True, encoding="utf-8")
        assert igual.returncode == 0 and '"ok": true' in igual.stdout


if __name__ == "__main__":
    falhas = 0
    for nome, funcao in sorted(globals().items()):
        if nome.startswith("test_") and callable(funcao):
            try:
                funcao()
                print(f"ok   {nome}")
            except Exception:
                import traceback
                falhas += 1
                print(f"FAIL {nome}")
                traceback.print_exc()
    if falhas:
        print(f"{falhas} FAILED")
        sys.exit(1)
    print("ALL PASS")
