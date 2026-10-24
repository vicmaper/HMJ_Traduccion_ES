# -*- coding: utf-8 -*-
"""hmj_gen_config.py - pantallas de configuracion de Hachimyoujin en espanol.
  python hmj_gen_config.py ORIGINAL(data/screen/config) SALIDA(ui_es/data/screen/config) FUENTE.otf
Ingles se queda (Game Setting, Screen Setting, Slow/Fast, Min/Max...)."""
import sys, os, re, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hmj_ui as U
from hmj_ui import z

PILL = (15, 52, 94)
# base -> (svg, pastilla, {indice_renglon: (tipo, texto)}, {imagen_boton: texto}, desplazamiento base)
PANTALLAS = {
 'game_base': ('game.svg', 'Juego', {
    (0, 119, 729, 44): ('head', 'Pantalla'), (0, 180, 139, 24): ('label', 'Modo de pantalla'),
    (18, 216, 253, 18): ('desc', 'Cambia el modo de visualización.'),
    (0, 354, 729, 44): ('head', 'Efectos'), (0, 414, 261, 25): ('label', 'Aparición de personajes'),
    (19, 451, 300, 18): ('desc', 'Elige cómo aparecen los personajes.'),
    (0, 550, 220, 25): ('label', 'Aparición de CG y fondos'), (21, 587, 300, 18): ('desc', 'Elige cómo aparecen las CG y los fondos.'),
    (2, 689, 355, 25): ('label', 'Animación de la ventana'), (20, 726, 357, 18): ('desc', 'Elige cómo aparece la ventana de mensajes.'),
    (737, 119, 735, 44): ('head', 'Detalles'), (748, 179, 213, 25): ('label', 'Corte de voz'),
    (768, 216, 331, 18): ('desc', 'Corta la voz al pasar al siguiente mensaje.'),
    (748, 318, 189, 25): ('label', 'Música durante las voces'), (767, 354, 275, 19): ('desc', 'Baja la música mientras suena una voz.'),
    (737, 504, 735, 44): ('head', 'Guardado'), (749, 565, 164, 24): ('label', 'Comentarios'),
    (767, 601, 348, 18): ('desc', 'Elige si se pide un comentario al guardar.'),
    (748, 703, 213, 25): ('label', 'Guardado automático'), (767, 740, 268, 18): ('desc', 'Activa o desactiva el guardado automático.'),
   }, {
    'screen_window': 'Ventana', 'screen_full': 'Pantalla completa',
    'cgeffect_normal': 'Normal', 'cgeffect_high': 'Instantánea',
    'mweffect_normal': 'Normal', 'mweffect_high': 'Instantánea',
    'voicecut_yes': 'Activado', 'voicecut_no': 'Desactivado',
    'fadebgm_no': 'Normal', 'fadebgm_yes': 'Bajar música',
    'savecomment_yes': 'Con comentario', 'savecomment_no': 'Sin comentario',
    'autosave_yes': 'Activado', 'autosave_no': 'Desactivado',
   }),

 'text_base': ('text.svg', 'Texto', {
    (0, 121, 220, 35): ('head', 'Mensajes'), (0, 179, 213, 25): ('label', 'Velocidad del texto'),
    (19, 216, 316, 18): ('desc', 'Ajusta la velocidad con que aparece el texto.'),
    (0, 299, 141, 25): ('label', 'Contorno de letras'), (21, 337, 284, 17): ('desc', 'Agrega un contorno al texto.'),
    (2, 450, 235, 25): ('label', 'Opacidad de la ventana'), (20, 487, 331, 18): ('desc', 'Ajusta la opacidad de la ventana de mensajes.'),
    (739, 121, 181, 35): ('head', 'Otros'), (748, 180, 213, 24): ('label', 'Modo automático'),
    (766, 216, 413, 18): ('desc', 'Ajusta la espera antes del siguiente mensaje.'),
    (748, 318, 213, 25): ('label', 'Texto con voz'), (767, 355, 380, 18): ('desc', 'Elige si se muestra el texto mientras suena la voz.'),
    (748, 459, 165, 25): ('label', 'Salto de texto'), (769, 496, 268, 18): ('desc', 'Elige qué texto se puede saltar.'),
    (748, 600, 165, 25): ('label', 'Velocidad de salto'), (769, 637, 332, 18): ('desc', 'Ajusta la velocidad al saltar texto.'),
    (747, 743, 190, 24): ('label', 'Mensajes leídos'), (768, 779, 253, 18): ('desc', 'Colorea los mensajes ya leídos.'),
   }, {
    'openface_yes': 'Con contorno', 'openface_no': 'Sin contorno',
    'autovoice_yes': 'Mostrar', 'autovoice_no': 'No mostrar',
    'skip_readonly': 'Solo lo leído', 'skip_all': 'Todo', 'skip_auto': 'Salto automático',
    'skspeed_normal': 'Normal', 'skspeed_high': 'Rápida',
    'readcolor_no': 'Sin color', 'readcolor_yes': 'Con color',
   }),
 'sound_base': ('sound.svg', 'Sonido', {
    (0, 125, 148, 35): ('head', 'Volumen'), (0, 183, 127, 25): ('label', 'Música'),
    (19, 218, 306, 20): ('desc', 'Ajusta el volumen de la música.'),
    (0, 333, 141, 25): ('label', 'Voces'), (19, 368, 316, 20): ('desc', 'Ajusta el volumen de las voces.'),
    (0, 483, 141, 25): ('label', 'Sonido ambiental'), (19, 518, 334, 20): ('desc', 'Ajusta el volumen del sonido ambiental.'),
    (747, 183, 142, 25): ('label', 'Efectos de sonido'), (767, 218, 334, 20): ('desc', 'Ajusta el volumen de los efectos de sonido.'),
    (748, 333, 237, 25): ('label', 'Sonidos del sistema'), (768, 368, 315, 20): ('desc', 'Ajusta el volumen de los sonidos del sistema.'),
    (749, 483, 164, 25): ('label', 'Videos'), (768, 519, 261, 19): ('desc', 'Ajusta el volumen de los videos.'),
   }, {}),
}
PANTALLAS['voice_base'] = ('voice.svg', 'Voces', {
    (0, 121, 316, 35): ('head', 'Voces de personajes'),
    (2, 181, 477, 18): ('desc', 'Activa, desactiva y ajusta el volumen de la voz de cada personaje.'),
   }, {})
