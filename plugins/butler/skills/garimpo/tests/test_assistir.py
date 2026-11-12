"""assistir.py: motor local (único), e metadados pelo yt-dlp."""
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
    base = dict(navegador="firefox", max_frames=12, resolucao=768, timeout=900)
    base.update(extra)
    return argparse.Namespace(**base)


def test_comando_watch_usa_motor_local():
    cmd = assistir.comando_watch("scripts", "https://youtu.be/x", opcoes(), "saida")
    assert cmd[cmd.index("--engine") + 1] == "local"
    assert cmd[cmd.index("--whisper") + 1] == "whisperx"
    assert cmd[cmd.index("--max-frames") + 1] == "12"
    assert cmd[cmd.index("--resolution") + 1] == "768"
    assert cmd[cmd.index("--cookies-from-browser") + 1] == "firefox"
    assert "--question" not in cmd


def test_argumentos_sem_engine():
    orig = sys.argv
    sys.argv = ["assistir.py", "https://youtu.be/x"]
    try:
        a = assistir.argumentos()
    finally:
        sys.argv = orig
    assert not hasattr(a, "engine") and not hasattr(a, "pergunta"), a


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


def _processar(relatorio, info=INFO, codigo=0, err="", frames=False):
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
            return assistir.processar(1, "https://www.instagram.com/reel/ABC123/?igsh=1", opcoes(),
                                      "scripts", {}, pasta)
        finally:
            assistir.rodar, assistir.metadados = orig_rodar, orig_meta


def test_local_ok_com_frames():
    item = _processar(RELATORIO_LOCAL, info=None, frames=True)
    assert item["status"] == "ok" and item["frames"], item
    assert "engine" not in item, item
    assert item["autor"] == "canal_do_relatorio" and item["titulo"] == "Título do relatório", item
    assert item["duracao"] == "1:05 (65.0s)" and item["transcricao_status"].startswith("12 segments"), item
    assert item["url_canonica"] == "https://www.instagram.com/reel/ABC123/", "sem metadado, a URL limpa"


def test_local_sem_frames_conta_como_falha():
    item = _processar(RELATORIO_LOCAL)
    assert item["status"] == "falhou", "sem frames não conta como ok"


def test_sem_video_e_falha_generica():
    sem = _processar("## Unavailable evidence\n\n- yt-dlp failed: There is no video in this post\n", codigo=1)
    assert sem["status"] == "sem_video", sem
    relatorio = "## Unavailable evidence\n\n- download failed: HTTP 503.\n"
    falhou = _processar(relatorio, codigo=1, err="[watch] baixando…")
    assert falhou["status"] == "falhou" and falhou["erro"] == "download failed: HTTP 503.", falhou


if __name__ == "__main__":
    test_comando_watch_usa_motor_local()
    test_argumentos_sem_engine()
    test_metadados_pelo_yt_dlp()
    test_local_ok_com_frames()
    test_local_sem_frames_conta_como_falha()
    test_sem_video_e_falha_generica()
    print("ALL PASS")
