#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hmj_kit.py - Kit de traduccion al espanol de Soushuu Senshinkan Gakuen: Hachimyoujin (light, 2017, motor MALIE).

  python hmj_kit.py extraer   [CARPETA_DEL_JUEGO] [--forzar] [--vacio]
        lee TU data1.dat y crea trabajo/HMJ_TRADUCCION.csv (japones de tu copia + espanol del grupo)
  python hmj_kit.py revisar   [ARCHIVO.csv | CARPETA ...]   revisa, CORRIGE lo seguro y lo guarda en el CSV de trabajo
  python hmj_kit.py validar   [ARCHIVO.csv | CARPETA ...]   solo revisa (no cambia nada)
  python hmj_kit.py generar   [ARCHIVO.csv] [--sin-videos]  (revisa ese CSV y) crea el data3.dat en la carpeta del juego
  python hmj_kit.py exe                                     crea malie_es.exe (menus de Windows en espanol)
  python hmj_kit.py dividir   [N]                           parte el CSV de trabajo en archivos de N mensajes (500)
  python hmj_kit.py compartir                               exporta tu traduccion SIN japones para compartirla

El CSV puede llamarse como quieras; necesita columnas id y spanish (las demas son opcionales).
Acepta coma, punto y coma (Excel en espanol) o tabulador, en UTF-8 o ANSI.
Dudas: Discord https://discord.gg/XJmNBWcP9
"""
import sys, os, re, io, csv, json, shutil, hashlib, datetime, tempfile
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
csv.field_size_limit(10 ** 8)
H = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):        # version .exe: las carpetas del kit estan junto al .exe
    KIT = os.path.dirname(os.path.abspath(sys.executable))
else:
    KIT = os.path.dirname(H)
sys.path.insert(0, H)

VERSION_KIT = '1.0'
JUEGO_NOMBRE = 'Soushuu Senshinkan Gakuen: Hachimyoujin (light, 2017)'
CLAVE = 'Soushuu Senshinkan Gakuen Hachimyoujin'
MD5_EXEC = 'bd677ce6ee9cb688838fce05166ad69d'      # data/system/exec.dat dentro de data1.dat
MD5_EXE = 'e45c0a09fb19f64d0ca5fc98bd4b5e47'       # malie.exe v1.1.0.0 (2017-09-07)
DISCORD = 'https://discord.gg/XJmNBWcP9'
CAMPOS = ['id', 'voice', 'japanese', 'spanish', 'status']
VIDEOS = ['akr', 'ats', 'aym', 'hrm', 'mzk', 'rnk', 'ysy']
PANTALLAS = ['title', 'extra', 'config', 'award']
FUENTE = 'data/font/anticcezannepro.otf'

TRAB = os.path.join(KIT, 'trabajo')
MAESTRO = os.path.join(TRAB, 'HMJ_TRADUCCION.csv')
CADENAS = os.path.join(TRAB, 'HMJ_NOMBRES_Y_OPCIONES.tsv')
EXEC0 = os.path.join(TRAB, 'original', 'exec.dat')
ORIG = os.path.join(TRAB, 'original')              # copias de TU juego (solo para uso local)
GEN = os.path.join(TRAB, 'generado')               # interfaz, fuente y videos en espanol hechos desde tu copia
REPORTES = os.path.join(TRAB, 'reportes')
CONFIG = os.path.join(KIT, 'config.txt')
TRAD_KIT = os.path.join(KIT, 'traduccion')

def ahora(): return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def leer_config():
    c = {}
    if os.path.isfile(CONFIG):
        for l in open(CONFIG, encoding='utf-8-sig'):
            if '=' in l: k, v = l.split('=', 1); c[k.strip()] = v.strip().strip('"')
    return c

def guardar_config(c):
    with open(CONFIG, 'w', encoding='utf-8') as f:
        for k, v in c.items(): f.write('%s=%s\n' % (k, v))

def carpeta_juego(arg=None):
    c = leer_config()
    j = arg or c.get('JUEGO')
    if not j:
        try:
            print('Escribe la carpeta del juego (donde estan malie.exe y data1.dat)')
            j = input('o arrastrala a esta ventana y presiona Enter: ').strip().strip('"')
        except EOFError: j = ''
    if not j: raise SystemExit('ERROR: falta la carpeta del juego.')
    j = os.path.abspath(j)
    if not os.path.isfile(os.path.join(j, 'data1.dat')):
        raise SystemExit('ERROR: en "%s" no esta data1.dat. Indica la carpeta raiz del juego (donde esta malie.exe).' % j)
    if c.get('JUEGO') != j: c['JUEGO'] = j; guardar_config(c)
    return j

def leer_tabla(path):
    """Lee un CSV/TSV con cualquier nombre. UTF-8 (con o sin BOM) o ANSI de Windows; separador , ; o tab."""
    raw = open(path, 'rb').read(); aviso = ''
    for enc in ('utf-8-sig', 'cp1252'):
        try: txt = raw.decode(enc); break
        except UnicodeDecodeError: continue
    if enc == 'cp1252': aviso = 'el archivo no estaba en UTF-8 (se leyo como ANSI de Windows); revisa acentos y 「」'
    prim = txt.replace('\r\n', '\n').split('\n', 1)[0]
    sep = '\t' if '\t' in prim else (';' if prim.count(';') > prim.count(',') else ',')
    filas = list(csv.DictReader(io.StringIO(txt, newline=''), delimiter=sep))
    norm = [{(k or '').strip().lower().lstrip('﻿'): (v if v is not None else '') for k, v in f.items()} for f in filas]
    return norm, aviso

def escribir_csv(rows, path, campos=CAMPOS, sep=','):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore', delimiter=sep); w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)

def respaldar(path):
    if not os.path.isfile(path): return None
    d = os.path.join(TRAB, 'respaldos'); os.makedirs(d, exist_ok=True)
    b, e = os.path.splitext(os.path.basename(path))
    dst = os.path.join(d, '%s_%s%s' % (b, ahora(), e)); shutil.copyfile(path, dst); return dst

def estilo():
    import hmj_revisar_estilo as est, hmj_wrap as hw
    hw._cargar()
    reglas = []
    p = os.path.join(TRAD_KIT, 'reglas_estilo_hmj.tsv')
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, encoding='utf-8-sig'), delimiter='\t'):
            if r.get('patron') and not r['patron'].startswith('#'):
                fl = 0 if (r.get('mayusculas') or '').strip() == 'si' else re.I
                try: reglas.append((re.compile(r['patron'], fl), r.get('problema', ''), (r.get('nivel') or 'AVISO').strip()))
                except re.error as e: print('AVISO: regla de estilo mal escrita (%s): %s' % (e, r['patron']))
    return est, hw, reglas

_EST = None
def _e():
    global _EST
    if _EST is None: _EST = estilo()
    return _EST

def revisar_msg(jp, es):
    est, hw, reglas = _e(); return est.revisar(jp, es, reglas, hw)

def errores_de(jp, es): return [p for n, p in revisar_msg(jp, es) if n == 'ERROR']

def corregir_msg(jp, es):
    est = _e()[0]; n = est.corregir(es, jp)
    return n, (['puntuacion, marcas o espacios'] if n != es else [])

def renglones(es): return _e()[1].wrap(es.replace('\n', '{n}'))[1]

def escribir_maestro(rows): escribir_csv(rows, MAESTRO)

# =====================================================================================
# 1) EXTRAER
# =====================================================================================
def cmd_extraer(args, aviso_final=True):
    forzar = '--forzar' in args; vacio = '--vacio' in args
    args = [a for a in args if not a.startswith('--')]
    juego = carpeta_juego(args[0] if args else None)
    import pl_extraer as px, pl_exec_tool as pt, pl_cadenas as pc
    os.makedirs(ORIG, exist_ok=True)
    print('Kit %s para %s' % (VERSION_KIT, JUEGO_NOMBRE))
    print('[1/5] Abriendo %s ...' % os.path.join(juego, 'data1.dat'))
    d = px.Dat(os.path.join(juego, 'data1.dat'))
    print('      clave de cifrado: %s' % d.clave)
    tmp = EXEC0 + '.nuevo'
    open(tmp, 'wb').write(d.data(d.find('data/system/exec.dat')))
    m = md5(tmp)
    print('[2/5] exec.dat md5 %s %s' % (m, '(edicion correcta)' if m == MD5_EXEC else '(EDICION DISTINTA)'))
    if m != MD5_EXEC and not forzar:
        os.remove(tmp)
        raise SystemExit('ERROR: tu juego no es la edicion para la que se hizo esta traduccion\n'
                         '(edicion esperada: %s, exec.dat md5 %s;\n tu copia: md5 %s). No se cambio nada.\n'
                         'Te ayudamos a adaptar el kit a tu version en el Discord %s\n'
                         'Manda de donde es tu copia, la version de malie.exe (clic derecho > Propiedades > Detalles)\n'
                         'y una captura de este mensaje. No apliques parches oficiales.' % (JUEGO_NOMBRE, MD5_EXEC, m, DISCORD))
    os.replace(tmp, EXEC0)
    print('[3/5] Copiando de tu juego la fuente, las pantallas de interfaz y los videos de estado (uso local) ...')
    for p in [FUENTE] + ['data/picture/event/mv_%ssta.webm' % q for q in VIDEOS]:
        dst = os.path.join(ORIG, *p.split('/'))
        if not os.path.isfile(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True); d.save(d.find(p), dst)
    for s in PANTALLAS:
        px.extraer(d, d.find('data/screen/' + s), os.path.join(ORIG, 'data', 'screen', s))
    d.f.close()
    print('[4/5] Creando el CSV de trabajo ...')
    if os.path.isfile(MAESTRO) and not forzar:
        print('      Ya existe trabajo\\HMJ_TRADUCCION.csv: NO se toca (tu trabajo esta a salvo).')
        print('      Para rehacerlo desde cero: extraer con --forzar (se guarda respaldo).')
    else:
        b = respaldar(MAESTRO)
        if b: print('      respaldo del CSV anterior: %s' % b)
        t = os.path.join(TRAB, '_extraido.csv'); pt.extract(EXEC0, t)
        rows = list(csv.DictReader(open(t, encoding='utf-8-sig'))); os.remove(t)
        es = {}
        ruta = os.path.join(TRAD_KIT, 'HMJ_es.csv')
        if os.path.isfile(ruta) and not vacio:
            for r in leer_tabla(ruta)[0]:
                if (r.get('spanish') or '').strip(): es[r['id'].strip()] = r['spanish']
        for r in rows:
            r['spanish'] = es.get(r['id'], ''); r['status'] = 'draft' if r['id'] in es else 'untranslated'
        escribir_csv(rows, MAESTRO)
        print('      %d mensajes, %d ya en espanol (traduccion del grupo)%s -> %s'
              % (len(rows), len(es), ' [--vacio: sin traduccion]' if vacio else '', MAESTRO))
    print('[5/5] Nombres (historial) y opciones de eleccion ...')
    t = os.path.join(TRAB, '_cad.tsv'); pc.extraer(EXEC0, t)
    cad = list(csv.DictReader(open(t, encoding='utf-8-sig'), delimiter='\t')); os.remove(t)
    previo = {}
    if os.path.isfile(CADENAS) and not forzar:
        for r in csv.DictReader(open(CADENAS, encoding='utf-8-sig'), delimiter='\t'): previo[r['offset']] = r['spanish']
    kit = {}
    rk = os.path.join(TRAD_KIT, 'cadenas_es.tsv')
    if os.path.isfile(rk) and not vacio:
        for r in csv.DictReader(open(rk, encoding='utf-8-sig'), delimiter='\t'): kit[r['offset']] = r['spanish']
    for r in cad: r['spanish'] = previo.get(r['offset']) or kit.get(r['offset'], '')
    if os.path.isfile(CADENAS): respaldar(CADENAS)
    escribir_csv(cad, CADENAS, ['offset', 'tipo', 'usos', 'japanese', 'spanish', 'nota'], '\t')
    print('      %d textos (%d en espanol) -> %s' % (len(cad), sum(1 for r in cad if r['spanish']), CADENAS))
    if aviso_final:
        print('\nLISTO. Abre trabajo\\HMJ_TRADUCCION.csv (columna spanish) y traduce o corrige.')
        print('Despues: REVISAR Y CORREGIR, y GENERAR DAT.')

# =====================================================================================
# 2) REVISAR Y CORREGIR
# =====================================================================================
def maestro_filas():
    if not os.path.isfile(MAESTRO):
        raise SystemExit('ERROR: todavia no hay CSV de trabajo. Corre primero el paso 1 (EXTRAER).')
    return list(csv.DictReader(open(MAESTRO, encoding='utf-8-sig')))

def archivos_de(args):
    out = []
    for a in args:
        if os.path.isdir(a):
            out += sorted(os.path.join(a, f) for f in os.listdir(a) if f.lower().endswith(('.csv', '.tsv')))
        elif os.path.isfile(a): out.append(a)
        else: raise SystemExit('ERROR: no encuentro: %s' % a)
    return out

def cmd_revisar(args):
    solo = '--solo-revisar' in args; args = [a for a in args if not a.startswith('--')]
    m = maestro_filas(); by = {r['id']: r for r in m}
    rutas = archivos_de(args) if args else [MAESTRO]
    est, hw, reglas = estilo()
    rep = []; n_tot = n_ok = n_corr = n_mal = n_vacio = n_noid = n_av = 0; avisos_enc = []
    for ruta in rutas:
        filas, aviso_enc = leer_tabla(ruta)
        if aviso_enc: avisos_enc.append('%s: %s' % (os.path.basename(ruta), aviso_enc))
        if not filas or 'id' not in filas[0] or 'spanish' not in filas[0]:
            raise SystemExit('ERROR: %s debe tener las columnas "id" y "spanish" (tiene: %s)'
                             % (os.path.basename(ruta), ', '.join(filas[0].keys() if filas else [])))
        for f in filas:
            i = (f.get('id') or '').strip()
            if not i: continue
            es0 = f.get('spanish') or ''
            if i not in by: n_noid += 1; rep.append((i, 'IGNORADO', 'id que no existe en el juego')); continue
            if not es0.strip(): n_vacio += 1; continue
            n_tot += 1; jp = by[i]['japanese']
            es1 = est.corregir(es0, jp)
            res = est.revisar(jp, es1, reglas, hw)
            err = [p for n, p in res if n == 'ERROR']; av = [p for n, p in res if n != 'ERROR']; n_av += len(av)
            if es1 != es0: n_corr += 1; rep.append((i, 'CORREGIDO', 'antes: %s || despues: %s' % (es0, es1)))
            if err: n_mal += 1; rep.append((i, 'ERROR', '; '.join(err) + ' -> se quedara en japones hasta que lo arregles'))
            else: n_ok += 1
            for a in av: rep.append((i, 'aviso', a))
            if not solo:
                by[i]['spanish'] = es1
                st = (f.get('status') or '').strip().lower()
                by[i]['status'] = 'error' if err else (st if st in ('draft', 'reviewed', 'approved') else 'draft')
    if not solo:
        b = respaldar(MAESTRO); escribir_csv(m, MAESTRO)
    pend = [r for r in m if not r['spanish'].strip()]
    os.makedirs(REPORTES, exist_ok=True)
    base = os.path.join(REPORTES, 'reporte_revision')
    with open(base + '.csv', 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['id', 'estado', 'detalle']); w.writerows(rep)
    with open(os.path.join(REPORTES, 'pendientes.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(CAMPOS)
        for r in pend: w.writerow([r['id'], r['voice'], r['japanese'], '', 'untranslated'])
    L = ['REVISION de %s  (%s)' % (', '.join(os.path.basename(r) for r in rutas), datetime.datetime.now().strftime('%Y-%m-%d %H:%M')),
         'Reglas del juego: 700 px por renglon (unos 60-70 caracteres), maximo 16 renglones por mensaje;',
         'las marcas {v:..}{/v}{end}{u000A}{uXXXX} deben ir igual y en el mismo orden que en el japones.']
    L += ['OJO: ' + a for a in avisos_enc]
    L += ['',
          'Mensajes con espanol revisados ..... %d' % n_tot,
          '  correctos al final .............. %d' % n_ok,
          '  con arreglos automaticos ........ %d' % n_corr,
          '  con ERRORES que no pude corregir  %d' % n_mal,
          'Filas sin espanol en tu archivo .... %d' % n_vacio,
          'ids que no existen (ignorados) ..... %d' % n_noid,
          'Avisos de estilo (revisar a mano) .. %d' % n_av]
    if not solo:
        L += ['', 'RESULTADO: trabajo\\HMJ_TRADUCCION.csv actualizado (respaldo del anterior en trabajo\\respaldos).',
              'Mensajes sin traducir: %d (lista en trabajo\\reportes\\pendientes.csv)' % len(pend)]
    else:
        L += ['', 'Modo solo revisar: no se cambio ningun archivo.']
    n_resumen = len(L)
    for titulo, clase in (('ERRORES QUE NO SE PUDIERON CORREGIR (arreglalos a mano)', 'ERROR'),
                          ('ARREGLOS AUTOMATICOS', 'CORREGIDO'), ('AVISOS DE ESTILO (no impiden generar el .dat)', 'aviso'),
                          ('IGNORADOS', 'IGNORADO')):
        xs = [x for x in rep if x[1] == clase]
        if xs: L += ['', '== %s ==' % titulo] + ['id %s: %s' % (x[0], x[2]) for x in xs]
    open(base + '.txt', 'w', encoding='utf-8-sig').write('\n'.join(L) + '\n')
    print('\n'.join(L[:n_resumen]))
    mal = [x for x in rep if x[1] == 'ERROR']
    for x in mal[:30]: print('  ERROR id %s: %s' % (x[0], x[2]))
    if len(mal) > 30: print('  ... y %d mas' % (len(mal) - 30))
    print('\nReporte completo: %s.txt (y .csv)' % base)
    print('\nLISTO.' + ('' if solo else ' Siguiente paso: GENERAR DAT.'))
    return n_mal

# =====================================================================================
# 3) GENERAR DAT
# =====================================================================================
def _sello(nombre):
    return os.path.join(GEN, nombre + '.ok')

def _hecho(nombre):
    p = _sello(nombre)
    return os.path.isfile(p) and open(p).read().strip() == VERSION_KIT

def _marcar(nombre):
    open(_sello(nombre), 'w').write(VERSION_KIT)

def preparar_interfaz():
    if _hecho('interfaz'): print('      interfaz en espanol: ya estaba hecha'); return
    import hmj_gen_title, hmj_gen_extra, hmj_gen_config, hmj_gen_misc
    src = os.path.join(ORIG, 'data', 'screen'); dst = os.path.join(GEN, 'interfaz', 'data', 'screen')
    fuente = os.path.join(ORIG, *FUENTE.split('/'))
    if os.path.isdir(dst): shutil.rmtree(dst)
    os.makedirs(dst)
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        hmj_gen_title.main(os.path.join(src, 'title'), os.path.join(dst, 'title'), fuente)
        hmj_gen_extra.main(os.path.join(src, 'extra'), os.path.join(dst, 'extra'), fuente)
        hmj_gen_config.main(os.path.join(src, 'config'), os.path.join(dst, 'config'), fuente)
        hmj_gen_misc.main(src, dst, fuente)
    _marcar('interfaz'); print('      interfaz en espanol: creada desde tu copia (titulo, extras, configuracion, guardar/cargar)')

def preparar_fuente():
    dst = os.path.join(GEN, 'fuente', *FUENTE.split('/'))
    if _hecho('fuente') and os.path.isfile(dst): print('      fuente adaptada: ya estaba hecha'); return
    import hmj_fuente_es, contextlib
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        hmj_fuente_es.main(os.path.join(ORIG, *FUENTE.split('/')), dst)
    _marcar('fuente'); print('      fuente adaptada (no se cortan g, j, p, q, y, ¿; «…» en la linea)')

def preparar_videos():
    if _hecho('videos'): print('      videos de estado: ya estaban hechos'); return True
    try:
        import hmj_estados_es
    except Exception as e:
        print('      AVISO: no puedo hacer los videos de estado (%s). Se quedan los originales.' % e); return False
    out = os.path.join(GEN, 'videos', 'data', 'picture', 'event'); os.makedirs(out, exist_ok=True)
    fuente = os.path.join(ORIG, *FUENTE.split('/'))
    import contextlib
    for k, q in enumerate(VIDEOS):
        dst = os.path.join(out, 'mv_%ssta.webm' % q)
        if os.path.isfile(dst): continue
        print('      video de estado %d/%d (tarda 1-3 minutos cada uno) ...' % (k + 1, len(VIDEOS)), flush=True)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                hmj_estados_es.main(os.path.join(ORIG, 'data', 'picture', 'event', 'mv_%ssta.webm' % q), dst + '.tmp.webm', fuente)
            os.replace(dst + '.tmp.webm', dst)
        except BaseException as e:
            print('      AVISO: fallo el video %s (%s). Se quedan los originales.' % (q, e))
            shutil.rmtree(os.path.join(GEN, 'videos'), ignore_errors=True); return False
    _marcar('videos'); print('      videos de estado: listos'); return True

def cmd_generar(args):
    sin_videos = '--sin-videos' in args
    archivos = [a for a in args if not a.startswith('--')]
    if archivos:
        cmd_revisar(archivos); print('\n' + '=' * 70 + '\n')
    juego = carpeta_juego()
    if not (os.path.isfile(MAESTRO) and os.path.isfile(EXEC0) and os.path.isfile(CADENAS)
            and os.path.isfile(os.path.join(ORIG, *FUENTE.split('/')))):
        print('Leyendo tu juego (solo la primera vez) ...'); cmd_extraer([juego], aviso_final=False); print()
    if md5(EXEC0) != MD5_EXEC: raise SystemExit('ERROR: trabajo\\original\\exec.dat no es el original. Corre EXTRAER con --forzar.')
    import pl_build as pb, pl_exec_tool as pt, pl_cadenas as pc, pl_extraer as px
    pb.usar_clave(CLAVE)
    est, hw, reglas = estilo()
    MARCAS = est.MARCAS
    rows = maestro_filas()
    print('[1/5] Revisando el CSV de trabajo ...')
    usados = 0; malos = []
    for r in rows:
        es = (r.get('spanish') or '').strip()
        if not es: r['spanish'] = ''; continue
        es = est.corregir(es, r['japanese'])
        err = [p for n, p in est.revisar(r['japanese'], es, reglas, hw) if n == 'ERROR']
        if MARCAS.findall(es) != MARCAS.findall(r['japanese']) and not err: err = ['marcas distintas al japones']
        if err: malos.append((r['id'], '; '.join(err))); r['spanish'] = ''; continue
        r['spanish'], _ = hw.wrap(es); r['status'] = 'draft'; usados += 1
    print('      %d mensajes en espanol, %d sin traducir%s' % (usados, len(rows) - usados - len(malos),
          (', %d con errores (se quedan en japones)' % len(malos)) if malos else ''))
    for i, e in malos[:20]: print('      ERROR id %s: %s' % (i, e))
    if malos:
        os.makedirs(REPORTES, exist_ok=True)
        with open(os.path.join(REPORTES, 'errores_al_generar.txt'), 'w', encoding='utf-8-sig') as f:
            f.write('Mensajes que se quedaron en japones (arreglalos en el CSV):\n' + '\n'.join('id %s: %s' % x for x in malos) + '\n')
        print('      lista completa: trabajo\\reportes\\errores_al_generar.txt')
    tmp = tempfile.mkdtemp()
    tcsv = os.path.join(tmp, 'w.csv'); texe = os.path.join(tmp, 'e.dat'); exe1 = EXEC0
    escribir_csv(rows, tcsv)
    print('[2/5] Guion, nombres y opciones ...')
    if any(r['spanish'].strip() for r in csv.DictReader(open(CADENAS, encoding='utf-8-sig'), delimiter='\t')):
        exe1 = os.path.join(tmp, 'c.dat'); pc.insertar(EXEC0, CADENAS, exe1)
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        pt.insert(exe1, tcsv, texe, 0)
    tree = {'data': {'system': {'exec.dat': open(texe, 'rb').read()}}}
    print('[3/5] Interfaz, fuente y videos (desde tu copia del juego) ...')
    os.makedirs(GEN, exist_ok=True)
    preparar_interfaz(); preparar_fuente()
    carpetas = [os.path.join(GEN, 'interfaz'), os.path.join(GEN, 'fuente')]
    if not sin_videos and preparar_videos(): carpetas.append(os.path.join(GEN, 'videos'))
    elif sin_videos: print('      videos de estado: omitidos (--sin-videos)')
    n = 0
    for base in carpetas:
        for raiz, dirs, fs in os.walk(base):
            for fn in fs:
                rel = os.path.relpath(os.path.join(raiz, fn), base).replace('\\', '/').split('/')
                node = tree
                for p in rel[:-1]: node = node.setdefault(p, {})
                node[rel[-1]] = open(os.path.join(raiz, fn), 'rb').read(); n += 1
    print('      %d archivos de interfaz/fuente/videos' % n)
    print('[4/5] Escribiendo y comprobando data3.dat (puede tardar un poco) ...')
    out = os.path.join(TRAB, 'data3.dat')
    pb.escribir_libp(tree, out)
    d = px.Dat(out)
    def check(node, path):
        for k, v in node.items():
            pp = path + '/' + k if path else k
            if isinstance(v, dict): check(v, pp)
            elif d.data(d.find(pp)) != v: raise SystemExit('ERROR: la relectura del data3 no coincide en ' + pp)
    check(tree, ''); d.f.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print('[5/5] Copiando al juego ...')
    dst = os.path.join(juego, 'data3.dat')
    if os.path.isfile(dst):
        rd = os.path.join(TRAB, 'respaldos'); os.makedirs(rd, exist_ok=True)
        b = os.path.join(rd, 'data3_anterior_%s.dat' % ahora()); shutil.copyfile(dst, b)
        print('      respaldo del data3.dat anterior: %s' % b)
    shutil.copyfile(out, dst)
    print('\nLISTO: %s (%d bytes, comprobado).' % (dst, os.path.getsize(dst)))
    print('Abre el juego (mejor malie_es.exe, paso 4) para probarlo. Para volver al japones, quita o renombra data3.dat.')

# =====================================================================================
# 4) MALIE_ES.EXE
# =====================================================================================
def cmd_exe(args):
    juego = carpeta_juego(args[0] if args and not args[0].startswith('--') else None)
    src = os.path.join(juego, 'malie.exe'); dst = os.path.join(juego, 'malie_es.exe')
    if not os.path.isfile(src): raise SystemExit('ERROR: no esta malie.exe en %s' % juego)
    p = json.load(open(os.path.join(H, 'hmj_exe_parche.json'), encoding='utf-8'))
    m = md5(src)
    print('malie.exe md5 %s %s' % (m, '(version correcta)' if m == p['md5_original'] else '(VERSION DISTINTA)'))
    if m != p['md5_original']:
        raise SystemExit('ERROR: tu malie.exe no es la version 1.1.0.0 (2017) de este kit; no se cambio nada.\n'
                         'Puedes jugar con tu malie.exe normal (los menus de Windows quedan en japones),\n'
                         'o pide ayuda en el Discord %s' % DISCORD)
    d = bytearray(open(src, 'rb').read())
    for off, hx in p['cambios']:
        b = bytes.fromhex(hx)
        if off + len(b) > len(d): d += b'\0' * (off + len(b) - len(d))
        d[off:off + len(b)] = b
    del d[p['tam_resultado']:]
    if hashlib.md5(d).hexdigest() != p['md5_resultado']: raise SystemExit('ERROR: el resultado no coincide; no se escribio nada.')
    if os.path.isfile(dst): respaldar(dst)
    open(dst, 'wb').write(d)
    print('LISTO: %s (menus de Windows y avisos en espanol; malie.exe original sin tocar).' % dst)
    print('Abre el juego con malie_es.exe.')

# =====================================================================================
# extras: dividir y compartir
# =====================================================================================
def cmd_dividir(args):
    n = int(args[0]) if args and args[0].isdigit() else 500
    rows = maestro_filas(); d = os.path.join(TRAB, 'partes'); os.makedirs(d, exist_ok=True)
    k = 0
    for i in range(0, len(rows), n):
        parte = rows[i:i + n]; k += 1
        escribir_csv(parte, os.path.join(d, 'HMJ_parte_%03d_%s-%s.csv' % (k, parte[0]['id'], parte[-1]['id'])))
    print('LISTO: %d archivos de %d mensajes en %s' % (k, n, d))
    print('Traduce los que quieras y despues usa REVISAR con la carpeta "partes" (se leen todos).')

def cmd_compartir(args):
    rows = maestro_filas(); d = os.path.join(TRAB, 'compartir'); os.makedirs(d, exist_ok=True)
    es = [{'id': r['id'], 'voice': r['voice'], 'spanish': r['spanish']} for r in rows if r['spanish'].strip()]
    escribir_csv(es, os.path.join(d, 'HMJ_es.csv'), ['id', 'voice', 'spanish'])
    cad = [{'offset': r['offset'], 'tipo': r['tipo'], 'spanish': r['spanish']}
           for r in csv.DictReader(open(CADENAS, encoding='utf-8-sig'), delimiter='\t')] if os.path.isfile(CADENAS) else []
    escribir_csv(cad, os.path.join(d, 'cadenas_es.tsv'), ['offset', 'tipo', 'spanish'], '\t')
    print('LISTO: %d mensajes y %d nombres/opciones SIN japones en %s' % (len(es), len(cad), d))
    print('Estos dos archivos se pueden compartir (no llevan el texto original del juego).')
    print('Para usarlos, otra persona los pone en la carpeta "traduccion" del kit y corre EXTRAER con --forzar.')

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    c, r = a[0], a[1:]
    cmds = {'extraer': cmd_extraer, 'revisar': cmd_revisar, 'corregir': cmd_revisar,
            'validar': lambda x: cmd_revisar(x + ['--solo-revisar']), 'generar': cmd_generar, 'integrar': cmd_generar,
            'exe': cmd_exe, 'dividir': cmd_dividir, 'compartir': cmd_compartir}
    if c not in cmds: print(__doc__); sys.exit(1)
    cmds[c](r)

if __name__ == '__main__': main()