PANTALLAS['shortcut_base'] = ('shortcut.svg', 'Lista de atajos', {
    (0, 125, 732, 26): ('label', 'Teclas de atajo para jugar con más comodidad'),
    (289, 197, 163, 25): ('desc2', 'Avanzar el texto'),
    (289, 247, 454, 25): ('desc2', 'Cancelar selección / mostrar menú'),
    (0, 247, 287, 32): ('key', '[Esc] [Backspace] [X] [0]'),
    (0, 297, 172, 26): ('key', '[Espacio] [H]'),
    (291, 297, 331, 25): ('desc2', 'Ocultar la ventana de mensajes'),
    (289, 347, 318, 25): ('desc2', 'Leer el historial (hacia atrás)'),
    (289, 397, 515, 25): ('desc2', 'Leer el historial (hacia adelante) / avanzar'),
    (289, 446, 510, 26): ('desc2', 'Mantener para saltar texto (solo lo leído)'),
    (289, 496, 486, 26): ('desc2', 'Mantener para saltar texto (también lo no leído)'),
    (290, 547, 186, 24): ('desc2', 'Repetir la voz'),
    (290, 596, 189, 25): ('desc2', 'Mostrar el historial'),
    (289, 646, 320, 26): ('desc2', 'Abrir o cerrar la pantalla de guardado'),
    (289, 696, 320, 26): ('desc2', 'Abrir o cerrar la pantalla de carga'),
    (291, 746, 283, 25): ('desc2', 'Abrir la configuración'),
    (289, 796, 191, 25): ('desc2', 'Cambiar ventana / pantalla completa'),
    (289, 846, 263, 25): ('desc2', 'Activar o desactivar el modo automático'),
    (290, 895, 450, 26): ('desc2', 'En modo automático: mostrar u ocultar'),
    (289, 945, 239, 25): ('desc2', 'el texto mientras suena la voz'),
    (290, 996, 333, 25): ('desc2', 'Volver al título / salir del recuerdo'),
    (982, 198, 211, 24): ('desc2', 'Minimizar la ventana'),
    (982, 247, 287, 25): ('desc2', 'Saltar hasta la siguiente opción'),
    (983, 297, 333, 26): ('desc2', 'Iniciar o detener el salto de texto'),
    (984, 347, 189, 25): ('desc2', 'Guardado rápido'),
    (910, 397, 476, 26): ('desc2x', 'Cargar el último guardado rápido'),
    (910, 446, 382, 26): ('desc2x', 'Mostrar la lista de atajos'),
   }, {})
# Nombres segun VNDB.
NOMBRES = {
 1: 'Hiiragi Yoshiya', 2: 'Sera Mizuki', 3: 'Manase Akira', 4: 'Tatsunobe Ayumi', 5: 'Gadou Rinko',
 6: 'Oosugi Harumitsu', 7: 'Narutaki Atsushi', 8: 'Hiiragi Eriko', 9: 'Manase Gouzou', 10: 'Ashizumi Hanae',
 11: 'Shinno Akikage', 12: 'Hiiragi Seijuurou', 13: 'Keira Georgievna Gurdjieva', 14: 'Dan Karuma',
 15: 'Nakiri Kuubou', 16: 'Tatsumiya Yurika', 17: 'Kurana Munefuyu', 18: 'Deigan', 19: 'Yasha',
 20: 'Ayakashi', 21: 'Amakasu Masahiko', 22: 'Itou Noe', 23: 'Hozumi Momo', 24: 'Sacerdote', 25: 'Otros',
}
KEY_FRAME = [  # (rect, renglones, tamano, color, alineado)
 ((11, 357, 453, 25), ['Asigna un atajo a cada tecla.'], 22, (95, 193, 212)),
 ((852, 395, 262, 104), ['Mantén pulsado el botón derecho', 'y mueve el ratón arriba, abajo,', 'a la izquierda o a la derecha', 'para usar los gestos.'], 17, (205, 212, 220)),
 ((0, 892, 823, 50), ['Puedes asignar atajos a las teclas 1–9, al botón derecho y a los gestos del ratón.',
                      'Arrastra cada icono hasta la posición que quieras.'], 18, (190, 196, 200)),
]

