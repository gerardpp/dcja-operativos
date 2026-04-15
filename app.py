from flask import Flask, render_template, request, jsonify
import sqlite3, json, os, random, secrets
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB = 'dcja.db'
COOLDOWN_DAYS = 21

PERSONAL = [
    {"id":1,"nombre":"OMAR ABDALA CHAMI ISA","cargo":"COORDINADOR","zona":"Distrito Nacional"},
    {"id":2,"nombre":"JUAN ROSARIO SANCHEZ","cargo":"COORDINADOR","zona":"Distrito Nacional"},
    {"id":3,"nombre":"ROBERTO CARLOS GUZMAN MARTINEZ","cargo":"COORDINADOR","zona":"SD Norte"},
    {"id":4,"nombre":"PEDRO JULIO CASTILLO","cargo":"COORDINADOR","zona":"Distrito Nacional"},
    {"id":5,"nombre":"ERCILIO ANTONIO VASQUEZ GUZMAN","cargo":"COORDINADOR","zona":"SD Oeste"},
    {"id":6,"nombre":"JUAN TOMAS BATISTA BAUTISTA","cargo":"COORDINADOR","zona":"Distrito Nacional"},
    {"id":7,"nombre":"DOMINDO MERCEDES","cargo":"INSPECTOR","zona":"SD Este"},
    {"id":8,"nombre":"CARLOS BENJAMIN HERNANDEZ MENDEZ","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":9,"nombre":"ELIEZER JIMENEZ DE LA CRUZ","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":10,"nombre":"JOSE MIGUEL RODRIGUEZ BENITEZ","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":11,"nombre":"JOSIAS LABOUR VERAS","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":12,"nombre":"JULIO BIENVENIDO DIAZ SANTANA","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":14,"nombre":"LEUDIS RAFAEL DIAZ SUAREZ","cargo":"INSPECTOR","zona":"SD Este"},
    {"id":16,"nombre":"PABLO FORTUNATO TAVERAS","cargo":"INSPECTOR","zona":"SD Norte"},
    {"id":18,"nombre":"ROBER JESUS GARCIA","cargo":"INSPECTOR","zona":"SD Este"},
    {"id":19,"nombre":"VICTOR OMAR MERCADO MEJIA","cargo":"INSPECTOR","zona":"San Cristóbal"},
    {"id":20,"nombre":"VLADIMIR TAVERAS MOYA","cargo":"INSPECTOR","zona":"San Cristóbal"},
    {"id":21,"nombre":"WALTERIO RAFAEL PELLERANO CASTILLO","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":22,"nombre":"FRANKLIN FELIX ALVAREZ","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":23,"nombre":"MANUEL BOLIVAR PATIN ENCARNACION","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":24,"nombre":"EDISON ALBERTO MEJIA DE LEON","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":25,"nombre":"KELMI MOISES DE LA CRUZ BERROA","cargo":"INSPECTOR","zona":"Distrito Nacional"},
    {"id":26,"nombre":"ANGEL DAVID HERNANDEZ CUAS","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":27,"nombre":"DENNY JOSE ACEVEDO MACARIO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":28,"nombre":"HENRY DE JESUS","cargo":"AUXILIAR","zona":"SD Norte"},
    {"id":29,"nombre":"GABRIEL A FLORENCIO POLANCO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":30,"nombre":"IVAN MEDINA","cargo":"AUXILIAR","zona":"SD Este"},
    {"id":31,"nombre":"JEISON CAMILO MERCEDES SENA","cargo":"AUXILIAR","zona":"SD Este"},
    {"id":32,"nombre":"JESUS FELIX GOMEZ BONILLA","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":33,"nombre":"JUAN LINARES REYES","cargo":"AUXILIAR","zona":"SD Oeste"},
    {"id":34,"nombre":"LEONEL DAVID HERNANDEZ","cargo":"AUXILIAR","zona":"SD Norte"},
    {"id":35,"nombre":"ANTHONY JUNIOR BRITO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":36,"nombre":"ELIS ENMANUEL MARTES POZO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":37,"nombre":"LORENZO WILLIAMS JANSER GIL","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":38,"nombre":"ROBIN DE JESUS GARCIA BELLIARD","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":39,"nombre":"MIGUEL ELIGIO TAVAREZ BELLO","cargo":"AUXILIAR","zona":"San Cristóbal"},
    {"id":40,"nombre":"AURELIO REYES MERCEDES","cargo":"AUXILIAR","zona":"SD Norte"},
    {"id":41,"nombre":"DALBERTO SUAREZ ENRIQUES","cargo":"AUXILIAR","zona":"SD Oeste"},
    {"id":42,"nombre":"CLAUDIO ANTONIO TEJADA CASTRO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":43,"nombre":"OMAR ANTONIO NUÑEZ AMPARO","cargo":"AUXILIAR","zona":"SD Norte"},
    {"id":44,"nombre":"ANDY ALMANZAR SANCHEZ","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":45,"nombre":"ANDERSON JULIO FELIZ ROMERO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":46,"nombre":"CRISTIAN ALEXIS LUGO MORILLO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":47,"nombre":"SIMON DE LOS SANTOS GARCIA RODRIGUEZ","cargo":"AUXILIAR","zona":"SD Oeste"},
    {"id":48,"nombre":"RANDEL RAMON PENA SUERO","cargo":"AUXILIAR","zona":"Distrito Nacional"},
    {"id":49,"nombre":"JOSE LUIS DIAZ ARIAS","cargo":"AUXILIAR","zona":"SD Oeste"},
]

