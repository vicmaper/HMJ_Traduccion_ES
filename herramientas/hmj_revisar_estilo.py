# -*- coding: utf-8 -*-
"""hmj_revisar_estilo.py - revisa formato y estilo de la traduccion de Hachimyoujin.
No lleva texto del juego: compara con el japones de TU copia (columna 'japanese' del CSV que
genera el kit al extraer tu juego).

Uso:
  python hmj_revisar_estilo.py script_es.csv              -> solo revisa, escribe reporte_estilo.tsv
  python hmj_revisar_estilo.py script_es.csv --corregir   -> ademas guarda script_es_corregido.csv
                                                             con los arreglos seguros (respaldo aparte)
Revisa (ERROR = el juego puede fallar o verse mal; AVISO = estilo):
  ERROR  marcas {v:..}{/v}{end}{u000A}{uXXXX} distintas al japones, llaves rotas, japones sin traducir,
         tabulador o salto real, mas de 16 renglones (si encuentra la fuente anticcezannepro.otf)
  AVISO  ¿? y ¡! sin pareja, «...», «……» dentro de una frase (se usa «…»; «……» solo en silencios),
         falta espacio entre partes unidas por {end}, espacios dobles o antes de signo,
         honorificos (-san, -kun...), formas de España, mexicanismos fuertes, nombres (reglas_estilo_hmj.tsv)
Arreglos seguros de --corregir: «...»->«…», «……»->«…» fuera de silencios, espacio tras {end} cuando
el texto sigue en el mismo renglon, ¡/¿ o !/? que faltan en casos claros, espacios dobles.
"""
import csv, os, re, sys, shutil, time
AQUI = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
csv.field_size_limit(10**8)
TAG = re.compile(r'\{[^}]*\}')
MARCAS = re.compile(r'\{v:[^}]*\}|\{/v\}|\{end\}|\{u000A\}|\{u0006\}.|\{u000[0-9A-F]\}')
MARCA_OK = re.compile(r'\{(?:n|end|/v|v:[^}]*|u[0-9A-Fa-f]{4})\}')
JP = re.compile(r'[ぁ-んァ-ヶ一-龯、。！？っ]')
SIL = re.compile(r'^[…─―!?¡¿\s　,.\-]*$')

def leer_reglas():
    p = os.path.join(AQUI, 'reglas_estilo_hmj.tsv'); out = []
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, encoding='utf-8-sig'), delimiter='\t'):
            if r.get('patron') and not r['patron'].startswith('#'):
                fl = 0 if (r.get('mayusculas') or '').strip() == 'si' else re.I
                out.append((re.compile(r['patron'], fl), r.get('problema', ''), (r.get('nivel') or 'AVISO').strip()))
    return out

def wrapper():
    try:
        sys.path.insert(0, AQUI); import hmj_wrap as hw
        for d in (AQUI, os.path.join(AQUI, '..', '..', 'work', 'extraido', 'data', 'font'),
                  os.path.join(AQUI, '..', 'work', 'extraido', 'data', 'font'),
                  os.path.join(AQUI, 'data', 'font')):
            if os.path.isfile(os.path.join(d, 'anticcezannepro.otf')): hw.AQUI = d; break
        hw._cargar(); return hw
    except BaseException: return None

def plano(s): return TAG.sub('', re.sub(r'\{n\}|\{u000A\}', '\n', s))

def vismap(s):
    vis = []; idx = []; i = 0
    while i < len(s):
        if s[i] == '{':
            j = s.find('}', i)
            if j < 0: break
            i = j + 1; continue
        vis.append(s[i]); idx.append(i); i += 1
    return ''.join(vis), idx

