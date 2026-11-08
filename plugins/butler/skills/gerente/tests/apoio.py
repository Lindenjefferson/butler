"""Apoio dos testes: vault sintético, configuração isolada e o CLI rodado como o usuário roda.

Cada teste chama `Ambiente()`, que cria numa pasta temporária um vault, uma pasta para o histórico e uma
configuração da máquina só dele (`BUTLER_CONFIG`), e roda o `butler.py` num processo à parte, com a saída em
cp1252 como no console do Windows, para pegar erro de acento na saída.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

AQUI = os.path.dirname(os.path.abspath(__file__))
BUTLER = os.path.join(os.path.dirname(AQUI), "butler.py")
sys.path.insert(0, os.path.dirname(AQUI))
BOM = chr(0xFEFF)

REGRAS = """---
title: Regras do Butler
type: referencia
tags: [butler, regras]
created: 2026-01-01
updated: 2026-01-01
source: teste
---

# Regras do Butler

## Notas protegidas

- `Veículo/Histórico de Manutenção.md` — histórico
- `Inventários/*.md` — inventários

## Formato rígido

- `Inventários/*.md` — segue a regra do CLAUDE.md

## Exceções aprendidas

- `Início.md` `sem_veja_tambem` — o índice não tem Veja também

## Liberações de dado sensível

## Caminhos

- inbox: `Inbox`
- indice: `Início.md`
- pendencias: `Sistema/Pendências.md`

## Veja também

- [[Início]]
"""


def nota(titulo, corpo="", links=("Início",), extra=""):
    veja = "\n".join(f"- [[{l}]]" for l in links)
    return (f"---\ntitle: {titulo}\ntype: referencia\ntags: [teste, nota]\ncreated: 2026-01-01\n"
            f"updated: 2026-01-01\nsource: teste\n{extra}---\n\n# {titulo}\n\n{corpo}\n\n## Veja também\n\n{veja}\n")


class Ambiente:
    def __init__(self, regras=True):
        self.raiz = tempfile.mkdtemp(prefix="butler-teste-")
        self.vault = os.path.join(self.raiz, "Meu Vault")
        self.historico = os.path.join(self.raiz, "historico")
        self.config = os.path.join(self.raiz, "maquina", "maquina.json")
        os.makedirs(self.vault)
        self.escrever("Início.md", BOM + "---\ntitle: Início\ntype: indice\ntags: [indice, vault]\n---\n\n# Início\n\n"
                      "- [[Histórico de Manutenção]]\n- [[Geladeira]]\n")
        self.escrever("CLAUDE.md", "# Regras\n\nUm assunto por nota.\n")
        self.escrever("Veículo/Histórico de Manutenção.md",
                      nota("Histórico de Manutenção", "- 2026-01-10 troca de óleo\n- 2026-03-02 pneus"))
        self.escrever("Inventários/Geladeira.md", nota("Geladeira", "- Voltagem: 127V\n- Loja: Não informado"))
        self.escrever("Inbox/.keep", "")
        os.remove(os.path.join(self.vault, "Inbox", ".keep"))
        if regras:
            self.escrever("Sistema/Regras do Butler.md", REGRAS)
            self.escrever("Sistema/Pendências.md", nota("Pendências", "- [ ] [eu] testar o X (desde 2026-01-01)"))

    # -- arquivos -------------------------------------------------------------------------------------------------

    def caminho(self, relativo):
        return os.path.join(self.vault, *relativo.split("/"))

    def escrever(self, relativo, texto, binario=False):
        destino = self.caminho(relativo)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as arquivo:
            arquivo.write(texto if binario else texto.encode("utf-8"))

    def ler(self, relativo):
        with open(self.caminho(relativo), "rb") as arquivo:
            return arquivo.read().decode("utf-8")

    def existe(self, relativo):
        return os.path.exists(self.caminho(relativo))

    def apagar(self, relativo):
        os.remove(self.caminho(relativo))

    # -- CLI ------------------------------------------------------------------------------------------------------

    def ambiente(self, **extra):
        env = dict(os.environ, BUTLER_CONFIG=self.config, BUTLER_PERMITIR_TEMP="1", PYTHONIOENCODING="cp1252",
                   LOCALAPPDATA=os.path.join(self.raiz, "local"))
        env.pop("PYTHONUTF8", None)
        env.update(extra)
        return env

    def rodar(self, *args, esperado=0, entrada=None, cwd=None, **env):
        processo = subprocess.run([sys.executable, BUTLER, *args], capture_output=True, input=entrada,
                                  cwd=cwd or self.vault, env=self.ambiente(**env))
        texto = processo.stdout.decode("utf-8", "replace")
        if processo.returncode != esperado:
            raise AssertionError(f"butler.py {' '.join(args)} saiu com {processo.returncode}, esperado {esperado}\n"
                                 f"stdout: {texto}\nstderr: {processo.stderr.decode('utf-8', 'replace')}")
        try:
            return json.loads(texto)
        except ValueError:
            raise AssertionError(f"saída não é JSON: {texto!r}\nstderr: {processo.stderr!r}")

    def preparar(self):
        resposta = self.rodar("preparar-historico", "--vault", self.vault, "--historico", self.historico)
        assert resposta["ok"], resposta
        return resposta

    def inicio(self, rotulo="pedido de teste", sessao=None, esperado=0):
        args = ["inicio", "--rotulo", rotulo]
        if sessao:
            args += ["--sessao", sessao]
        return self.rodar(*args, esperado=esperado)

    def git(self, *args):
        return subprocess.run(["git", f"--git-dir={os.path.join(self.historico, 'git')}", f"--work-tree={self.vault}",
                               *args], capture_output=True, check=True).stdout.decode("utf-8")

    def estado(self):
        with open(os.path.join(self.historico, "estado.json"), encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def fechar(self):
        shutil.rmtree(self.raiz, ignore_errors=True)


def rodar_testes(globais):
    falhas = 0
    for nome, funcao in sorted(globais.items()):
        if nome.startswith("test_") and callable(funcao):
            try:
                funcao()
                print(f"ok   {nome}")
            except Exception:
                falhas += 1
                print(f"FAIL {nome}")
                traceback.print_exc()
    if falhas:
        print(f"{falhas} FAILED")
        sys.exit(1)
    print("ALL PASS")