PROV_COORDS = {
    "Distrito Nacional":[18.4861,-69.9312],"SD Este":[18.5001,-69.8500],
    "SD Norte":[18.5850,-69.9500],"SD Oeste":[18.5000,-70.0500],
    "San Cristóbal":[18.4175,-70.1106],"San Cristóbal / Haina":[18.4300,-70.0500],
    "Santiago":[19.4517,-70.6970],"La Romana":[18.4273,-68.9728],
    "Puerto Plata":[19.7930,-70.6880],"San Juan":[18.8053,-71.2284],
    "Espaillat":[19.3941,-70.5232],"Dajabón":[19.5497,-71.7085],
    "San Pedro de Macorís":[18.4586,-69.3058],"La Vega":[19.2211,-70.5294],
    "Barahona":[18.2053,-71.0981],"Baní / Peravia":[18.2800,-70.3314],
    "Monte Plata":[18.8064,-69.7836],"La Altagracia":[18.6200,-68.7200],
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS personal_state (
                persona_id INTEGER PRIMARY KEY,
                carga_total INTEGER DEFAULT 0,
                no_disponible INTEGER DEFAULT 0,
                motivo_no_disponible TEXT DEFAULT '',
                motivo_detalle TEXT DEFAULT '',
                conflicto INTEGER DEFAULT 0,
                ultima_asignacion TEXT,
                zona_counts TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS personal_disponibilidad_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id INTEGER,
                fecha_registro TEXT,
                motivo TEXT,
                detalle TEXT,
                disponible INTEGER,
                semana TEXT
            );
            CREATE TABLE IF NOT EXISTS operativos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                semana TEXT, fecha TEXT, tipo TEXT, nombre TEXT,
                direccion TEXT, municipio TEXT, provincia TEXT,
                zona_operativo TEXT, brigadas_requeridas INTEGER DEFAULT 1,
                fuente TEXT DEFAULT 'denuncia', no_oficio TEXT,
                estado TEXT DEFAULT 'pendiente',
                ejecutado INTEGER DEFAULT -1,
                resultado TEXT DEFAULT '',
                observaciones TEXT DEFAULT '',
                decomiso INTEGER DEFAULT 0,
                decomiso_detalle TEXT DEFAULT '',
                brigadas_json TEXT DEFAULT '[]',
                vehiculos_json TEXT DEFAULT '[]',
                seed TEXT, created_at TEXT,
                confirmed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS denuncias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no_oficio TEXT, fecha_entrada TEXT, tipo TEXT, nombre TEXT,
                sector TEXT, municipio TEXT, provincia TEXT, zona_inferida TEXT,
                estado TEXT DEFAULT 'pendiente', cargado_semana TEXT
            );
            CREATE TABLE IF NOT EXISTS semanas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                semana TEXT UNIQUE,
                vehiculos_disponibles INTEGER DEFAULT 6,
                militares_disponibles INTEGER DEFAULT 6,
                notas TEXT, estado TEXT DEFAULT 'borrador', created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS uploads_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT, semana TEXT, archivo TEXT,
                pendientes_cargadas INTEGER
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT, accion TEXT, detalle TEXT, referencia_id INTEGER
            );
        ''')
        # Migrations
        for col, defval in [
            ("motivo_no_disponible","TEXT DEFAULT ''"),
            ("motivo_detalle","TEXT DEFAULT ''"),
        ]:
            try: db.execute(f"ALTER TABLE personal_state ADD COLUMN {col} {defval}")
            except: pass
        for col, defval in [
            ("ejecutado","INTEGER DEFAULT -1"),
            ("observaciones","TEXT DEFAULT ''"),
            ("decomiso","INTEGER DEFAULT 0"),
            ("decomiso_detalle","TEXT DEFAULT ''"),
            ("vehiculos_json","TEXT DEFAULT '[]'"),
            ("confirmed_at","TEXT"),
        ]:
            try: db.execute(f"ALTER TABLE operativos ADD COLUMN {col} {defval}")
            except: pass
        try: db.execute("ALTER TABLE semanas ADD COLUMN militares_disponibles INTEGER DEFAULT 6")
        except: pass

        if db.execute('SELECT COUNT(*) as c FROM personal_state').fetchone()['c'] == 0:
            for p in PERSONAL:
                db.execute('INSERT INTO personal_state (persona_id, zona_counts) VALUES (?,?)', (p['id'],'{}'))

init_db()

def audit(accion, detalle, ref_id=None):
    with get_db() as db:
        db.execute('INSERT INTO audit_log (fecha,accion,detalle,referencia_id) VALUES (?,?,?,?)',
                   (datetime.now().isoformat(), accion, detalle, ref_id))

def get_state(pid):
    with get_db() as db:
        row = db.execute('SELECT * FROM personal_state WHERE persona_id=?',(pid,)).fetchone()
        return dict(row) if row else {"persona_id":pid,"carga_total":0,"no_disponible":0,
            "motivo_no_disponible":"","motivo_detalle":"","conflicto":0,
            "ultima_asignacion":None,"zona_counts":"{}"}

def zona_count(pid, zona):
    return json.loads(get_state(pid).get('zona_counts') or '{}').get(zona, 0)

def is_elegible(p, zona, fecha, skip_cooldown=False):
    st = get_state(p['id'])
    LOCAL = ["Distrito Nacional","SD Este","SD Norte","SD Oeste","San Cristóbal","San Cristóbal / Haina"]
    if zona in LOCAL and p['zona'] == zona: return False, ["Zona residencia"]
    if st['no_disponible']: return False, [st.get('motivo_no_disponible') or "No disponible"]
    if st['conflicto']: return False, ["Conflicto de interes"]
    if not skip_cooldown and st['ultima_asignacion']:
        try:
            ref = datetime.fromisoformat(fecha) if fecha else datetime.now()
            d = (ref - datetime.fromisoformat(st['ultima_asignacion'])).days
            if d < COOLDOWN_DAYS: return False, [f"Cooldown {d}/{COOLDOWN_DAYS}d"]
        except: pass
    return True, []

def select_fair(pool, n, zona):
    if not pool: return []
    scored = sorted([(zona_count(p['id'],zona), get_state(p['id'])['carga_total'], p) for p in pool], key=lambda x:(x[0],x[1]))
    if not scored: return []
    mn,mx = scored[0][0],scored[-1][0]; rng=mx-mn
    t = lambda zc: 1 if rng==0 else (1 if zc<=mn+rng/3 else (2 if zc<=mn+2*rng/3 else 3))
    t1=[x[2] for x in scored if t(x[0])==1]; random.shuffle(t1)
    t2=[x[2] for x in scored if t(x[0])==2]; random.shuffle(t2)
    t3=[x[2] for x in scored if t(x[0])==3]; random.shuffle(t3)
    return (t1+t2+t3)[:n]

def inferir_zona(prov, mun):
    p = str(prov).upper() if prov and str(prov).lower() not in ['nan','none',''] else ''
    m = str(mun).upper() if mun and str(mun).lower() not in ['nan','none',''] else ''
    if not p: return 'Sin especificar'
    if 'DAJABON' in p or 'DAJABÓN' in p: return 'Dajabón'
    if 'ESPAILLAT' in p: return 'Espaillat'
    if 'SAN JUAN' in p: return 'San Juan'
    if 'SAN PEDRO' in p: return 'San Pedro de Macorís'
    if 'SAN CRISTOBAL' in p or 'SAN CRISTÓBAL' in p:
        return 'San Cristóbal / Haina' if 'HAINA' in m or 'BAJOS' in m else 'San Cristóbal'
    if 'SANTO DOMINGO' in p:
        if 'NORTE' in m: return 'SD Norte'
        if 'ESTE' in m: return 'SD Este'
        if 'OESTE' in m: return 'SD Oeste'
        return 'Distrito Nacional'
    if 'DISTRITO NACIONAL' in p: return 'Distrito Nacional'
    for k,v in [('SANTIAGO','Santiago'),('LA VEGA','La Vega'),('PUERTO PLATA','Puerto Plata'),
                ('LA ROMANA','La Romana'),('BARAHONA','Barahona'),('PERAVIA','Baní / Peravia'),
                ('MONTE PLATA','Monte Plata'),('DUARTE','Duarte'),('SAMANA','Samaná'),
                ('ALTAGRACIA','La Altagracia'),('EL SEIBO','El Seibo'),('HATO MAYOR','Hato Mayor'),
                ('AZUA','Azua'),('ELIAS PIÑA','Elías Piña'),('VALVERDE','Valverde')]:
        if k in p: return v
    return prov.strip().title()

def dias_pendiente(fecha_str):
    try: return (datetime.now() - datetime.fromisoformat(str(fecha_str)[:10])).days
    except: return 0

# ── ROUTES ────────────────────────────────────────────────────
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/stats')
def api_stats():
    semana = datetime.now().strftime('%Y-W%V')
    with get_db() as db:
        pend = db.execute("SELECT COUNT(*) as c FROM denuncias WHERE estado='pendiente'").fetchone()['c']
        ops  = db.execute("SELECT COUNT(*) as c FROM operativos WHERE semana=?",(semana,)).fetchone()['c']
        brig = db.execute("SELECT COALESCE(SUM(brigadas_requeridas),0) as c FROM operativos WHERE semana=?",(semana,)).fetchone()['c']
        hist = db.execute("SELECT COUNT(*) as c FROM operativos WHERE estado='asignado'"  ).fetchone()['c']
        sem  = db.execute("SELECT * FROM semanas WHERE semana=?",(semana,)).fetchone()
    return jsonify(pendientes=pend,operativos=ops,brigadas=int(brig),historico=hist,
                   vehiculos=sem['vehiculos_disponibles'] if sem else 6,
                   militares=sem['militares_disponibles'] if sem else 6)

@app.route('/personal')
def personal_view():
    with get_db() as db:
        all_states = {row['persona_id']:dict(row) for row in
                      db.execute('SELECT * FROM personal_state').fetchall()}
        logs = [dict(r) for r in db.execute(
            "SELECT * FROM personal_disponibilidad_log ORDER BY fecha_registro DESC LIMIT 50").fetchall()]
    personal = []
    for p in PERSONAL:
        st = all_states.get(p['id'], {"persona_id":p['id'],"carga_total":0,"no_disponible":0,
            "motivo_no_disponible":"","motivo_detalle":"","conflicto":0,
            "ultima_asignacion":None,"zona_counts":"{}"})
        personal.append({**p, **st})
    return render_template('personal.html', personal=personal, cooldown=COOLDOWN_DAYS, logs=logs)

@app.route('/personal/update', methods=['POST'])
def personal_update():
    d = request.json; pid = d['id']
    with get_db() as db:
        st = db.execute('SELECT * FROM personal_state WHERE persona_id=?',(pid,)).fetchone()
        if not st:
            return jsonify(ok=True)
        nd = d.get('no_disponible', st['no_disponible'])
        motivo = d.get('motivo_no_disponible', st['motivo_no_disponible'] or '')
        detalle = d.get('motivo_detalle', st['motivo_detalle'] or '')
        ci = d.get('conflicto', st['conflicto'])
        db.execute('''UPDATE personal_state SET no_disponible=?,motivo_no_disponible=?,
                      motivo_detalle=?,conflicto=? WHERE persona_id=?''',
                   (nd, motivo, detalle, ci, pid))
        # Only log when availability actually changes
        if nd != st['no_disponible']:
            semana = datetime.now().strftime('%Y-W%V')
            db.execute('''INSERT INTO personal_disponibilidad_log
                (persona_id,fecha_registro,motivo,detalle,disponible,semana)
                VALUES (?,?,?,?,?,?)''',
                (pid, datetime.now().isoformat(), motivo, detalle, 1-nd, semana))
    return jsonify(ok=True)

@app.route('/personal/reset_carga', methods=['POST'])
def reset_carga():
    with get_db() as db:
        db.execute("UPDATE personal_state SET carga_total=0,zona_counts='{}'")
    audit('RESET_CARGA','Reset general de carga de todo el personal')
    return jsonify(ok=True)

@app.route('/denuncias')
def denuncias_view():
    with get_db() as db:
        rows = [dict(r) for r in db.execute("SELECT * FROM denuncias ORDER BY provincia,municipio").fetchall()]
        logs = [dict(r) for r in db.execute("SELECT * FROM uploads_log ORDER BY id DESC LIMIT 10").fetchall()]
    for r in rows:
        r['zona_inferida'] = inferir_zona(r['provincia'],r['municipio'])
        r['dias'] = dias_pendiente(r['fecha_entrada'])
    return render_template('denuncias.html', denuncias=rows, logs=logs)

@app.route('/denuncias/upload', methods=['POST'])
def denuncias_upload():
    if 'file' not in request.files: return jsonify(ok=False,error='No file'),400
    f = request.files['file']
    fname = secure_filename(f.filename)
    path = os.path.join(UPLOAD_FOLDER, fname); f.save(path)
    try:
        df = pd.read_excel(path); df.columns=[c.strip() for c in df.columns]
        rc = next(c for c in df.columns if 'RESOLUCION' in c.upper())
        tc = next(c for c in df.columns if 'TIPO' in c.upper())
        nc = next(c for c in df.columns if 'NOMBRE' in c.upper())
        sc = next(c for c in df.columns if 'SECTOR' in c.upper())
        mc = next(c for c in df.columns if 'MUNICIPIO' in c.upper())
        pc = next(c for c in df.columns if 'PROVINCIA' in c.upper())
        oc = next(c for c in df.columns if 'OFICIO MH' in c.upper())
        fc = next(c for c in df.columns if 'FECHA DE ENTRADA' in c.upper())
        pend = df[df[rc].astype(str).str.upper().str.contains('PENDIENTE',na=False)]
        semana = datetime.now().strftime('%Y-W%V')
        with get_db() as db:
            db.execute("DELETE FROM denuncias WHERE estado='pendiente'")
            for _,row in pend.iterrows():
                pv=str(row[pc]).strip() if pd.notna(row[pc]) else ''
                mu=str(row[mc]).strip() if pd.notna(row[mc]) else ''
                db.execute('INSERT INTO denuncias (no_oficio,fecha_entrada,tipo,nombre,sector,municipio,provincia,zona_inferida,estado,cargado_semana) VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (str(row[oc]),str(row[fc])[:10],str(row[tc]),str(row[nc]),
                     str(row[sc]) if pd.notna(row[sc]) else '',mu,pv,inferir_zona(pv,mu),'pendiente',semana))
            db.execute('INSERT INTO uploads_log (fecha,semana,archivo,pendientes_cargadas) VALUES (?,?,?,?)',
                       (datetime.now().strftime('%Y-%m-%d %H:%M'),semana,fname,len(pend)))
        audit('CARGA_EXCEL', f"Archivo: {fname} — {len(pend)} denuncias pendientes cargadas")
        return jsonify(ok=True,inserted=len(pend))
    except Exception as e: return jsonify(ok=False,error=str(e)),500

@app.route('/planificacion')
def planificacion_view():
    semana = datetime.now().strftime('%Y-W%V')
    # Build week days Mon-Fri
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    week_days = [(monday + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]
    with get_db() as db:
        dp = [dict(r) for r in db.execute("SELECT * FROM denuncias WHERE estado='pendiente' ORDER BY provincia,municipio").fetchall()]
        sr = db.execute("SELECT * FROM semanas WHERE semana=?",(semana,)).fetchone()
        ops = [dict(r) for r in db.execute("SELECT * FROM operativos WHERE semana=? ORDER BY fecha,id",(semana,)).fetchall()]
    grupos={}
    for d in dp:
        z=inferir_zona(d['provincia'],d['municipio']); grupos.setdefault(z,[]).append(d)
    # Build set of already-added zonas for this week
    zonas_agregadas = set()
    for o in ops:
        if o['zona_operativo']:
            zonas_agregadas.add(o['zona_operativo'])
    return render_template('planificacion.html',grupos=grupos,semana=semana,
                           semana_row=dict(sr) if sr else None,operativos=ops,
                           week_days=week_days, zonas_agregadas=list(zonas_agregadas))

@app.route('/planificacion/guardar_semana', methods=['POST'])
def guardar_semana():
    d=request.json
    with get_db() as db:
        db.execute('''INSERT INTO semanas (semana,vehiculos_disponibles,militares_disponibles,created_at)
                      VALUES (?,?,?,?) ON CONFLICT(semana) DO UPDATE SET
                      vehiculos_disponibles=?,militares_disponibles=?''',
                   (d['semana'],int(d.get('vehiculos',6)),int(d.get('militares',6)),
                    datetime.now().isoformat(),int(d.get('vehiculos',6)),int(d.get('militares',6))))
    audit('SEMANA', f"Semana {d['semana']}: {d.get('vehiculos',6)} vehiculos, {d.get('militares',6)} militares")
    return jsonify(ok=True)

@app.route('/planificacion/agregar_operativo', methods=['POST'])
def agregar_operativo():
    d=request.json
    br=2 if 'DEPORTIVA' in str(d.get('tipo','')).upper() else 1
    with get_db() as db:
        db.execute('''INSERT INTO operativos (semana,fecha,tipo,nombre,direccion,municipio,provincia,
                      zona_operativo,brigadas_requeridas,fuente,no_oficio,created_at)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (d['semana'],d.get('fecha',''),d.get('tipo',''),d.get('nombre',''),
                    d.get('direccion',''),d.get('municipio',''),d.get('provincia',''),
                    d.get('zona',''),br,d.get('fuente','denuncia'),d.get('no_oficio',''),
                    datetime.now().isoformat()))
    audit('OPERATIVO_AGREGADO', f"{d.get('nombre','')} — {d.get('provincia','')} — {d.get('fecha','')}")
    return jsonify(ok=True)

