# -*- coding: utf-8 -*-
"""hmj_gen_extra.py - pantalla EXTRA de Hachimyoujin en espanol.
Lo que esta en ingles (CG GALLERY, MUSIC APPRECIATION, Next/Prev...) y los nombres de canciones se quedan.
  python hmj_gen_extra.py ORIGINAL(data/screen/extra) SALIDA(ui_es/data/screen/extra) FUENTE.otf
- frame: borra el menu izquierdo japones (inpainting) y escribe el espanol.
- tab_*/close_o/exitgame_o/returntitle_o (resaltado): se dibujan de nuevo y se ajusta x/width en extra.svg.
- *_base: descripcion, etiqueta de la pastilla y porcentaje obtenido."""
import sys, os, re, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kit'))
import hmj_dzi as z

MENU = [  # id en svg, imagen de resaltado, texto
 ('tab_cg', 'tab_cg', 'Galería de CG'),
 ('tab_music', 'tab_music', 'Galería de música'),
 ('tab_scene', 'tab_scene', 'Galería de escenas'),
 ('tab_movie', 'tab_movie', 'Galería de videos'),
 ('returntitle_o', 'returntitle_o', 'Volver al título'),
 ('exitgame_o', 'exitgame_o', 'Salir del juego'),
 ('close_o', 'close_o', 'Cerrar'),
]
BASES = {  # pastilla, descripcion, etiqueta de recoleccion
 'cg_base': ('Galería CG', 'Aquí puedes ver las CG de los eventos que aparecieron en el juego.', 'CG obtenidas'),
 'music_base': ('Música', 'Aquí puedes escuchar la música que sonó en el juego.', None),
 'movie_base': ('Videos', 'Aquí puedes ver los videos que aparecieron en el juego.', 'Videos vistos'),
 'scene_base': ('Escenas', 'Aquí puedes elegir una escena del juego y volver a verla.', 'Escenas vistas'),
}
NORMAL = (182, 216, 234); HOVER = (178, 246, 253)
FS_MENU = 30

def F(fuente, s): return ImageFont.truetype(fuente, s)

def capa(size, xy, text, f, color, glow, glow_r, glow_k, anchor):
    W, H = size; out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text(xy, text, font=f, fill=255, anchor=anchor)
    if glow:
        g = m.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * glow_k)))
        L = Image.new('RGBA', (W, H), glow + (0,)); L.putalpha(g); out.alpha_composite(L)
    T = Image.new('RGBA', (W, H), color + (0,)); T.putalpha(m); out.alpha_composite(T)
    return out

def borrar_opaco(img, rect, pad=6):
    a = np.array(img.convert('RGBA')); x, y, w, h = rect
    rgb = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2BGR)
    box = np.zeros(a.shape[:2], np.uint8); box[y - pad:y + h + pad, x - pad:x + w + pad] = 255
    lum = a[..., :3].astype(int).mean(2); txt = (lum > 85).astype(np.uint8) * 255
    txt = cv2.dilate(txt, np.ones((7, 7), np.uint8)); mask = cv2.bitwise_and(box, txt)
    out = cv2.inpaint(rgb, mask, 6, cv2.INPAINT_TELEA)
    a[..., :3] = cv2.cvtColor(out, cv2.COLOR_BGR2RGB); return Image.fromarray(a)

def svg_rect(svg, iid):
    m = re.search(r"<image id='%s' x='(-?\d+)' y='(-?\d+)' width='(\d+)' height='(\d+)'" % iid, svg)
    return tuple(int(v) for v in m.groups())

def svg_set(svg, iid, x, w):
    return re.sub(r"(<image id='%s' )x='-?\d+'( y='-?\d+' )width='\d+'" % iid, r"\g<1>x='%d'\g<2>width='%d'" % (x, w), svg)

def caja(img, y0, y1, x0, x1):
    a = np.array(img)[y0:y1, x0:x1, 3]; ys, xs = np.where(a > 30)
    return x0 + xs.min(), y0 + ys.min(), x0 + xs.max(), y0 + ys.max()

def reemplazar_dzi(src, dst, nm, img):
    for x in os.listdir(os.path.join(dst, 'tex')):
        if x.lower() == nm.lower(): shutil.rmtree(os.path.join(dst, 'tex', x))
    z.escribir(dst, nm, img, src)

