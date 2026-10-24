# -*- coding: utf-8 -*-
"""hmj_fuente_es.py - adapta la fuente del juego (anticcezannepro.otf) al español.
El motor recorta lo que baja de la linea base mas de 120 unidades: las colas de g, j, p, q, y, ¿ se cortan.
Esto reduce un poco (91 %) y sube las letras latinas para que todo quepa entre -120 y 880,
y cambia «…» (centrado, al estilo japones) por tres puntos sobre la linea base.
Trabaja sobre TU copia de la fuente (no se distribuye la fuente).
  python hmj_fuente_es.py original.otf salida.otf"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
ESC = 0.91; SUBE = 75

def latino(cp):
    return 0x20 < cp < 0x250 or cp in (0x2018, 0x2019, 0x201C, 0x201D, 0x2013, 0x2122)

def main(src, dst):
    f = TTFont(src)
    cmap = f.getBestCmap(); gs = f.getGlyphSet(); hmtx = f['hmtx'].metrics
    cff = f['CFF '].cff; top = cff[cff.fontNames[0]]; cs = top.CharStrings
    hechos = set()
    def rehacer(gname, dibujar, ancho):
        c = cs[gname]
        pen = T2CharStringPen(ancho, gs)
        dibujar(pen)
        nuevo = pen.getCharString(private=c.private, globalSubrs=c.globalSubrs)
        cs[gname] = nuevo if False else nuevo
        top.CharStrings.charStrings  # noqa
        idx = cs.charStrings[gname]
        if cs.charStringsAreIndexed: cs.charStringsIndex[idx] = nuevo
        else: cs.charStrings[gname] = nuevo
        hmtx[gname] = (ancho, hmtx[gname][1])
    # 1) letras latinas
    originales = {}
    for cp, g in cmap.items():
        if latino(cp) and g not in hechos:
            hechos.add(g); originales[g] = hmtx[g][0]
    for g in hechos:
        w = originales[g]; nw = int(round(w * ESC))
        def dib(pen, g=g):
            gs[g].draw(TransformPen(pen, (ESC, 0, 0, ESC, 0, SUBE)))
        rehacer(g, dib, nw)
    # 2) «…» -> tres puntos en la linea base (copiando el punto ya ajustado)
    gpunto = cmap[ord('.')]; gell = cmap[0x2026]
    gs = f.getGlyphSet()
    wp = hmtx[gpunto][0]
    def dib3(pen):
        for k in range(3): gs[gpunto].draw(TransformPen(pen, (1, 0, 0, 1, k * wp, 0)))
    rehacer(gell, dib3, 3 * wp)
    f.save(dst)
    # comprobacion
    g2 = TTFont(dst); gs2 = g2.getGlyphSet(); cm2 = g2.getBestCmap()
    peor = []
    for ch in 'gjpqy¿¡ÁÉÍÓÚÑ_|()[]{}…':
        b = BoundsPen(gs2); gs2[cm2[ord(ch)]].draw(b)
        if b.bounds: peor.append((ch, b.bounds[1], b.bounds[3]))
    print('limites (letra, abajo, arriba):', peor)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