@app.route('/planificacion/eliminar_operativo/<int:oid>', methods=['DELETE'])
def eliminar_operativo(oid):
    with get_db() as db:
        op = db.execute("SELECT * FROM operativos WHERE id=?",(oid,)).fetchone()
        db.execute("DELETE FROM operativos WHERE id=?",(oid,))
    if op: audit('OPERATIVO_ELIMINADO', f"ID {oid}: {op['nombre']}", oid)
    return jsonify(ok=True)

@app.route('/asignacion')
def asignacion_view():
    semana=datetime.now().strftime('%Y-W%V')
    with get_db() as db:
        ops=[dict(r) for r in db.execute(
            "SELECT * FROM operativos WHERE semana=? ORDER BY CASE fuente WHEN 'orden_direccion' THEN 0 ELSE 1 END,fecha,id",
            (semana,)).fetchall()]
        sr=db.execute("SELECT * FROM semanas WHERE semana=?",(semana,)).fetchone()
        # Count available pool for display
        all_states={row['persona_id']:dict(row) for row in db.execute('SELECT * FROM personal_state').fetchall()}
    disponibles = sum(1 for p in PERSONAL if not all_states.get(p['id'],{}).get('no_disponible',0)
                      and not all_states.get(p['id'],{}).get('conflicto',0))
    tb=sum(o['brigadas_requeridas'] for o in ops)
    v=sr['vehiculos_disponibles'] if sr else 6
    m=sr['militares_disponibles'] if sr else 6
    return render_template('asignacion.html',operativos=ops,semana=semana,vehiculos=v,militares=m,
                           total_brigadas=tb,disponibles=disponibles)