def reemplazar_dzi_tam(dst, nm, img):
    """imagen de otro tamano: escribe .dzi con 3 niveles"""
    for x in os.listdir(os.path.join(dst, 'tex')):
        if x.lower() == nm.lower(): shutil.rmtree(os.path.join(dst, 'tex', x))
    w, h = img.size; T = 256; out = ['DZI', '%d,%d' % (w, h), '3']
    for k in range(3):
        im = img if k == 0 else img.resize((max(1, w >> k), max(1, h >> k)), Image.LANCZOS)
        c = -(-im.size[0] // T); r = -(-im.size[1] // T); n = 0
        d = os.path.join(dst, 'tex', nm, str(k)); os.makedirs(d, exist_ok=True); out.append('%d,%d' % (c, r))
        for yy in range(r):
            fila = []
            for xx in range(c):
                t = Image.new('RGBA', (T, T), (0, 0, 0, 0)); t.paste(im.crop((xx * T, yy * T, min(im.size[0], (xx + 1) * T), min(im.size[1], (yy + 1) * T))), (0, 0))
                t.save(os.path.join(d, '%02d.png' % n)); fila.append('%s\\%d\\%02d' % (nm, k, n)); n += 1
            out.append(','.join(fila))
    open(os.path.join(dst, nm + '.dzi'), 'w', encoding='utf-8', newline='\r\n').write('\n'.join(out) + '\n')

def main(src, dst, fuente):
    if os.path.isdir(dst): shutil.rmtree(dst)
    shutil.copytree(src, dst)
    svgp = os.path.join(dst, 'extra.svg'); svg = open(svgp, encoding='utf-8').read()
    frame = z.armar(src, 'frame'); fm = F(fuente, FS_MENU)
    for iid, img, txt in MENU:
        key = iid + '_c' if iid.startswith('tab_') else iid
        x, y, w, h = svg_rect(svg, key)
        frame = borrar_opaco(frame, (x, y, w, h))
        cx = x + w / 2; cy = y + h / 2
        frame.alpha_composite(capa(frame.size, (cx, cy), txt, fm, NORMAL, (60, 130, 210), 2, 1.0, 'mm'))
        tw = int(fm.getlength(txt)) + 20; nx = int(round(cx - tw / 2))
        hi = capa((tw, h), (tw / 2, h / 2), txt, fm, HOVER, (60, 220, 240), 3, 1.9, 'mm')
        reemplazar_dzi_tam(dst, img, hi)
        for suf in (('_c', '_o') if iid.startswith('tab_') else ('',)):
            svg = svg_set(svg, iid + suf, nx, tw)
        print('menu', txt, 'x', nx, 'w', tw)
    reemplazar_dzi(src, dst, 'frame', frame)
    open(svgp, 'w', encoding='utf-8', newline='').write(svg)
    for nm, (pill, desc, rec) in BASES.items():
        b = z.armar(src, nm); a = np.array(b); W = b.size[0]
        # pastilla (texto azul oscuro a la derecha, arriba)
        x0, y0, x1, y1 = caja(b, 0, 50, 1300, W)
        a[0:50, 1300:W, 3] = 0
        b = Image.fromarray(a); fp = F(fuente, 22)
        b.alpha_composite(capa(b.size, (x1, (y0 + y1) / 2), pill, fp, (15, 52, 94), None, 0, 0, 'rm'))
        # descripcion
        a = np.array(b); dx0, dy0, dx1, dy1 = caja(b, 118, 158, 0, 900); a[dy0 - 2:dy1 + 3, 0:900, 3] = 0; b = Image.fromarray(a)
        fd = F(fuente, 24)
        b.alpha_composite(capa(b.size, (dx0, (dy0 + dy1) / 2), desc, fd, (108, 213, 228), (20, 80, 120), 1.5, 0.8, 'lm'))
        if rec:
            a = np.array(b); a[118:157, 1176:1400, 3] = 0; b = Image.fromarray(a)
            fr = F(fuente, 24)
            b.alpha_composite(capa(b.size, (1181, (dy0 + dy1) / 2), rec, fr, (133, 182, 205), None, 0, 0, 'lm'))
        reemplazar_dzi(src, dst, nm, b); print('base', nm)

if __name__ == '__main__': main(*sys.argv[1:4])
