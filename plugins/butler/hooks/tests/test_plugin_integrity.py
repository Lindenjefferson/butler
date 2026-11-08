"""Integridade do plugin: manifesto, skills, caminhos citados, histórico de versões e nada de um vault específico.

O plugin não pode carregar regra, caminho nem nome de pessoa de um vault (as regras moram no vault). Este teste
procura em tudo o que se instala (`plugins/butler/`) caminhos de usuário do Windows, e-mails e os nomes que só um
vault teria. Os testes ficam de fora da busca de nomes porque os vaults sintéticos deles precisam de nomes.
"""
import hashlib
import json
import os
import re
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(os.path.dirname(PLUGIN))
sys.path.insert(0, os.path.join(PLUGIN, "skills", "gerente", "tests"))

from apoio import rodar_testes  # noqa: E402

INVISIVEIS = "[" + "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C,
                                            0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0xFEFF)) + "]"
PROIBIDOS = [
    (re.compile(r"[A-Za-z]:\\+Users\\+(?!<)[^\\\s]+", re.I), "caminho de usuário do Windows"),
    (re.compile(r"/c/Users/(?!<)[^/\s]+", re.I), "caminho de usuário do Git Bash"),
    (re.compile(r"[\w.+-]+@(?!localhost\b)[\w-]+\.[\w.]+"), "e-mail"),
]
# Os nomes que só o vault do autor tem (pessoas, carro, projetos), guardados pelo hash para o teste, que vai junto
# com o plugin, não publicar os próprios nomes. Para acrescentar um: hashlib.sha256(nome.lower().encode()).hexdigest()[:16]
NOMES_DE_UM_VAULT = {"0ac19ab1fa193669", "a051e62c16c385ab", "bea359bea8f7d88e", "757b737e152bcd5f",
                     "0b691f0b0e8a4034"}


def _arquivos(raiz, pular_testes=False):
    for pasta, subpastas, nomes in os.walk(raiz):
        subpastas[:] = [s for s in subpastas if s != "__pycache__" and not (pular_testes and s == "tests")]
        for nome in nomes:
            if nome.endswith((".md", ".py", ".json", ".sh")):
                yield os.path.join(pasta, nome)


def _ler(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        return arquivo.read()


def test_manifesto_e_marketplace():
    manifesto = json.loads(_ler(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")))
    assert manifesto["name"] == "butler" and re.fullmatch(r"\d+\.\d+\.\d+", manifesto["version"])
    mercado = json.loads(_ler(os.path.join(REPO, ".claude-plugin", "marketplace.json")))
    assert [p["source"] for p in mercado["plugins"] if p["name"] == "butler"] == ["./plugins/butler"]
    json.loads(_ler(os.path.join(PLUGIN, "hooks", "hooks.json")))


def test_versao_tem_secao_no_historico():
    versao = json.loads(_ler(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")))["version"]
    historico = _ler(os.path.join(PLUGIN, "UPGRADING.md"))
    assert re.search(r"^## " + re.escape(versao) + r"\b", historico, re.M), versao
    secao = historico.split("## " + versao, 1)[1].split("\n## ", 1)[0]
    assert "**Ao atualizar:**" in secao


def test_cada_skill_tem_nome_e_descricao():
    pasta = os.path.join(PLUGIN, "skills")
    for nome in sorted(os.listdir(pasta)):
        texto = _ler(os.path.join(pasta, nome, "SKILL.md"))
        topo = texto.split("---", 2)[1]
        assert re.search(r"^name: " + re.escape(nome) + r"$", topo, re.M), nome
        descricao = re.search(r"^description: (.+)$", topo, re.M)
        assert descricao and len(descricao.group(1)) > 80, nome


def test_caminhos_citados_existem():
    padrao = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^`\"\n\\]+)")
    for caminho in _arquivos(PLUGIN):
        for citado in padrao.findall(_ler(caminho)):
            citado = citado.rstrip(".,;:")
            assert os.path.exists(os.path.join(PLUGIN, *citado.split("/"))), f"{caminho}: {citado}"


def test_nada_de_um_vault_especifico_no_que_se_instala():
    for caminho in _arquivos(PLUGIN, pular_testes=True):
        if os.path.basename(os.path.dirname(caminho)) == ".claude-plugin":
            continue  # o manifesto traz o autor, de propósito
        texto = _ler(caminho)
        for padrao, tipo in PROIBIDOS:
            achado = padrao.search(texto)
            assert not achado, f"{os.path.relpath(caminho, PLUGIN)}: {tipo}: {achado.group(0)}"
        for palavra in set(re.findall(r"[^\W\d_]+", texto.lower())):
            if hashlib.sha256(palavra.encode("utf-8")).hexdigest()[:16] in NOMES_DE_UM_VAULT:
                raise AssertionError(f"{os.path.relpath(caminho, PLUGIN)}: nome de um vault: {palavra}")


def test_sem_caractere_invisivel():
    for caminho in _arquivos(PLUGIN):
        texto = _ler(caminho)
        assert not re.search(INVISIVEIS, texto), caminho


if __name__ == "__main__":
    rodar_testes(globals())
