"""assistir.py: motor Gemini por padrão, local sob pedido, e metadados pelo yt-dlp em qualquer motor."""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "assistir.py")
_spec = importlib.util.spec_from_file_location("assistir", SCRIPT)
assistir = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(assistir)

RELATORIO_GEMINI = """
# watch: video report

- **Source:** https://www.instagram.com/reel/ABC123/ (video uploaded to Google, deleted after the answer)
- **Engine:** gemini-x (ok)

## Answer (from Gemini)

_These are Gemini's observations of the video._

0:03 a tela mostra o repositório dono/projeto.
"""

RELATORIO_LOCAL = """
# watch: video report

- **Source:** https://youtu.be/xyz
- **Title:** Título do relatório
- **Uploader:** canal_do_relatorio
- **Duration:** 1:05 (65.0s)
- **Transcript:** 12 segments (via whisperx)
"""

INFO = {"uploader": "Fulano Exemplo", "channel": "fulano", "title": "Um Reel", "duration": 65.4,
        "webpage_url": "https://www.instagram.com/reel/ABC123/?igsh=xyz"}


def opcoes(**extra):
    base = dict(engine="gemini", navegador="firefox", max_frames=12, resolucao=768, timeout=900, pergunta=None)
    base.update(extra)
    return argparse.Namespace(**base)


def test_engine_padrao_e_gemini():
    orig = sys.argv
    sys.argv = ["assistir.py", "https://youtu.be/x"]
    try:
        a = assistir.argumentos()
    finally:
        sys.argv = orig
    assert a.engine == "gemini", a
    cmd = assistir.comando_watch("scripts", "https://youtu.be/x", a, "saida")
    assert cmd[cmd.index("--engine") + 1] == "gemini", cmd
    assert cmd[cmd.index("--cookies-from-browser") + 1] == "firefox", cmd
    assert "--whisper" not in cmd and "--max-frames" not in cmd, "opções só do motor local"
    assert "--question" in cmd


def test_engine_local_mantem_whisperx_e_frames():
    cmd = assistir.comando_watch("scripts", "https://youtu.be/x", opcoes(engine="local"), "saida")
    assert cmd[cmd.index("--engine") + 1] == "local"
    assert cmd[cmd.index("--whisper") + 1] == "whisperx"
    assert cmd[cmd.index("--max-frames") + 1] == "12"
    assert cmd[cmd.index("--cookies-from-browser") + 1] == "firefox"
    assert "--question" not in cmd, "o motor local não usa a pergunta"


def test_pergunta_estruturada():
    padrao = assistir.pergunta_gemini(None)
    assert "nomes exatos" in padrao and "tela" in padrao and "timestamp" in padrao.lower(), padrao
    com = assistir.pergunta_gemini("  Qual o preço?  ")
    assert com.startswith(padrao) and com.endswith("Qual o preço?"), com
    cmd = assistir.comando_watch("s", "u", opcoes(pergunta="Qual o preço?"), "p")
    assert cmd[cmd.index("--question") + 1] == com


def test_metadados_pelo_yt_dlp():
    chamadas = []

    def executar(cmd, **_):
        chamadas.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, json.dumps(INFO), "")

    m = assistir.metadados("https://www.instagram.com/reel/ABC123/", "firefox", executar=executar)
    assert m == {"autor": "Fulano Exemplo", "titulo": "Um Reel", "duracao": "1:05",
                 "url_canonica": "https://www.instagram.com/reel/ABC123/"}, m
    cmd = chamadas[0]
    assert "--dump-json" in cmd and "--skip-download" in cmd and "--no-playlist" in cmd, cmd
    assert cmd[cmd.index("--cookies-from-browser") + 1] == "firefox"

    longo = dict(INFO, uploader=None, duration=3725)
    m = assistir.metadados("u", "firefox", executar=lambda c, **_: subprocess.CompletedProcess(c, 0, json.dumps(longo), ""))
    assert m["autor"] == "fulano" and m["duracao"] == "1:02:05", m

    falha = assistir.metadados("u", "firefox", executar=lambda c, **_: subprocess.CompletedProcess(c, 1, "", "ERROR: x"))
    assert falha == {}, falha


def _processar(relatorio, engine, info=INFO, codigo=0, err="", frames=False):
    with tempfile.TemporaryDirectory() as pasta:
        if frames:
            os.makedirs(os.path.join(pasta, "watch-1", "frames"))
            open(os.path.join(pasta, "watch-1", "frames", "frame_0001.jpg"), "wb").close()
        orig_rodar, orig_meta = assistir.rodar, assistir.metadados
        assistir.rodar = lambda cmd, env, timeout: (codigo, relatorio, err, False)
        assistir.metadados = lambda url, navegador: ({} if info is None else {
            "autor": "Fulano Exemplo", "titulo": "Um Reel", "duracao": "1:05",
            "url_canonica": "https://www.instagram.com/reel/ABC123/"})
        try:
            return assistir.processar(1, "https://www.instagram.com/reel/ABC123/?igsh=1", opcoes(engine=engine),
                                      "scripts", {}, pasta)
        finally:
            assistir.rodar, assistir.metadados = orig_rodar, orig_meta


def test_gemini_ok_sem_frames():
    item = _processar(RELATORIO_GEMINI, "gemini")
    assert item["status"] == "ok" and item["engine"] == "gemini" and item["frames"] is None, item
    assert item["autor"] == "Fulano Exemplo" and item["titulo"] == "Um Reel" and item["duracao"] == "1:05", item
    assert item["url_canonica"] == "https://www.instagram.com/reel/ABC123/", item


def test_gemini_sem_video_e_falha():
    sem = _processar("## Unavailable evidence\n\n- yt-dlp failed: There is no video in this post\n", "gemini", codigo=1)
    assert sem["status"] == "sem_video", sem
    relatorio = ("- **Engine:** gemini-x (failed)\n\n## Unavailable evidence\n\n"
                 "- Gemini service: HTTP 503: high demand.\n")
    falhou = _processar(relatorio, "gemini", codigo=1, err="[watch] asking gemini-x…")
    assert falhou["status"] == "falhou" and falhou["erro"] == "Gemini service: HTTP 503: high demand.", falhou


def test_local_usa_relatorio_quando_falta_metadado():
    item = _processar(RELATORIO_LOCAL, "local", info=None, frames=True)
    assert item["status"] == "ok" and item["engine"] == "local" and item["frames"], item
    assert item["autor"] == "canal_do_relatorio" and item["titulo"] == "Título do relatório", item
    assert item["duracao"] == "1:05 (65.0s)" and item["transcricao_status"].startswith("12 segments"), item
    assert item["url_canonica"] == "https://www.instagram.com/reel/ABC123/", "sem metadado, a URL limpa"
    sem_frames = _processar(RELATORIO_LOCAL, "local")
    assert sem_frames["status"] == "falhou", "no motor local, sem frames não conta como ok"


if __name__ == "__main__":
    test_engine_padrao_e_gemini()
    test_engine_local_mantem_whisperx_e_frames()
    test_pergunta_estruturada()
    test_metadados_pelo_yt_dlp()
    test_gemini_ok_sem_frames()
    test_gemini_sem_video_e_falha()
    test_local_usa_relatorio_quando_falta_metadado()
    print("ALL PASS")
