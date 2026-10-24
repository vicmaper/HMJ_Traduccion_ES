# -*- coding: utf-8 -*-
"""hmj_dzi.py - imagenes DZI de MALIE (Hachimyoujin): cabecera 'DZI', ancho,alto, niveles, y por nivel
'cols,rows' + lista de teselas 'nombre\\nivel\\NN' (png 256x256 en tex/nombre/nivel/NN.png).
Nivel 0 = tamano completo, cada nivel siguiente = mitad.
  armar(carpeta, nombre) -> PIL.Image (nivel 0 completo)
  escribir(carpeta_salida, nombre, img, plantilla_dzi) -> escribe .dzi + teselas de todos los niveles"""
import os
from PIL import Image
T = 256
def leer(carpeta, nombre):
    L = [x.strip() for x in open(os.path.join(carpeta, nombre + '.dzi'), encoding='utf-8').read().split('\n')]
    assert L[0].strip() == 'DZI'
    w, h = map(int, L[1].split(',')); n = int(L[2]); lv = []; i = 3
    for k in range(n):
        c, r = map(int, L[i].split(',')); i += 1; tiles = []
        for _ in range(r): tiles.append(L[i].split(',')); i += 1
        lv.append((c, r, tiles))
    return w, h, lv
def _ruta(carpeta, nm):
    p = os.path.join(carpeta, 'tex', *nm.replace('\\', '/').split('/')) + '.png'
    if os.path.isfile(p): return p
    # Windows no distingue mayusculas: buscar sin distinguir
    cur = os.path.join(carpeta, 'tex')
    for part in nm.replace('\\', '/').split('/')[:-1] + [nm.replace('\\', '/').split('/')[-1] + '.png']:
        m = [x for x in os.listdir(cur) if x.lower() == part.lower()]
        assert m, p
        cur = os.path.join(cur, m[0])
    return cur
def armar(carpeta, nombre, nivel=0):
    w, h, lv = leer(carpeta, nombre); c, r, tiles = lv[nivel]
    img = Image.new('RGBA', (c * T, r * T), (0, 0, 0, 0))
    for y in range(r):
        for x in range(c):
            nm = tiles[y][x] if x < len(tiles[y]) else ''
            if not nm: continue                          # tesela vacia (transparente)
            img.paste(Image.open(_ruta(carpeta, nm)).convert('RGBA'), (x * T, y * T))
    return img.crop((0, 0, max(1, w >> nivel), max(1, h >> nivel)))
def escribir(salida, nombre, img, carpeta_original):
    """mismo tamano y misma cantidad de niveles que el original"""
    w, h, lv = leer(carpeta_original, nombre)
    assert img.size == (w, h), (nombre, img.size, (w, h))
    out = ['DZI', '%d,%d' % (w, h), str(len(lv))]
    for k in range(len(lv)):
        im = img if k == 0 else img.resize((max(1, w >> k), max(1, h >> k)), Image.LANCZOS)
        c = -(-im.size[0] // T); r = -(-im.size[1] // T); n = 0
        assert (c, r) == lv[k][:2], (nombre, k, (c, r), lv[k][:2])
        d = os.path.join(salida, 'tex', nombre, str(k)); os.makedirs(d, exist_ok=True)
        out.append('%d,%d' % (c, r))
        for y in range(r):
            fila = []
            for x in range(c):
                t = Image.new('RGBA', (T, T), (0, 0, 0, 0))
                t.paste(im.crop((x * T, y * T, min(im.size[0], (x + 1) * T), min(im.size[1], (y + 1) * T))), (0, 0))
                t.save(os.path.join(d, '%02d.png' % n)); fila.append('%s\\%d\\%02d' % (nombre, k, n)); n += 1
            out.append(','.join(fila))
    open(os.path.join(salida, nombre + '.dzi'), 'w', encoding='utf-8', newline='\r\n').write('\n'.join(out) + '\n')