MENU = [
 ('tab_save', 'tab_save', 'Guardar'), ('tab_load', 'tab_load', 'Cargar'), ('tab_game', 'tab_game', 'Juego'),
 ('tab_text', 'tab_text', 'Texto'), ('tab_sound', 'tab_sound', 'Sonido'), ('tab_voice', 'tab_voice', 'Voces'),
 ('tab_key', 'tab_key', 'Atajos de teclado'), ('tab_shortcut', 'tab_shortcut', 'Lista de atajos'),
 ('returntitle_o', 'returntitle_o', 'Volver al título'), ('exitgame_o', 'exitgame_o', 'Salir del juego'),
 ('close_o', 'close_o', 'Cerrar'),
]

def main(src, dst, fuente, solo=None):
    U.FUENTE = fuente
    if not os.path.isdir(dst): shutil.copytree(src, dst)
    if not solo: U.menu_lateral(src, dst, 'config.svg', MENU, size=28)
    if not solo:
        kf = U.z.armar(src, 'keyconfig_frame')
        for rect, lin, sz, col in KEY_FRAME: U.texto_opaco(kf, rect, lin, sz, col, x=rect[0] + 2)
        U.pastilla(kf, (1324, 44, 180, 36), 'Atajos', 22)
        U.reemplazar_dzi(src, dst, 'keyconfig_frame', kf); print('keyconfig_frame')
    for base, (svgf, pill, lin, btn) in PANTALLAS.items():
        if solo and base != solo: continue
        svg = open(os.path.join(src, svgf), encoding='utf-8').read(); R = U.svg_imgs(svg)
        X0, Y0 = R[base][:2]
        img = U.z.armar(src, base); W = img.size[0]
        # rectangulos de botones dentro de la base (por id *_c)
        brect = {}
        for iid, (x, y, w, h) in R.items():
            if iid.endswith('_c'):
                brect[iid[:-2]] = (x - X0, y - Y0, w, h)
        for box, (kind, txt) in lin.items():
            xh = box[0] + 420 if kind == 'head' else None
            if kind in ('desc2', 'desc2x', 'key'):
                U.reemplazar_linea(img, box, txt, 'desc', size=22, x_desde=box[0] + 72 if kind == 'desc2x' else None,
                                   maxw=img.size[0] - box[0] - 80)
            else:
                U.reemplazar_linea(img, box, txt, kind, x_hasta=xh)
        # pastilla arriba a la derecha (texto azul oscuro)
        a = np.array(img); a[0:52, W - 200:W, 3] = np.where(a[0:52, W - 200:W, 3] > 0, 0, 0); img = Image.fromarray(a)
        U.escribir(img, W - 2, 34, pill, 22, PILL, None, anchor='rm')
        # botones dibujados en la base (estado normal)
        hechos = set()
        for iid, rect in brect.items():
            png = re.search(r"<image id='%s_c'[^>]*xlink:href='\./([^']*)\.png'" % iid, svg).group(1)
            if png in btn: U.boton(img, rect, btn[png], size=24); hechos.add(png)
        U.reemplazar_dzi(src, dst, base, img); print('base', base)
        if base == 'voice_base':
            for i, nom in NOMBRES.items():
                for suf, rect in (('', (0, 2, 241, 31)), ('_c', (0, 6, 254, 31)), ('_o', (0, 4, 246, 32)), ('_1', (0, 4, 246, 32))):
                    nm = 'chara%02d%s' % (i, suf)
                    if not os.path.isfile(os.path.join(src, nm + '.dzi')): continue
                    b = U.z.armar(src, nm); r = rect or (0, 0) + b.size
                    U.boton(b, r, nom, size=22, x_txt=16 if suf == '' else None, color=(150, 150, 150) if suf == '_1' else (245, 248, 255), umbral=18, zx=.97, total=(i == 13), zy=(.05, .97))
                    U.reemplazar_dzi(src, dst, nm, b)
            print('  nombres de voces')
        # imagenes de boton (estado elegido / encima)
        for png, txt in btn.items():
            b = U.z.armar(src, png); U.boton(b, (0, 0) + b.size, txt, size=24, glow=(40, 160, 200))
            U.reemplazar_dzi(src, dst, png, b); print('  boton', png, '->', txt)

if __name__ == '__main__': main(*sys.argv[1:5])
