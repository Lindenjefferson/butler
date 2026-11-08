"""A conferência na hora do toque e a revisão do vault inteiro. Só lê e relata: nunca corrige.

`conferir` olha uma nota e devolve os achados, cada um com um `codigo` estável (é o código que uma exceção aprendida
cala, em `## Exceções aprendidas` nas regras):

- `sem_frontmatter`, `frontmatter_invalido`: o frontmatter falta ou não fecha. Quais campos e valores são válidos é
  regra do `CLAUDE.md` do vault, que a skill confere;
- `titulo_diferente`: o `title` do frontmatter não é o nome do arquivo (tirando os caracteres que o Windows proíbe
  num nome). Não vale para um arquivo de atualização (campo `atualiza`, que leva o título da original) nem para um
  modelo (`{{title}}`);
- `sem_veja_tambem`: falta a seção de links do fim da nota (título em `## Caminhos`, padrão `Veja também`);
- `link_quebrado`: wikilink para uma nota ou arquivo que não existe (fora de blocos de código). Quando uma nota tem
  nome muito parecido (difflib, razão de pelo menos 0,85), o achado traz a `sugestao`: é um palpite para a pessoa
  confirmar, nunca uma correção;
- `dado_sensivel`: um achado de `sensivel.py`, sem o valor;
- `copia_conflito`: o nome tem cara de cópia de conflito do sincronizador (`Nota (1).md`);
- `nome_nfd`: o nome está em Unicode decomposto e convive mal com o mesmo nome composto.

O `CLAUDE.md` da raiz não é nota: passa só pela detecção de dado sensível. O arquivo também diz se a nota é protegida ou de formato rígido, para a skill aplicar a regra dela. A conferência
ignora o BOM no começo do arquivo.

`revisar` aplica a conferência a todas as notas e acrescenta:

- `arvore`: cada pasta, com as notas que ficam direto nela;
- `pastas_vazias` (menos a do Inbox), `copias_conflito` e `nomes_nfd`;
- `fora_do_indice`: as notas que a nota índice não cita (quando as regras dizem qual é o índice);
- `links_quebrados_recorrentes`: o alvo inexistente que três ou mais notas citam, sem nota parecida, candidato a
  ganhar nota própria (a pessoa decide). Uma exceção aprendida com o código `link_quebrado_recorrente` tira as notas
  que ela casa da contagem;
- `possiveis_duplicatas`: notas com o mesmo título em pastas diferentes, ou com o mesmo link em `source`. Unir é
  sempre uma parada;
- `links_markdown`: o vault usa links em Markdown, que a conferência e o `renomear` não leem.
"""
import difflib
import re

from . import notas, sensivel
from .regras import sem_acento

PROIBIDOS = re.compile(r'[:*?"<>|/\\]')
PARECIDO = 0.85
RECORRENTE = 3


def _achado(codigo, mensagem, **extra):
    return dict({"codigo": codigo, "mensagem": mensagem}, **extra)


def _titulo_normal(texto):
    return re.sub(r"\s+", " ", PROIBIDOS.sub("", texto)).strip().lower()


def nomes_de_notas(lista):
    """Nome sem `.md` em minúsculas → o nome como está, das notas do vault (o `CLAUDE.md` não é nota)."""
    return {c.rsplit("/", 1)[-1][:-3].lower(): c.rsplit("/", 1)[-1][:-3] for c in lista
            if c.lower().endswith(".md") and c != "CLAUDE.md"}


def _sugestao(alvo, bases):
    """O nome de nota mais parecido com o alvo de um link quebrado, ou None."""
    nome = alvo.rsplit("/", 1)[-1]
    if nome.lower().endswith(".md"):
        nome = nome[:-3]
    achados = difflib.get_close_matches(nome.lower(), list(bases), n=1, cutoff=PARECIDO)
    return bases[achados[0]] if achados else None


