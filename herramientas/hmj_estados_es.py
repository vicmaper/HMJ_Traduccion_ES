# -*- coding: utf-8 -*-
"""hmj_estados_es.py - cambia los 10 subtitulos en kanji de los videos de estado (mv_*sta.webm)
por abreviaturas en español, siguiendo el zoom de la camara cuadro por cuadro.
  python hmj_estados_es.py entrada.webm salida.webm fuente.otf"""
import sys, os, subprocess, tempfile, glob
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def buscar_ffmpeg():
    import shutil
    f = shutil.which('ffmpeg')
    if f: return f
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit('ERROR: falta ffmpeg (pip install imageio-ffmpeg)')
FFMPEG = None
_NW = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if os.name == 'nt': _NW['creationflags'] = 0x08000000   # sin ventana negra en Windows
ETIQ = [  # (x0, y0, x1, y1) en coordenadas del ultimo cuadro, texto
    ((12, 168, 48, 189), 'FUE'), ((12, 217, 48, 238), 'RAP'),
    ((12, 304, 48, 325), 'DUR'), ((12, 353, 48, 373), 'REG'),
    ((12, 441, 48, 461), 'DIS'), ((12, 489, 48, 509), 'DSP'),
    ((703, 168, 740, 189), 'RUP'), ((703, 217, 740, 238), 'TRA'),
    ((703, 304, 740, 325), 'FOR'), ((703, 353, 740, 373), 'ENT')]

def main(src, dst, fuente):
    global FFMPEG
    FFMPEG = FFMPEG or buscar_ffmpeg()
    tmp = tempfile.mkdtemp()
    subprocess.check_call([FFMPEG, '-v', 'error', '-i', src, os.path.join(tmp, 'f_%04d.png')], **_NW)
    fs = sorted(glob.glob(os.path.join(tmp, 'f_*.png'))); N = len(fs)
    ref = cv2.imread(fs[-1]); H, Wd = ref.shape[:2]
    gref = cv2.GaussianBlur(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32), (5, 5), 0)
    # 1) zoom de la camara: W[k] lleva coordenadas del ultimo cuadro -> cuadro k
    Ws = [None] * N; ccs = [0] * N
    W = np.eye(2, 3, dtype=np.float32)
    for k in range(N - 1, -1, -1):
        g = cv2.GaussianBlur(cv2.imread(fs[k], 0).astype(np.float32), (5, 5), 0)
        try:
            cc, W2 = cv2.findTransformECC(gref, g, W.copy(), cv2.MOTION_AFFINE,
                                          (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6), None, 5)
            if cc > 0.15: W = W2
        except cv2.error: cc = 0
        Ws[k] = W.copy(); ccs[k] = cc
    # 2) mascara del kanji y color en el ultimo cuadro
    hsv_g = ref[:, :, 1].astype(int) - np.maximum(ref[:, :, 0], ref[:, :, 2]).astype(int)
    font = ImageFont.truetype(fuente, 16)
    capas = []
    for (x0, y0, x1, y1), txt in ETIQ:
        caja = hsv_g[y0:y1, x0:x1]; m = caja > 50
        col = ref[y0:y1, x0:x1][m].mean(0) if m.any() else np.array([43, 160, 20])
        base_f = np.where(m, caja, 0).sum() + 1e-6
        dil = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        img = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        bb = d.textbbox((0, 0), txt, font=font); tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pos = ((x1 - x0 - tw) // 2 - bb[0], (y1 - y0 - th) // 2 - bb[1])
        c = tuple(int(v) for v in col[::-1])
        glow = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).text(pos, txt, font=font, fill=c + (150,))
        glow = glow.filter(ImageFilter.GaussianBlur(1.5))
        img = Image.alpha_composite(glow, img); ImageDraw.Draw(img).text(pos, txt, font=font, fill=c + (255,))
        a = np.array(img).astype(np.float32)
        capas.append(((x0, y0, x1, y1), m, dil, base_f, a[:, :, 2::-1], a[:, :, 3] / 255.0))
    # 3) cada cuadro: se borra el kanji (inpaint sobre el mismo cuadro) y se pone el español con la misma aparicion
    for k in range(N):
        if ccs[k] < 0.15: continue
        fr8 = cv2.imread(fs[k]); fr = fr8.astype(np.float32); Winv = cv2.invertAffineTransform(Ws[k])
        al = cv2.warpAffine(fr8, Winv, (Wd, H))
        gk = al[:, :, 1].astype(np.float32) - np.maximum(al[:, :, 0], al[:, :, 2]).astype(np.float32)
        lienzo = al.astype(np.float32).copy(); alfa = np.zeros((H, Wd), np.float32); hay = False
        for (x0, y0, x1, y1), m, dil, base_f, rgb, a in capas:
            v = np.clip(gk[y0:y1, x0:x1] - 45, 0, None)
            p = float(np.clip(np.where(m, v, 0).sum() / (np.where(m, np.clip(hsv_g[y0:y1, x0:x1] - 45, 0, None), 0).sum() + 1e-6), 0, 1))
            if p < 0.04: continue
            hay = True
            sub = al[y0:y1, x0:x1].copy()
            limpio = cv2.inpaint(sub, dil.astype(np.uint8), 3, cv2.INPAINT_TELEA).astype(np.float32)
            parche = limpio * (1 - a[:, :, None] * p) + rgb * (a[:, :, None] * p)
            zona = np.maximum(dil.astype(np.float32), (a > 0.02).astype(np.float32))
            lienzo[y0:y1, x0:x1] = parche; alfa[y0:y1, x0:x1] = np.maximum(alfa[y0:y1, x0:x1], zona)
        if not hay: continue
        lw = cv2.warpAffine(lienzo, Ws[k], (Wd, H)); aw = cv2.warpAffine(alfa, Ws[k], (Wd, H))[:, :, None]
        out = fr * (1 - aw) + lw * aw
        cv2.imwrite(fs[k], np.clip(out, 0, 255).astype(np.uint8))
    subprocess.check_call([FFMPEG, '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'f_%04d.png'),
                           '-i', src, '-map', '0:v', '-map', '1:a?', '-c:v', 'libvpx', '-b:v', '2500k', '-crf', '8',
                           '-auto-alt-ref', '0', '-pix_fmt', 'yuv420p', '-c:a', 'copy', dst], **_NW)
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print('OK', dst)

if __name__ == '__main__':
    main(*sys.argv[1:4])