@app.route('/asignacion/ejecutar', methods=['POST'])
def ejecutar_asignacion():
    d=request.json; semana=d['semana']; veh=int(d.get('vehiculos',6))
    fb=d.get('fecha_base',datetime.now().strftime('%Y-%m-%d'))
    with get_db() as db:
        ops=[dict(r) for r in db.execute(
            "SELECT * FROM operativos WHERE semana=? AND estado='pendiente' ORDER BY CASE fuente WHEN 'orden_direccion' THEN 0 ELSE 1 END,fecha,id",
            (semana,)).fetchall()]
    sel,used=[],0
    for o in ops:
        if used+o['brigadas_requeridas']<=veh: sel.append(o); used+=o['brigadas_requeridas']
    coords=[p for p in PERSONAL if p['cargo']=='COORDINADOR']
    insps =[p for p in PERSONAL if p['cargo']=='INSPECTOR']
    auxs  =[p for p in PERSONAL if p['cargo']=='AUXILIAR']
    arun=set(); aday={}; seed=secrets.token_hex(4).upper(); resultado=[]; cooldown_relajado=False
    for op in sel:
        zona=op['zona_operativo'] or inferir_zona(op['provincia'],op['municipio'])
        fecha=op['fecha'] or fb; bops=[]
        for b in range(op['brigadas_requeridas']):
            def pool(lst, skip_cd=False):
                return [p for p in lst if p['id'] not in arun
                        and (fecha not in aday or p['id'] not in aday[fecha])
                        and is_elegible(p,zona,fecha,skip_cooldown=skip_cd)[0]]
            # Try strict first
            cp=pool(coords); ip=pool(insps); ap=pool(auxs)
            # If any role has no candidates, relax cooldown
            if not cp or not ip or not ap:
                cp2=pool(coords,True); ip2=pool(insps,True); ap2=pool(auxs,True)
                if (cp2 or cp) and (ip2 or ip) and (ap2 or ap):
                    if not cp: cp=cp2; cooldown_relajado=True
                    if not ip: ip=ip2; cooldown_relajado=True
                    if not ap: ap=ap2; cooldown_relajado=True
            c=select_fair(cp,1,zona); i=select_fair(ip,1,zona); a=select_fair(ap,1,zona)
            bops.append({"num":b+1,"coordinador":c[0] if c else None,
                         "inspector":i[0] if i else None,"auxiliar":a[0] if a else None,
                         "cooldown_relajado":cooldown_relajado})
            for p in filter(None,[c[0] if c else None,i[0] if i else None,a[0] if a else None]):
                arun.add(p['id']); aday.setdefault(fecha,set()).add(p['id'])
        resultado.append({**op,'brigadas_asignadas':bops,'seed':seed,'cooldown_relajado':cooldown_relajado})
    audit('SORTEO', f"Semana {semana} — {len(resultado)} operativos sorteados — semilla {seed}")
    return jsonify(ok=True,resultado=resultado,seed=seed)

