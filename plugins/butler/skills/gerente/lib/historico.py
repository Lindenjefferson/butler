"""O histórico git do vault, guardado fora dele.

Todo comando roda como `git --git-dir=<histórico>/git --work-tree=<vault>`: nenhum arquivo do git entra no vault, nem
`.git`, nem apontador, nem `.gitignore` (a lista do que ignorar fica em `<histórico>/git/info/exclude`). O git é
configurado para nunca mexer no conteúdo (sem conversão de fim de linha, acentos e caminhos longos preservados),
com identidade própria e sem hooks. O histórico nunca tem remoto: com remoto configurado, `motivo_quebra` acusa e o
Butler trata o vault como sem histórico.

Com `core.ignorecase=false`, uma renomeação só de maiúsculas (`nota.md` para `Nota.md`) aparece como apagado + novo,
e o desfazer devolve a grafia certa.

Cada ponto de retorno é um commit com a mensagem `[<tipo>] <rótulo>` e os trailers `Butler-Pedido: <id>`,
`Butler-Rotulo: <rótulo do pedido, o do inicio>` e `Butler-Tipo: <tipo>`, com tipo `preparar` (a foto inicial), `fora` (mudanças feitas fora do Butler), `nota` (uma nota
concluída dentro de um pedido) ou `desfaz` (uma restauração). Os caminhos são sempre relativos ao vault, com `/`.
"""
import os
import subprocess
import time

EXCLUIR = [
    ".obsidian/workspace.json",
    ".obsidian/workspace-mobile.json",
    ".obsidian/workspaces.json",
    ".tmp.drivedownload/",
    ".tmp.driveupload/",
    ".trash/",
    "desktop.ini",
    "Thumbs.db",
    ".DS_Store",
    "~$*",
    "*.tmp",
    "*.crdownload",
]
CONFIG = {
    "core.autocrlf": "false",
    "core.safecrlf": "false",
    "core.eol": "lf",
    "core.quotepath": "false",
    "core.longpaths": "true",
    "core.precomposeunicode": "true",
    "core.fsmonitor": "false",
    "core.filemode": "false",
    "core.symlinks": "false",
    "core.ignorecase": "false",
    "i18n.commitEncoding": "utf-8",
    "i18n.logOutputEncoding": "utf-8",
    "user.name": "Butler",
    "user.email": "butler@localhost",
    "commit.gpgsign": "false",
    "tag.gpgsign": "false",
    "gc.auto": "256",
    "advice.detachedHead": "false",
}
TIPOS = ("preparar", "fora", "nota", "desfaz")


class ErroGit(Exception):
    pass


