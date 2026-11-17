"""Guarda das escritas: nada se escreve no vault sem o pedido desta sessão."""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "skills", "gerente", "tests"))

from apoio import Ambiente, nota, rodar_testes  # noqa: E402

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


def test_a_guarda_nao_le_o_conteudo_da_escrita():
    # Nota protegida que perde texto, por qualquer ferramenta: com o pedido da sessão, segue. A parada é da skill.
    amb = Ambiente()
    try:
        amb.preparar()
        amb.inicio("registra", sessao="sessao-teste")
        alvo = amb.caminho("Veículo/Histórico de Manutenção.md")
        assert guarda(amb, "Edit", {"file_path": alvo, "old_string": "- 2026-01-10 troca de óleo\n- 2026-03-02 pneus",
                                    "new_string": "- 2026-03-02 pneus"}) is None
        assert guarda(amb, "MultiEdit", {"file_path": alvo, "edits": [
            {"old_string": "- 2026-01-10 troca de óleo\n", "new_string": ""}]}) is None
        assert guarda(amb, "Write", {"file_path": alvo, "content": nota("Histórico de Manutenção")}) is None
        assert guarda(amb, "NotebookEdit", {"notebook_path": amb.caminho("Inventários/Medidas.ipynb"),
                                            "cell_id": "c1", "edit_mode": "delete", "new_source": ""}) is None
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


if __name__ == "__main__":
    rodar_testes(globals())