@app.route('/asignacion/confirmar', methods=['POST'])
def confirmar_asignacion():
    now = datetime.now().isoformat()
    with get_db() as db:
        for op in request.json['resultado']:
            db.execute("UPDATE operativos SET brigadas_json=?,seed=?,estado='asignado',confirmed_at=? WHERE id=?",
                       (json.dumps(op['brigadas_asignadas']),op.get('seed',''),now,op['id']))
            for b in op['brigadas_asignadas']:
                for role in ['coordinador','inspector','auxiliar']:
                    p=b.get(role)
                    if not p: continue
                    pid=p['id']; zona=op.get('zona_operativo','')
                    st=get_state(pid); zc=json.loads(st.get('zona_counts') or '{}')
                    zc[zona]=zc.get(zona,0)+1
                    db.execute('UPDATE personal_state SET carga_total=carga_total+1,ultima_asignacion=?,zona_counts=? WHERE persona_id=?',
                               (op.get('fecha',datetime.now().strftime('%Y-%m-%d')),json.dumps(zc),pid))
            audit('ASIGNACION_CONFIRMADA', f"Operativo ID {op['id']}: {op.get('nombre','')} — {op.get('fecha','')}", op['id'])
    return jsonify(ok=True)

@app.route('/operativo/resultado', methods=['POST'])
def guardar_resultado():
    d=request.json; oid=d['id']
    with get_db() as db:
        db.execute('''UPDATE operativos SET ejecutado=?,resultado=?,observaciones=?,
                      decomiso=?,decomiso_detalle=? WHERE id=?''',
                   (d.get('ejecutado',-1),d.get('resultado',''),d.get('observaciones',''),
                    d.get('decomiso',0),d.get('decomiso_detalle',''),oid))
        if d.get('cerrar_denuncia') and d.get('no_oficio'):
            db.execute("UPDATE denuncias SET estado='cerrada' WHERE no_oficio=?", (d['no_oficio'],))
    audit('RESULTADO', f"Operativo ID {oid}: {d.get('resultado','')} — Decomiso: {d.get('decomiso',0)}", oid)
    return jsonify(ok=True)

