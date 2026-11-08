"""O `estado.json`, que o Wingman (ou qualquer outro painel) lê para mostrar o vault sem ler o terminal.

Fica na pasta de estado do vault (a do histórico, achada pela configuração da máquina), nunca dentro do vault. Não
guarda conteúdo de nota nem dado sensível: só caminhos, títulos, vereditos e classificações. É regravado por
`preparar-historico`, `inicio`, `ponto`, `fim`, `aviso`, `desfazer`, `soltar-sessao` e `liberar-trava`, sempre por arquivo temporário e
`os.replace` (quem lê nunca vê o arquivo pela metade). O formato, versão 1:

    {
      "versao": 1,
      "gravado_em": "2026-11-07T08:00:00-03:00",
      "vault": "<caminho do vault>",
      "historico": {"ok": true, "motivo": null},
      "trava": null | {"pedido", "rotulo", "sessao", "inicio", "atualizado", "minutos_parada", "duvidas"?},
      "avisos": {
        "protegidas_com_remocao": ["Pasta/Nota.md"],
        "copias_conflito": ["Pasta/Nota (1).md"],
        "regras_mudaram": ["CLAUDE.md"],
        "fora_do_historico": [{"arquivo": "Inbox/Nota.md", "motivo": "dado sensível" | "binário" | "ilegível (...)" | "<erro do git>"}],
        "nomes_nfd": ["Pasta/Nota.md"]
      },
      "perguntas": [{"pergunta": "...", "proposta": "...", "nota": "Inbox/Nota.md"}],
      "ultimo_pedido": {
        "id", "rotulo", "inicio", "fim",
        "notas": [{"acao": "movida" | "criada" | "alterada" | "apagada" | "renomeada", "de": "...", "para": "..."}],
        "garimpo": [{"url", "nota", "veredito": "✅" | "🤔" | "❌", "classificacao", "destino_sugerido"}],
        "colhidos": [{"url", "classificacao", "nota"}]
      }
    }

As `perguntas` do `fim` são as `duvidas` anotadas na trava durante o pedido, mais as do resumo. Os `avisos` se acumulam do aviso do início da sessão até o `fim` do pedido seguinte, que os limpa depois de o pedido
os mostrar.

`trava.json` é a fonte da trava; aqui ela é uma cópia. Um leitor que precise da trava exata lê o `trava.json` ao lado.
Campos novos podem entrar sem subir a `versao`; renomear ou tirar um campo sobe a `versao`.
"""
import datetime
import json
import os
import time

ARQUIVO = "estado.json"
VERSAO = 1


def ler(pasta):
    try:
        with open(os.path.join(pasta, ARQUIVO), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def gravar(pasta, **campos):
    """Mescla os campos no estado atual e grava. Devolve o estado gravado, ou None se não deu para gravar."""
    dados = ler(pasta)
    dados.update(campos)
    dados["versao"] = VERSAO
    dados["gravado_em"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    dados.setdefault("avisos", {})
    dados.setdefault("perguntas", [])
    try:
        os.makedirs(pasta, exist_ok=True)
        destino = os.path.join(pasta, ARQUIVO)
        temporario = destino + ".novo"
        with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
        for tentativa in range(10):
            try:
                os.replace(temporario, destino)
                break
            except PermissionError:
                if tentativa == 9:
                    raise
                time.sleep(0.2)
    except OSError:
        return None
    return dados
