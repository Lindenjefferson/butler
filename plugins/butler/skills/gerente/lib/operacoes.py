"""As operações que gravam: mudanças de fora, desfazer e renomear.

**Mudanças de fora.** Tudo o que mudou no vault desde o último ponto foi feito fora do Butler. `registrar_fora` grava
essas mudanças num ponto próprio, antes de o pedido começar, e relata o que merece aviso: nota protegida que perdeu
linhas ou foi apagada, cópia de conflito nova, mudança no `CLAUDE.md` ou nas regras e nome em NFD. Arquivo com dado
sensível e binário (imagem, PDF) ficam fora do ponto, a menos que a impressão digital esteja liberada nas regras, e
voltam a aparecer a cada pedido até a pessoa decidir. Arquivo que o git não consegue ler fica fora e é relatado; o
histórico continua funcionando. Na retomada de um pedido (`inicio` chamado de novo no meio dele), o que está sem
ponto pode ser trabalho do próprio pedido ou uma mudança real de fora, e o git não distingue uma coisa da outra;
`ignorar` tira do cálculo os caminhos que quem chama (o `--continuando` do `inicio`) já sabe que são do pedido.

**Desfazer um pedido** é uma mescla de três vias por arquivo (`git merge-file`): parte da versão atual e tira dela
só o que o pedido mudou. Uma mudança posterior em outro trecho da mesma nota (outra triagem no `Início.md`) fica; um
trecho que o pedido mudou e que mudou de novo depois é conflito, e o arquivo só é restaurado inteiro com `--aceitar`.
Nota que o pedido criou só é apagada se ninguém a mudou depois; nota que o pedido apagou é recriada se o nome
estiver livre (comparado sem maiúsculas, como o Windows compara).

**Voltar uma nota a uma data** (`--nota --ate`) restaura a nota inteira como estava no último ponto antes da data, e
lista os pedidos que a mudaram depois: quem chama mostra as duas versões e pede o sim antes de `--aplicar`.

**Renomear** move a nota e reescreve os wikilinks que apontam para ela (`[[Nome]]`, `[[Nome|apelido]]`,
`[[Nome#seção]]`, `![[Nome]]` e a forma com caminho), mantendo apelido e seção.
"""
import os
import re
import subprocess
import tempfile
import unicodedata

from . import notas, sensivel
from .regras import SEMPRE_PROTEGIDAS


def registrar_fora(hist, regras, rotulo, pedido, ignorar=None):
    """`ignorar` tira do que se conta como mudança de fora os caminhos que quem chama já sabe que são do próprio
    pedido (ainda sem ponto): eles continuam sem ponto, sem entrar no relato nem no commit de fora."""
    liberadas = regras.liberacoes if regras else set()
    itens = [item for item in hist.mudancas() if item[1] not in (ignorar or ())]
    fora, avisos = set(), {"protegidas_com_remocao": [], "copias_conflito": [], "regras_mudaram": [],
                           "fora_do_historico": [], "nomes_nfd": []}
    for estado, caminho in itens:
        if estado != "apagado":
            try:
                achados, binario, marca = sensivel.no_arquivo(notas.absoluto(hist.vault, caminho), liberadas)
            except OSError as erro:
                fora.add(caminho)
                avisos["fora_do_historico"].append({"arquivo": caminho, "motivo": f"ilegível ({erro})"})
                continue
            if binario and not (regras and regras.libera_binario(caminho, marca)):
                fora.add(caminho)
                avisos["fora_do_historico"].append({"arquivo": caminho, "motivo": "binário", "digital": marca})
                continue
            if achados:
                fora.add(caminho)
                avisos["fora_do_historico"].append({"arquivo": caminho, "motivo": "dado sensível",
                                                    "achados": achados})
                continue
        protegida = regras.protegida(caminho) if regras else caminho in SEMPRE_PROTEGIDAS
        if protegida:
            removidas = hist.linhas_removidas(caminho) if estado != "novo" else 0
            if estado == "apagado" or removidas is None or removidas > 0:
                avisos["protegidas_com_remocao"].append(caminho)
        if estado == "novo" and notas.copia_conflito(caminho):
            avisos["copias_conflito"].append(caminho)
        if estado == "novo" and notas.nome_nfd(caminho):
            avisos["nomes_nfd"].append(caminho)
        if caminho in SEMPRE_PROTEGIDAS:
            avisos["regras_mudaram"].append(caminho)
    gravar = [caminho for _, caminho in itens if caminho not in fora]
    sha, gravados, nao_gravados = (None, [], [])
    if gravar:
        sha, gravados, nao_gravados = hist.gravar(gravar, "fora", f"mudanças de fora, antes de: {rotulo}", pedido)
    for item in nao_gravados:
        avisos["fora_do_historico"].append({"arquivo": item["arquivo"], "motivo": item["motivo"]})
    return {"ponto": sha, "arquivos": [{"estado": e, "arquivo": c} for e, c in itens],
            "gravados": len(gravados), **avisos}