@app.route('/operativo/vehiculos', methods=['POST'])
def guardar_vehiculos_operativo():
    d=request.json
    with get_db() as db:
        db.execute("UPDATE operativos SET vehiculos_json=? WHERE id=?",
                   (json.dumps(d['vehiculos']), d['id']))
    audit('VEHICULOS_ACTUALIZADOS', f"Operativo ID {d['id']}", d['id'])
    return jsonify(ok=True)

@app.route('/plan_semanal')
def plan_semanal():
    semana=request.args.get('semana',datetime.now().strftime('%Y-W%V'))
    with get_db() as db:
        ops=[dict(r) for r in db.execute(
            "SELECT * FROM operativos WHERE semana=? AND estado='asignado' ORDER BY fecha,id",(semana,)).fetchall()]
        sr=db.execute("SELECT * FROM semanas WHERE semana=?",(semana,)).fetchone()
    for o in ops:
        o['brigadas']=json.loads(o['brigadas_json'] or '[]')
        o['vehiculos_data']=json.loads(o['vehiculos_json'] or '[]')
    return render_template('plan_semanal.html',operativos=ops,semana=semana,
                           semana_row=dict(sr) if sr else None)

@app.route('/ejecucion_diaria')
def ejecucion_diaria():
    fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    semana = datetime.now().strftime('%Y-W%V')
    with get_db() as db:
        ops=[dict(r) for r in db.execute(
            "SELECT * FROM operativos WHERE fecha=? AND estado='asignado' ORDER BY id",(fecha,)).fetchall()]
        # All assigned ops for the week for date picker
        all_ops=[dict(r) for r in db.execute(
            "SELECT DISTINCT fecha FROM operativos WHERE semana=? AND estado='asignado' ORDER BY fecha",(semana,)).fetchall()]
    for o in ops:
        o['brigadas']=json.loads(o['brigadas_json'] or '[]')
    return render_template('ejecucion_diaria.html', operativos=ops, fecha=fecha,
                           fechas_disponibles=[x['fecha'] for x in all_ops], semana=semana)

