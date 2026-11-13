#!/usr/bin/env python3
"""Guarda a proposta de uma exploração fora do vault, consolida as respostas dos subagentes e acompanha cada item.

Tudo fica em `<pasta de estado do vault>/explorar/<id>/` (`lib.config.pasta_de_estado`), nunca dentro do vault:
`proposta.json` e um `g<N>.json` por grupo, gravado pelo subagente daquele grupo. Gravação atômica.

Subcomandos (`python proposta.py <vault> <subcomando>`), todos imprimem JSON:

- `iniciar --alvo <alvo.json> --rotulo "<texto>"`: cria a proposta a partir da saída do `alvo.py montar`, com a
  digital (sha256 do conteúdo) de cada nota dos grupos. Imprime `{"id", "pasta", "grupos": [{"id", "saida"}]}`;
  `saida` é o caminho que vai no prompt do subagente do grupo.
- `consolidar --id <id>`: lê os `g*.json`, junta por destino e grava `itens`. Imprime
  `{"itens": N, "blocos": M, "faltam_grupos": [...], "avisos": [...], "refeitos": [n...], "mudaram": [n...],
  "bloqueados": [n...]}`. Refazer mantém o número e o estado dos itens que continuam (mesmo tipo e destino); item
  novo ganha o próximo número. Item aberto que continua e cujas origens, operações ou detalhes mudaram vem em
  `mudaram`, em qualquer estado (um `pendente` que absorveu um item refeito também: o dono não viu o item como
  ficou); se estava `aprovado` ou `bloqueado`, volta a `pendente` e vem também em `refeitos`. Item `aplicado` ou
  `recusado` fica como estava, mesmo sem entrada no `g*.json`: origem nova no mesmo destino vira item novo. Item
  aberto que depende de um recusado ou bloqueado vem em `bloqueados`.
  Avisos de entrada ignorada: `alvo_vazio: <nota>` (`linha` ou `fundir` sem alvo), `fundir_em_si: <nota>` e
  `linha_em_si: <nota>` (a lista seria apagada depois de ganhar a linha).
- `bloco --id <id> --n <N>`: os itens do bloco N (até 10).
- `marcar --id <id> --itens 1,3 --estado pendente|aprovado|aplicado|recusado`: só a partir de, respectivamente,
  `aprovado` (devolve um item refeito), `pendente`, `aprovado` e `pendente|aprovado|bloqueado` (ou o próprio
  estado, exceto `pendente`); um item fora disso faz o pedido inteiro sair com erro, sem marcar nenhum. Recusar
  marca como `bloqueado` os itens pendentes ou aprovados que dependem dele (em cadeia).
- `conferir --id <id> [--itens 1,3]`: recalcula as digitais das origens e dos destinos de cada item;
  `{"mudou": [n...], "ok": [n...]}`. Item que mudou não se aplica: a sessão refaz só ele e chama `redigitar`.
  Marcar `aplicado` atualiza a digital do destino do item, que os outros itens com o mesmo destino conferem.
- `redigitar --id <id> --itens 1,3`: grava as digitais atuais das origens e do destino desses itens.
- `listar`: propostas ainda não consolidadas ou com item `pendente`/`aprovado`, e em `pasta` a pasta de
  trabalho do explorar (`<pasta de estado>/explorar`), onde vão o `alvo.json` e os vídeos reassistidos.
  `remover --id <id>`.

Saída: 0 ok, 2 proposta, item ou argumento inválido.

Formato do `g<N>.json` (o que o subagente grava):

    {"grupo": "g1",
     "notas": [{"nota": "<caminho>", "destino": {"tipo": "linha|detalhe|fundir|mover|descartar|arquivar",
                                               "alvo": "<nota ou pasta>"},
                "porque": "...", "linha": "<linha pronta, se tipo linha>", "cortes": [], "esboco": [],
                "acrescimos": [{"texto", "url", "confianca": "confirmado|provavel|nao_verificado"}],
                "atencao": []}],
     "temas": [{"nome", "pasta", "notas": []}]}

O `alvo` de `linha`, `detalhe` e `fundir` é um caminho (`Pasta/Nome`, com ou sem `.md`) ou só um nome. Só o nome:
`fundir` vai para a nota criada por outro item ou para a nota existente com esse nome; `linha` vai para a nota
existente com esse nome ou nasce na pasta do tema de mesmo nome, ou na pasta comum das origens; `detalhe` nasce na
pasta comum das origens. `mover` e `arquivar` recebem uma pasta (a nota mantém o nome) ou um caminho `.md`
(renomeia); `arquivar` sem alvo vai para `Arquivo/<caminho>`. `descartar` não tem alvo; `detalhe` sem alvo fica
na própria nota; `linha` e `fundir` sem alvo são ignorados com aviso.

Item consolidado: um aberto por destino e tipo, numerado na ordem dos blocos (listas, notas de detalhe e fusões,
movidos, descartes e arquivados) no primeiro `consolidar`; o número não muda depois (item que chega num
`consolidar` seguinte vai para o fim):

    {"n", "destino", "tipo", "origens": [...], "operacoes": [...], "depende_de": [n...],
     "links_de_entrada": {origem: [notas que linkam]}, "avisos": [...], "detalhes": {origem: {...}},
     "estado": "pendente|aprovado|aplicado|recusado|bloqueado"}

Nomes comparados sem caixa e em NFC; o destino mostrado guarda a primeira grafia vista. `depende_de`: o item escreve
num destino que outro item cria ou reescreve (lista ou nota de detalhe). `links_de_entrada`: para cada origem que
some ou muda de nome, as notas com `[[Nome]]`, `[[Nome|...]]` ou `[[Nome#...]]`. Avisos: `nome_invalido`
(`: * ? " < > | / \\` ou vazio), `nome_repetido` (destino novo com o nome de uma nota existente que não
é origem do item),
`pasta_nova` (a pasta do destino não existe) e `protegida` (origem ou destino protegidos pela nota de regras).
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import posixpath
import re
import secrets
import shutil
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "gerente"))
from lib import config as config_lib  # noqa: E402
from lib import regras as regras_lib  # noqa: E402

TIPOS = ("linha", "detalhe", "fundir", "mover", "descartar", "arquivar")
ORDEM = {"linha": (0, 0), "detalhe": (1, 0), "fundir": (1, 1), "mover": (2, 0), "descartar": (3, 0),
         "arquivar": (3, 1)}
CRIAM = ("linha", "detalhe")
ESTADOS_ABERTOS = ("pendente", "aprovado")
FECHADOS = ("aplicado", "recusado")
# estado pedido -> estados de onde ele pode vir; fora disso o `marcar` sai com erro e não muda nada
VEM_DE = {"pendente": ("aprovado",), "aprovado": ("pendente", "aprovado"), "aplicado": ("aprovado", "aplicado"),
          "recusado": ("pendente", "aprovado", "bloqueado", "recusado")}
INVALIDOS = set(':*?"<>|/\\')
ID = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{4}$")
WIKILINK = re.compile(r"\[\[([^\]|#\n]+)(?:[#|][^\]\n]*)?\]\]")
BLOCO = 10


class Erro(Exception):
    pass


def norm(texto):
    return unicodedata.normalize("NFC", texto).casefold()


def stem(caminho):
    nome = posixpath.basename(caminho)
    return nome[:-3] if nome.lower().endswith(".md") else nome


def com_md(caminho):
    return caminho if caminho.lower().endswith(".md") else caminho + ".md"


def gravar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = caminho + ".novo"
    with open(temporario, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temporario, caminho)


def ler_json(caminho):
    with open(caminho, encoding="utf-8-sig") as f:
        return json.load(f)


def digital(vault, nota):
    try:
        with open(os.path.join(vault, *nota.split("/")), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def raiz_explorar(vault):
    return os.path.join(config_lib.pasta_de_estado(vault), "explorar")


def pasta_da(vault, ident):
    if not ident or not ID.match(ident):
        raise Erro(f"id inválido: {ident}")
    pasta = os.path.join(raiz_explorar(vault), ident)
    if not os.path.isfile(os.path.join(pasta, "proposta.json")):
        raise Erro(f"proposta não encontrada: {ident}")
    return pasta


def notas_do_vault(vault):
    """Caminhos relativos de todas as notas `.md`, fora das pastas ocultas."""
    notas = []
    for dirpath, dirnomes, nomes in os.walk(vault):
        dirnomes[:] = sorted(d for d in dirnomes if not d.startswith("."))
        for nome in sorted(nomes):
            if nome.lower().endswith(".md"):
                notas.append(os.path.relpath(os.path.join(dirpath, nome), vault).replace(os.sep, "/"))
    return notas


def links_por_nome(vault, notas):
    """{nome normalizado: {notas que linkam para ele}}."""
    mapa = {}
    for nota in notas:
        try:
            with open(os.path.join(vault, *nota.split("/")), encoding="utf-8-sig") as f:
                texto = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        for alvo in WIKILINK.findall(texto):
            mapa.setdefault(norm(stem(alvo.strip())), set()).add(nota)
    return mapa


# -- iniciar ---------------------------------------------------------------------------------------------------------

def iniciar(vault, args):
    alvo = ler_json(args.alvo)
    ident = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
    pasta = os.path.join(raiz_explorar(vault), ident)
    grupos = [{"id": g["id"], "pasta": g.get("pasta", ""), "notas": list(g["notas"])} for g in alvo.get("grupos", [])]
    digitais = {n: digital(vault, n) for g in grupos for n in g["notas"]}
    gravar_json(os.path.join(pasta, "proposta.json"), {
        "versao": 1, "id": ident, "rotulo": args.rotulo, "criada": datetime.datetime.now().isoformat(timespec="seconds"),
        "alvo": alvo.get("alvo"), "grupos": grupos, "fora": alvo.get("fora", []),
        "reassistir": alvo.get("reassistir", []), "digitais": digitais, "temas": [], "itens": []})
    return {"id": ident, "pasta": pasta,
            "grupos": [{"id": g["id"], "saida": os.path.join(pasta, g["id"] + ".json")} for g in grupos]}


# -- consolidar ------------------------------------------------------------------------------------------------------

def ler_respostas(pasta, proposta):
    """(entradas, temas, faltam, avisos): uma entrada por nota respondida que pertence ao grupo."""
    entradas, temas, faltam, avisos = [], [], [], []
    for grupo in proposta["grupos"]:
        caminho = os.path.join(pasta, grupo["id"] + ".json")
        if not os.path.isfile(caminho):
            faltam.append(grupo["id"])
            continue
        try:
            resposta = ler_json(caminho)
        except (OSError, ValueError):
            faltam.append(grupo["id"])
            avisos.append(f"{grupo['id']}: arquivo ilegível")
            continue
        respondidas = set()
        for nota in resposta.get("notas", []):
            caminho_nota, destino = nota.get("nota"), nota.get("destino") or {}
            if caminho_nota not in grupo["notas"]:
                avisos.append(f"{grupo['id']}: {caminho_nota} não é do grupo, ignorada")
                continue
            if destino.get("tipo") not in TIPOS:
                avisos.append(f"{grupo['id']}: {caminho_nota} com tipo inválido ({destino.get('tipo')})")
                continue
            respondidas.add(caminho_nota)
            alvo = (destino.get("alvo") or "").strip()
            if not alvo and destino["tipo"] in ("linha", "fundir"):
                avisos.append(f"alvo_vazio: {caminho_nota}")
                continue
            if not alvo and destino["tipo"] == "detalhe":
                alvo = caminho_nota
            entradas.append({"nota": caminho_nota, "tipo": destino["tipo"], "alvo": alvo,
                             "detalhe": {k: nota.get(k) for k in ("porque", "linha", "cortes", "esboco", "acrescimos",
                                                                  "atencao") if nota.get(k)}})
        for falta in grupo["notas"]:
            if falta not in respondidas:
                avisos.append(f"{grupo['id']}: {falta} sem resposta")
        temas += [t for t in resposta.get("temas", []) if isinstance(t, dict) and t.get("nome")]
    return entradas, temas, faltam, avisos


def pasta_comum(notas):
    pastas = [posixpath.dirname(n) for n in notas]
    try:
        return posixpath.commonpath(pastas) if all(pastas) else ""
    except ValueError:
        return ""


def juntar(caminho_pasta, nome):
    return com_md(posixpath.join(caminho_pasta, nome) if caminho_pasta else nome)


def resolver(entradas, temas, existentes):
    """Dá a cada entrada o `destino` (caminho), resolvendo os alvos que são só um nome."""
    por_nome = {}
    for nota in existentes:
        por_nome.setdefault(norm(stem(nota)), []).append(nota)
    tema_pasta = {norm(t["nome"]): t.get("pasta") or "" for t in temas}
    criados = {}

    def unico_existente(nome):
        achadas = por_nome.get(norm(nome), [])
        return achadas[0] if len(achadas) == 1 else None

    soltas = {}
    for e in entradas:
        t, alvo, nota = e["tipo"], e["alvo"], e["nota"]
        if t == "descartar":
            e["destino"] = nota
        elif t in ("mover", "arquivar"):
            if not alvo:
                alvo = "Arquivo/" + posixpath.dirname(nota) if t == "arquivar" else posixpath.dirname(nota)
            e["destino"] = com_md(alvo) if alvo.lower().endswith(".md") else juntar(alvo.strip("/"), stem(nota))
        elif "/" in alvo:
            e["destino"] = com_md(alvo.strip("/"))
        elif t in CRIAM:
            soltas.setdefault((t, norm(alvo)), []).append(e)
    for (t, _), grupo in soltas.items():
        nome = stem(grupo[0]["alvo"]) if grupo[0]["alvo"] else stem(grupo[0]["nota"])
        destino = unico_existente(nome) if t == "linha" else None
        if not destino:
            pasta = tema_pasta.get(norm(nome)) if t == "linha" and norm(nome) in tema_pasta else \
                pasta_comum([e["nota"] for e in grupo])
            destino = juntar(pasta.strip("/"), nome)
        for e in grupo:
            e["destino"] = destino
    for e in entradas:
        if e["tipo"] in CRIAM:
            criados.setdefault(norm(stem(e["destino"])), e["destino"])
    for e in entradas:
        if e["tipo"] == "fundir" and "destino" not in e:
            nome = stem(e["alvo"]) or stem(e["nota"])
            e["destino"] = criados.get(norm(nome)) or unico_existente(nome) or \
                juntar(posixpath.dirname(e["nota"]), nome)


def operacoes(tipo, destino, origens, existe, detalhes):
    ops = []
    if tipo == "linha":
        if not existe:
            ops.append({"op": "criar", "nota": destino})
        for o in origens:
            ops.append({"op": "linha", "origem": o, "em": destino, "texto": detalhes.get(o, {}).get("linha", "")})
            ops.append({"op": "apagar", "nota": o})
    elif tipo == "detalhe":
        for o in origens:
            ops.append({"op": "reescrever", "nota": o})
            if norm(o) != norm(destino):
                ops.append({"op": "unir" if existe or o != origens[0] else "renomear", "de": o, "para": destino})
    elif tipo == "fundir":
        for o in origens:
            ops.append({"op": "fundir", "origem": o, "em": destino})
            ops.append({"op": "apagar", "nota": o})
    elif tipo in ("mover", "arquivar"):
        ops += [{"op": "renomear", "de": o, "para": destino} for o in origens if norm(o) != norm(destino)]
    else:
        ops += [{"op": "apagar", "nota": o} for o in origens]
    return ops


def consolidar(vault, args):
    pasta = pasta_da(vault, args.id)
    proposta = ler_json(os.path.join(pasta, "proposta.json"))
    entradas, temas, faltam, avisos = ler_respostas(pasta, proposta)
    existentes = notas_do_vault(vault)
    existe = {norm(n) for n in existentes}
    resolver(entradas, temas, existentes)
    for e in [e for e in entradas if e["tipo"] in ("fundir", "linha") and norm(e["destino"]) == norm(e["nota"])]:
        avisos.append(f"{e['tipo']}_em_si: {e['nota']}")
        entradas.remove(e)

    # item aplicado ou recusado fica com as origens que tinha (chave com o número dele); origem nova no mesmo
    # destino vira outro item, nunca herda o estado de um item fechado
    fechados = {}
    for i in proposta.get("itens", []):
        if i["estado"] in FECHADOS:
            for o in i["origens"]:
                fechados[(i["tipo"], norm(i["destino"]), o)] = i["n"]
    juntos, ordem = {}, []
    for e in entradas:
        chave = (e["tipo"], norm(e["destino"]), fechados.get((e["tipo"], norm(e["destino"]), e["nota"]), 0))
        if chave not in juntos:
            juntos[chave] = {"destino": e["destino"], "tipo": e["tipo"], "origens": [], "detalhes": {}}
            ordem.append(chave)
        if e["nota"] not in juntos[chave]["origens"]:
            juntos[chave]["origens"].append(e["nota"])
            juntos[chave]["detalhes"][e["nota"]] = e["detalhe"]
    chaves = sorted(ordem, key=lambda k: (ORDEM[k[0]], k[1]))

    regras = regras_lib.ler(vault)
    links = links_por_nome(vault, existentes)
    por_nome = {}
    for nota in existentes:
        por_nome.setdefault(norm(stem(nota)), []).append(nota)
    antigos = {(i["tipo"], norm(i["destino"]), i["n"] if i["estado"] in FECHADOS else 0): i
               for i in proposta.get("itens", [])}
    proximo = max((i["n"] for i in antigos.values()), default=0) + 1
    # item fechado fica como estava, com ou sem entrada no g*.json: o registro do que foi feito ou recusado
    itens = [i for i in antigos.values() if i["estado"] in FECHADOS]
    refeitos, mudaram = [], []
    for chave in chaves:
        if chave in antigos and antigos[chave]["estado"] in FECHADOS:
            continue
        if chave in antigos:
            n = antigos[chave]["n"]
        else:
            n, proximo = proximo, proximo + 1
        item = juntos[chave]
        tipo, destino, origens = item["tipo"], item["destino"], sorted(item["origens"])
        destino_existe = norm(destino) in existe
        some = [o for o in origens if tipo in ("linha", "fundir", "descartar") or norm(stem(o)) != norm(stem(destino))]
        avisos_item = []
        nome = stem(destino)
        if not nome.strip() or INVALIDOS & set(nome):
            avisos_item.append("nome_invalido")
        proprias = {norm(o) for o in origens} | {norm(destino)}
        if not destino_existe and any(norm(p) not in proprias for p in por_nome.get(norm(nome), [])):
            avisos_item.append("nome_repetido")
        pasta_destino = posixpath.dirname(destino)
        if pasta_destino and not os.path.isdir(os.path.join(vault, *pasta_destino.split("/"))):
            avisos_item.append("pasta_nova")
        if regras and any(regras.protegida(p) for p in origens + [destino]):
            avisos_item.append("protegida")
        novo = {
            "n": n, "destino": destino, "tipo": tipo, "origens": origens,
            "operacoes": operacoes(tipo, destino, origens, destino_existe, item["detalhes"]),
            "depende_de": [],
            "links_de_entrada": {o: sorted(x for x in links.get(norm(stem(o)), ()) if x != o) for o in some},
            "avisos": avisos_item, "detalhes": item["detalhes"],
            "estado": antigos[chave]["estado"] if chave in antigos else "pendente"}
        if chave in antigos and mudou_o_item(antigos[chave], novo):
            # o dono viu (e talvez aprovou) o item como ele era: refeito, ajustado ou com origem nova, pede novo ok
            mudaram.append(n)
            if novo["estado"] in ("aprovado", "bloqueado"):
                novo["estado"] = "pendente"
                refeitos.append(n)
        itens.append(novo)
        if destino not in proposta["digitais"]:
            proposta["digitais"][destino] = digital(vault, destino)
    for item in [i for i in itens if i["estado"] not in FECHADOS]:
        item["depende_de"] = [o["n"] for o in itens if o is not item and o["tipo"] in CRIAM
                              and norm(o["destino"]) == norm(item["destino"])
                              and ORDEM[o["tipo"]] < ORDEM[item["tipo"]]]
    itens.sort(key=lambda i: i["n"])
    bloqueados = propagar_bloqueio(itens)
    proposta["itens"], proposta["temas"] = itens, temas
    gravar_json(os.path.join(pasta, "proposta.json"), proposta)
    return {"itens": len(itens), "blocos": -(-len(itens) // BLOCO), "faltam_grupos": faltam, "avisos": avisos,
            "refeitos": sorted(n for n in refeitos if n not in bloqueados), "mudaram": sorted(mudaram),
            "bloqueados": bloqueados}


def mudou_o_item(antigo, novo):
    return any(antigo.get(k) != novo[k] for k in ("origens", "operacoes", "detalhes"))


def propagar_bloqueio(itens):
    """Item aberto que depende de um recusado ou bloqueado fica `bloqueado` (em cadeia). Devolve os números."""
    estado = {i["n"]: i for i in itens}
    bloqueados, mudou = [], True
    while mudou:
        mudou = False
        for i in itens:
            if i["estado"] in ESTADOS_ABERTOS and any(
                    estado[d]["estado"] in ("recusado", "bloqueado") for d in i["depende_de"] if d in estado):
                i["estado"] = "bloqueado"
                bloqueados.append(i["n"])
                mudou = True
    return sorted(bloqueados)


# -- bloco, marcar, conferir, listar, remover ------------------------------------------------------------------------

def carregar(vault, ident):
    pasta = pasta_da(vault, ident)
    return pasta, ler_json(os.path.join(pasta, "proposta.json"))


def numeros(texto, itens):
    validos = {i["n"] for i in itens}
    try:
        pedidos = [int(x) for x in texto.replace(" ", "").split(",") if x]
    except ValueError:
        raise Erro(f"itens inválidos: {texto}")
    fora = [n for n in pedidos if n not in validos]
    if fora or not pedidos:
        raise Erro(f"itens que não existem: {fora or texto}")
    return pedidos


def bloco(vault, args):
    _, proposta = carregar(vault, args.id)
    itens = [i for i in proposta["itens"] if (args.n - 1) * BLOCO < i["n"] <= args.n * BLOCO]
    if not itens:
        raise Erro(f"bloco {args.n} não existe")
    return {"bloco": args.n, "blocos": -(-len(proposta["itens"]) // BLOCO), "itens": itens}


def marcar(vault, args):
    pasta, proposta = carregar(vault, args.id)
    pedidos = numeros(args.itens, proposta["itens"])
    por_n = {i["n"]: i for i in proposta["itens"]}
    fora = [f"{n} ({por_n[n]['estado']})" for n in pedidos if por_n[n]["estado"] not in VEM_DE[args.estado]]
    if fora:
        raise Erro(f"{args.estado} só vale para item {' ou '.join(VEM_DE[args.estado])}; nada marcado: "
                   + ", ".join(fora))
    for n in pedidos:
        por_n[n]["estado"] = args.estado
        if args.estado == "aplicado":
            # o destino mudou de propósito: os outros itens que escrevem nele conferem contra o novo conteúdo
            destino = norm(por_n[n]["destino"])
            for nota in [p for p in proposta["digitais"] if norm(p) == destino]:
                proposta["digitais"][nota] = digital(vault, nota)
    bloqueados = propagar_bloqueio(proposta["itens"]) if args.estado == "recusado" else []
    gravar_json(os.path.join(pasta, "proposta.json"), proposta)
    return {"marcados": pedidos, "estado": args.estado, "bloqueados": sorted(bloqueados)}


def conferir(vault, args):
    _, proposta = carregar(vault, args.id)
    escolhidos = numeros(args.itens, proposta["itens"]) if args.itens else [i["n"] for i in proposta["itens"]]
    mudou, ok = [], []
    for item in proposta["itens"]:
        if item["n"] not in escolhidos:
            continue
        notas = [p for p in item["origens"] + [item["destino"]] if p in proposta["digitais"]]
        alterada = any(digital(vault, p) != proposta["digitais"][p] for p in notas)
        (mudou if alterada else ok).append(item["n"])
    return {"mudou": mudou, "ok": ok}


def redigitar(vault, args):
    pasta, proposta = carregar(vault, args.id)
    pedidos = numeros(args.itens, proposta["itens"])
    for item in proposta["itens"]:
        if item["n"] in pedidos:
            for nota in item["origens"] + [item["destino"]]:
                proposta["digitais"][nota] = digital(vault, nota)
    gravar_json(os.path.join(pasta, "proposta.json"), proposta)
    return {"redigitados": pedidos}


def listar(vault, _args):
    propostas = []
    for caminho in sorted(glob.glob(os.path.join(raiz_explorar(vault), "*", "proposta.json"))):
        try:
            p = ler_json(caminho)
        except (OSError, ValueError):
            continue
        estados = [i["estado"] for i in p.get("itens", [])]
        consolidada = bool(estados)
        if consolidada and not any(e in ESTADOS_ABERTOS for e in estados):
            continue
        propostas.append({"id": p["id"], "rotulo": p.get("rotulo", ""), "criada": p.get("criada"),
                          "consolidada": consolidada, "itens": len(estados),
                          "pendentes": estados.count("pendente"), "aprovados": estados.count("aprovado")})
    return {"pasta": raiz_explorar(vault), "propostas": propostas}


def remover(vault, args):
    pasta = pasta_da(vault, args.id)
    shutil.rmtree(pasta)
    return {"removida": args.id}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    sub = ap.add_subparsers(dest="subcomando", required=True)
    s = sub.add_parser("iniciar")
    s.add_argument("--alvo", required=True)
    s.add_argument("--rotulo", required=True)
    for nome in ("consolidar", "remover"):
        sub.add_parser(nome).add_argument("--id", required=True)
    s = sub.add_parser("bloco")
    s.add_argument("--id", required=True)
    s.add_argument("--n", type=int, required=True)
    s = sub.add_parser("marcar")
    s.add_argument("--id", required=True)
    s.add_argument("--itens", required=True)
    s.add_argument("--estado", required=True, choices=["pendente", "aprovado", "aplicado", "recusado"])
    s = sub.add_parser("conferir")
    s.add_argument("--id", required=True)
    s.add_argument("--itens")
    s = sub.add_parser("redigitar")
    s.add_argument("--id", required=True)
    s.add_argument("--itens", required=True)
    sub.add_parser("listar")
    args = ap.parse_args()
    if not os.path.isdir(args.vault):
        print(f"vault não encontrado: {args.vault}", file=sys.stderr)
        return 2
    acoes = {"iniciar": iniciar, "consolidar": consolidar, "bloco": bloco, "marcar": marcar, "conferir": conferir,
             "redigitar": redigitar, "listar": listar, "remover": remover}
    try:
        resultado = acoes[args.subcomando](args.vault, args)
    except (Erro, OSError, ValueError, KeyError) as erro:
        print(str(erro), file=sys.stderr)
        return 2
    sys.stdout.buffer.write((json.dumps(resultado, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