# -- desfazer ----------------------------------------------------------------------------------------------------

def commits_do_pedido(hist, pedido):
    """Os commits do pedido que mudaram o vault por ele (sem o das mudanças de fora), do mais velho ao mais novo."""
    return [c for c in reversed(hist.commits(limite=None, pedido=pedido))
            if c["pedido"] == pedido and c["tipo"] in ("nota", "desfaz")]


def _ler_atual(hist, caminho):
    # No Windows, `nota.md` abre o `Nota.md` do disco: só a grafia exata conta como o mesmo arquivo.
    if not hist.existe_exato(caminho):
        return None
    try:
        with open(notas.absoluto(hist.vault, caminho), "rb") as arquivo:
            return arquivo.read()
    except FileNotFoundError:
        return None


def _nome_ocupado(vault, caminho):
    """O caminho (relativo ao vault) do outro arquivo com o mesmo nome, só com outra grafia de maiúsculas, que já
    ocupa o lugar, ou None."""
    proprio = notas.absoluto(vault, caminho)
    pasta, _, nome = proprio.rpartition(os.sep)
    try:
        for n in os.listdir(pasta or "."):
            outro = os.path.join(pasta, n)
            # Só ocupa quando o disco resolve o nosso nome para o outro arquivo (Windows, macOS). Num disco que
            # diferencia maiúsculas, `nota.md` e `Nota.md` são dois arquivos e um não ocupa o outro.
            if n.lower() == nome.lower() and n != nome and os.path.exists(proprio)                     and os.path.samefile(proprio, outro):
                return caminho.rsplit("/", 1)[0] + "/" + n if "/" in caminho else n
    except (FileNotFoundError, OSError):
        pass
    return None


def _mesclar(atual, depois, antes):
    """Tira de `atual` o que levou `antes` a `depois`. Devolve (resultado, conflitos)."""
    with tempfile.TemporaryDirectory() as pasta:
        caminhos = []
        for nome, conteudo in (("atual", atual), ("depois", depois), ("antes", antes)):
            caminho = os.path.join(pasta, nome)
            with open(caminho, "wb") as arquivo:
                arquivo.write(conteudo)
            caminhos.append(caminho)
        saida = subprocess.run(["git", "merge-file", "-p", "-L", "atual", "-L", "pedido", "-L", "antes", *caminhos],
                               capture_output=True)
    if saida.returncode < 0 or saida.returncode > 127:
        return None, 1
    return saida.stdout, saida.returncode


def plano_pedido(hist, pedido):
    lista = commits_do_pedido(hist, pedido)
    if not lista:
        return None
    base = lista[0]["sha"] + "^"
    ultimo = lista[-1]["sha"]
    caminhos = []
    for commit in lista:
        for caminho in hist.arquivos_do_commit(commit["sha"]):
            if caminho not in caminhos:
                caminhos.append(caminho)
    # Um ponto de outra origem no meio do pedido (as mudanças de fora gravadas numa retomada) mistura no `depois`
    # uma mudança que não é do pedido: esses arquivos só voltam com o aceite.
    do_pedido = {c["sha"] for c in lista}
    intrusos = set()
    for sha in hist.texto("rev-list", f"{base}..{ultimo}").split():
        if sha not in do_pedido:
            intrusos.update(hist.arquivos_do_commit(sha))
    itens = []
    for caminho in caminhos:
        antes = hist.conteudo(base, caminho)
        depois = hist.conteudo(ultimo, caminho)
        atual = _ler_atual(hist, caminho)
        item = {"arquivo": caminho, "conflito": False}
        if caminho in intrusos:
            item.update(acao="nada" if atual == antes else "restaurar", conflito=atual != antes, resultado=antes,
                        mudou_por_fora=True)
            if antes is None and atual is not None:
                item["acao"] = "apagar"
            elif atual is None and antes is not None:
                item["acao"] = "recriar"
        elif atual == antes:
            item["acao"] = "nada"
            item["resultado"] = atual
        elif antes is None:
            item["acao"] = "apagar"
            item["conflito"] = atual != depois
        elif atual is None:
            item["acao"] = "recriar"
            ocupado = _nome_ocupado(hist.vault, caminho)
            item["conflito"] = depois is not None or ocupado is not None
            item["resultado"] = antes
            if ocupado:
                item["ocupado_por"] = ocupado
        elif depois is None:
            item["acao"] = "restaurar"
            item["conflito"] = True
            item["resultado"] = antes
        else:
            mesclado, conflitos = _mesclar(atual, depois, antes)
            item["acao"] = "nada" if not conflitos and mesclado == atual else "restaurar"
            item["conflito"] = conflitos != 0
            item["resultado"] = antes if conflitos else mesclado
        itens.append(item)
    # Renomeação só de maiúsculas: o nome antigo está "ocupado" pelo novo, que o próprio desfazer apaga. Sem
    # conflito no apagar, o recriar também fica sem conflito (o `aplicar` apaga antes de recriar).
    apagaveis = {i["arquivo"] for i in itens if i["acao"] == "apagar" and not i["conflito"]}
    for item in itens:
        if item.get("ocupado_por") in apagaveis and hist.conteudo(ultimo, item["arquivo"]) is None:
            item["conflito"] = False
    rotulo = rotulo_do_pedido(lista)
    return {"pedido": pedido, "rotulo": rotulo, "base": base, "itens": itens}