@app.route('/historial')
def historial_view():
    with get_db() as db:
        ops=[dict(r) for r in db.execute(
            "SELECT * FROM operativos WHERE estado='asignado' ORDER BY fecha DESC,id DESC").fetchall()]
    for o in ops: o['brigadas']=json.loads(o['brigadas_json'] or '[]')
    return render_template('historial.html', operativos=ops)

@app.route('/reportes')
def reportes_view():
    filtro = request.args.get('filtro','semana')
    valor  = request.args.get('valor', datetime.now().strftime('%Y-W%V'))
    with get_db() as db:
        if filtro=='dia':
            ops=[dict(r) for r in db.execute(
                "SELECT * FROM operativos WHERE fecha=? AND estado='asignado'",(valor,)).fetchall()]
        elif filtro=='mes':
            ops=[dict(r) for r in db.execute(
                "SELECT * FROM operativos WHERE substr(fecha,1,7)=? AND estado='asignado'",(valor,)).fetchall()]
        else:
            ops=[dict(r) for r in db.execute(
                "SELECT * FROM operativos WHERE semana=? AND estado='asignado'",(valor,)).fetchall()]
        denuncias_all=[dict(r) for r in db.execute("SELECT * FROM denuncias ORDER BY fecha_entrada").fetchall()]
        personal_states=[{**p,**get_state(p['id'])} for p in PERSONAL]
    for d in denuncias_all:
        d['dias']=dias_pendiente(d['fecha_entrada'])
        d['semaforo']='rojo' if d['dias']>90 else ('amarillo' if d['dias']>30 else 'verde')
    for o in ops: o['brigadas']=json.loads(o['brigadas_json'] or '[]')
    ejecutados = [o for o in ops if o.get('ejecutado')==1]
    no_ejecutados = [o for o in ops if o.get('ejecutado')==0]
    con_decomiso = [o for o in ops if o.get('decomiso')==1]
    with get_db() as db2:
        all_st = {r['persona_id']:dict(r) for r in db2.execute('SELECT * FROM personal_state').fetchall()}
    rendimiento=[]
    for p in PERSONAL:
        st = all_st.get(p['id'], {"carga_total":0,"ultima_asignacion":None,"zona_counts":"{}"})
        rendimiento.append({**p,'st':st})
    rendimiento.sort(key=lambda x:-x['st']['carga_total'])
    return render_template('reportes.html',
        ops=ops, ejecutados=ejecutados, no_ejecutados=no_ejecutados,
        con_decomiso=con_decomiso, denuncias=denuncias_all,
        rendimiento=rendimiento, filtro=filtro, valor=valor,
        total_pendientes=sum(1 for d in denuncias_all if d['estado']=='pendiente'))

@app.route('/mapa')
def mapa_view():
    with get_db() as db:
        denuncias=[dict(r) for r in db.execute("SELECT * FROM denuncias WHERE estado='pendiente'").fetchall()]
    puntos=[]
    for d in denuncias:
        zona=d['zona_inferida'] or inferir_zona(d['provincia'],d['municipio'])
        coords=PROV_COORDS.get(zona) or PROV_COORDS.get(d['provincia'])
        if coords:
            puntos.append({'lat':coords[0]+random.uniform(-0.05,0.05),
                           'lng':coords[1]+random.uniform(-0.05,0.05),
                           'nombre':d['nombre'],'tipo':d['tipo'],
                           'municipio':d['municipio'],'provincia':d['provincia'],
                           'zona':zona,'dias':dias_pendiente(d['fecha_entrada'])})
    return render_template('mapa.html', puntos=puntos)

if __name__=='__main__':
    port=int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port,debug=False)
