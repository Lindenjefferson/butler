"""Hooks de sessão: aviso no início, silêncio fora de um vault, trava solta no fim."""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "skills", "gerente", "tests"))

from apoio import Ambiente, nota, rodar_testes  # noqa: E402

SESSAO = os.path.join(os.path.dirname(AQUI), "sessao.py")


def hook(amb, acao, cwd, sessao="sessao-teste"):
    entrada = json.dumps({"session_id": sessao, "cwd": cwd, "source": "startup"}).encode("utf-8")
    processo = subprocess.run([sys.executable, SESSAO, acao], input=entrada, capture_output=True,
                              env=amb.ambiente(), cwd=cwd)
    assert processo.returncode == 0, processo.stderr
    texto = processo.stdout.decode("utf-8").strip()
    return json.loads(texto) if texto else None


def test_fora_de_um_vault_nao_imprime_nada():
    amb = Ambiente(regras=False)
    try:
        assert hook(amb, "inicio", amb.raiz) is None
    finally:
        amb.fechar()


def test_no_vault_da_o_aviso_e_a_regra_de_entrada():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Inbox/Nova.md", nota("Nova"))
        saida = hook(amb, "inicio", amb.caminho("Inbox"))
        assert saida["systemMessage"].startswith("Butler: Inbox com 1 nota")
        contexto = saida["hookSpecificOutput"]["additionalContext"]
        assert "butler:gerente" in contexto and "sessao-teste" in contexto
        assert "Inbox/Nova.md" in amb.git("ls-files")
    finally:
        amb.fechar()


def test_vault_sem_preparar_avisa_sem_historico():
    amb = Ambiente()
    try:
        saida = hook(amb, "inicio", amb.vault)
        assert "sem histórico" in saida["systemMessage"]
    finally:
        amb.fechar()


def test_fim_solta_so_a_trava_da_sessao():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="outra")
        hook(amb, "fim", amb.vault, sessao="sessao-teste")
        assert os.path.exists(os.path.join(amb.historico, "trava.json"))
        hook(amb, "fim", amb.vault, sessao="outra")
        assert not os.path.exists(os.path.join(amb.historico, "trava.json"))
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