def rotulo_do_pedido(lista):
    """O rótulo do `inicio` do pedido; nos pontos antigos, sem o trailer, o do primeiro ponto."""
    for commit in lista:
        if commit.get("rotulo_pedido"):
            return commit["rotulo_pedido"]
    return re.sub(r"^\[[^\]]+\]\s*", "", lista[0]["assunto"]) if lista else ""


def _data_inclusiva(ate):
    """`AAAA-MM-DD` é o fim do dia, `AAAA-MM-DD HH:MM` é o fim do minuto: o ponto gravado nele conta."""
    ate = ate.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", ate):
        return ate + " 23:59:59"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}", ate):
        return ate + ":59"
    return ate


def plano_nota(hist, caminho, ate):
    alvo = hist.commit_antes(_data_inclusiva(ate), caminho)
    if not alvo:
        return {"arquivo": caminho, "sem_ponto": True, "itens": []}
    antes = hist.conteudo(alvo, caminho)
    atual = _ler_atual(hist, caminho)
    depois = [c for c in hist.commits(limite=5000, caminho=caminho)]
    posteriores = []
    for commit in depois:
        if commit["sha"] == alvo:
            break
        posteriores.append({"pedido": commit["pedido"], "tipo": commit["tipo"], "data": commit["data"],
                            "assunto": commit["assunto"]})
    if atual == antes:
        acao = "nada"
    elif antes is None:
        acao = "apagar"
    elif atual is None:
        acao = "recriar"
    else:
        acao = "restaurar"
    item = {"arquivo": caminho, "acao": acao, "conflito": bool(posteriores), "resultado": antes}
    if acao == "recriar" and _nome_ocupado(hist.vault, caminho):
        item["ocupado_por"] = _nome_ocupado(hist.vault, caminho)
    return {"arquivo": caminho, "ponto": alvo, "base": alvo, "mudancas_posteriores": posteriores, "itens": [item]}


def aplicar(hist, plano, aceitar=(), manter=()):
    """Aplica o que não tem conflito e o que foi aceito, os `apagar` primeiro (uma renomeação só de maiúsculas
    desocupa o nome antes de recriar). Um arquivo cujo nome outra grafia ainda ocupa é pulado: escrever nele
    sobrescreveria o outro no Windows; ele vai para `ocupados`, porque aceitar não resolve: o outro arquivo precisa
    sair (ou mudar de nome) antes. Devolve (aplicados, pulados, ocupados)."""
    aplicados, pulados, ocupados = [], [], []
    for item in sorted(plano["itens"], key=lambda i: i["acao"] != "apagar"):
        if item["acao"] == "nada":
            continue
        outro = _nome_ocupado(hist.vault, item["arquivo"]) if item["acao"] != "apagar" else None
        if outro:
            ocupados.append({"arquivo": item["arquivo"], "ocupado_por": outro})
            continue
        if item["conflito"] and item["arquivo"] not in aceitar:
            pulados.append(item["arquivo"])
            continue
        destino = notas.absoluto(hist.vault, item["arquivo"])
        if item["acao"] == "apagar":
            if os.path.exists(destino):
                os.remove(destino)
            _limpar_pastas(hist, plano.get("base"), os.path.dirname(destino), manter)
        else:
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "wb") as arquivo:
                arquivo.write(item["resultado"])
        aplicados.append(item["arquivo"])
    return aplicados, pulados, ocupados


