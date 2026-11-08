"""Guarda das escritas: nada se escreve no vault sem o pedido desta sessão, e nota protegida que perde linhas pergunta."""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "skills", "gerente", "tests"))

from apoio import REGRAS, Ambiente, nota, rodar_testes  # noqa: E402

SESSAO = os.path.join(os.path.dirname(AQUI), "sessao.py")


def guarda(amb, ferramenta, entrada, sessao="sessao-teste", cwd=None):
    dados = {"session_id": sessao, "cwd": cwd or amb.vault, "hook_event_name": "PreToolUse",
             "tool_name": ferramenta, "tool_input": entrada}
    processo = subprocess.run([sys.executable, SESSAO, "guarda"], input=json.dumps(dados).encode("utf-8"),
                              capture_output=True, env=amb.ambiente(), cwd=cwd or amb.vault)
    assert processo.returncode == 0, processo.stderr
    texto = processo.stdout.decode("utf-8").strip()
    return json.loads(texto)["hookSpecificOutput"] if texto else None


def test_fora_de_um_vault_nao_diz_nada():
    amb = Ambiente(regras=False)
    try:
        alvo = os.path.join(amb.raiz, "outro", "x.md")
        assert guarda(amb, "Write", {"file_path": alvo, "content": "oi"}, cwd=amb.raiz) is None
    finally:
        amb.fechar()


def test_escrita_sem_pedido_e_negada():
    amb = Ambiente()
    try:
        amb.preparar()
        saida = guarda(amb, "Write", {"file_path": amb.caminho("Inbox/Nova.md"), "content": nota("Nova")})
        assert saida["permissionDecision"] == "deny"
        assert "butler:gerente" in saida["permissionDecisionReason"]
    finally:
        amb.fechar()


def test_vault_sem_preparar_tambem_exige_o_pedido():
    amb = Ambiente()
    try:
        saida = guarda(amb, "Edit", {"file_path": amb.caminho("Inventários/Geladeira.md"), "old_string": "a",
                                     "new_string": "b"})
        assert saida["permissionDecision"] == "deny"
    finally:
        amb.fechar()


def test_escrita_com_o_pedido_desta_sessao_segue():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("anota", sessao="sessao-teste")
        assert guarda(amb, "Write", {"file_path": amb.caminho("Inbox/Nova.md"), "content": nota("Nova")}) is None
    finally:
        amb.fechar()


def test_pedido_de_outra_sessao_nega():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("triagem", sessao="outra")
        saida = guarda(amb, "Write", {"file_path": amb.caminho("Inbox/Nova.md"), "content": nota("Nova")})
        assert saida["permissionDecision"] == "deny" and "triagem" in saida["permissionDecisionReason"]
    finally:
        amb.fechar()


def test_trava_sem_sessao_nao_nega():
    # Um `inicio` sem --sessao não diz de quem é a trava: negar prenderia a sessão que a pegou.
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("anota")
        assert guarda(amb, "Write", {"file_path": amb.caminho("Inbox/Nova.md"), "content": nota("Nova")}) is None
    finally:
        amb.fechar()


def test_nota_protegida_que_perde_linha_pergunta():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("registra", sessao="sessao-teste")
        alvo = amb.caminho("Veículo/Histórico de Manutenção.md")
        saida = guarda(amb, "Edit", {"file_path": alvo, "old_string": "- 2026-01-10 troca de óleo\n- 2026-03-02 pneus",
                                     "new_string": "- 2026-03-02 pneus"})
        assert saida["permissionDecision"] == "ask"
        assert "protegida" in saida["permissionDecisionReason"]
    finally:
        amb.fechar()


def test_nota_protegida_que_troca_ou_acrescenta_segue():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("registra", sessao="sessao-teste")
        alvo = amb.caminho("Inventários/Geladeira.md")
        assert guarda(amb, "Edit", {"file_path": alvo, "old_string": "- Voltagem: 127V",
                                    "new_string": "- Voltagem: 220V"}) is None
        assert guarda(amb, "Edit", {"file_path": alvo, "old_string": "- Voltagem: 127V",
                                    "new_string": "- Voltagem: 127V\n- Cor: branca"}) is None
        assert guarda(amb, "MultiEdit", {"file_path": alvo, "edits": [
            {"old_string": "- Voltagem: 127V\n", "new_string": ""}]})["permissionDecision"] == "ask"
    finally:
        amb.fechar()