# ------------------------------------------------------------------ arreglos
def fix_puntos(s):
    s = re.sub(r'\.{3,}', '…', s); out = []
    for m in re.finditer(r'…{2,}', s):
        a, b = m.span()
        l = max(s.rfind('「', 0, a), s.rfind('{end}', 0, a), s.rfind('{u000A}', 0, a), s.rfind('」', 0, a))
        rr = [x for x in (s.find('」', b), s.find('{end}', b), s.find('{u000A}', b), s.find('「', b)) if x != -1]
        unidad = TAG.sub('', s[l + 1:(min(rr) if rr else len(s))]).replace('end}', '').replace('u000A}', '')
        if not SIL.match(unidad): out.append((a, b))
    for a, b in reversed(out): s = s[:a] + '…' + s[b:]
    return s

def fix_espacio_end(s):
    return re.sub(r'(?<=[^\s　「『─―}\]\[(])((?:\{/v\})?\{end\}(?:\{v:[^}]*\})?)(?=[^\s　{」』─―,.;:!?…\]\)])', r'\1 ', s)

def fix_signos(s):
    for ab, cl in (('¡', '!'), ('¿', '?')):
        res = []; last = 0
        for m in re.finditer(r'「([^「」]*)」', s):
            a, b = m.start(1), m.end(1); seg = s[a:b]; v, idx = vismap(seg); vv = v.rstrip(); new = seg
            if vv.endswith(cl) and ab not in v:
                k = 0
                for mm in re.finditer(r'[.?!;](?:\s|　)+|　+', vv[:-1]): k = mm.end()
                while k < len(v) and v[k] in ' 　': k += 1
                if k < len(idx): p = idx[k]; new = seg[:p] + ab + seg[p:]
            elif ab in v:
                q = v.rfind(ab)
                if cl not in v[q:] and not re.search(r'[.?!¿]', v[q + 1:]) and re.search(r'[─―…]$', vv):
                    p = idx[len(vv) - 1] + 1; new = seg[:p] + cl + seg[p:]
            res.append(s[last:a] + new); last = b
        res.append(s[last:]); s = ''.join(res)
    return s

PUNT_JP = [('、', ', '), ('。', '. '), ('！', '!'), ('？', '?'), ('：', ':'), ('；', ';'), ('（', '('), ('）', ')'), ('，', ', '), ('．', '.')]

def corregir_marcas(jp, es):
    """Arreglos mecanicos de marcas en casos claros (mensaje de una sola parte)."""
    es = es.replace('\r\n', '{n}').replace('\n', '{n}').replace('\r', '{n}').replace('\t', ' ')
    es = re.sub(r'\{\s*(n|end|/v)\s*\}', lambda m: '{' + m.group(1).lower() + '}', es, flags=re.I)
    es = re.sub(r'\{\s*u000a\s*\}', '{u000A}', es, flags=re.I)
    if not jp or MARCAS.findall(jp) == MARCAS.findall(es): return es
    mv = re.fullmatch(r'(\{v:[^}]*\})([^{]*)\{/v\}\{end\}', jp)          # voz simple: {v:..}texto{/v}{end}
    if mv:
        cuerpo = re.sub(r'\{v:[^}]*\}|\{/v\}|\{end\}', '', es).strip()
        if '{' not in cuerpo.replace('{n}', ''): return mv.group(1) + cuerpo + '{/v}{end}'
    if re.fullmatch(r'[^{]*\{end\}', jp):                                 # narracion simple: texto{end}
        cuerpo = re.sub(r'\{v:[^}]*\}|\{/v\}|\{end\}', '', es).strip()
        if '{' not in cuerpo.replace('{n}', ''): return cuerpo + '{end}'
    return es

def corregir(es, jp=''):
    es = corregir_marcas(jp, es)
    partes = re.split(r'(\{[^}]*\})', es)
    t = ''
    for p in partes:
        if not p.startswith('{'):
            for a, b in PUNT_JP: p = p.replace(a, b)
        t += p
    es = t
    t = fix_signos(fix_espacio_end(fix_puntos(es)))
    partes = re.split(r'(\{[^}]*\})', t)
    t = ''.join(p if p.startswith('{') else re.sub(r' +([」』,.;:!?])', r'\1', re.sub(r'(?<=\S) {2,}(?=\S)', ' ', p)) for p in partes)
    return t

