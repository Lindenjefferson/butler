"""Butler: o que o gerente do vault confere e grava sem depender de um modelo.

Uso: python butler.py <subcomando> [--vault PASTA] [opções]. Sem `--vault`, usa o vault configurado que contém a
pasta atual (ou a própria pasta atual). Todo subcomando imprime um JSON em UTF-8 e sai com:
0 ok; 2 erro de uso, de pasta ou de arquivo (o JSON traz `erro`); 3 trava ocupada por outro pedido; 4 sem histórico
para o que foi pedido; 5 token que não é o da trava em vigor; 6 o `fim` achou arquivo mudado sem ponto. `ponto`, `fim`, `inicio` e `desfazer` devolvem
`estado_gravado: false` quando não deu para gravar o estado.json.

Subcomandos:
  preparar-historico [--historico DIR] [--so-conferir]
      Confere a pasta do histórico (fora do vault, de pasta sincronizada e de pasta temporária), cria o git, registra
      o vault na configuração da máquina e grava a foto inicial (`arquivos_na_foto`), sem os arquivos com dado
      sensível nem binários, conferindo também a pasta `.obsidian`. Recusa uma pasta que já é o histórico de outro
      vault. `--so-conferir` só relata o que impediria ou ficaria de fora. Rodado de novo, só confere e completa.
  situacao
      Só lê: histórico ok ou o motivo, trava, quantas mudanças de fora esperam, Inbox, pendências e os pontos do
      pedido em andamento (para dizer onde um Lote parou). Num vault sem histórico nesta máquina, lista em
      `historicos_de_vaults_que_sumiram` os vaults registrados cuja pasta não existe mais (um vault movido).
  inicio --rotulo R [--sessao ID]
      Pega a trava (a mesma sessão retoma a dela) e grava o ponto das mudanças de fora. Devolve `token`, `pedido`,
      `historico_ok`, `motivo` e `mudancas_de_fora`, com os avisos que o aviso do início da sessão já tinha gravado
      e nenhum pedido mostrou ainda. Sem histórico, pega a trava do mesmo jeito e diz o motivo. Numa retomada, traz
      também `pontos_do_pedido` e as `duvidas` já anotadas.
  ponto --token T --rotulo R ARQUIVO...
      Grava um ponto com só esses arquivos (um apagado ou movido entra pelo caminho antigo e pelo novo). Recusa
      pasta, arquivo ilegível, arquivo com dado sensível e binário, e os devolve em `recusados`. Cada ponto leva o
      rótulo do pedido (o do `inicio`), que `pedidos` e `desfazer` mostram.
  duvida --token T --pergunta P [--proposta X] [--nota ARQ]
      Anota na trava uma dúvida de um Lote, na hora em que ela aparece: volta na retomada e entra nas `perguntas`
      do `fim`, mesmo que a conversa tenha sido compactada no meio.
  fim --token T [--resumo ARQ.json | --resumo -] [--sem-ponto-ok]
      Com histórico, confere antes se algum arquivo do vault mudou desde o último ponto (fora da `.obsidian`). Se
      mudou, sai com 6 e a lista em `sem_ponto`, sem soltar a trava: grave o ponto do que o pedido tocou e rode de
      novo; `--sem-ponto-ok` solta mesmo assim (o resto mudou por fora e entra no próximo pedido como mudança de
      fora). Depois grava o resumo no estado.json (campos `notas`, `garimpo`, `colhidos`, `perguntas`, estas
      somadas às `duvidas` anotadas), limpa os avisos já mostrados e solta a trava.
  aviso [--sessao ID]
      O aviso do início da sessão: com a trava livre, pega a trava em nome da sessão, grava as mudanças de fora e
      solta; devolve `linha`. Com BUTLER_SO_LEITURA=1 (uma consulta pelo Wingman, por exemplo), não grava nada.
  soltar-sessao --sessao ID
      Solta a trava se for daquela sessão (hook de fim de sessão).
  liberar-trava --forcar
      Solta a trava de outra sessão, depois do sim do usuário.
  pedidos [--nota ARQ] [--limite N] [--todos]
      Os pedidos gravados, do mais novo ao mais velho (`--todos` inclui os pontos das mudanças de fora). Este,
      `mostrar` e `desfazer` precisam só do git, não da nota de regras: é assim que o preparar a restaura.
  mostrar --pedido ID
      O diff do que o pedido mudou.
  desfazer --token T (--pedido ID | --nota ARQ --ate DATA) [--aplicar] [--aceitar ARQ ...] [--conteudo ARQ ...]
      Sem `--aplicar`, mostra o plano: cada arquivo, a ação e se há conflito (`--conteudo` junta a versão que o
      desfazer deixaria). `--ate` com dia ou minuto inclui o dia ou o minuto inteiro. Com `--aplicar`, restaura o que não tem
      conflito e o aceito, num ponto novo do tipo `desfaz`, com o mesmo filtro do `ponto`. Um nome que outra grafia
      ocupa vai para `nome_ocupado`, que aceitar não resolve.
  renomear --token T DE PARA
      Move a nota, reescreve os wikilinks que apontam para ela e grava tudo num ponto, com o filtro do `ponto`.
      `links_markdown: true` quer dizer que o vault usa links em Markdown, que ele não reescreve.
  conferir ARQUIVO...
      A conferência do toque (ver lib/conferencia.py).
  sensivel ARQUIVO...
      Só a detecção de dado sensível.
  revisar
      A conferência no vault inteiro, mais a árvore de pastas, pastas vazias, cópias de conflito, nomes em NFD,
      notas fora do índice, links quebrados citados por várias notas, possíveis duplicatas e se o vault usa links
      em Markdown (ver lib/conferencia.py).

As regras de cada parte estão nas docstrings de lib/: historico.py (o git fora do vault), trava.py, estado.py (o
formato que o Wingman lê), regras.py (a nota de regras do vault), sensivel.py, conferencia.py e operacoes.py
(mudanças de fora, desfazer, renomear).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config, conferencia, estado, notas, operacoes, regras as regras_mod, sensivel, trava  # noqa: E402
from lib.historico import ErroGit, Historico  # noqa: E402

OK, USO, OCUPADA, SEM_HISTORICO, TOKEN, SEM_PONTO = 0, 2, 3, 4, 5, 6


class Contexto:
    def __init__(self, vault_arg):
        inicio = vault_arg or os.getcwd()
        self.vault = os.path.abspath(config.achar_vault(inicio) or inicio)
        self.configurado = config.historico_de(self.vault) is not None
        pasta = config.historico_de(self.vault)
        self.hist = Historico(self.vault, pasta) if pasta else None
        self.pasta_estado = config.pasta_de_estado(self.vault)
        self.regras = regras_mod.ler(self.vault)
        self.motivo_git = self._motivo_git()
        self.motivo = self.motivo_git
        if self.motivo is None and self.regras is None:
            self.motivo = f"a nota {regras_mod.ARQUIVO} não existe ou não dá para ler"

    def _motivo_git(self):
        if not os.path.isdir(self.vault):
            return "a pasta do vault não existe"
        if not self.hist:
            return "o vault não foi preparado nesta máquina (falta rodar o preparar)"
        return self.hist.motivo_quebra()

    @property
    def ok(self):
        """Histórico funcionando e regras lidas: o modo de parar pelo risco."""
        return self.motivo is None

    @property
    def git_ok(self):
        """Só o git funcionando: dá para listar, mostrar e desfazer, inclusive para restaurar a nota de regras."""
        return self.motivo_git is None

    def gravar_estado(self, **campos):
        """Grava o estado.json; devolve se conseguiu."""
        campos.setdefault("historico", {"ok": self.ok, "motivo": self.motivo})
        campos.setdefault("trava", trava.descrever(trava.ler(self.pasta_estado)))
        campos["vault"] = self.vault
        return estado.gravar(self.pasta_estado, **campos) is not None

    def filtrar(self, caminhos):
        """Separa o que pode entrar no histórico do que não pode: pasta (o ponto lista arquivos), arquivo ilegível,
        binário e dado sensível sem liberação. Devolve (gravar, recusados)."""
        liberadas = self.regras.liberacoes if self.regras else set()
        gravar, recusados = [], []
        for caminho in dict.fromkeys(self.relativo(c) for c in caminhos):
            absoluto = notas.absoluto(self.vault, caminho)
            if os.path.isdir(absoluto):
                recusados.append({"arquivo": caminho, "motivo": "pasta"})
                continue
            if os.path.isfile(absoluto) and self.hist and not self.hist.existe_exato(caminho) \
                    and not self.hist.rastreado(caminho):
                # No Windows, `casa/x.md` abre o `Casa/X.md`, mas o git grava pela grafia: nada entraria.
                recusados.append({"arquivo": caminho, "motivo": "outra grafia: o arquivo no disco é "
                                                                + str(notas.grafia_no_disco(self.vault, caminho))})
                continue
            if os.path.isfile(absoluto):
                try:
                    achados, binario, marca = sensivel.no_arquivo(absoluto, liberadas)
                except OSError as erro:
                    recusados.append({"arquivo": caminho, "motivo": f"ilegível ({erro})"})
                    continue
                if (binario and not (self.regras and self.regras.libera_binario(caminho, marca))) or achados:
                    recusados.append({"arquivo": caminho, "motivo": "binário" if binario else "dado sensível",
                                      "achados": achados, "digital": marca})
                    continue
            gravar.append(caminho)
        return gravar, recusados

    def relativo(self, caminho):
        if os.path.isabs(caminho):
            return notas.rel(self.vault, caminho)
        caminho = caminho.replace("\\", "/")
        while caminho.startswith("./"):
            caminho = caminho[2:]
        return caminho


def saida(dados, codigo=OK):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    return codigo


def _contar_inbox(ctx):
    pasta = (ctx.regras.caminho("inbox") if ctx.regras else None) or "Inbox"
    raiz = notas.absoluto(ctx.vault, pasta)
    if not os.path.isdir(raiz):
        return 0
    return sum(1 for _, _, nomes in os.walk(raiz) for n in nomes if n.lower().endswith(".md"))


def _contar_pendencias(ctx):
    caminho = ctx.regras.caminho("pendencias") if ctx.regras else None
    if not caminho:
        return None
    try:
        texto, _ = notas.ler_texto(ctx.vault, caminho)
    except OSError:
        return None
    return sum(1 for linha in texto.splitlines() if linha.lstrip().startswith("- [ ]"))


def _pontos_do_pedido(ctx, pedido):
    """Os pontos que o pedido gravou (sem o das mudanças de fora), do mais velho ao mais novo."""
    if not ctx.git_ok or not pedido:
        return []
    return [{"data": c["data"], "assunto": c["assunto"], "tipo": c["tipo"]}
            for c in operacoes.commits_do_pedido(ctx.hist, pedido)]


AVISOS = ("protegidas_com_remocao", "copias_conflito", "regras_mudaram", "fora_do_historico", "nomes_nfd")


def _avisos(ctx, fora):
    """Junta os avisos novos aos que o estado.json ainda guarda (os do aviso do início da sessão, que o primeiro
    pedido precisa ver). Eles saem no `fim` do pedido, depois de mostrados."""
    guardados = estado.ler(ctx.pasta_estado).get("avisos") or {}
    juntos = {}
    for chave in AVISOS:
        lista = []
        for item in list(guardados.get(chave) or []) + list((fora or {}).get(chave) or []):
            if item not in lista:
                lista.append(item)
        juntos[chave] = lista
    return juntos


def _token(ctx, args):
    try:
        return trava.tocar(ctx.pasta_estado, args.token)
    except trava.TokenInvalido as erro:
        raise SystemExit(saida({"ok": False, "erro": str(erro)}, TOKEN))


# -- subcomandos -------------------------------------------------------------------------------------------------

def cmd_preparar_historico(args):
    vault = os.path.abspath(args.vault or os.getcwd())
    if not os.path.isdir(vault):
        return saida({"ok": False, "erro": "a pasta do vault não existe"}, USO)
    pasta = os.path.abspath(args.historico or config.historico_de(vault) or config.historico_padrao(vault))
    proibida = config.motivo_pasta_proibida(pasta, vault)
    outro = config.dono_do_historico(pasta, vault)
    if outro and not proibida:
        proibida = f"a pasta já é o histórico de outro vault ({outro})"
    regras = regras_mod.ler(vault)
    liberadas = regras.liberacoes if regras else set()
    ficariam_fora, copias = [], []
    for caminho in notas.arquivos(vault, com_obsidian=True):
        if notas.copia_conflito(caminho):
            copias.append(caminho)
        try:
            achados, binario, marca = sensivel.no_arquivo(notas.absoluto(vault, caminho), liberadas)
        except OSError as erro:
            ficariam_fora.append({"arquivo": caminho, "motivo": f"ilegível ({erro})"})
            continue
        if binario and not (regras and regras.libera_binario(caminho, marca)):
            ficariam_fora.append({"arquivo": caminho, "motivo": "binário", "digital": marca})
        elif achados:
            ficariam_fora.append({"arquivo": caminho, "motivo": "dado sensível", "achados": achados})
    relatorio = {"vault": vault, "historico": pasta, "pasta_proibida": proibida, "copias_conflito": copias,
                 "fora_do_historico": ficariam_fora}
    if proibida:
        return saida(dict(relatorio, ok=False, erro=proibida), USO)
    if args.so_conferir:
        return saida(dict(relatorio, ok=True, so_conferir=True))
    hist = Historico(vault, pasta)
    ja_existia = hist.existe() and hist.tem_commit()
    try:
        hist.criar()
        config.registrar(vault, pasta)
        sha, gravados = None, []
        if not hist.tem_commit():
            fora = {item["arquivo"] for item in ficariam_fora}
            todos = [c for _, c in hist.mudancas() if c not in fora]
            sha, gravados, nao = hist.gravar(todos, "preparar", "foto inicial do vault", "preparar")
            relatorio["fora_do_historico"] += [{"arquivo": i["arquivo"], "motivo": i["motivo"]} for i in nao]
            if sha is None:
                hist.git("commit", "-q", "--allow-empty", "--no-verify", "-m",
                         "[preparar] foto inicial do vault (vazio)\n\nButler-Pedido: preparar\nButler-Tipo: preparar")
    except (ErroGit, OSError) as erro:
        return saida(dict(relatorio, ok=False, erro=f"não deu para criar o histórico: {erro}"), SEM_HISTORICO)
    ctx = Contexto(vault)
    ctx.gravar_estado(avisos={"fora_do_historico": relatorio["fora_do_historico"], "copias_conflito": copias})
    return saida(dict(relatorio, ok=True, ja_existia=ja_existia, foto_inicial=sha, arquivos_na_foto=len(gravados),
                      historico_ok=ctx.ok, motivo=ctx.motivo))


def cmd_situacao(args):
    ctx = Contexto(args.vault)
    atual = trava.ler(ctx.pasta_estado)
    pendentes = None
    if ctx.ok:
        try:
            pendentes = len(ctx.hist.mudancas())
        except ErroGit:
            pendentes = None
    return saida({"vault": ctx.vault, "configurado": ctx.configurado, "historico_ok": ctx.ok, "motivo": ctx.motivo,
                  "trava": trava.descrever(atual), "mudancas_de_fora_pendentes": pendentes,
                  "inbox": _contar_inbox(ctx), "pendencias": _contar_pendencias(ctx),
                  "pontos_do_pedido_em_andamento": _pontos_do_pedido(ctx, (atual or {}).get("pedido")),
                  "regras": ctx.regras.como_dict() if ctx.regras else None,
                  "historicos_de_vaults_que_sumiram": [] if ctx.configurado else config.sumidos()})


def cmd_inicio(args):
    ctx = Contexto(args.vault)
    try:
        atual = trava.pegar(ctx.pasta_estado, args.rotulo, args.sessao)
    except trava.Ocupada as ocupada:
        return saida({"ok": False, "trava_ocupada": trava.descrever(ocupada.trava)}, OCUPADA)
    resposta = {"ok": True, "token": atual["token"], "pedido": atual["pedido"], "retomada": atual["retomada"],
                "historico_ok": ctx.ok, "motivo": ctx.motivo, "mudancas_de_fora": None}
    if ctx.ok:
        ctx.hist.limpar_index_lock()
        # Na retomada (compactação, ou um serviço que chama `inicio` de novo no meio do próprio pedido), o que
        # está sem ponto pode ser trabalho do próprio pedido (escreveu e ainda não apontou) ou uma mudança
        # genuína de fora (a trava impede outra sessão do Claude de escrever, mas não o Obsidian): o git não
        # distingue uma coisa da outra. Quem está retomando e sabe o que escreveu e ainda não apontou avisa em
        # `--continuando`; só esses caminhos ficam de fora da varredura (continuam sem ponto, não "fora"). Sem
        # `--continuando`, o comportamento é o de sempre: tudo o que está sem ponto vira um ponto de "fora".
        ignorar = {ctx.relativo(a) for a in (args.continuando or [])}
        try:
            resposta["mudancas_de_fora"] = operacoes.registrar_fora(ctx.hist, ctx.regras, args.rotulo,
                                                                    atual["pedido"], ignorar=ignorar)
        except (ErroGit, OSError) as erro:
            ctx.motivo = f"não deu para gravar as mudanças de fora ({erro})"
            resposta.update(historico_ok=False, motivo=ctx.motivo)
    if atual["retomada"]:
        resposta["pontos_do_pedido"] = _pontos_do_pedido(ctx, atual["pedido"])
        resposta["duvidas"] = atual.get("duvidas") or []
    avisos = _avisos(ctx, resposta["mudancas_de_fora"])
    if resposta["mudancas_de_fora"] is not None:
        resposta["mudancas_de_fora"].update(avisos)
    resposta["estado_gravado"] = ctx.gravar_estado(avisos=avisos)
    return saida(resposta)


def cmd_ponto(args):
    ctx = Contexto(args.vault)
    atual = _token(ctx, args)
    if not ctx.ok:
        return saida({"ok": False, "historico_ok": False, "motivo": ctx.motivo}, SEM_HISTORICO)
    gravar, recusados = ctx.filtrar(args.arquivos)
    try:
        sha, gravados, nao = (ctx.hist.gravar(gravar, "nota", args.rotulo, atual["pedido"],
                                              rotulo_pedido=atual["rotulo"]) if gravar else (None, [], []))
    except ErroGit as erro:
        return saida({"ok": False, "erro": str(erro)}, SEM_HISTORICO)
    return saida({"ok": True, "ponto": sha, "gravados": gravados, "recusados": recusados + nao,
                  "estado_gravado": ctx.gravar_estado()})


def cmd_duvida(args):
    ctx = Contexto(args.vault)
    duvida = {"pergunta": args.pergunta}
    if args.proposta:
        duvida["proposta"] = args.proposta
    if args.nota:
        duvida["nota"] = ctx.relativo(args.nota)
    try:
        duvidas = trava.anotar_duvida(ctx.pasta_estado, args.token, duvida)
    except trava.TokenInvalido as erro:
        return saida({"ok": False, "erro": str(erro)}, TOKEN)
    return saida({"ok": True, "duvidas": len(duvidas)})


def _sem_ponto(ctx):
    """O que mudou no vault desde o último ponto, fora da configuração do Obsidian (que muda sozinha)."""
    if not ctx.ok:
        return []
    try:
        return [{"estado": e, "arquivo": c} for e, c in ctx.hist.mudancas() if not c.startswith(".obsidian/")]
    except ErroGit:
        return []


def cmd_fim(args):
    ctx = Contexto(args.vault)
    atual = _token(ctx, args)
    sem_ponto = _sem_ponto(ctx)
    if sem_ponto and not args.sem_ponto_ok:
        return saida({"ok": False, "sem_ponto": sem_ponto,
                      "erro": "há arquivo mudado sem ponto: grave o ponto do que o pedido tocou e rode o fim de "
                              "novo, ou use --sem-ponto-ok se o resto mudou por fora"}, SEM_PONTO)
    resumo = {}
    if args.resumo:
        try:
            texto = sys.stdin.read() if args.resumo == "-" else open(args.resumo, encoding="utf-8").read()
            resumo = json.loads(texto) if texto.strip() else {}
        except (OSError, ValueError) as erro:
            return saida({"ok": False, "erro": f"resumo ilegível: {erro}"}, USO)
    if not isinstance(resumo, dict):
        return saida({"ok": False, "erro": "o resumo precisa ser um objeto JSON"}, USO)
    ultimo = {"id": atual["pedido"], "rotulo": atual["rotulo"], "inicio": atual["inicio"], "fim": trava.agora()}
    for campo in ("notas", "garimpo", "colhidos"):
        if isinstance(resumo.get(campo), list):
            ultimo[campo] = resumo[campo]
    perguntas = list(atual.get("duvidas") or [])
    for pergunta in resumo.get("perguntas") if isinstance(resumo.get("perguntas"), list) else []:
        trava.somar_duvida(perguntas, pergunta)
    trava.soltar(ctx.pasta_estado, args.token)
    gravado = ctx.gravar_estado(trava=None, ultimo_pedido=ultimo, perguntas=perguntas,
                                avisos={chave: [] for chave in AVISOS})
    return saida({"ok": True, "pedido": atual["pedido"], "pontos": len(_pontos_do_pedido(ctx, atual["pedido"])),
                  "sem_ponto": sem_ponto, "estado_gravado": gravado})


def _linha_aviso(ctx, fora, ocupada, sessao=None):
    partes = []
    inbox = _contar_inbox(ctx)
    partes.append(f"Inbox com {inbox} nota{'s' if inbox != 1 else ''}")
    pend = _contar_pendencias(ctx)
    if pend is not None:
        partes.append(f"{pend} pendência{'s' if pend != 1 else ''}")
    if ocupada and sessao and ocupada.get("sessao") == sessao:
        partes.append(f"pedido desta sessão em andamento: {ocupada.get('rotulo', '?')} (continua com o mesmo token)")
    elif ocupada:
        partes.append(f"pedido em andamento: {ocupada.get('rotulo', '?')} (parado há {ocupada.get('minutos_parada')}"
                      " min)")
    if fora:
        if fora["arquivos"]:
            partes.append(f"{len(fora['arquivos'])} arquivo(s) mudaram por fora")
        for chave, texto in (("protegidas_com_remocao", "nota protegida perdeu dados por fora"),
                             ("copias_conflito", "cópia de conflito nova"), ("regras_mudaram", "regras mudaram"),
                             ("fora_do_historico", "fora do histórico")):
            if fora.get(chave):
                nomes = [i["arquivo"] if isinstance(i, dict) else i for i in fora[chave]]
                partes.append(f"{texto}: {', '.join(nomes[:3])}{' …' if len(nomes) > 3 else ''}")
    partes.append("histórico ok" if ctx.ok else f"sem histórico ({ctx.motivo}): mostrar antes de alterar várias notas")
    return "Butler: " + " · ".join(partes)


def cmd_aviso(args):
    ctx = Contexto(args.vault)
    if not ctx.configurado and ctx.regras is None:
        return saida({"vault_do_butler": False})
    fora, ocupada = None, None
    if os.environ.get("BUTLER_SO_LEITURA") != "1":
        try:
            # Como `aviso:<sessão>`: o hook de fim a solta se este processo morrer no meio, e o aviso nunca retoma
            # (nem solta, no finally) o pedido em andamento da própria sessão, depois de uma compactação.
            sessao = trava.AVISO + args.sessao if args.sessao else None
            atual = trava.pegar(ctx.pasta_estado, "aviso do início da sessão", sessao)
        except trava.Ocupada as erro:
            ocupada = trava.descrever(erro.trava)
        else:
            try:
                if ctx.ok:
                    ctx.hist.limpar_index_lock()
                    fora = operacoes.registrar_fora(ctx.hist, ctx.regras, "início da sessão", atual["pedido"])
            except (ErroGit, OSError) as erro:
                ctx.motivo = f"não deu para gravar as mudanças de fora ({erro})"
            finally:
                try:
                    trava.soltar(ctx.pasta_estado, atual["token"])
                except trava.TokenInvalido:
                    pass  # o inicio da sessão tomou a trava de um aviso lento: ela já não é deste aviso
    if fora is not None:
        ctx.gravar_estado(avisos=_avisos(ctx, fora))
    return saida({"vault_do_butler": True, "historico_ok": ctx.ok, "motivo": ctx.motivo,
                  "linha": _linha_aviso(ctx, fora, ocupada, args.sessao), "mudancas_de_fora": fora})


def cmd_soltar_sessao(args):
    ctx = Contexto(args.vault)
    solta = trava.soltar_da_sessao(ctx.pasta_estado, args.sessao)
    if solta and ctx.configurado:
        ctx.gravar_estado(trava=None)
    return saida({"soltou": solta})


def cmd_liberar_trava(args):
    if not args.forcar:
        return saida({"ok": False, "erro": "use --forcar, depois do sim do usuário"}, USO)
    ctx = Contexto(args.vault)
    anterior = trava.forcar(ctx.pasta_estado)
    ctx.gravar_estado(trava=None)
    return saida({"ok": True, "liberada": trava.descrever(anterior)})


def _exigir_historico(ctx):
    """Listar, mostrar e desfazer precisam só do git: funcionam sem a nota de regras, para poder restaurá-la."""
    if not ctx.git_ok:
        raise SystemExit(saida({"ok": False, "historico_ok": False, "motivo": ctx.motivo}, SEM_HISTORICO))


def cmd_pedidos(args):
    ctx = Contexto(args.vault)
    _exigir_historico(ctx)
    caminho = ctx.relativo(args.nota) if args.nota else None
    grupos, ordem = {}, []
    for commit in ctx.hist.commits(limite=5000, caminho=caminho):
        if not args.todos and commit["tipo"] not in ("nota", "desfaz"):
            continue
        chave = commit["pedido"] or commit["sha"]
        if chave not in grupos and len(ordem) >= args.limite:
            break  # os pontos de um pedido são seguidos (a trava): os próximos já são de pedidos mais velhos
        if chave not in grupos:
            grupos[chave] = {"pedido": chave, "rotulo": "", "rotulos": [], "tipos": [], "primeiro": commit["data"],
                             "ultimo": commit["data"], "arquivos": [], "pontos": 0}
            ordem.append(chave)
        grupo = grupos[chave]
        grupo["rotulo"] = commit["rotulo_pedido"] or grupo["rotulo"] or commit["assunto"].split("] ", 1)[-1]
        grupo["primeiro"] = commit["data"]
        grupo["pontos"] += 1
        rotulo = commit["assunto"].split("] ", 1)[-1]
        if rotulo not in grupo["rotulos"]:
            grupo["rotulos"].insert(0, rotulo)
        if commit["tipo"] not in grupo["tipos"]:
            grupo["tipos"].append(commit["tipo"])
        for arquivo in ctx.hist.arquivos_do_commit(commit["sha"]):
            if caminho and arquivo != caminho:
                continue  # com --nota, só a nota pedida (a foto inicial tem o vault inteiro)
            if arquivo not in grupo["arquivos"]:
                grupo["arquivos"].append(arquivo)
    return saida({"ok": True, "pedidos": [grupos[c] for c in ordem[:args.limite]]})


def cmd_mostrar(args):
    ctx = Contexto(args.vault)
    _exigir_historico(ctx)
    lista = operacoes.commits_do_pedido(ctx.hist, args.pedido)
    if not lista:
        return saida({"ok": False, "erro": "nenhum ponto com esse pedido"}, USO)
    # Ponto por ponto: o que mudou por fora no meio do pedido (numa retomada) não aparece como se fosse dele.
    diff = "".join(ctx.hist.texto("show", "--no-color", "--no-renames", "--format=", commit["sha"])
                   for commit in lista)
    return saida({"ok": True, "pedido": args.pedido, "diff": diff})


def cmd_desfazer(args):
    ctx = Contexto(args.vault)
    atual = _token(ctx, args)
    _exigir_historico(ctx)
    if args.pedido:
        plano = operacoes.plano_pedido(ctx.hist, args.pedido)
        if plano is None:
            return saida({"ok": False, "erro": "nenhum ponto com esse pedido"}, USO)
        rotulo = f"desfaz: {plano['rotulo']}"
    elif args.nota and args.ate:
        plano = operacoes.plano_nota(ctx.hist, ctx.relativo(args.nota), args.ate)
        if plano.get("sem_ponto"):
            return saida({"ok": False, "erro": "não há ponto de retorno dessa nota antes dessa data",
                          "plano": plano}, USO)
        rotulo = f"volta {plano['arquivo']} como estava em {args.ate}"
    else:
        return saida({"ok": False, "erro": "use --pedido, ou --nota com --ate"}, USO)
    if not args.aplicar:
        conteudo = {ctx.relativo(a) for a in args.conteudo or []}
        return saida({"ok": True, "aplicado": False, "plano": operacoes.publico(plano, conteudo)})
    aceitar = {ctx.relativo(a) for a in args.aceitar or []}
    manter = [(ctx.regras.caminho("inbox") if ctx.regras else None) or "Inbox"]
    aplicados, pulados, ocupados = operacoes.aplicar(ctx.hist, plano, aceitar, manter)
    sha, recusados = None, []
    if aplicados:
        gravar, recusados = ctx.filtrar(aplicados)
        if gravar:
            sha, _, nao = ctx.hist.gravar(gravar, "desfaz", rotulo, atual["pedido"], rotulo_pedido=atual["rotulo"])
            recusados += nao
    return saida({"ok": True, "aplicado": True, "ponto": sha, "aplicados": aplicados, "pulados_por_conflito": pulados,
                  "nome_ocupado": ocupados, "recusados": recusados, "plano": operacoes.publico(plano), "estado_gravado": ctx.gravar_estado()})


def cmd_renomear(args):
    ctx = Contexto(args.vault)
    atual = _token(ctx, args)
    de, para = ctx.relativo(args.de), ctx.relativo(args.para)
    try:
        tocadas = operacoes.renomear(ctx.vault, de, para)
    except (FileNotFoundError, FileExistsError) as erro:
        return saida({"ok": False, "erro": str(erro)}, USO)
    sha, recusados = None, []
    if ctx.ok:
        gravar, recusados = ctx.filtrar([de, para, *tocadas])
        if para in {r["arquivo"] for r in recusados}:
            # Sem o destino, gravar só a saída da origem deixaria o histórico com a nota sumida.
            gravar = [c for c in gravar if c != de]
        if gravar:
            sha, _, nao = ctx.hist.gravar(gravar, "nota", f"renomeia {de} para {para}", atual["pedido"],
                                          rotulo_pedido=atual["rotulo"])
            recusados += nao
    return saida({"ok": True, "de": de, "para": para, "links_atualizados": tocadas, "ponto": sha,
                  "recusados": recusados, "historico_ok": ctx.ok,
                  "links_markdown": notas.usa_links_markdown(ctx.vault)})


def cmd_conferir(args):
    ctx = Contexto(args.vault)
    lista = notas.arquivos(ctx.vault)
    nomes, bases = notas.indice(lista), conferencia.nomes_de_notas(lista)
    resultados = [conferencia.conferir(ctx.vault, ctx.relativo(a), ctx.regras, nomes, bases) for a in args.arquivos]
    return saida({"ok": True, "regras_lidas": ctx.regras is not None, "notas": resultados})


def cmd_sensivel(args):
    ctx = Contexto(args.vault)
    liberadas = ctx.regras.liberacoes if ctx.regras else set()
    resultado = []
    for arquivo in args.arquivos:
        caminho = ctx.relativo(arquivo)
        achados, binario, marca = sensivel.no_arquivo(notas.absoluto(ctx.vault, caminho), liberadas)
        resultado.append({"arquivo": caminho, "achados": achados, "binario": binario, "digital": marca})
    return saida({"ok": True, "arquivos": resultado})


def cmd_revisar(args):
    ctx = Contexto(args.vault)
    return saida(dict(conferencia.revisar(ctx.vault, ctx.regras), ok=True, regras_lidas=ctx.regras is not None))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="butler.py", description="Gerente do vault: histórico, trava e conferência.")
    sub = parser.add_subparsers(dest="comando", required=True)

    def novo(nome, funcao):
        p = sub.add_parser(nome)
        p.add_argument("--vault")
        p.set_defaults(funcao=funcao)
        return p

    p = novo("preparar-historico", cmd_preparar_historico)
    p.add_argument("--historico")
    p.add_argument("--so-conferir", action="store_true")
    novo("situacao", cmd_situacao)
    p = novo("inicio", cmd_inicio)
    p.add_argument("--rotulo", required=True)
    p.add_argument("--sessao")
    p.add_argument("--continuando", nargs="*")
    p = novo("ponto", cmd_ponto)
    p.add_argument("--token", required=True)
    p.add_argument("--rotulo", required=True)
    p.add_argument("arquivos", nargs="+")
    p = novo("duvida", cmd_duvida)
    p.add_argument("--token", required=True)
    p.add_argument("--pergunta", required=True)
    p.add_argument("--proposta")
    p.add_argument("--nota")
    p = novo("fim", cmd_fim)
    p.add_argument("--token", required=True)
    p.add_argument("--resumo")
    p.add_argument("--sem-ponto-ok", action="store_true")
    p = novo("aviso", cmd_aviso)
    p.add_argument("--sessao")
    p = novo("soltar-sessao", cmd_soltar_sessao)
    p.add_argument("--sessao", required=True)
    p = novo("liberar-trava", cmd_liberar_trava)
    p.add_argument("--forcar", action="store_true")
    p = novo("pedidos", cmd_pedidos)
    p.add_argument("--nota")
    p.add_argument("--limite", type=int, default=20)
    p.add_argument("--todos", action="store_true")
    p = novo("mostrar", cmd_mostrar)
    p.add_argument("--pedido", required=True)
    p = novo("desfazer", cmd_desfazer)
    p.add_argument("--token", required=True)
    p.add_argument("--pedido")
    p.add_argument("--nota")
    p.add_argument("--ate")
    p.add_argument("--aplicar", action="store_true")
    p.add_argument("--aceitar", nargs="*")
    p.add_argument("--conteudo", nargs="*")
    p = novo("renomear", cmd_renomear)
    p.add_argument("--token", required=True)
    p.add_argument("de")
    p.add_argument("para")
    for nome, funcao in (("conferir", cmd_conferir), ("sensivel", cmd_sensivel)):
        p = novo(nome, funcao)
        p.add_argument("arquivos", nargs="+")
    novo("revisar", cmd_revisar)
    args = parser.parse_args(argv)
    try:
        return args.funcao(args)
    except SystemExit as saida_antecipada:
        return saida_antecipada.code
    except trava.TokenInvalido as erro:
        return saida({"ok": False, "erro": str(erro)}, TOKEN)
    except (ErroGit, OSError) as erro:
        # Arquivo travado pelo sincronizador, arquivo que não existe, git que falhou: a saída continua JSON.
        return saida({"ok": False, "erro": f"{type(erro).__name__}: {erro}"}, USO)


if __name__ == "__main__":
    sys.exit(main())
