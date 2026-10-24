# -*- coding: utf-8 -*-
"""hmj_gen_title.py - subtitulos de los botones del titulo de Hachimyoujin en espanol.
El texto en ingles (START, CONFIG...) se queda; solo cambia el renglon pequeno japones de abajo.
  python hmj_gen_title.py CARPETA_ORIGINAL(data/screen/title) CARPETA_SALIDA(ui_es/data/screen/title) FUENTE.otf
Copia la carpeta COMPLETA y reescribe solo los .dzi/teselas de los botones."""
import sys, os, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kit'))
import hmj_dzi as z

SUB = {
 'newgame': 'Nueva partida', 'load': 'Continuar partida', 'prologue': 'Prólogo',
 'extra': 'Extras', 'config': 'Configuración', 'end': 'Salir del juego',
 'cg': 'Galería de CG', 'music': 'Galería de música', 'movie': 'Galería de videos',
 'scene': 'Galería de escenas', 'award': 'Premios',
}

def subtitulo(img, texto, fuente, hover):
    a = np.array(img); al = a[..., 3]
    rows = (al > 40).sum(1); runs = []; cur = None
    for y, v in enumerate(rows):
        if v and cur is None: cur = y
        if not v and cur is not None: runs.append((cur, y)); cur = None
    if cur is not None: runs.append((cur, len(rows)))
    assert len(runs) >= 2, runs
    y0, y1 = runs[-1]
    sel = a[y0:y1][al[y0:y1] > 200][:, :3]; col = tuple(int(v) for v in sel.mean(0))
    glow = (90, 230, 255) if hover else (120, 170, 255)
    a[y0 - 2:, :, 3] = 0                           # borra el renglon japones
    out = Image.fromarray(a); W, H = out.size
    t = '— %s —' % texto
    size = 15   # el juego reduce 1920->1024: 17 px aqui ~ 9 px en pantalla (como el japones)
    f = ImageFont.truetype(fuente, size)
    while f.getlength(t) > W - 4 and size > 8: size -= 1; f = ImageFont.truetype(fuente, size)
    cy = (y0 + y1) / 2
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((W / 2, cy), t, font=f, fill=255, anchor='mm')
    g = m.filter(ImageFilter.GaussianBlur(2 if hover else 1.4)).point(lambda v: min(255, int(v * (1.8 if hover else 1.2))))
    L = Image.new('RGBA', (W, H), glow + (0,)); L.putalpha(g); out.alpha_composite(L)
    T = Image.new('RGBA', (W, H), col + (0,)); T.putalpha(m); out.alpha_composite(T)
    size_usado[0] = size
    return out
size_usado = [0]

def main(src, dst, fuente):
    if os.path.isdir(dst): shutil.rmtree(dst)
    shutil.copytree(src, dst)
    for base, txt in SUB.items():
        for suf in ('_n', '_o'):
            nm = base + suf
            if not os.path.isfile(os.path.join(src, nm + '.dzi')): print('falta', nm); continue
            img = z.armar(src, nm); new = subtitulo(img, txt, fuente, suf == '_o')
            shutil.rmtree(os.path.join(dst, 'tex', nm), ignore_errors=True)
            # quitar variantes con otra capitalizacion
            for x in os.listdir(os.path.join(dst, 'tex')):
                if x.lower() == nm.lower(): shutil.rmtree(os.path.join(dst, 'tex', x))
            z.escribir(dst, nm, new, src); print('ok', nm, '->', txt, 'tam', size_usado[0])

if __name__ == '__main__': main(*sys.argv[1:4])
