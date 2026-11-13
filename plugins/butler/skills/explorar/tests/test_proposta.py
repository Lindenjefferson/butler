"""proposta.py: guarda a proposta fora do vault, consolida por destino, mostra blocos, marca estado e confere digitais."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(AQUI), "scripts", "proposta.py")

REGRAS = """# Regras do Butler

## Notas protegidas

- `Casa/Protegida.md` — protegida
"""


class Caso:
    """Um vault e uma configuração da máquina numa pasta temporária, com o script rodado como o usuário roda."""

    def __init__(self):
        self.raiz = tempfile.mkdtemp(prefix="explorar-teste-")
        self.vault = os.path.join(self.raiz, "Vault")
        self.config = os.path.join(self.raiz, "maquina", "maquina.json")
        os.makedirs(self.vault)

    def escrever(self, rel, texto="# x\n"):
        destino = os.path.join(self.vault, *rel.split("/"))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)

    def rodar(self, *args, esperado=0):
        env = dict(os.environ, BUTLER_CONFIG=self.config, PYTHONIOENCODING="cp1252",
                   LOCALAPPDATA=os.path.join(self.raiz, "local"))
        env.pop("PYTHONUTF8", None)
        p = subprocess.run([sys.executable, SCRIPT, self.vault, *args], capture_output=True, env=env)
        texto = p.stdout.decode("utf-8", "replace")
        assert p.returncode == esperado, (args, p.returncode, texto, p.stderr.decode("utf-8", "replace"))
        return json.loads(texto) if texto.strip() else None

    def iniciar(self, grupos, rotulo="explorar: Viagens"):
        caminho = os.path.join(self.raiz, "alvo.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"alvo": {"tipo": "pasta", "valor": "X"},
                       "grupos": [{"id": f"g{i + 1}", "pasta": "", "notas": g} for i, g in enumerate(grupos)],
                       "fora": [], "reassistir": [], "tema_candidatos": []}, f, ensure_ascii=False)
        return self.rodar("iniciar", "--alvo", caminho, "--rotulo", rotulo)

    def responder(self, saida, grupo, notas, temas=()):
        with open(saida, "w", encoding="utf-8") as f:
            json.dump({"grupo": grupo, "notas": notas, "temas": list(temas)}, f, ensure_ascii=False)

    def proposta(self, ident):
        with open(os.path.join(self.pasta(ident), "proposta.json"), encoding="utf-8") as f:
            return json.load(f)

    def pasta(self, ident):
        return os.path.join(os.path.dirname(self.config), "sem-historico", os.listdir(
            os.path.join(os.path.dirname(self.config), "sem-historico"))[0], "explorar", ident)

    def fechar(self):
        shutil.rmtree(self.raiz, ignore_errors=True)


def item(nota, tipo, alvo, linha=""):
    return {"nota": nota, "destino": {"tipo": tipo, "alvo": alvo}, "porque": "teste", "linha": linha,
            "cortes": [], "esboco": [], "acrescimos": [], "atencao": []}


def por_destino(itens, destino):
    achados = [i for i in itens if i["destino"].lower() == destino.lower()]
    assert len(achados) == 1, (destino, [i["destino"] for i in itens])
    return achados[0]


def test_iniciar_grava_digitais_e_caminhos_de_saida():
    c = Caso()
    try:
        c.escrever("Viagens/A.md", "conteúdo A\n")
        c.escrever("Viagens/B.md", "conteúdo B\n")
        r = c.iniciar([["Viagens/A.md"], ["Viagens/B.md"]])
        assert len(r["id"].split("-")) == 3 and len(r["id"].split("-")[2]) == 4, r["id"]
        assert os.path.isdir(r["pasta"]) and not r["pasta"].startswith(c.vault), r
        assert [g["id"] for g in r["grupos"]] == ["g1", "g2"], r
        assert r["grupos"][0]["saida"] == os.path.join(r["pasta"], "g1.json"), r
        p = c.proposta(r["id"])
        esperado = hashlib.sha256("conteúdo A\n".encode("utf-8")).hexdigest()
        assert p["digitais"]["Viagens/A.md"] == esperado, p["digitais"]
        assert set(p["digitais"]) == {"Viagens/A.md", "Viagens/B.md"}, p["digitais"]
        assert p["rotulo"] == "explorar: Viagens" and p["itens"] == [], p
    finally:
        c.fechar()


def test_consolidar_junta_mesmo_destino_de_grupos_diferentes():
    c = Caso()
    try:
        c.escrever("Viagens/A.md")
        c.escrever("Viagens/B.md")
        r = c.iniciar([["Viagens/A.md"], ["Viagens/B.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "linha", "Dicas de Viagem", "- A")])
        c.responder(r["grupos"][1]["saida"], "g2", [item("Viagens/B.md", "linha", "dicas de viagem", "- B")])
        s = c.rodar("consolidar", "--id", r["id"])
        assert s["itens"] == 1 and s["blocos"] == 1 and s["faltam_grupos"] == [], s
        it = c.proposta(r["id"])["itens"][0]
        assert it["destino"] == "Viagens/Dicas de Viagem.md", it
        assert it["origens"] == ["Viagens/A.md", "Viagens/B.md"], it
        assert it["tipo"] == "linha" and it["estado"] == "pendente" and it["n"] == 1, it
    finally:
        c.fechar()


def test_consolidar_marca_dependencia():
    c = Caso()
    try:
        c.escrever("Viagens/A.md")
        c.escrever("Viagens/B.md")
        r = c.iniciar([["Viagens/A.md"], ["Viagens/B.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "detalhe", "Roteiro Lisboa")])
        c.responder(r["grupos"][1]["saida"], "g2", [item("Viagens/B.md", "fundir", "Roteiro Lisboa")])
        c.rodar("consolidar", "--id", r["id"])
        itens = c.proposta(r["id"])["itens"]
        criador = [i for i in itens if i["tipo"] == "detalhe"][0]
        fundir = [i for i in itens if i["tipo"] == "fundir"][0]
        assert fundir["destino"] == criador["destino"] == "Viagens/Roteiro Lisboa.md", itens
        assert fundir["depende_de"] == [criador["n"]] and criador["depende_de"] == [], itens
    finally:
        c.fechar()


def test_consolidar_lista_links_de_entrada():
    c = Caso()
    try:
        c.escrever("Viagens/A.md", "# A\n")
        c.escrever("Viagens/Outra.md", "ver [[A]]\n")
        c.escrever("Casa/Mais.md", "ver [[A|apelido]] e [[Nada]]\n")
        c.escrever("Casa/Nada.md", "sem links\n")
        r = c.iniciar([["Viagens/A.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "descartar", "")])
        c.rodar("consolidar", "--id", r["id"])
        it = c.proposta(r["id"])["itens"][0]
        assert it["links_de_entrada"] == {"Viagens/A.md": ["Casa/Mais.md", "Viagens/Outra.md"]}, it
    finally:
        c.fechar()


def test_consolidar_nome_invalido_e_repetido():
    c = Caso()
    try:
        c.escrever("Viagens/A.md")
        c.escrever("Viagens/B.md")
        c.escrever("Casa/Geladeira.md")
        r = c.iniciar([["Viagens/A.md", "Viagens/B.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "linha", "Dicas: Viagem"),
                                                     item("Viagens/B.md", "detalhe", "Viagens/Geladeira")])
        c.rodar("consolidar", "--id", r["id"])
        itens = c.proposta(r["id"])["itens"]
        assert "nome_invalido" in por_destino(itens, "Viagens/Dicas: Viagem.md")["avisos"], itens
        repetido = por_destino(itens, "Viagens/Geladeira.md")
        assert "nome_repetido" in repetido["avisos"] and "nome_invalido" not in repetido["avisos"], repetido
    finally:
        c.fechar()


def test_consolidar_pasta_nova():
    c = Caso()
    try:
        c.escrever("Viagens/A.md")
        c.escrever("Viagens/B.md")
        c.escrever("Casa/Protegida.md")
        c.escrever("Sistema/Regras do Butler.md", REGRAS)
        r = c.iniciar([["Viagens/A.md", "Viagens/B.md", "Casa/Protegida.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "mover", "Viagens/Europa"),
                                                     item("Viagens/B.md", "mover", "Viagens"),
                                                     item("Casa/Protegida.md", "descartar", "")])
        c.rodar("consolidar", "--id", r["id"])
        itens = c.proposta(r["id"])["itens"]
        assert "pasta_nova" in por_destino(itens, "Viagens/Europa/A.md")["avisos"], itens
        assert "pasta_nova" not in por_destino(itens, "Viagens/B.md")["avisos"], itens
        assert por_destino(itens, "Casa/Protegida.md")["avisos"] == ["protegida"], itens
    finally:
        c.fechar()


def test_consolidar_avisa_grupo_faltando():
    c = Caso()
    try:
        c.escrever("Viagens/A.md")
        c.escrever("Viagens/B.md")
        r = c.iniciar([["Viagens/A.md"], ["Viagens/B.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "descartar", "")])
        s = c.rodar("consolidar", "--id", r["id"])
        assert s["faltam_grupos"] == ["g2"] and s["itens"] == 1, s
    finally:
        c.fechar()


def test_bloco_ate_dez_na_ordem():
    c = Caso()
    try:
        notas = []
        respostas = []
        for i in range(4):
            notas.append(f"V/D{i}.md")
            respostas.append(item(f"V/D{i}.md", "descartar", ""))
        for i in range(4):
            notas.append(f"V/M{i}.md")
            respostas.append(item(f"V/M{i}.md", "mover", "W"))
        for i in range(4):
            notas.append(f"V/L{i}.md")
            respostas.append(item(f"V/L{i}.md", "linha", f"Lista {i}", "- x"))
        c.escrever("W/.keep.md")
        for i in range(4):
            notas.append(f"V/T{i}.md")
            respostas.append(item(f"V/T{i}.md", "detalhe", f"Detalhe {i}"))
        for n in notas:
            c.escrever(n)
        r = c.iniciar([notas])
        c.responder(r["grupos"][0]["saida"], "g1", respostas)
        s = c.rodar("consolidar", "--id", r["id"])
        assert s["itens"] == 16 and s["blocos"] == 2, s
        b1 = c.rodar("bloco", "--id", r["id"], "--n", "1")
        b2 = c.rodar("bloco", "--id", r["id"], "--n", "2")
        assert [i["n"] for i in b1["itens"]] == list(range(1, 11)), b1
        assert [i["n"] for i in b2["itens"]] == list(range(11, 17)), b2
        tipos = [i["tipo"] for i in b1["itens"] + b2["itens"]]
        assert tipos == ["linha"] * 4 + ["detalhe"] * 4 + ["mover"] * 4 + ["descartar"] * 4, tipos
    finally:
        c.fechar()


def test_recusar_bloqueia_dependentes():
    c = Caso()
    try:
        c.escrever("Viagens/A.md")
        c.escrever("Viagens/B.md")
        c.escrever("Viagens/C.md")
        r = c.iniciar([["Viagens/A.md", "Viagens/B.md", "Viagens/C.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "detalhe", "Roteiro"),
                                                     item("Viagens/B.md", "fundir", "Roteiro"),
                                                     item("Viagens/C.md", "descartar", "")])
        c.rodar("consolidar", "--id", r["id"])
        itens = c.proposta(r["id"])["itens"]
        criador = [i for i in itens if i["tipo"] == "detalhe"][0]["n"]
        dependente = [i for i in itens if i["tipo"] == "fundir"][0]["n"]
        solto = [i for i in itens if i["tipo"] == "descartar"][0]["n"]
        c.rodar("marcar", "--id", r["id"], "--itens", str(criador), "--estado", "recusado")
        estados = {i["n"]: i["estado"] for i in c.proposta(r["id"])["itens"]}
        assert estados == {criador: "recusado", dependente: "bloqueado", solto: "pendente"}, estados
        c.rodar("marcar", "--id", r["id"], "--itens", str(solto), "--estado", "aprovado")
        assert {i["n"]: i["estado"] for i in c.proposta(r["id"])["itens"]}[solto] == "aprovado"
    finally:
        c.fechar()


def test_conferir_detecta_nota_editada():
    c = Caso()
    try:
        c.escrever("Viagens/A.md", "um\n")
        c.escrever("Viagens/B.md", "dois\n")
        r = c.iniciar([["Viagens/A.md", "Viagens/B.md"]])
        c.responder(r["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "descartar", ""),
                                                     item("Viagens/B.md", "descartar", "")])
        c.rodar("consolidar", "--id", r["id"])
        c.escrever("Viagens/A.md", "um editado\n")
        itens = {i["origens"][0]: i["n"] for i in c.proposta(r["id"])["itens"]}
        s = c.rodar("conferir", "--id", r["id"])
        assert s == {"mudou": [itens["Viagens/A.md"]], "ok": [itens["Viagens/B.md"]]}, s
        s = c.rodar("conferir", "--id", r["id"], "--itens", str(itens["Viagens/B.md"]))
        assert s == {"mudou": [], "ok": [itens["Viagens/B.md"]]}, s
    finally:
        c.fechar()


def test_listar_e_remover():
    c = Caso()
    try:
        c.escrever("Viagens/A.md")
        r1 = c.iniciar([["Viagens/A.md"]], rotulo="um")
        c.responder(r1["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "descartar", "")])
        c.rodar("consolidar", "--id", r1["id"])
        r2 = c.iniciar([["Viagens/A.md"]], rotulo="dois")
        c.responder(r2["grupos"][0]["saida"], "g1", [item("Viagens/A.md", "descartar", "")])
        c.rodar("consolidar", "--id", r2["id"])
        c.rodar("marcar", "--id", r2["id"], "--itens", "1", "--estado", "aplicado")
        lista = c.rodar("listar")
        assert [p["id"] for p in lista["propostas"]] == [r1["id"]], lista
        assert lista["propostas"][0]["rotulo"] == "um" and lista["propostas"][0]["pendentes"] == 1, lista
        c.rodar("remover", "--id", r1["id"])
        assert not os.path.exists(r1["pasta"]), r1
        assert c.rodar("listar")["propostas"] == []
        c.rodar("remover", "--id", "nao-existe", esperado=2)
    finally:
        c.fechar()


if __name__ == "__main__":
    falhas = []
    for nome, funcao in sorted(globals().items()):
        if nome.startswith("test_") and callable(funcao):
            try:
                funcao()
                print("ok  ", nome)
            except Exception:
                falhas.append(nome)
                print("FAIL", nome)
                traceback.print_exc()
    if falhas:
        print(f"{len(falhas)} FAILED: {', '.join(falhas)}")
        sys.exit(1)
    print("ALL PASS")
