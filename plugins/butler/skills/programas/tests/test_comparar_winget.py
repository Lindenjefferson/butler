"""comparar_winget.py: novos, sumidos e versão mudada, com BOM e mais de uma fonte."""
import json
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))

from comparar_winget import comparar  # noqa: E402


def _export(pasta, nome, fontes):
    caminho = os.path.join(pasta, nome)
    dados = {"Sources": [{"SourceDetails": {"Name": fonte}, "Packages": [{"PackageIdentifier": i, "Version": v}
                                                                          for i, v in pacotes]}
                         for fonte, pacotes in fontes]}
    with open(caminho, "w", encoding="utf-8-sig") as arquivo:
        json.dump(dados, arquivo)
    return caminho


def test_novos_sumidos_e_versao():
    with tempfile.TemporaryDirectory() as pasta:
        antigo = _export(pasta, "a.json", [("winget", [("Git.Git", "2.50"), ("Fora.DoCatalogo", "1.0")]),
                                           ("msstore", [("9NBLGGH4NNS1", "1.0")])])
        novo = _export(pasta, "n.json", [("winget", [("Git.Git", "2.54"), ("Novo.Programa", "3")]),
                                         ("msstore", [("9NBLGGH4NNS1", "1.0")])])
        resultado = comparar(antigo, novo)
        assert [p["id"] for p in resultado["novos"]] == ["Novo.Programa"]
        assert [p["id"] for p in resultado["sumidos"]] == ["Fora.DoCatalogo"]
        assert resultado["versao_mudou"] == [{"id": "Git.Git", "de": "2.50", "para": "2.54"}]


if __name__ == "__main__":
    test_novos_sumidos_e_versao()
    print("ALL PASS")
