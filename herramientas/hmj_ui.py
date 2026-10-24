# -*- coding: utf-8 -*-
"""hmj_ui.py - utilidades para reescribir textos de interfaz de Hachimyoujin (imagenes DZI + SVG).
Detecta renglones de texto en una imagen base (fondo transparente), los borra y escribe el espanol
con la fuente del juego. Los botones (fondo opaco) se borran con inpainting."""
import os, re, sys, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kit'))
import hmj_dzi as z
FUENTE = None
def F(s): return ImageFont.truetype(FUENTE, int(round(s)))

def svg_imgs(svg):
    return {m[0]: tuple(int(v) for v in m[1:5]) for m in
            re.findall(r"<image id='([^']*)' x='(-?\d+)' y='(-?\d+)' width='(\d+)' height='(\d+)'", svg)}

def txtmask(a, thr=40):
    lum = (a[..., :3].astype(int).mean(2) * a[..., 3] / 255).astype(int)
    bg = cv2.medianBlur(np.clip(lum, 0, 255).astype(np.uint8), 41).astype(int)
    return (lum - bg > thr) & (a[..., 3] > 60)

def lineas(img, excl=()):
    a = np.array(img.convert('RGBA')); t = txtmask(a)
    for x, y, w, h in excl: t[max(0, y):y + h, max(0, x):x + w] = False
    m = cv2.dilate(t.astype(np.uint8) * 255, np.ones((3, 25), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    B = [tuple(int(v) for v in st[i][:4]) for i in range(1, n) if st[i][3] >= 8 and st[i][2] >= 14]
    B.sort(key=lambda b: (b[0] > a.shape[1] // 2, b[1]))
    return B

def glifos(a, box, x_hasta=None):
    """bbox de los pixeles de texto dentro de box, sin las lineas horizontales largas"""
    x, y, w, h = box; t = txtmask(a)[y:y + h, x:x + w].copy()
    if x_hasta: t[:, x_hasta - x:] = False
    rows = t.sum(1); t[rows > 0.6 * w] = False            # quita subrayados
    ys, xs = np.where(t)
    if not len(xs): return None
    col = a[y:y + h, x:x + w][t][:, :3].mean(0).astype(int)
    return x + xs.min(), y + ys.min(), x + xs.max() + 1, y + ys.max() + 1, tuple(int(c) for c in col)

def escribir(img, x, cy, text, size, color, glow=None, anchor='lm', glow_r=1.6, glow_k=1.0, maxw=None):
    f = F(size)
    while maxw and f.getlength(text) > maxw and size > 10: size -= 1; f = F(size)
    W, H = img.size
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((x, cy), text, font=f, fill=255, anchor=anchor)
    if glow:
        g = m.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * glow_k)))
        L = Image.new('RGBA', (W, H), glow + (0,)); L.putalpha(g); img.alpha_composite(L)
    T = Image.new('RGBA', (W, H), color + (0,)); T.putalpha(m); img.alpha_composite(T)
    return size

def reemplazar_linea(img, box, text, kind='label', x_hasta=None, size=None, color=None, maxw=None, x_desde=None):
    """borra solo los pixeles de texto del renglon (no las lineas del marco) y escribe el texto.
    kind: head (deja el icono de la izquierda) / label / desc"""
    a = np.array(img.convert('RGBA')); x, y, w, h = box
    t = txtmask(a)[y:y + h, x:x + w].copy()
    if kind == 'head': t[:, :40] = False
    if x_hasta: t[:, x_hasta - x:] = False
    if x_desde: t[:, :x_desde - x] = False
    rows = t.sum(1); t[rows > 0.5 * w] = False
    ys, xs = np.where(t); assert len(xs), ('sin texto', box, text)
    col = tuple(int(c) for c in a[y:y + h, x:x + w][t][:, :3].mean(0))
    x0, y0, x1, y1 = x + xs.min(), y + ys.min(), x + xs.max() + 1, y + ys.max() + 1
    m = cv2.dilate(t.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    sub = a[y:y + h, x:x + w]; sub[..., 3] = np.where(m, 0, sub[..., 3]); a[y:y + h, x:x + w] = sub
    out = Image.fromarray(a)
    sz = size or {'head': 32, 'label': 27, 'desc': 19}[kind]
    c = color or col
    glow = (int(c[0] * .5), int(c[1] * .6), int(c[2] * .7)) if kind != 'desc' else None
    escribir(out, x0, (y0 + y1) / 2, text, sz, c, glow, maxw=maxw)
    img.paste(out)
    return out

def boton(img, rect, text, size=24, color=None, x_txt=None, glow=None, umbral=28, zx=.90, zy=(.15, .88), total=False):
    """borra el texto de un boton opaco (inpainting) y escribe el nuevo, alineado a la izquierda"""
    x, y, w, h = rect
    w = min(w, img.size[0] - x); h = min(h, img.size[1] - y)
    a = np.array(img.convert('RGBA')); sub = a[y:y + h, x:x + w]
    lum = sub[..., :3].astype(int).mean(2); g = sub[..., 1].astype(int) - sub[..., 0].astype(int)
    zona = np.zeros(lum.shape, bool); zona[int(h * zy[0]):int(h * zy[1]), 8:int(w * zx)] = True
    med = np.median(lum[zona]); t = ((lum > med + umbral) | (g > np.median(g[zona]) + 40)) & zona
    cols = np.where(t.sum(0) >= 2)[0]; rows = np.where(t.sum(1) >= 3)[0]
    xs = cols; ys = rows
    col = color or (tuple(int(v) for v in sub[t][:, :3].mean(0)) if len(xs) else (240, 245, 255))
    tx = x + (xs.min() if len(xs) else 14) if x_txt is None else x + x_txt
    mask = cv2.dilate(t.astype(np.uint8) * 255, np.ones((9, 9), np.uint8))
    # el brillo del boton cambia de arriba a abajo y casi nada de lado: cada pixel borrado toma
    # el color mediano de su renglon (sin texto)
    mk = mask > 0
    if total: mk = zona.copy()
    for yy in range(h):
        lim = int(w * zx); fila = sub[yy, 8:lim, :3]; libre = ~mk[yy, 8:lim]
        if total and mk[yy].any():
            sub[yy, :, :3][mk[yy]] = np.median(fila, axis=0).astype(np.uint8)
        elif mk[yy].any() and libre.sum() > 5:
            sub[yy, :, :3][mk[yy]] = np.median(fila[libre], axis=0).astype(np.uint8)
    a[y:y + h, x:x + w] = sub; out = Image.fromarray(a)
    cy = y + (ys.min() + ys.max()) / 2 if len(ys) else y + h / 2 - 1
    escribir(out, tx, cy, text, size, col, glow, maxw=x + w * 0.86 - tx)
    img.paste(out)

def reemplazar_dzi(src, dst, nm, img, mismo_tam=True):
    for x in os.listdir(os.path.join(dst, 'tex')):
        if x.lower() == nm.lower(): shutil.rmtree(os.path.join(dst, 'tex', x))
    if mismo_tam: z.escribir(dst, nm, img, src); return
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

NORMAL = (182, 216, 234); HOVER = (178, 246, 253)
def borrar_opaco(img, rect, pad=6):
    a = np.array(img.convert('RGBA')); x, y, w, h = rect
    rgb = cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2BGR)
    box = np.zeros(a.shape[:2], np.uint8); box[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 255
    lum = a[..., :3].astype(int).mean(2); txt = (lum > 85).astype(np.uint8) * 255
    txt = cv2.dilate(txt, np.ones((7, 7), np.uint8)); mask = cv2.bitwise_and(box, txt)
    out = cv2.inpaint(rgb, mask, 6, cv2.INPAINT_TELEA)
    a[..., :3] = cv2.cvtColor(out, cv2.COLOR_BGR2RGB); return Image.fromarray(a)

def menu_lateral(src, dst, svgf, menu, size=30):
    """menu de la izquierda pintado en frame + imagenes de resaltado; ajusta x/width en el svg.
    menu = [(id_svg_sin_sufijo, imagen, texto)]; los ids tab_* tienen _c y _o."""
    svgp = os.path.join(dst, svgf); svg = open(svgp, encoding='utf-8').read(); R = svg_imgs(svg)
    frame = z.armar(src, 'frame'); fm = F(size)
    for iid, img, txt in menu:
        key = iid + '_c' if (iid + '_c') in R else iid
        x, y, w, h = R[key]
        frame = borrar_opaco(frame, (x, y, w, h))
        cx = x + w / 2; cy = y + h / 2
        escribir(frame, cx, cy, txt, size, NORMAL, (60, 130, 210), 'mm', 2, 1.0)
        tw = int(fm.getlength(txt)) + 20; nx = int(round(cx - tw / 2))
        hi = Image.new('RGBA', (tw, h), (0, 0, 0, 0))
        escribir(hi, tw / 2, h / 2, txt, size, HOVER, (60, 220, 240), 'mm', 3, 1.9)
        reemplazar_dzi(src, dst, img, hi, mismo_tam=False)
        for suf in (('_c', '_o') if (iid + '_c') in R else ('',)):
            svg = re.sub(r"(<image id='%s' )x='-?\d+'( y='-?\d+' )width='\d+'" % (iid + suf),
                         r"\g<1>x='%d'\g<2>width='%d'" % (nx, tw), svg)
        print('menu', txt)
    reemplazar_dzi(src, dst, 'frame', frame)
    open(svgp, 'w', encoding='utf-8', newline='').write(svg)


def texto_opaco(img, rect, lineas, size, color, x=None, cy=None, salto=None, glow=None, anchor='lm'):
    """borra con inpainting el texto claro de rect (fondo opaco oscuro) y escribe 1 o mas renglones"""
    out = borrar_opaco(img, rect, pad=3)
    rx, ry, rw, rh = rect
    if isinstance(lineas, str): lineas = [lineas]
    salto = salto or size * 1.3
    y = cy if cy is not None else ry + rh / 2 - salto * (len(lineas) - 1) / 2
    for L in lineas:
        escribir(out, rx if x is None else x, y, L, size, color, glow, anchor); y += salto
    img.paste(out)

def pastilla(img, rect, text, size=22, color=(15, 52, 94)):
    """pastilla clara con texto oscuro: rellena cada renglon con su color mediano y escribe a la derecha"""
    a = np.array(img.convert('RGBA')); x, y, w, h = rect; sub = a[y:y + h, x:x + w]
    lum = sub[..., :3].astype(int).mean(2); med = np.median(lum); t = lum < med - 40
    mk = cv2.dilate(t.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    for yy in range(h):
        libre = ~mk[yy]
        if mk[yy].any() and libre.sum() > 5: sub[yy, :, :3][mk[yy]] = np.median(sub[yy, libre, :3], axis=0).astype(np.uint8)
    a[y:y + h, x:x + w] = sub; out = Image.fromarray(a)
    escribir(out, x + w - 14, y + h / 2, text, size, color, None, 'rm'); img.paste(out)
