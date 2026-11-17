"""Hooks de sessão do Butler.

`sessao.py inicio` (SessionStart): numa pasta que é um vault do Butler (preparado nesta máquina, ou com a nota de
regras), roda o `aviso` do gerente, que grava as mudanças de fora quando a trava está livre, e devolve:
- ao usuário, a linha do aviso (`systemMessage`);
- à sessão, a mesma linha, o id da sessão e a regra de entrada: pedido que altera o vault passa pela skill
  `butler:gerente`; consulta não (`additionalContext`).
Fora de um vault do Butler, não imprime nada. Uma falha do aviso nunca impede a sessão de abrir: vira uma linha
dizendo que o Butler não respondeu.

`sessao.py fim` (SessionEnd): solta a trava do vault se ela for desta sessão. A trava de outra sessão fica.

`sessao.py guarda` (PreToolUse de Write, Edit, MultiEdit e NotebookEdit): confere a escrita num arquivo de um vault
do Butler (o vault é achado pelo caminho do arquivo, não pela pasta da sessão, com a mesma busca do `butler.py`).
- Sem pedido em andamento, ou com o pedido de outra sessão, nega (`deny`) e diz para começar pelo
  `butler:gerente`. Uma trava sem sessão (um `inicio` sem `--sessao`) não diz de quem é: não nega.
- Com o pedido desta sessão, segue: a guarda não confere o conteúdo da escrita. Nota protegida e perda de
  informação continuam sendo paradas da skill `butler:gerente`, pelo próprio julgamento dela.
Fora de um vault, ou com qualquer erro, não diz nada: a guarda nunca impede uma escrita fora do Butler.
Só as ferramentas do Claude passam por aqui: escritas pelo Bash (o `butler.py`, um `mv`) e as escritas toleradas do
painel, que o próprio app grava esperando a trava sair, não.

Lê do stdin o JSON que o Claude Code manda aos hooks (`session_id`, `cwd`, `source`, `tool_name`, `tool_input`).
"""
import contextlib
import io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "skills", "gerente"))

ENTRADA = ("Este é um vault do Butler. Todo pedido que altera o vault passa pela skill butler:gerente antes de "
           "qualquer escrita; consulta sobre o que há no vault é respondida direto (ou pela butler:consultar), sem o "
           "gerente. Id desta sessão para o --sessao do butler.py: {sessao}.")


def _ler_entrada():
    try:
        dados = json.loads(sys.stdin.read() or "{}")
        return dados if isinstance(dados, dict) else {}
    except ValueError:
        return {}


def _rodar(argv):
    import butler  # noqa: E402

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        try:
            butler.main(argv)
        except SystemExit:
            pass
    try:
        return json.loads(buffer.getvalue() or "{}")
    except ValueError:
        return {}


def _imprimir(dados):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(dados, ensure_ascii=False))


def inicio(entrada):
    pasta = entrada.get("cwd") or os.getcwd()
    sessao = entrada.get("session_id") or ""
    try:
        resposta = _rodar(["aviso", "--vault", pasta, "--sessao", sessao])
    except Exception as erro:  # o aviso nunca impede a sessão de abrir
        resposta = {"vault_do_butler": True, "linha": f"Butler: o aviso do início da sessão falhou ({erro})"}
    if not resposta.get("vault_do_butler"):
        return
    linha = resposta.get("linha") or "Butler: sem aviso"
    _imprimir({"systemMessage": linha,
               "hookSpecificOutput": {"hookEventName": "SessionStart",
                                      "additionalContext": linha + "\n" + ENTRADA.format(sessao=sessao or "?")}})


FERRAMENTAS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
ENTRADA_GERENTE = ("Escrita no vault do Butler sem um pedido desta sessão em andamento. Comece pela skill "
                   "butler:gerente: o preâmbulo dela (`inicio --sessao <id desta sessão>`) pega a trava.")


def _decisao(decisao, motivo):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decisao,
                                   "permissionDecisionReason": motivo}}


def _conferir_escrita(entrada):
    from lib import config, trava  # noqa: E402

    ferramenta = entrada.get("tool_name")
    dados = entrada.get("tool_input") or {}
    sessao = entrada.get("session_id")
    caminho = dados.get("file_path") or dados.get("notebook_path")
    if ferramenta not in FERRAMENTAS or not caminho or not sessao:
        return None
    absoluto = os.path.abspath(os.path.join(entrada.get("cwd") or os.getcwd(), caminho))
    vault = config.achar_vault(os.path.dirname(absoluto))
    if not vault:
        return None
    atual = trava.ler(config.pasta_de_estado(vault))
    if atual is None or atual.get("corrompida") or str(atual.get("sessao", "")).startswith(trava.AVISO):
        return _decisao("deny", ENTRADA_GERENTE)
    dona = atual.get("sessao") or ""
    if dona and dona != sessao:
        return _decisao("deny", f"Outro pedido está em andamento neste vault ({atual.get('rotulo', '?')}), de outra "
                                "sessão. Pergunte ao usuário se espera ou para, como o preâmbulo do butler:gerente "
                                "manda; nunca force.")
    return None


def guarda(entrada):
    try:
        resposta = _conferir_escrita(entrada)
    except Exception:  # a guarda nunca impede uma escrita por erro dela mesma
        return
    if resposta:
        _imprimir(resposta)


def fim(entrada):
    sessao = entrada.get("session_id")
    if not sessao:
        return
    try:
        _rodar(["soltar-sessao", "--vault", entrada.get("cwd") or os.getcwd(), "--sessao", sessao])
    except Exception:
        pass


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    dados = _ler_entrada()
    if acao == "inicio":
        inicio(dados)
    elif acao == "fim":
        fim(dados)
    elif acao == "guarda":
        guarda(dados)