class Historico:
    def __init__(self, vault, pasta):
        self.vault = os.path.abspath(vault)
        self.pasta = os.path.abspath(pasta)
        self.gitdir = os.path.join(self.pasta, "git")

    # -- execução -------------------------------------------------------------------------------------------------

    def git(self, *args, entrada=None, verificar=True):
        ambiente = dict(os.environ)
        for nome in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
            ambiente.pop(nome, None)
        # GIT_OPTIONAL_LOCKS=0: um `status` de leitura (situacao, aviso) não pega o index.lock de um `ponto`.
        ambiente.update({"GIT_LITERAL_PATHSPECS": "1", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C.UTF-8",
                         "GIT_OPTIONAL_LOCKS": "0",
                         "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        comando = ["git", "--git-dir=" + self.gitdir, "--work-tree=" + self.vault, *args]
        resultado = subprocess.run(comando, input=entrada, capture_output=True, env=ambiente, cwd=self.vault)
        if verificar and resultado.returncode != 0:
            raise ErroGit(resultado.stderr.decode("utf-8", "replace").strip() or f"git {args[0]} falhou")
        return resultado

    def texto(self, *args, **kw):
        return self.git(*args, **kw).stdout.decode("utf-8", "replace")

    # -- criação e saúde ------------------------------------------------------------------------------------------

    def existe(self):
        return os.path.isfile(os.path.join(self.gitdir, "HEAD"))

    def criar(self):
        os.makedirs(self.pasta, exist_ok=True)
        if not self.existe():
            subprocess.run(["git", "init", "--bare", "-q", "-b", "main", self.gitdir], check=True,
                           capture_output=True, env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
                                                     "GIT_CONFIG_NOSYSTEM": "1"})
        self.git("config", "core.bare", "false")
        for nome, valor in CONFIG.items():
            self.git("config", nome, valor)
        ganchos = os.path.join(self.pasta, "sem-hooks")
        os.makedirs(ganchos, exist_ok=True)
        self.git("config", "core.hooksPath", ganchos)
        info = os.path.join(self.gitdir, "info")
        os.makedirs(info, exist_ok=True)
        with open(os.path.join(info, "exclude"), "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write("# Mantido pelo Butler: o que não entra no histórico do vault.\n")
            arquivo.write("\n".join(EXCLUIR) + "\n")
        # Nenhum filtro nem conversão de texto, venha de onde vier a configuração de atributos.
        atributos = os.path.join(info, "attributes")
        with open(atributos, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write("* -text -filter -ident\n")
        self.git("config", "core.attributesFile", atributos)

    def limpar_index_lock(self, minutos=10):
        """Apaga um `index.lock` deixado por um git que caiu. Só chamar com a trava do Butler na mão: com ela,
        nenhum outro git do Butler está rodando neste vault."""
        caminho = os.path.join(self.gitdir, "index.lock")
        try:
            if time.time() - os.path.getmtime(caminho) > minutos * 60:
                os.remove(caminho)
                return True
        except OSError:
            pass
        return False

    def tem_commit(self):
        return self.git("rev-parse", "--verify", "-q", "HEAD", verificar=False).returncode == 0

    def motivo_quebra(self):
        """None se o histórico está pronto para gravar; senão, o motivo em uma frase."""
        if not os.path.isdir(self.vault):
            return "a pasta do vault não existe"
        if not self.existe():
            return "o histórico não existe nesta máquina"
        try:
            if self.texto("remote").strip():
                return "o histórico tem um remoto configurado, e o Butler nunca envia o vault para fora"
            if not self.tem_commit():
                return "o histórico não tem a foto inicial"
            self.git("status", "--porcelain", "-uno")
        except (ErroGit, OSError) as erro:
            return f"o git não respondeu ({erro})"
        return None

    # -- leitura --------------------------------------------------------------------------------------------------

    def mudancas(self):
        """Arquivos do vault que diferem do último ponto: lista de (estado, caminho), com estado `novo`, `alterado`
        ou `apagado`. Movidos aparecem como apagado + novo."""
        saida = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames",
                         "--ignore-submodules").stdout.decode("utf-8", "replace")
        itens = []
        for entrada in saida.split("\0"):
            if len(entrada) < 4:
                continue
            codigo, caminho = entrada[:2], entrada[3:]
            if codigo == "??":
                estado = "novo"
            elif "D" in codigo:
                estado = "apagado"
            else:
                estado = "alterado"
            itens.append((estado, caminho))
        vistos = {caminho for _, caminho in itens}
        for caminho in self.rastreados():
            if caminho not in vistos and not self.existe_exato(caminho):
                itens.append(("apagado", caminho))
        return itens

    def rastreados(self):
        if not self.tem_commit():
            return []
        saida = self.git("ls-files", "-z").stdout.decode("utf-8", "replace")
        return [caminho for caminho in saida.split("\0") if caminho]

    def existe_exato(self, caminho):
        """O arquivo existe com esta grafia exata. No Windows, `nota.md` "existe" quando o disco tem `Nota.md`, e o
        git não percebe a renomeação só de maiúsculas sem esta conferência."""
        atual = self.vault
        for parte in caminho.split("/"):
            try:
                if parte not in os.listdir(atual):
                    return False
            except OSError:
                return False
            atual = os.path.join(atual, parte)
        return True

    def linhas_removidas(self, caminho):
        """Quantas linhas o arquivo perdeu desde o último ponto (apagado conta tudo). None se binário."""
        if not self.rastreado(caminho):
            return 0
        saida = self.texto("diff", "--numstat", "HEAD", "--", caminho).strip()
        if not saida:
            return 0
        removidas = saida.split("\t")[1]
        return None if removidas == "-" else int(removidas)

    def rastreado(self, caminho, commit="HEAD"):
        return self.git("cat-file", "-e", f"{commit}:{caminho}", verificar=False).returncode == 0

    def conteudo(self, commit, caminho):
        resultado = self.git("cat-file", "blob", f"{commit}:{caminho}", verificar=False)
        return resultado.stdout if resultado.returncode == 0 else None

    def arquivos_do_commit(self, commit):
        saida = self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "--no-renames", "--root",
                         commit).stdout.decode("utf-8", "replace")
        return [caminho for caminho in saida.split("\0") if caminho]

    def commits(self, limite=500, caminho=None, pedido=None):
        """Commits do mais novo ao mais velho: dicts com sha, data, assunto, pedido, tipo e rotulo_pedido.
        `pedido` busca só os daquele pedido, em todo o histórico (sem teto); `limite=None` também tira o teto."""
        if not self.tem_commit():
            return []
        separador = "\x1f"
        formato = separador.join(["%H", "%aI", "%s", "%(trailers:key=Butler-Pedido,valueonly,separator=%x2C)",
                                  "%(trailers:key=Butler-Tipo,valueonly,separator=%x2C)",
                                  "%(trailers:key=Butler-Rotulo,valueonly,separator=%x2C)"]) + "\x1e"
        args = ["log", f"--format={formato}"]
        if limite:
            args.append(f"--max-count={limite}")
        if pedido:
            args += ["-F", f"--grep=Butler-Pedido: {pedido}"]
        if caminho:
            args += ["--", caminho]
        lista = []
        for registro in self.texto(*args).split("\x1e"):
            registro = registro.strip("\n")
            if not registro:
                continue
            sha, data, assunto, pedido, tipo, rotulo = (registro.split(separador) + [""] * 6)[:6]
            lista.append({"sha": sha, "data": data, "assunto": assunto, "pedido": pedido.strip(),
                          "tipo": tipo.strip(), "rotulo_pedido": rotulo.strip()})
        return lista

    def commit_antes(self, data, caminho):
        saida = self.texto("rev-list", "-1", f"--before={data}", "HEAD", "--", caminho).strip()
        return saida or None

    def head(self):
        return self.texto("rev-parse", "HEAD").strip()

    # -- escrita --------------------------------------------------------------------------------------------------

    def gravar(self, caminhos, tipo, rotulo, pedido, todos=False, rotulo_pedido=None):
        """Grava um ponto com só os `caminhos` (ou com tudo, se `todos`). Devolve (sha ou None, gravados,
        nao_gravados): um arquivo que o git não consegue ler (aberto por outro programa, por exemplo) fica de fora
        e vai para `nao_gravados` com o motivo, em vez de derrubar o ponto inteiro."""
        assert tipo in TIPOS
        if self.tem_commit():
            self.git("reset", "-q")
        else:
            self.git("read-tree", "--empty")
        gravados, nao_gravados = [], []
        if todos:
            alvos = [caminho for _, caminho in self.mudancas()]
        else:
            alvos = list(dict.fromkeys(caminhos))
        rastreados = set(self.rastreados()) if alvos else set()
        tirar = [c for c in alvos if c in rastreados and not self.existe_exato(c)]
        por = [c for c in alvos if c not in set(tirar)]

        def um_por_um(comando, lista):
            for caminho in lista:
                resultado = self.git(*comando, "--", caminho, verificar=False)
                if resultado.returncode == 0:
                    gravados.append(caminho)
                else:
                    nao_gravados.append({"arquivo": caminho,
                                         "motivo": resultado.stderr.decode("utf-8", "replace").strip()[:300]})

        # Todos de uma vez (um processo do git por ponto, não por arquivo); se um falhar, um por um, para só
        # aquele ficar de fora.
        for comando, lista in ((("rm", "--cached", "-q", "--ignore-unmatch"), tirar), (("add", "-A"), por)):
            if not lista:
                continue
            junto = self.git(*comando, "--pathspec-from-file=-", "--pathspec-file-nul",
                             entrada="\0".join(lista).encode("utf-8"), verificar=False)
            if junto.returncode == 0:
                gravados.extend(lista)
            else:
                um_por_um(comando, lista)
        if self.git("diff", "--cached", "--quiet", verificar=False).returncode == 0:
            return None, [], nao_gravados
        linha_rotulo = " ".join(rotulo_pedido.split()) if rotulo_pedido else ""
        mensagem = (f"[{tipo}] {rotulo}\n\nButler-Pedido: {pedido}\n"
                    + (f"Butler-Rotulo: {linha_rotulo}\n" if linha_rotulo else "") + f"Butler-Tipo: {tipo}\n")
        self.git("commit", "-q", "--no-verify", "-F", "-", entrada=mensagem.encode("utf-8"))
        return self.head(), gravados, nao_gravados
