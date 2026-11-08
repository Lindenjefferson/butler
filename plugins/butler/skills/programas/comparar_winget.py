"""Compara dois `winget export --include-versions`: o que está na nota e o export novo.

Uso: python comparar_winget.py <json antigo> <json novo>

Imprime um JSON com:
- `novos`: pacotes que só estão no novo (programa instalado desde a última atualização, ou que voltou ao catálogo);
- `sumidos`: pacotes que só estão no antigo. O export deixa de fora o programa cuja versão instalada não está no
  catálogo do winget, então um sumido não quer dizer desinstalado: quem chama confere se o programa ainda está na
  máquina antes de mover a linha dele na nota;
- `versao_mudou`: pacotes nos dois, com a versão de cada lado.

Só lê. Aceita JSON com BOM (o PowerShell grava assim) e pacotes de várias fontes (winget, msstore).
"""
import json
import sys


def pacotes(caminho):
    with open(caminho, encoding="utf-8-sig") as arquivo:
        dados = json.load(arquivo)
    mapa = {}
    for fonte in dados.get("Sources", []):
        nome = (fonte.get("SourceDetails") or {}).get("Name", "")
        for pacote in fonte.get("Packages", []):
            identificador = pacote.get("PackageIdentifier")
            if identificador:
                mapa[identificador] = {"id": identificador, "versao": pacote.get("Version"), "fonte": nome}
    return mapa


def comparar(antigo, novo):
    a, n = pacotes(antigo), pacotes(novo)
    return {
        "novos": [n[i] for i in sorted(n.keys() - a.keys(), key=str.lower)],
        "sumidos": [a[i] for i in sorted(a.keys() - n.keys(), key=str.lower)],
        "versao_mudou": [{"id": i, "de": a[i]["versao"], "para": n[i]["versao"]}
                         for i in sorted(a.keys() & n.keys(), key=str.lower) if a[i]["versao"] != n[i]["versao"]],
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python comparar_winget.py <json antigo> <json novo>")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(comparar(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
