# -*- coding: utf-8 -*-
"""hmj_wrap.py - saltos de renglon por ANCHO EN PIXELES para Hachimyoujin (fuente proporcional).
Medido en el juego (prueba 1): la fuente es data/font/anticcezannepro.otf a 20 px; caben 35 caracteres
japoneses (700 px) por renglon y 16 renglones por pagina. El motor corta a mitad de palabra, asi que
ponemos {n} entre palabras antes de llegar al limite. Limite conservador: 700 px (el real esta entre 713 y 719).
Una pagina = un mensaje; los parrafos se separan con {u000A} (salto real) y el texto se acumula hasta el final
del mensaje, asi que se cuentan TODOS los renglones del mensaje.
  python hmj_wrap.py "texto"            -> muestra el texto con {n} y cuantos renglones ocupa
"""
import os, re, sys
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
AQUI = os.path.dirname(os.path.abspath(__file__))
ANCHO_PX = 700; TAM = 20; RENGLONES = 16
_W = None
def _cargar():
    global _W
    if _W is not None: return
    j = os.path.join(AQUI, 'anchos_fuente.json')   # tabla de anchos ya medida (solo numeros, sin la fuente)
    if os.path.isfile(j):
        import json
        _W = {int(k): v for k, v in json.load(open(j)).items()}; return
    from fontTools.ttLib import TTFont
    for p in (os.path.join(AQUI, 'anticcezannepro.otf'),
              os.path.join(AQUI, '..', '..', '..', 'work', 'extraido', 'data', 'font', 'anticcezannepro.otf')):
        if os.path.isfile(p): break
    else: raise SystemExit('ERROR: falta anticcezannepro.otf (copiala junto a hmj_wrap.py)')
    f = TTFont(p); cmap = f.getBestCmap(); hm = f['hmtx']
    _W = {cp: hm[g][0] for cp, g in cmap.items()}
def px(s):
    _cargar(); return sum(round(_W.get(ord(c), 1000) * TAM / 1000) for c in s)
TAG = re.compile(r'\{[^}]*\}')
def vis(tok):
    tok = re.sub(r'\{r:([^}|]*)\|[^}]*\}', r'\1', tok)
    return px(TAG.sub('', tok))

def wrap(t, ancho=ANCHO_PX):
    """Devuelve (texto_con_{n}, renglones_totales). Respeta {n} y {u000A} ya puestos."""
    t = re.sub(r'\{n\}', '\0N', t); t = t.replace('{u000A}', '\0P')
    out = []; lines = 1; col = 0; line = ''
    toks = re.findall(r'\0N|\0P|\{[^}]*\}|[^\s{\0]+|\s+', t)
    def flush(sep):
        nonlocal line, col, lines
        out.append(line.rstrip(' ') + sep); line = ''; col = 0; lines += 1
    for tok in toks:
        if tok == '\0N': flush('{n}'); continue
        if tok == '\0P': flush('{u000A}'); continue
        if tok.startswith('{') and not tok.startswith('{r:'):
            line += tok; continue
        if tok.isspace():
            if col: line += ' '; col += px(' ')
            continue
        L = vis(tok)
        if col and col + L > ancho:
            flush('{n}')
        # palabra mas larga que el renglon: se deja (el motor la corta)
        line += tok; col += L
    out.append(line)
    res = ''.join(out)
    # un {u000A} final no agrega renglon visible
    if res.endswith('{u000A}') or re.search(r'\{u000A\}(\{[^}]*\})*$', res): lines -= 1
    return res, lines

if __name__ == '__main__':
    r, n = wrap(' '.join(sys.argv[1:]))
    print(r); print('renglones:', n, '(max %d)' % RENGLONES)
