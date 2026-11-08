"""Um pedido por vez no vault.

A trava é o arquivo `trava.json` na pasta de estado do vault (a do histórico), criado de forma atômica
(`O_CREAT | O_EXCL`): de duas sessões que tentam ao mesmo tempo, só uma consegue. Ela guarda `pedido`, `token`,
`rotulo`, `sessao`, `inicio`, `atualizado` e, quando o pedido anotou alguma, `duvidas` (as perguntas que esperam o
fim de um Lote, guardadas aqui para não se perderem numa compactação).

- Quem pega recebe o `token` e o passa a cada `ponto`, `desfazer`, `renomear` e ao `fim`.
- A mesma sessão (mesmo `sessao`) retoma a própria trava em vez de ficar presa nela: é o que salva o pedido depois
  de uma compactação da conversa, quando o token se perdeu.
- A trava não expira sozinha. Uma sessão viva pode passar horas esperando as respostas de um Lote. Quem acha a trava
  de outra sessão recebe a trava com a idade (`minutos_parada`) e mostra ao usuário, que decide liberar
  (`liberar-trava --forcar`).
- O hook de fim de sessão solta só a trava daquela sessão.
- O aviso do início da sessão pega a trava como `aviso:<sessão>`: nunca retoma (nem solta) o pedido em andamento
  da própria sessão, que continua depois de uma compactação. Se ele morrer segurando a trava, o fim da sessão a
  solta, e o próximo `inicio` da mesma sessão a toma.
- Trava ilegível (a sessão caiu no meio da escrita) conta como ocupada, com `corrompida: true`.

`trava.json` é a fonte. O `estado.json` repete a trava para o Wingman, regravado a cada mudança dela.
"""
import datetime
import json
import os
import re
import secrets
import time

from .regras import sem_acento

ARQUIVO = "trava.json"
AVISO = "aviso:"  # prefixo da sessão do aviso do início da sessão, que nunca retoma o pedido da sessão


class Ocupada(Exception):
    def __init__(self, trava):
        super().__init__("há um pedido em andamento no vault")
        self.trava = trava


class TokenInvalido(Exception):
    pass


def agora():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _caminho(pasta):
    return os.path.join(pasta, ARQUIVO)


def ler(pasta):
    """A trava atual, ou None se livre. Ilegível vira {"corrompida": True}."""
    try:
        with open(_caminho(pasta), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {"corrompida": True}
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return {"corrompida": True}


def _repetir(funcao, *args):
    """No Windows, um leitor com o arquivo aberto (o Wingman lendo a trava) faz `replace` e `remove` falharem por
    um instante: tenta de novo por até 2 s."""
    for tentativa in range(10):
        try:
            return funcao(*args)
        except PermissionError:
            if tentativa == 9:
                raise
            time.sleep(0.2)


def _remover(pasta):
    _repetir(os.remove, _caminho(pasta))


def _escrever(pasta, dados):
    temporario = _caminho(pasta) + ".novo"
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    _repetir(os.replace, temporario, _caminho(pasta))


def descrever(trava):
    """A trava sem o token, com a idade em minutos: o que se mostra a outra sessão e ao Wingman."""
    if trava is None:
        return None
    publica = {chave: valor for chave, valor in trava.items() if chave != "token"}
    try:
        atualizado = datetime.datetime.fromisoformat(trava["atualizado"])
        publica["minutos_parada"] = int((datetime.datetime.now().astimezone() - atualizado).total_seconds() // 60)
    except (KeyError, TypeError, ValueError):
        publica["minutos_parada"] = None
    return publica


def pegar(pasta, rotulo, sessao=None):
    """Pega a trava ou levanta Ocupada. A mesma sessão retoma a dela (`retomada: True`)."""
    os.makedirs(pasta, exist_ok=True)
    token = secrets.token_hex(8)
    momento = agora()
    dados = {"pedido": datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + token[:4], "token": token,
             "rotulo": rotulo, "sessao": sessao or "", "inicio": momento, "atualizado": momento}
    try:
        descritor = os.open(_caminho(pasta), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        atual = ler(pasta)
        if atual and not atual.get("corrompida") and sessao and atual.get("sessao") == sessao:
            atual["atualizado"] = momento
            _escrever(pasta, atual)
            return dict(atual, retomada=True)
        if atual and sessao and atual.get("sessao") == AVISO + sessao:
            # O aviso desta mesma sessão morreu segurando a trava (o hook passou do tempo): não há pedido a retomar.
            _escrever(pasta, dados)
            return dict(dados, retomada=False)
        if atual is None:
            return pegar(pasta, rotulo, sessao)
        raise Ocupada(atual)
    with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return dict(dados, retomada=False)


def verificar(pasta, token):
    atual = ler(pasta)
    if not atual or atual.get("corrompida") or atual.get("token") != token:
        raise TokenInvalido("o token não é o da trava em vigor: o pedido precisa começar de novo com `inicio`")
    return atual


def tocar(pasta, token):
    atual = verificar(pasta, token)
    atual["atualizado"] = agora()
    _escrever(pasta, atual)
    return atual


def anotar_duvida(pasta, token, duvida):
    """Guarda na trava uma dúvida do pedido (`pergunta`, `proposta`, `nota`), sem repetir: ela sobrevive a uma
    compactação da conversa e volta na retomada e no `fim`."""
    atual = verificar(pasta, token)
    atual["atualizado"] = agora()
    duvidas = atual.setdefault("duvidas", [])
    somar_duvida(duvidas, duvida)
    _escrever(pasta, atual)
    return duvidas


def _chave_duvida(duvida):
    """A mesma pergunta sobre a mesma nota, ainda que reescrita sem acento, com outra pontuação ou outra proposta."""
    if not isinstance(duvida, dict):
        return json.dumps(duvida, sort_keys=True, ensure_ascii=False)
    texto = " ".join(re.sub(r"[^\w]+", " ", sem_acento(str(duvida.get("pergunta", "")))).split())
    return texto, duvida.get("nota")


def somar_duvida(duvidas, duvida):
    """Acrescenta a dúvida à lista se ela ainda não está lá; a primeira versão fica."""
    if _chave_duvida(duvida) not in {_chave_duvida(d) for d in duvidas}:
        duvidas.append(duvida)


def soltar(pasta, token):
    verificar(pasta, token)
    _remover(pasta)


def soltar_da_sessao(pasta, sessao):
    atual = ler(pasta)
    if sessao and atual and atual.get("sessao") in (sessao, AVISO + sessao):
        _remover(pasta)
        return True
    return False


def forcar(pasta):
    atual = ler(pasta)
    try:
        _remover(pasta)
    except FileNotFoundError:
        pass
    return atual