def conferir(vault, relativo, regras, nomes=None, bases=None):
    if nomes is None or bases is None:
        lista = notas.arquivos(vault)
        nomes = notas.indice(lista) if nomes is None else nomes
        bases = nomes_de_notas(lista) if bases is None else bases
    liberadas = regras.liberacoes if regras else set()
    resultado = {"arquivo": relativo, "protegida": bool(regras and regras.protegida(relativo)),
                 "rigida": bool(regras and regras.rigida(relativo)), "achados": []}
    achados = resultado["achados"]
    if notas.copia_conflito(relativo):
        achados.append(_achado("copia_conflito", "o nome tem cara de cópia de conflito do sincronizador"))
    if notas.nome_nfd(relativo):
        achados.append(_achado("nome_nfd", "o nome está em Unicode decomposto (NFD)"))
    try:
        encontrados, binario, _ = sensivel.no_arquivo(notas.absoluto(vault, relativo), liberadas)
    except OSError as erro:
        achados.append(_achado("ilegivel", f"não deu para ler o arquivo ({erro})"))
        return resultado
    for item in encontrados:
        achados.append(_achado("dado_sensivel", f"possível {item['tipo']} na linha {item['linha']}",
                               tipo=item["tipo"], linha=item["linha"], digital=item["digital"]))
    if binario or not relativo.lower().endswith(".md") or relativo == "CLAUDE.md":
        return _filtrar(resultado, regras)
    texto, _ = notas.ler_texto(vault, relativo)
    campos, erro = notas.frontmatter(texto)
    if campos is None:
        achados.append(_achado("sem_frontmatter", "a nota não tem frontmatter"))
    elif erro:
        achados.append(_achado("frontmatter_invalido", erro))
    else:
        titulo = campos.get("title")
        nome = relativo.rsplit("/", 1)[-1][:-3]
        # Um arquivo de atualização leva o título da original, e um modelo leva o marcador do Obsidian.
        if titulo and _titulo_normal(titulo) != _titulo_normal(nome) and not campos.get("atualiza") \
                and "{{" not in titulo:
            achados.append(_achado("titulo_diferente", f"o title é \"{titulo}\", o arquivo é \"{nome}\""))
    titulo_links = regras.caminho("veja tambem") if regras else "Veja também"
    if titulo_links and notas.secao(texto, titulo_links) is None:
        achados.append(_achado("sem_veja_tambem", f"falta a seção \"{titulo_links}\""))
    quebrados = sorted({alvo for alvo in notas.wikilinks(texto) if not notas.link_existe(alvo, nomes)})
    for alvo in quebrados:
        sugestao = _sugestao(alvo, bases)
        if sugestao:
            achados.append(_achado("link_quebrado", f"[[{alvo}]] não aponta para nada (seria [[{sugestao}]]?)",
                                   alvo=alvo, sugestao=sugestao))
        else:
            achados.append(_achado("link_quebrado", f"[[{alvo}]] não aponta para nada", alvo=alvo))
    return _filtrar(resultado, regras)


def _filtrar(resultado, regras):
    if regras:
        resultado["achados"] = [a for a in resultado["achados"]
                                if not regras.calado(resultado["arquivo"], a["codigo"])]
    return resultado


def _duplicatas(vault, lista):
    por_titulo, por_source = {}, {}
    for caminho in lista:
        if not caminho.lower().endswith(".md") or caminho == "CLAUDE.md":
            continue
        chave = re.sub(r"\W+", " ", sem_acento(caminho.rsplit("/", 1)[-1][:-3])).strip()
        por_titulo.setdefault(chave, []).append(caminho)
        try:
            campos, _ = notas.frontmatter(notas.ler_texto(vault, caminho)[0])
        except OSError:
            continue
        fonte = (campos or {}).get("source", "")
        if re.match(r"https?://", fonte):
            por_source.setdefault(fonte.rstrip("/").lower(), []).append(caminho)
    saida = [{"motivo": "mesmo título", "notas": sorted(v)} for v in por_titulo.values() if len(v) > 1]
    return saida + [{"motivo": "mesmo source", "notas": sorted(v)} for v in por_source.values() if len(v) > 1]


def revisar(vault, regras):
    lista = notas.arquivos(vault)
    nomes, bases = notas.indice(lista), nomes_de_notas(lista)
    inbox = regras.caminho("inbox") if regras else "Inbox"
    relatorio = {"notas": [], "arvore": notas.arvore(vault),
                 "pastas_vazias": notas.pastas_vazias(vault, manter=[inbox]),
                 "copias_conflito": [c for c in lista if notas.copia_conflito(c)],
                 "nomes_nfd": [c for c in lista if notas.nome_nfd(c)], "fora_do_indice": None,
                 "links_quebrados_recorrentes": [], "possiveis_duplicatas": _duplicatas(vault, lista),
                 "links_markdown": notas.usa_links_markdown(vault)}
    citantes = {}
    for caminho in lista:
        resultado = conferir(vault, caminho, regras, nomes, bases)
        if resultado["achados"]:
            relatorio["notas"].append(resultado)
        for achado in resultado["achados"]:
            if achado["codigo"] == "link_quebrado" and not achado.get("sugestao"):
                citantes.setdefault(achado["alvo"], []).append(caminho)
    for alvo, quem in sorted(citantes.items()):
        quem = sorted(c for c in quem if not (regras and regras.calado(c, "link_quebrado_recorrente")))
        if len(quem) >= RECORRENTE:
            relatorio["links_quebrados_recorrentes"].append({"alvo": alvo, "notas": quem})
    indice = regras.caminho("indice") if regras else None
    if indice and indice in lista:
        texto, _ = notas.ler_texto(vault, indice)
        citados = notas.indice([alvo for alvo in notas.wikilinks(texto)])
        pular = {indice.lower(), "claude.md"}
        relatorio["fora_do_indice"] = [
            c for c in lista if c.lower().endswith(".md") and c.lower() not in pular
            and not (inbox and c.lower().startswith(inbox.lower() + "/"))
            and not (notas.link_existe(c[:-3], citados) or notas.link_existe(c.rsplit("/", 1)[-1][:-3], citados))]
    return relatorio
