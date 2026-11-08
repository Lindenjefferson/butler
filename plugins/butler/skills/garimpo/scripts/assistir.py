#!/usr/bin/env python3
"""Assiste a uma lista de links de vídeo com o plugin claude-video e deixa tudo pronto para virar nota.

Para cada link: roda o watch.py do plugin (motor local, transcrição local WhisperX, cookies do
navegador, poucos frames, largura 768 para ler o texto da tela) e guarda o relatório. Só vídeos:
se o post não tem vídeo (carrossel de imagens), o status fica "sem_video" e quem chamou decide.
No fim grava <saida>/resultado.json e imprime o mesmo JSON, com os links na ordem recebida.
Sai com código 1 se nenhum link deu certo e 2 se faltar ferramenta do plugin.

Uso: python assistir.py URL [URL ...] [--saida PASTA] [--pausa 25] [--navegador firefox]
                        [--max-frames 12] [--timeout 900]
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit, urlunsplit

SEM_VIDEO = ("No video formats found", "There is no video in this post")


def achar_scripts_plugin():
    base = os.path.join(os.path.expanduser("~"), ".claude", "plugins", "cache", "claude-video", "watch")
    candidatos = glob.glob(os.path.join(base, "*", "skills", "watch", "scripts", "watch.py"))
    if not candidatos:
        sys.exit("watch.py não encontrado: instale o plugin com 'claude plugin install watch@claude-video'.")
    # a pasta da versão (0.3.2, 0.10.0...) ordena numericamente
    candidatos.sort(key=lambda p: [int(x) if x.isdigit() else 0 for x in re.split(r"[.\-]", p.split(os.sep)[-5])])
    return os.path.dirname(candidatos[-1])


def campo(texto, nome):
    m = re.search(r"\*\*%s:\*\* (.*)" % re.escape(nome), texto)
    return m.group(1).strip() if m else ""


def url_limpa(url):
    """Tira query e fragmento (igsh, utm_* identificam quem compartilhou), exceto o v= do YouTube."""
    p = urlsplit(url)
    if "youtube.com" in p.netloc and "v=" in p.query:
        v = [q for q in p.query.split("&") if q.startswith("v=")][0]
        return urlunsplit((p.scheme, p.netloc, p.path, v, ""))
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def url_canonica(pasta, url):
    for info in glob.glob(os.path.join(pasta, "**", "video.info.json"), recursive=True):
        try:
            with open(info, encoding="utf-8") as f:
                web = json.load(f).get("webpage_url")
            if web:
                return url_limpa(web)
        except (OSError, ValueError):
            pass
    return url_limpa(url)


def rodar(cmd, env, timeout):
    """Roda o watch.py; no timeout mata a árvore inteira (yt-dlp, ffmpeg, whisperx), não só o filho."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         encoding="utf-8", errors="replace", env=env)
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out, err, False
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            p.kill()
        out, err = p.communicate()
        return -1, out or "", (err or "") + "\ntimeout após %d s" % timeout, True


def main():
    # sem isso, no Windows com Python <= 3.14 um emoji no título quebra o print final (cp1252)
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--pausa", type=int, default=25, help="segundos entre links do Instagram")
    ap.add_argument("--navegador", default="firefox")
    ap.add_argument("--max-frames", type=int, default=12, help="12 para Reels; 40 a 60 para vídeos longos")
    ap.add_argument("--resolucao", type=int, default=768)
    ap.add_argument("--timeout", type=int, default=900, help="segundos por vídeo antes de desistir")
    a = ap.parse_args()

    scripts = achar_scripts_plugin()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")

    # confere ffmpeg e yt-dlp antes do lote, para não falhar vídeo por vídeo
    chk = subprocess.run([sys.executable, os.path.join(scripts, "setup.py"), "--check"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if chk.returncode != 0:
        print((chk.stderr or chk.stdout).strip() or "setup.py --check falhou", file=sys.stderr)
        sys.exit(2)

    saida = a.saida or tempfile.mkdtemp(prefix="video-vault-")
    os.makedirs(saida, exist_ok=True)
    resultados = []

    # enumerate sobre a lista: o número do vídeo é a posição, nunca uma chave de dicionário
    for n, url in enumerate(a.urls, start=1):
        pasta = os.path.join(saida, "%02d" % n)
        os.makedirs(pasta, exist_ok=True)
        # --engine local: sem isso, com GEMINI_API_KEY, o vídeo iria ao Google e não haveria frames.
        # --whisper whisperx: sem isso, com GROQ/OPENAI_API_KEY no ambiente ou num .env, o áudio iria à nuvem.
        cmd = [sys.executable, os.path.join(scripts, "watch.py"), url, "--engine", "local", "--whisper", "whisperx",
               "--cookies-from-browser", a.navegador, "--max-frames", str(a.max_frames),
               "--resolution", str(a.resolucao), "--out-dir", pasta]
        codigo, out, err, estourou = rodar(cmd, env, a.timeout)
        with open(os.path.join(pasta, "relatorio.md"), "w", encoding="utf-8") as f:
            f.write(out)
        with open(os.path.join(pasta, "erro.txt"), "w", encoding="utf-8") as f:
            f.write(err)

        # só conta pasta com frames de fato; se --saida for reaproveitada, fica a execução mais recente
        frames = [d for d in glob.glob(os.path.join(pasta, "**", "frames"), recursive=True)
                  if glob.glob(os.path.join(d, "frame_*.jpg"))]
        frames.sort(key=os.path.getmtime, reverse=True)
        item = {
            "n": n, "url": url, "url_canonica": url_canonica(pasta, url), "pasta": pasta,
            "relatorio": os.path.join(pasta, "relatorio.md"),
            "frames": frames[0] if frames else None,
            "autor": campo(out, "Uploader"), "titulo": campo(out, "Title"), "duracao": campo(out, "Duration"),
            # é o estado da transcrição ("N segments (via ...)", "failed", "no speech"...), não o texto dela
            "transcricao_status": campo(out, "Transcript"),
            "status": "ok", "erro": None,
        }
        if codigo != 0 or not frames:
            linhas = [l for l in err.splitlines() if "ERROR" in l or "failed" in l]
            item["erro"] = "timeout" if estourou else ((linhas[-1] if linhas else err.strip()[-300:]) or "sem detalhe")
            item["status"] = "sem_video" if any(m in err + out for m in SEM_VIDEO) else "falhou"
        resultados.append(item)
        # pausa só antes de outro link do Instagram, para ele não bloquear
        if n < len(a.urls) and "instagram.com" in a.urls[n]:
            time.sleep(a.pausa)

    texto = json.dumps({"saida": saida, "itens": resultados}, ensure_ascii=False, indent=2)
    with open(os.path.join(saida, "resultado.json"), "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)
    sys.exit(0 if any(i["status"] == "ok" for i in resultados) else 1)


if __name__ == "__main__":
    main()
