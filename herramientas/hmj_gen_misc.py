# -*- coding: utf-8 -*-
"""hmj_gen_misc.py - Guardar/Cargar, historial y pantalla de Game Award de Hachimyoujin.
  python hmj_gen_misc.py SCREEN_ORIGINAL(data/screen) SCREEN_SALIDA(ui_es/data/screen) FUENTE.otf
(config debe existir ya en la salida: lo crea hmj_gen_config.py)"""
import sys, os, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hmj_ui as U

def main(src, dst, fuente):
    U.FUENTE = fuente
    cs, cd = os.path.join(src, 'config'), os.path.join(dst, 'config')
    FR = {'save_frame': ('Guarda tu partida.', 'Guardar', (19, 103, 244, 19), (1403, 23, 69, 23))}
    for f in ('load_frame', 'quicksave_frame', 'autosave_frame'):
        FR[f] = ('Carga una partida guardada.', 'Cargar', (19, 106, 262, 20), (1404, 28, 68, 22))
    for nm, (desc, pill, dbox, pbox) in FR.items():
        img = U.z.armar(cs, nm)
        U.reemplazar_linea(img, dbox, desc, 'desc')
        a = np.array(img); W = img.size[0]; a[0:55, W - 200:W, 3] = 0; img = Image.fromarray(a)
        U.escribir(img, W - 2, pbox[1] + pbox[3] / 2, pill, 22, (15, 52, 94), None, 'rm')
        U.reemplazar_dzi(cs, cd, nm, img); print('ok', nm)
    b = U.z.armar(cs, 'backlog_base'); U.pastilla(b, (1740, 44, 180, 36), 'Historial', 22)
    U.reemplazar_dzi(cs, cd, 'backlog_base', b); print('ok backlog_base')
    # Game Award (pagina de promocion)
    asrc, adst = os.path.join(src, 'award'), os.path.join(dst, 'award')
    if os.path.isdir(adst): shutil.rmtree(adst)
    shutil.copytree(asrc, adst)
    aw = U.z.armar(asrc, 'award_base')
    U.texto_opaco(aw, (896, 596, 1010, 90), '¡Moe Game Award 2014!', 58, (201, 225, 244), x=902, glow=(60, 110, 200))
    U.texto_opaco(aw, (898, 730, 980, 210), [
        '¡El Moe Game Award se renueva en 2014 y pasa a un sistema',
        'de votación sin código!',
        '¡La votación con el nuevo sistema empieza en abril! ¡Esperamos tu apoyo!',
        'Más detalles en la página oficial de abajo.'], 29, (230, 230, 230), x=904, salto=54)
    U.reemplazar_dzi(asrc, adst, 'award_base', aw); print('ok award_base')

if __name__ == '__main__': main(*sys.argv[1:4])