def test_multiedit_que_apaga_num_trecho_e_acrescenta_noutro_pergunta():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("registra", sessao="sessao-teste")
        alvo = amb.caminho("Veículo/Histórico de Manutenção.md")
        saida = guarda(amb, "MultiEdit", {"file_path": alvo, "edits": [
            {"old_string": "- 2026-01-10 troca de óleo\n", "new_string": ""},
            {"old_string": "- 2026-03-02 pneus", "new_string": "- 2026-03-02 pneus\n- 2026-04-01 alinhamento"}]})
        assert saida["permissionDecision"] == "ask"
    finally:
        amb.fechar()


def test_write_que_sobrescreve_nota_e_perde_linhas_pergunta():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Casa/Lista.md", nota("Lista", "- um\n- dois\n- três"))
        amb.inicio("altera", sessao="sessao-teste")
        saida = guarda(amb, "Write", {"file_path": amb.caminho("Casa/Lista.md"), "content": nota("Lista", "- um")})
        assert saida["permissionDecision"] == "ask"
        assert guarda(amb, "Write", {"file_path": amb.caminho("Casa/Lista.md"),
                                     "content": nota("Lista", "- um\n- dois\n- três\n- quatro")}) is None
    finally:
        amb.fechar()


def test_entrada_estranha_nao_quebra():
    amb = Ambiente()
    try:
        processo = subprocess.run([sys.executable, SESSAO, "guarda"], input=b"nao e json", capture_output=True,
                                  env=amb.ambiente(), cwd=amb.vault)
        assert processo.returncode == 0 and not processo.stdout.strip()
    finally:
        amb.fechar()


def test_vault_sem_registro_com_pedido_aberto_de_uma_subpasta_segue():
    # Sem preparar nesta máquina, o `inicio` rodado de uma subpasta acha a raiz pela nota de regras, como a guarda.
    amb = Ambiente()
    try:
        amb.rodar("inicio", "--rotulo", "anota", "--sessao", "sessao-teste", cwd=amb.caminho("Inventários"))
        assert guarda(amb, "Write", {"file_path": amb.caminho("Inbox/Nova.md"), "content": nota("Nova")},
                      cwd=amb.caminho("Inventários")) is None
    finally:
        amb.fechar()


def test_reformatar_nota_sem_perder_palavras_segue():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Casa/Texto.md", nota("Texto", "Uma frase.\n\nOutra frase."))
        amb.inicio("altera", sessao="sessao-teste")
        assert guarda(amb, "Write", {"file_path": amb.caminho("Casa/Texto.md"),
                                     "content": nota("Texto", "Uma frase. Outra frase.")}) is None
    finally:
        amb.fechar()


def test_espalhar_menos_palavras_em_mais_linhas_pergunta():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("registra", sessao="sessao-teste")
        alvo = amb.caminho("Veículo/Histórico de Manutenção.md")
        saida = guarda(amb, "Edit", {"file_path": alvo, "old_string": "- 2026-01-10 troca de óleo\n- 2026-03-02 pneus",
                                     "new_string": "- 2026-03-02\n- pneus\n- ok"})
        assert saida["permissionDecision"] == "ask"
    finally:
        amb.fechar()


def test_notebook_protegido_que_apaga_ou_encolhe_celula_pergunta():
    amb = Ambiente()
    try:
        import json as _json
        caderno = {"cells": [{"cell_type": "markdown", "id": "c1", "metadata": {},
                              "source": ["Voltagem 127V e loja X"]}],
                   "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
        amb.escrever("Sistema/Regras do Butler.md", REGRAS.replace(
            "- `Inventários/*.md` — inventários", "- `Inventários/*.md` — inventários\n- `Inventários/*.ipynb` — medidas"))
        amb.escrever("Inventários/Medidas.ipynb", _json.dumps(caderno))
        amb.preparar()
        amb.inicio("registra", sessao="sessao-teste")
        alvo = amb.caminho("Inventários/Medidas.ipynb")
        apagar = guarda(amb, "NotebookEdit", {"notebook_path": alvo, "cell_id": "c1", "edit_mode": "delete",
                                              "new_source": ""})
        assert apagar["permissionDecision"] == "ask"
        encolher = guarda(amb, "NotebookEdit", {"notebook_path": alvo, "cell_id": "c1", "new_source": "127V"})
        assert encolher["permissionDecision"] == "ask"
        assert guarda(amb, "NotebookEdit", {"notebook_path": alvo, "cell_id": "c1",
                                            "new_source": "Voltagem 220V e loja X"}) is None
        assert guarda(amb, "NotebookEdit", {"notebook_path": alvo, "edit_mode": "insert",
                                            "new_source": "nova"}) is None
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