# ------------------------------------------------------------------ revision
def revisar(jp, es, reglas, hw):
    out = []; E = lambda m: out.append(('ERROR', m)); A = lambda m: out.append(('AVISO', m))
    if jp and MARCAS.findall(jp) != MARCAS.findall(es): E('marcas distintas al japones ({v:..}{/v}{end}{u000A}{uXXXX} deben ir igual y en el mismo orden)')
    for m in re.findall(r'\{[^}]*\}?', es):
        if not MARCA_OK.fullmatch(m): E('marca desconocida o rota: ' + m)
    p = plano(es)
    if JP.search(p.replace('「', '').replace('」', '').replace('『', '').replace('』', '')): E('queda texto japones')
    if '\t' in es or '\r' in es or '\n' in es: E('tabulador o salto de linea real (usa {n})')
    if hw:
        _, n = hw.wrap(es)
        if n > 16: E('%d renglones (maximo 16): acortar' % n)
    for g in re.split(r'\{end\}|\{u000A\}', es):
        g = plano(g)
        if g.count('¿') != g.count('?'): A('¿ y ? sin pareja'); break
    for g in re.split(r'\{end\}|\{u000A\}', es):
        g = plano(g)
        if g.count('¡') != g.count('!'): A('¡ y ! sin pareja'); break
    if '...' in p: A('«...»: usa «…»')
    for g in re.split(r'[「」]|\{end\}|\{u000A\}', es):
        g2 = plano(g)
        if '……' in g2 and not SIL.match(g2): A('«……» dentro de una frase: usa «…» (solo silencios llevan «……»)'); break
    if fix_espacio_end(es) != es: A('falta espacio entre partes unidas por {end} (el texto sigue en el mismo renglon)')
    if re.search(r'[  ]{2,}', p): A('espacios dobles')
    if re.search(r' [,.;:!?」』]', p): A('espacio antes de un signo')
    for rx, prob, niv in reglas:
        m = rx.search(p)
        if m: out.append((niv, '%s: «%s»' % (prob, m.group(0))))
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args: print(__doc__); input('Enter para salir'); return
    src = args[0]; fix = '--corregir' in sys.argv
    rows = list(csv.DictReader(open(src, encoding='utf-8-sig')))
    reglas = leer_reglas(); hw = wrapper()
    if not hw: print('AVISO: no encontre hmj_wrap.py o la fuente anticcezannepro.otf; no reviso los renglones.')
    rep = []; cambios = 0
    for r in rows:
        es = r.get('spanish') or ''
        if not es.strip(): continue
        if fix:
            n = corregir(es, r.get('japanese') or '')
            if n != es: r['spanish'] = n; cambios += 1; es = n
        for niv, prob in revisar(r.get('japanese') or '', es, reglas, hw):
            rep.append((r['id'], niv, prob, plano(es).replace('\n', ' ')[:150]))
    base = os.path.splitext(src)[0]
    with open(os.path.join(os.path.dirname(os.path.abspath(src)), 'reporte_estilo.tsv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter='\t'); w.writerow(['id', 'nivel', 'problema', 'texto (sin marcas)']); w.writerows(rep)
    if fix:
        out = base + '_corregido.csv'
        if os.path.exists(out): shutil.copyfile(out, out + '.respaldo_' + time.strftime('%Y%m%d_%H%M%S'))
        with open(out, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
        print('Corregidos', cambios, 'mensajes ->', out, '(tu archivo original no se toco)')
    ne = sum(1 for x in rep if x[1] == 'ERROR'); na = len(rep) - ne
    print('Revisados', len(rows), 'mensajes:', ne, 'errores,', na, 'avisos. Detalle en reporte_estilo.tsv')

if __name__ == '__main__':
    main()
