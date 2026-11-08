#!/usr/bin/env python3
"""Junta os frames de uma pasta numa folha de contato (3 colunas), numerados.

Ler uma imagem por vídeo custa bem menos do que ler 12. Use a folha para ver os nomes e o texto
da tela; abra um frame sozinho quando o texto estiver pequeno demais.

Precisa do Pillow. Rode assim: uv run --no-project --with pillow python folha_contato.py PASTA_FRAMES SAIDA.jpg
"""
import glob
import os
import sys

if len(sys.argv) != 3:
    sys.exit("uso: folha_contato.py PASTA_FRAMES SAIDA.jpg")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402 (depois da checagem, para dar a mensagem de uso sem o Pillow)
pasta, saida = sys.argv[1], sys.argv[2]
frames = sorted(glob.glob(os.path.join(pasta, "frame_*.jpg")))
if not frames:
    sys.exit("nenhum frame em " + pasta)

L, colunas = 440, 3  # 440 px por frame mantém legível o texto da tela dos frames de 768 px
try:
    fonte = ImageFont.load_default(size=32)  # Pillow 10.1 ou mais novo
except TypeError:
    fonte = ImageFont.load_default()

imgs = []
for f in frames:
    with Image.open(f) as im:
        im = im.convert("RGB")
        imgs.append(im.resize((L, int(im.height * L / im.width))))
H = max(i.height for i in imgs)
linhas = (len(imgs) + colunas - 1) // colunas
folha = Image.new("RGB", (colunas * L, linhas * H), "black")
desenho = ImageDraw.Draw(folha)
for k, im in enumerate(imgs):
    x, y = (k % colunas) * L, (k // colunas) * H
    folha.paste(im, (x, y))
    rotulo = str(k + 1)
    caixa = desenho.textbbox((x + 6, y + 6), rotulo, font=fonte)
    desenho.rectangle((caixa[0] - 4, caixa[1] - 4, caixa[2] + 4, caixa[3] + 4), fill="black")
    desenho.text((x + 6, y + 6), rotulo, fill="yellow", font=fonte)
folha.save(saida, quality=85)
print(saida, folha.size, len(imgs))