def _limpar_pastas(hist, base, pasta, manter=()):
    """Tira a pasta que ficou vazia só se ela não existia antes do pedido (o pedido a criou). Uma pasta que já
    existia fica, e as de `manter` (o Inbox) ficam sempre: tirá-las é decisão do `CLAUDE.md`, que a skill lê."""
    raiz = os.path.abspath(hist.vault)
    manter = {m.strip("/").lower() for m in manter if m}
    while os.path.abspath(pasta) != raiz and os.path.isdir(pasta) and not os.listdir(pasta):
        relativa = notas.rel(hist.vault, pasta)
        if relativa.lower() in manter or not base or hist.texto("ls-tree", "--name-only", base, "--", relativa + "/").strip():
            return
        os.rmdir(pasta)
        pasta = os.path.dirname(pasta)


def publico(plano, conteudo=()):
    """O plano sem o conteúdo dos arquivos, para imprimir. `conteudo` lista os arquivos cuja versão que o desfazer
    deixaria vai junto, em `conteudo` (None quando o desfazer apagaria o arquivo)."""
    copia = {k: v for k, v in plano.items() if k != "itens"}
    copia["itens"] = [{k: v for k, v in item.items() if k != "resultado"} for item in plano["itens"]]
    if conteudo:
        copia["conteudo"] = {}
        for item in plano["itens"]:
            if item["arquivo"] in conteudo:
                resultado = None if item["acao"] == "apagar" else item.get("resultado")
                copia["conteudo"][item["arquivo"]] = (resultado.decode("utf-8", "replace") if resultado is not None
                                                      else None)
    return copia


# -- renomear ----------------------------------------------------------------------------------------------------

def renomear(vault, de, para):
    """Move `de` para `para` e reescreve os wikilinks. Devolve a lista das notas cujos links mudaram."""
    origem, destino = notas.absoluto(vault, de), notas.absoluto(vault, para)
    if not os.path.isfile(origem):
        raise FileNotFoundError(f"{de} não existe")
    if os.path.exists(destino) and os.path.normcase(origem) != os.path.normcase(destino):
        raise FileExistsError(f"{para} já existe")
    lista = notas.arquivos(vault)
    velho_nome = de.rsplit("/", 1)[-1]
    velho_nome = velho_nome[:-3] if velho_nome.lower().endswith(".md") else velho_nome
    velho_caminho = de[:-3] if de.lower().endswith(".md") else de
    novo_nome = para.rsplit("/", 1)[-1]
    novo_nome = novo_nome[:-3] if novo_nome.lower().endswith(".md") else novo_nome
    novo_caminho = para[:-3] if para.lower().endswith(".md") else para
    homonimos = [c for c in lista if c != de and c.rsplit("/", 1)[-1].lower() in (novo_nome.lower() + ".md",
                                                                                  novo_nome.lower())]
    novo_alvo = novo_caminho if homonimos else novo_nome
    nfc = lambda texto: unicodedata.normalize("NFC", texto).lower()
    alvos_velhos = {nfc(velho_nome), nfc(velho_caminho), nfc(de)}

    def trocar(casado):
        inteiro, dentro = casado.group(0), casado.group(1)
        alvo, resto = re.match(r"^([^|#^]*)(.*)$", dentro, re.S).groups()
        if nfc(alvo.strip()) not in alvos_velhos:
            return inteiro
        prefixo = "![[" if inteiro.startswith("!") else "[["
        return f"{prefixo}{novo_alvo}{resto}]]"

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    os.replace(origem, destino)  # a pasta de origem fica, mesmo vazia: tirá-la é decisão do `CLAUDE.md`
    tocadas = []
    for caminho in notas.arquivos(vault):
        if not caminho.lower().endswith(".md"):
            continue
        absoluto = notas.absoluto(vault, caminho)
        with open(absoluto, "rb") as arquivo:
            bruto = arquivo.read()
        texto = bruto.decode("utf-8", "replace")
        novo = re.sub(r"!?\[\[([^\]\n]+?)\]\]", trocar, texto)
        if novo != texto:
            with open(absoluto, "wb") as arquivo:
                arquivo.write(novo.encode("utf-8"))
            tocadas.append(caminho)
    return tocadas
