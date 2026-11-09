#!/usr/bin/env python3
"""Assiste a uma lista de links de vídeo com o plugin claude-video e deixa tudo pronto para virar nota.

Para cada link: busca os metadados (autor, título, duração, URL canônica) com o yt-dlp, sem baixar o
vídeo, e roda o watch.py do plugin com os cookies do navegador. Dois motores (--engine):
- gemini (padrão): o Gemini assiste ao vídeo e responde a uma pergunta fixa (nomes exatos do que
  aparece na tela e resumo com tempos), mais a do usuário (--pergunta). O vídeo vai ao Google: a URL,
  se for do YouTube; senão, o arquivo baixado, apagado de lá depois da resposta. Sem frames.
- local: frames e transcrição local WhisperX, nada sai da máquina (vídeo privado). Poucos frames,
  largura 768 para ler o texto da tela.
Só vídeos: se o post não tem vídeo (carrossel de imagens), o status fica "sem_video" e quem chamou decide.
No fim grava <saida>/resultado.json e imprime o mesmo JSON, com os links na ordem recebida.
Sai com código 1 se nenhum link deu certo e 2 se faltar ferramenta do plugin.

Uso: python assistir.py URL [URL ...] [--saida PASTA] [--engine gemini|local] [--pergunta TEXTO]
                        [--pausa 25] [--navegador firefox] [--max-frames 12] [--timeout 900]
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit, urlunsplit

SEM_VIDEO = ("No video formats found", "There is no video in this post")
RESPOSTA_GEMINI = "## Answer (from Gemini)"
PERGUNTA_PADRAO = (
    "Responda em português do Brasil. Primeiro, liste os nomes exatos, com a grafia que aparece na tela, "
    "de toda ferramenta, aplicativo, site, repositório (dono/nome), comando, preço e número citado; "
    "copie também o texto relevante que aparece na tela (legendas, títulos, código, READMEs). "
    "Depois, faça um resumo com o timestamp de cada ponto principal, separando o que é mostrado do que é dito. "
    "Se um nome só é falado e não aparece na tela, diga isso.")


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


def tempo(segundos):
    s = int(round(segundos))
    h, m, s = s // 3600, s // 60 % 60, s % 60
    return "%d:%02d:%02d" % (h, m, s) if h else "%d:%02d" % (m, s)


def metadados(url, navegador, executar=subprocess.run):
    """Autor, título, duração e URL canônica pelo yt-dlp, sem baixar o vídeo; {} se não der."""
    cmd = [shutil.which("yt-dlp") or "yt-dlp", "--dump-json", "--skip-download", "--no-playlist",
           "--cookies-from-browser", navegador, url]
    try:
        r = executar(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        info = json.loads(r.stdout) if r.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        info = None
    if not isinstance(info, dict):
        return {}
    m = {"autor": info.get("uploader") or info.get("channel") or info.get("uploader_id") or "",
         "titulo": info.get("title") or "",
         "duracao": tempo(info["duration"]) if isinstance(info.get("duration"), (int, float)) else ""}
    if info.get("webpage_url"):
        m["url_canonica"] = url_limpa(info["webpage_url"])
    return m


def pergunta_gemini(pergunta):
    pergunta = (pergunta or "").strip()
    return PERGUNTA_PADRAO + ("\n\nPergunta do usuário: " + pergunta if pergunta else "")


def comando_watch(scripts, url, a, pasta):
    cmd = [sys.executable, os.path.join(scripts, "watch.py"), url, "--engine", a.engine,
           "--cookies-from-browser", a.navegador, "--out-dir", pasta]
    if a.engine == "gemini":
        return cmd + ["--question", pergunta_gemini(a.pergunta)]
    # --whisper whisperx: sem isso, com GROQ/OPENAI_API_KEY no ambiente ou num .env, o áudio iria à nuvem.
    return cmd + ["--whisper", "whisperx", "--max-frames", str(a.max_frames), "--resolution", str(a.resolucao)]


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


def processar(n, url, a, scripts, env, pasta):
    os.makedirs(pasta, exist_ok=True)
    meta = metadados(url, a.navegador)
    codigo, out, err, estourou = rodar(comando_watch(scripts, url, a, pasta), env, a.timeout)
    with open(os.path.join(pasta, "relatorio.md"), "w", encoding="utf-8") as f:
        f.write(out)
    with open(os.path.join(pasta, "erro.txt"), "w", encoding="utf-8") as f:
        f.write(err)

    # só conta pasta com frames de fato; se --saida for reaproveitada, fica a execução mais recente
    frames = [d for d in glob.glob(os.path.join(pasta, "**", "frames"), recursive=True)
              if glob.glob(os.path.join(d, "frame_*.jpg"))]
    frames.sort(key=os.path.getmtime, reverse=True)
    item = {
        "n": n, "url": url, "url_canonica": meta.get("url_canonica") or url_canonica(pasta, url),
        "pasta": pasta, "engine": a.engine, "relatorio": os.path.join(pasta, "relatorio.md"),
        "frames": frames[0] if frames else None,
        # o relatório do motor local também traz esses campos; o do Gemini, não
        "autor": meta.get("autor") or campo(out, "Uploader"), "titulo": meta.get("titulo") or campo(out, "Title"),
        "duracao": meta.get("duracao") or campo(out, "Duration"),
        # é o estado da transcrição ("N segments (via ...)", "failed", "no speech"...), não o texto dela;
        # vazio no motor Gemini, que não transcreve
        "transcricao_status": campo(out, "Transcript"),
        "status": "ok", "erro": None,
    }
    ok = RESPOSTA_GEMINI in out if a.engine == "gemini" else bool(frames)
    if codigo != 0 or not ok:
        # o Gemini põe o erro no relatório, no primeiro item de "## Unavailable evidence", não no stderr
        gemini = re.search(r"^## Unavailable evidence\s+- (.+)$", out, re.M)
        linhas = [l for l in err.splitlines() if "ERROR" in l or "failed" in l]
        erro = gemini.group(1).strip() if gemini else (linhas[-1] if linhas else err.strip()[-300:])
        item["erro"] = "timeout" if estourou else (erro or "sem detalhe")
        item["status"] = "sem_video" if any(m in err + out for m in SEM_VIDEO) else "falhou"
    return item


def argumentos():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--engine", choices=["gemini", "local"], default="gemini",
                    help="gemini (padrão; o vídeo vai ao Google) ou local (vídeo privado: nada sai da máquina)")
    ap.add_argument("--pergunta", default=None, help="pergunta do usuário, somada à pergunta fixa do Gemini")
    ap.add_argument("--pausa", type=int, default=25, help="segundos entre links do Instagram")
    ap.add_argument("--navegador", default="firefox")
    ap.add_argument("--max-frames", type=int, default=12,
                    help="só no motor local: 12 para Reels; 40 a 60 para vídeos longos")
    ap.add_argument("--resolucao", type=int, default=768, help="só no motor local")
    ap.add_argument("--timeout", type=int, default=900, help="segundos por vídeo antes de desistir")
    return ap.parse_args()


def main():
    # sem isso, no Windows com Python <= 3.14 um emoji no título quebra o print final (cp1252)
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")

    a = argumentos()
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
        resultados.append(processar(n, url, a, scripts, env, os.path.join(saida, "%02d" % n)))
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
