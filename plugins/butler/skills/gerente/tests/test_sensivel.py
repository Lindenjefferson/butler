"""Dado sensível: o que casa, o que não casa, liberação e o valor nunca na saída."""
import json

from apoio import Ambiente, nota, rodar_testes
from lib import sensivel

CPF_VALIDO = "529.982.247-25"
CARTAO_VALIDO = "4111 1111 1111 1111"


def tipos(texto, liberadas=()):
    return [a["tipo"] for a in sensivel.achar(texto, liberadas)]


def test_casa_cpf_cartao_senha_pin_rg_e_token():
    assert tipos(f"CPF {CPF_VALIDO}") == ["cpf"]
    assert tipos("cpf: 52998224725") == ["cpf"]
    assert tipos(f"Cartão {CARTAO_VALIDO}") == ["cartao"]
    assert tipos("número do cartão de crédito: 4111111111111111") == ["cartao"]
    assert tipos("Senha: hunter22") == ["senha"]
    assert tipos('{"password": "hunter22"}') == ["senha"]
    assert tipos("| Wi-Fi | senha | abc12345 |") == ["senha"]
    assert tipos("a senha é abc12345") == ["senha"]
    assert tipos("PIN: 4821") == ["pin"]
    assert tipos("RG: 12.345.678-9") == ["rg"]
    assert tipos("chave ghp_" + "a" * 36) == ["token"]


def test_nao_casa_o_que_o_vault_guarda_de_proposito():
    assert tipos("Número de série: 4111111111111111") == []
    assert tipos("cartão SD de 128 GB, serial 4111111111111111") == []
    assert tipos("Cartão SIM, IMEI 490154203237518") == []
    assert tipos("MAC 00:1A:2B:3C:4D:5E") == []
    assert tipos("Placa ABC1D23") == []
    assert tipos("R$ 1.234,56 em 12x de R$ 102,88") == []
    assert tipos("PIN: 24 (pinos do conector)") == []
    assert tipos("CPF 111.111.111-11") == []
    assert tipos("123.456.789-00") == []
    assert tipos("Não guardar senhas, cartões ou documentos (CPF, RG etc.).") == []
    assert tipos("| Conta | Senha |\n|---|---|") == []
    assert tipos("Senha: Não informado") == []
    assert tipos("2026-11-06 13:45:10") == []


def test_liberacao_pela_digital_vale_com_a_nota_mudada():
    achado = sensivel.achar(f"CPF {CPF_VALIDO}")[0]
    assert tipos(f"linha nova\nCPF {CPF_VALIDO}", liberadas=[achado["digital"]]) == []
    assert achado["linha"] == 1


def test_dado_sensivel_de_fora_fica_fora_do_ponto_e_o_resto_entra():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Inbox/Banco.md", nota("Banco", f"Senha: hunter22\nCPF {CPF_VALIDO}"))
        amb.escrever("Inbox/Livre.md", nota("Livre"))
        resposta = amb.inicio()
        texto = json.dumps(resposta, ensure_ascii=False)
        assert "hunter22" not in texto and CPF_VALIDO not in texto
        fora = resposta["mudancas_de_fora"]["fora_do_historico"]
        assert [f["arquivo"] for f in fora] == ["Inbox/Banco.md"] and fora[0]["motivo"] == "dado sensível"
        arquivos = amb.git("ls-files")
        assert "Inbox/Livre.md" in arquivos and "Inbox/Banco.md" not in arquivos
        assert resposta["historico_ok"] is True
    finally:
        amb.fechar()


def test_binario_fica_fora_ate_ser_liberado():
    amb = Ambiente()
    try:
        amb.preparar()
        amb.escrever("Inbox/print.png", b"\x89PNG\r\n\x1a\n\x00\x00binario", binario=True)
        fora = amb.inicio()["mudancas_de_fora"]["fora_do_historico"]
        assert fora[0]["motivo"] == "binário"
        assert "Inbox/print.png" not in amb.git("ls-files")
        regras = amb.ler("Sistema/Regras do Butler.md").replace(
            "## Liberações de dado sensível\n", f"## Liberações de dado sensível\n\n- `{fora[0]['digital']}` — print\n")
        amb.escrever("Sistema/Regras do Butler.md", regras)
        amb.rodar("liberar-trava", "--forcar")
        amb.inicio()
        assert "Inbox/print.png" in amb.git("ls-files")
    finally:
        amb.fechar()


def test_ponto_recusa_arquivo_sensivel():
    amb = Ambiente()
    try:
        amb.preparar()
        token = amb.inicio()["token"]
        amb.escrever("Inventários/Geladeira.md", nota("Geladeira", "Senha: hunter22"))
        resposta = amb.rodar("ponto", "--token", token, "--rotulo", "x", "Inventários/Geladeira.md")
        assert resposta["recusados"][0]["motivo"] == "dado sensível" and resposta["ponto"] is None
    finally:
        amb.fechar()


if __name__ == "__main__":
    rodar_testes(globals())
