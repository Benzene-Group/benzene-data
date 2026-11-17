"""Build the Benzene project table from the TEC register, REPD and the CfD register.
Usage: python3 -I build.py TEC.csv REPD.csv CFD.csv OUTDIR PYPSA_DIR [TEC_DATE]
"""
import math, csv, sys, io, re, json, collections, datetime as dt, difflib, statistics, os
TEC, REPD, CFD, OUT, PYPSA = sys.argv[1:6]
SUBS = PYPSA + '/data/network/ETYS/substation_coordinates.csv'; ZONES = PYPSA + '/data/network/zonal/zones.geojson'
GSPS = [PYPSA + f'/data/network/ETYS/fes{y}_regional_breakdown_gsp_info.csv' for y in (2025, 2024, 2023, 2022, 2021)]
DUKES = PYPSA + '/data/generators/dukes_power_station_coordinates.csv'
import pyproj
TO_OSGB = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:27700', always_xy=True)
TODAY = dt.date.today()
# Register date from argument 7, else from the NESO file name (e.g. tec-register-13-november-2026.csv)
_m = re.search(r'(\d{1,2})-([a-z]+)-(\d{4})', os.path.basename(TEC).lower())
TEC_DATE = sys.argv[6] if len(sys.argv) > 6 else (f'{int(_m.group(1))} {_m.group(2).capitalize()} {_m.group(3)}' if _m else TODAY.strftime('%d %B %Y').lstrip('0'))

def read(p, enc):
    return list(csv.DictReader(io.StringIO(open(p, 'rb').read().decode(enc))))
tec = read(TEC, 'utf-8-sig'); repd = read(REPD, 'cp1252'); cfd = read(CFD, 'utf-8-sig')
num = lambda s: float(str(s).replace(',', '')) if str(s).strip() not in ('', 'NA') else 0.0
def pdate(s):
    s = (s or '').strip()
    if not s: return None
    try: return dt.datetime.strptime(s, '%d/%m/%Y').date()
    except ValueError: return None

GAS = {'CCGT (Combined Cycle Gas Turbine)', 'OCGT (Open Cycle Gas Turbine)', 'Gas Reciprocating',
       'CHP (Combined Heat and Power)', 'Thermal', 'Oil & AGT (Advanced Gas Turbine)'}
WATER = {'Hydro', 'Pump Storage', 'Tidal'}
ESS, PV, WON, WOFF = 'Energy Storage System', 'PV Array (Photo Voltaic/solar)', 'Wind Onshore', 'Wind Offshore'
def tech(pt):
    t = set(x.strip() for x in pt.split(';'))
    demand = 'Demand' in t
    core = t - {'Demand', 'Reactive Compensation', 'Substation'}
    if WOFF in core: k = 'Offshore wind'
    elif core == {ESS}: k = 'Battery storage'
    elif core == {PV}: k = 'Solar'
    elif core == {ESS, PV}: k = 'Solar + storage'
    elif core == {WON}: k = 'Onshore wind'
    elif core == {ESS, WON}: k = 'Onshore wind + storage'
    elif core and core <= GAS: k = 'Gas and thermal'
    elif core == {'Nuclear'}: k = 'Nuclear'
    elif core and core <= WATER: k = 'Hydro, pumped storage and tidal'
    elif not core: k = 'Demand or network only'
    else: k = 'Mixed and other'
    return k, demand, (ESS in core)

# ---------- projects ----------
by = collections.OrderedDict()
for r in tec: by.setdefault(r['Project ID'], []).append(r)
projects = []
for pid, rows in by.items():
    r0 = rows[0]
    k, demand, has_storage = tech(r0['Plant Type'])
    unbuilt = [r for r in rows if r['Project Status'] != 'Built']
    connected = sum(num(r['MW Connected']) for r in rows)
    queued = sum(num(r['MW Increase / Decrease']) for r in unbuilt)
    dates = sorted(d for d in (pdate(r['MW Effective From']) for r in unbuilt) if d)
    gates = sorted(set(r['Gate'].strip() for r in unbuilt if r['Gate'].strip()))
    statuses = [r['Project Status'] for r in unbuilt] or [r['Project Status'] for r in rows]
    order = ['Under Construction/Commissioning', 'Consents Approved', 'Awaiting Consents', 'Scoping', 'Built']
    status = sorted(set(statuses), key=order.index)[0]
    projects.append(dict(
        id=pid, numbers=';'.join(r['Project Number'] for r in rows), name=r0['Project Name'].strip(),
        customer=r0['Customer Name'].strip(), site=r0['Connection Site'].strip(), to=r0['HOST TO'],
        agreement=r0['Agreement Type'], plant_type=r0['Plant Type'], tech=k, demand=demand, has_storage=has_storage,
        connected_mw=round(connected, 2), queued_mw=round(queued, 2), stages=len(rows),
        first_date=dates[0].isoformat() if dates else '', last_date=dates[-1].isoformat() if dates else '',
        gate='/'.join(gates) if gates else '', status=status, built=not unbuilt))

# ---------- name matching ----------
DROP = r"\b(wind ?farm|windfarm|wind park|wind energy project|solar farm|solar park|solar pv|solar project|solar|pv|bess|battery energy storage system|battery storage|energy storage|storage|battery|energy park|renewable energy park|energy centre|energy hub|energy project|limited|ltd|llp|plc|the|and|project|farm|park|ext|extension|phase \d+|stage \d+|\d+ ?mw)\b"
def norm(s):
    s = s.lower().replace('&', ' and ')
    s = re.sub(r"[^a-z0-9 ]", ' ', s)
    s = re.sub(DROP, ' ', s)
    return re.sub(r'\s+', ' ', s).strip()
def raw(s): return re.sub(r'\s+', ' ', re.sub(r"[^a-z0-9 ]", ' ', s.lower())).strip()

REPD_TECH = {'Solar Photovoltaics': {'Solar', 'Solar + storage', 'Mixed and other'},
             'Battery': {'Battery storage', 'Solar + storage', 'Onshore wind + storage', 'Mixed and other'},
             'Wind Onshore': {'Onshore wind', 'Onshore wind + storage', 'Mixed and other'},
             'Wind Offshore': {'Offshore wind'},
             'Pumped Storage Hydroelectricity': {'Hydro, pumped storage and tidal'},
             'Large Hydro': {'Hydro, pumped storage and tidal'}, 'Small Hydro': {'Hydro, pumped storage and tidal'},
             'Tidal Stream': {'Hydro, pumped storage and tidal'}, 'Tidal Lagoon': {'Hydro, pumped storage and tidal'},
             'Tidal Barrage and Tidal Stream': {'Hydro, pumped storage and tidal'},
             'Biomass (dedicated)': {'Gas and thermal', 'Mixed and other'}, 'Biomass (co-firing)': {'Gas and thermal', 'Mixed and other'},
             'Nuclear': {'Nuclear'}}
DEAD = {'Planning Permission Refused', 'Planning Application Withdrawn', 'Abandoned', 'Revised', 'Planning Permission Expired',
        'Appeal Refused', 'Appeal Withdrawn', 'Decommissioned', 'Secretary of State - Refusal'}
repd_idx = collections.defaultdict(list); repd_raw = collections.defaultdict(list)
for i, r in enumerate(repd):
    if r['Country'] == 'Northern Ireland': continue
    n = norm(r['Site Name'])
    if n: repd_idx[n].append(i)
    repd_raw[raw(r['Site Name'])].append(i)
def best(cands, p):
    ok = [i for i in cands if p['tech'] in REPD_TECH.get(repd[i]['Technology Type'], set())]
    if not ok: return None, 0
    target = p['queued_mw'] + p['connected_mw']
    def score(i):
        r = repd[i]; cap = num(r['Installed Capacity (MWelec)'])
        live = 0 if r['Development Status'] in DEAD else 1
        close = -abs(cap - target) / max(target, 1) if cap else -1
        return (live, close)
    ok.sort(key=score, reverse=True)
    return ok[0], len(ok)
for p in projects:
    p.update(repd_ref='', repd_match='', repd_status='', repd_authority='', repd_planning_ref='', repd_mw='', x='', y='', repd_site='', repd_expiry='', repd_cfd='')
    i, n = best(repd_raw.get(raw(p['name']), []), p); q = 'exact name'
    if i is None:
        nn = norm(p['name'])
        if len(nn) >= 5:
            i, n = best(repd_idx.get(nn, []), p); q = 'name after removing generic words'
    if i is None: continue
    r = repd[i]
    p.update(repd_ref=r['Ref ID'], repd_match=q + ('' if n == 1 else f' ({n} candidates, closest capacity)'),
             repd_status=r['Development Status'], repd_authority=r['Planning Authority'], repd_planning_ref=r['Planning Application Reference'],
             repd_mw=r['Installed Capacity (MWelec)'], x=r['X-coordinate'].replace(',', ''), y=r['Y-coordinate'].replace(',', ''),
             repd_site=r['Site Name'], repd_expiry=r['Planning Permission Expired'], repd_cfd=r['CfD Allocation Round'])

# ---------- CfD ----------
cfd_idx = collections.defaultdict(list)
for c in cfd:
    cfd_idx[raw(c['Name_of_CFD_Unit'])].append(c)
    n = norm(c['Name_of_CFD_Unit'])
    if len(n) >= 5 and n != raw(c['Name_of_CFD_Unit']): cfd_idx['~' + n].append(c)
CFD_TECH = {'Onshore Wind': {'Onshore wind', 'Onshore wind + storage'}, 'Remote Island Wind': {'Onshore wind', 'Onshore wind + storage'},
            'Solar PV': {'Solar', 'Solar + storage'}, 'Offshore Wind': {'Offshore wind'}, 'Floating Offshore Wind': {'Offshore wind'},
            'Tidal Stream': {'Hydro, pumped storage and tidal'}, 'Nuclear': {'Nuclear'}}
for p in projects:
    p.update(cfd_ids='', cfd_round='', cfd_status='', cfd_start='', cfd_mw='', cfd_match='', cfd_names='')
    for key, q in ((raw(p['name']), 'exact name'), ('~' + norm(p['name']), 'name after removing generic words')):
        cs = [c for c in cfd_idx.get(key, []) if p['tech'] in CFD_TECH.get(c['Technology_Type'], {p['tech']})]
        if not cs: continue
        mw = sum(num(c['Maximum_Contract_Capacity_MW']) for c in cs); tot = p['queued_mw'] + p['connected_mw']
        if not tot or not (0.65 <= mw / tot <= 1.5): continue
        p.update(cfd_ids=';'.join(c['CFD_ID'] for c in cs), cfd_round=';'.join(sorted(set(c['Allocation_Round'].replace('Allocation Round ', 'AR') for c in cs))),
                 cfd_status=';'.join(sorted(set(c['Status'] for c in cs))), cfd_names=';'.join(c['Name_of_CFD_Unit'] for c in cs),
                 cfd_start=min((c['Expected_Start_Date'][:10] for c in cs if c['Expected_Start_Date']), default=''),
                 cfd_mw=round(mw, 2), cfd_match=q)
        break

# ---------- sites ----------
def place(site):
    s = re.sub(r"\b(\d+(\.\d+)?\s*kv|substation|gsp|grid supply point|s/s|sgt\d*|bsp|\d+)\b", ' ', site, flags=re.I)
    return re.sub(r'\s+', ' ', re.sub(r"[^A-Za-z' -]", ' ', s)).strip()
addr_words = []
for r in repd:
    if r['Country'] == 'Northern Ireland' or r['Technology Type'] == 'Wind Offshore': continue
    try: x, y = float(r['X-coordinate'].replace(',', '')), float(r['Y-coordinate'].replace(',', ''))
    except ValueError: continue
    addr_words.append((' ' + raw(r['Address'] + ' ' + r['Site Name']) + ' ', x, y))
sites = collections.OrderedDict()
for p in projects:
    s = sites.setdefault(p['site'], dict(site=p['site'], to=p['to'], projects=[]))
    s['projects'].append(p)
def med_cluster(pts):
    if not pts: return None
    mx, my = statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts)
    near = [p for p in pts if abs(p[0] - mx) < 25000 and abs(p[1] - my) < 25000]
    if not near: return None
    return statistics.median(p[0] for p in near), statistics.median(p[1] for p in near), len(near), len(pts)
SITE_EXTRA = {'north', 'south', 'east', 'west', 'new', 'near', 'a', 'b', 'c', 'd', 'main', 'gis', 'extension', 'busbar', 'storage', 'bess', 'battery', 'solar', 'energy', 'station', 'switching', 'collector', 'psh', 'wind', 'ii', 'idno', 'spd', 'sepd', 'and'}
GAZ_EXTRA = {'wind', 'farm', 'windfarm', 'sse', 'main', 'gis', 'extension'}
gaz = {}
for r in csv.DictReader(open(SUBS, encoding='utf-8-sig')):
    try: x, y = TO_OSGB.transform(float(r['lon']), float(r['lat']))
    except ValueError: continue
    gaz[raw(r['site_name'])] = (x, y, 'substation coordinate list in the open PyPSA-GB dataset')
for g in GSPS:
    for r in csv.DictReader(open(g, encoding='utf-8-sig')):
        try: x, y = TO_OSGB.transform(float(r['Longitude']), float(r['Latitude']))
        except (ValueError, KeyError): continue
        gaz.setdefault(raw(r['Name']), (x, y, 'grid supply point location in the open PyPSA-GB dataset'))
stations = {}
for r in csv.DictReader(open(DUKES, encoding='utf-8-sig')):
    try: stations.setdefault(raw(r['station_name']), (float(r['x_coordinate']), float(r['y_coordinate'])))
    except ValueError: pass
def area_ok(to, x, y):
    scot = y > 566000 + max(0, x - 330000) * 1.31
    if to == 'NGET': return not scot
    if to == 'SPT': return scot and y <= 745000 and x >= 200000
    if to == 'SHET': return scot and (y >= 690000 or x < 230000)
    return True
AMBIGUOUS = {'coddington', 'hope', 'oakley', 'newchurch', 'andrew'}
# Positions placed by hand from the place name, for large sites no list covers. Rough: may be 15 km out.
HAND = {'longside': (403700, 847300), 'branxton': (374500, 673000), 'banniskirk': (316500, 957500), 'hurlie': (380000, 788000), 'greens': (382000, 846000),
        'northern shetland': (445000, 1180000), 'earba powerhouse': (247000, 782000), 'glen earrach': (245000, 828000), 'arnish lewis': (142500, 930500),
        'pont abraham': (257500, 207000), 'botley': (445000, 207000), 'farmoor': (444500, 206500), 'cousland': (337500, 668500), 'balliemeanoch': (201000, 715000),
        'loch kemp': (246500, 816500), 'loch na cathrach': (260000, 833000), 'thormanby': (449500, 474500), 'tideford': (234500, 59500), 'llanteg': (218000, 210000),
        'harlaston': (421500, 311000), 'birkhill wood': (502000, 434000), 'redshaw': (286000, 628000), 'wyseby hill': (324500, 572500), 'devilla': (295500, 688500),
        'auchentiber': (236500, 647500), 'friston': (641000, 260500), 'bishopbriggs': (261400, 670400), 'kirkby': (340900, 398700),
        'iver': (504200, 179000), 'jersey farm': (517700, 209300)}
HAND_DROP = SITE_EXTRA | {'farm', 'hub', 'psh', 'pump', 'hydro', 'storage', 'powerhouse', 'substation', 'station', 'natpower', 'green', 'park'}
REGIONS = {  # connection-node region -> (planning database counties, optional half: N S E W or two letters)
    'trent valley south': (['Nottinghamshire', 'Leicestershire'], ''), 'trent valley north': (['Nottinghamshire', 'Lincolnshire'], 'N'),
    'west anglia': (['Cambridgeshire', 'Bedfordshire'], ''), 'north anglia': (['Norfolk'], ''), 'south anglia': (['Essex', 'Suffolk'], ''),
    'derbyshire': (['Derbyshire'], ''), 'cheshire': (['Cheshire'], ''), 'teeside': (['Cleveland'], ''), 'sussex and romney': (['East Sussex'], 'E'),
    'wearside': (['Tyne And Wear', 'County Durham'], ''), 'east kent': (['Kent'], 'E'), 'north kent': (['Kent'], 'N'), 'chiltern': (['Buckinghamshire', 'Hertfordshire'], ''),
    'leeds north': (['West Yorkshire'], 'N'), 'leeds south': (['West Yorkshire'], 'S'), 'south wales west': (['Dyfed', 'West Glamorgan', 'Carmarthenshire', 'Pembrokeshire'], ''),
    'south wales east': (['Gwent', 'Mid Glamorgan', 'South Glamorgan'], ''), 'north humber': (['East Riding of Yorkshire'], ''), 'south humber': (['Humberside'], 'S'),
    'west country': (['Somerset'], ''), 'solent': (['Hampshire'], 'S'), 'london north west': (['London'], 'NW'), 'london north east': (['London'], 'NE'),
    'london south': (['London'], 'S'), 'london west': (['London'], 'W'), 'west london': (['London'], 'W'), 'warwickshire': (['Warwickshire'], ''),
    'severn': (['Gloucestershire', 'Avon'], ''), 'lincolnshire coastal': (['Lincolnshire'], 'E'), 'north wales': (['Clwyd', 'Gwynedd'], ''), 'merseyside': (['Merseyside'], ''),
    'lancashire': (['Lancashire'], ''), 'manchester south': (['Greater Manchester'], 'S'), 'staffordshire': (['Staffordshire'], ''), 'borders': (['Borders', 'Scottish Borders'], ''),
    'mid wales': (['Powys'], '')}
OFF_ALIAS = {'east anglia three': 'East Anglia 3 (EA 3)', 'east anglia two': 'East Anglia 2 (EA 2)', 'five estuaries offshore wind farm': 'Five Estuaries - Wind Farm'}
off_xy = {}
for r in repd:
    if r['Technology Type'] == 'Wind Offshore':
        try: off_xy[r['Site Name'].strip()] = (float(r['X-coordinate'].replace(',', '')), float(r['Y-coordinate'].replace(',', '')))
        except ValueError: pass
county_pts = collections.defaultdict(list)
for r in repd:
    if r['Technology Type'] == 'Wind Offshore': continue
    try: county_pts[r['County'].strip().lower()].append((float(r['X-coordinate'].replace(',', '')), float(r['Y-coordinate'].replace(',', ''))))
    except ValueError: pass
def region_centre(key):
    counties, half = REGIONS[key]
    pts = [q for c in counties for q in county_pts.get(c.lower(), [])]
    if not pts: return None
    for h in half:
        mx, my = statistics.median(q[0] for q in pts), statistics.median(q[1] for q in pts)
        pts = [q for q in pts if (h == 'N' and q[1] >= my) or (h == 'S' and q[1] <= my) or (h == 'E' and q[0] >= mx) or (h == 'W' and q[0] <= mx)]
    return statistics.median(q[0] for q in pts), statistics.median(q[1] for q in pts)
def node_region(site):
    m = re.split(r'\s+(?:connection\s+|coastal\s+)?node\b', site, flags=re.I)
    if len(m) < 2: return None
    k = raw(m[0].split('(')[-1])
    k = {'erbyshire': 'derbyshire'}.get(k, k)
    if 'coastal' in site.lower() and k == 'lincolnshire': k = 'lincolnshire coastal'
    return k if k in REGIONS else None
def big_cluster(hits):
    if not hits: return None
    best = None
    for h in hits:
        near = [q for q in hits if abs(q[0] - h[0]) < 25000 and abs(q[1] - h[1]) < 25000]
        if best is None or len(near) > len(best): best = near
    if len(best) * 2 < len(hits): return None
    return statistics.median(q[0] for q in best), statistics.median(q[1] for q in best), len(best), len(hits)
ring = collections.Counter()
for s in sites.values():
    ps = s['projects']; un = [p for p in ps if not p['built']]
    s['n_projects'] = len(ps); s['n_queued'] = len([p for p in un if p['queued_mw'] > 0]); s['customers'] = len(set(p['customer'] for p in un))
    s['connected_mw'] = round(sum(p['connected_mw'] for p in ps), 1); s['queued_mw'] = round(sum(p['queued_mw'] for p in ps), 1)
    for g, key in (('1', 'gate1_mw'), ('2', 'gate2_mw'), ('', 'nogate_mw')):
        s[key] = round(sum(p['queued_mw'] for p in ps if p['gate'] == g), 1)
    s['mixedgate_mw'] = round(s['queued_mw'] - s['gate1_mw'] - s['gate2_mw'] - s['nogate_mw'], 1)
    tm = collections.Counter()
    for p in ps: tm[p['tech']] += p['queued_mw']
    s['tech_mw'] = {k: round(v, 1) for k, v in tm.most_common() if v > 0}
    w = [(p['queued_mw'], (dt.date.fromisoformat(p['first_date']) - TODAY).days / 365.25) for p in un if p['first_date'] and p['queued_mw'] > 0]
    s['wait_years'] = round(sum(a * b for a, b in w) / sum(a for a, _ in w), 1) if w else ''
    s['first_date'] = min((p['first_date'] for p in un if p['first_date']), default=''); s['last_date'] = max((p['last_date'] for p in un if p['last_date']), default='')
    s['x'] = s['y'] = ''; s['loc_basis'] = ''; s['loc_q'] = ''; s['region'] = ''
    def put(x, y, basis, q): s['x'], s['y'], s['loc_basis'], s['loc_q'] = round(x), round(y), basis, q
    low = s['site'].lower(); is_node = bool(re.search(r'\bnode\b', low)); is_off = 'offshore' in low or 'platform' in low
    pts = [(float(p['x']), float(p['y'])) for p in ps if p['x'] and p['tech'] != 'Offshore wind']
    c = med_cluster(pts)
    pl0 = '' if (is_node or is_off) else raw(place(s['site']))
    pl0g = pl0; core = ''
    if pl0:
        base = re.sub(r'\b(wind farm|windfarm|solar farm)\b', ' ', pl0)
        core = ' '.join(t for t in base.split() if t not in SITE_EXTRA)
        if pl0 not in gaz:
            pl0g = ''
            if core in gaz: pl0g = core
            elif core:
                pre = [k for k in gaz if k.startswith(core + ' ') and all(t in GAZ_EXTRA or re.fullmatch(r'\d+(kv)?', t) for t in k[len(core):].split())]
                pl0g = pre[0] if len(pre) == 1 else ''
    if pl0g in gaz and (not c or abs(gaz[pl0g][0] - c[0]) < 40000 and abs(gaz[pl0g][1] - c[1]) < 40000):
        put(gaz[pl0g][0], gaz[pl0g][1], gaz[pl0g][2] + ('' if pl0g == pl0 else f', matched as "{pl0g.title()}"'), 'a')
    elif c: put(c[0], c[1], f'{c[2]} matched project location{"s" if c[2] > 1 else ""} in the planning database', 'a' if c[2] >= 2 else 'r')
    if s['x'] == '' and core:
        hk = ' '.join(t for t in core.split() if t not in HAND_DROP)
        for k in (core, hk):
            if k in HAND and area_ok(s['to'], *HAND[k]): put(HAND[k][0], HAND[k][1], f'placed by hand from the place name "{k.title()}"', 'r'); break
    if s['x'] == '' and core and len(core) >= 5 and core not in AMBIGUOUS:
        hits = [(x, y) for a, x, y in addr_words if f' {core} ' in a and area_ok(s['to'], x, y)]; bc = big_cluster(hits)
        if bc and (bc[2] >= 2 or not core.endswith(' farm')):
            put(bc[0], bc[1], f'{bc[2]} planning database address{"es" if bc[2] > 1 else ""} naming "{core.title()}"', 'a' if bc[2] >= 2 and bc[2] >= 0.6 * bc[3] else 'r')
    if s['x'] == '' and core in stations and core not in AMBIGUOUS and area_ok(s['to'], *stations[core]):
        put(stations[core][0], stations[core][1], f'a power station named "{core.title()}" in the government power station list', 'r')
    if s['x'] == '' and not is_node:
        for p in sorted(ps, key=lambda p: -p['queued_mw']):
            nn = norm(p['name'])
            if len(nn) < 6 or nn in AMBIGUOUS: continue
            hits = [(x, y) for a, x, y in addr_words if f' {nn} ' in a and area_ok(s['to'], x, y)]; bc = big_cluster(hits)
            if bc: put(bc[0], bc[1], f'planning database address naming the project "{p["name"]}"', 'r'); break
    if s['x'] == '' and is_off:
        for p in ps:
            al = OFF_ALIAS.get(raw(p['name']))
            if al and al in off_xy: put(off_xy[al][0], off_xy[al][1], f'planning database location of the offshore wind project "{al}"', 'r'); break
    if s['x'] == '' and is_off:
        op = [(float(p['x']), float(p['y'])) for p in ps if p['x']]
        if op: put(statistics.median(q[0] for q in op), statistics.median(q[1] for q in op), 'location of the matched offshore wind project in the planning database', 'r')
    if is_node:
        k = node_region(s['site'])
        if k:
            s['region'] = k.title().replace('Teeside', 'Teesside')
            rc = region_centre(k)
            if rc and s['x'] != '':
                if math.hypot(s['x'] - rc[0], s['y'] - rc[1]) > 60000: s['x'] = s['y'] = ''
                else: s['loc_q'] = 'r'; s['loc_basis'] = 'planning database location of a project queued at this node. The register gives only a region'
            if rc and s['x'] == '':
                i = ring[k]; ring[k] += 1; ang = i * 2.399963; rr = 4000 + 3500 * math.sqrt(i)
                put(rc[0] + rr * math.cos(ang), rc[1] + rr * math.sin(ang), f'the register gives only a region. Placed near the centre of planning records in {" and ".join(REGIONS[k][0])}', 'r')

os.makedirs(OUT, exist_ok=True)
pf = ['id', 'numbers', 'name', 'customer', 'site', 'to', 'agreement', 'plant_type', 'tech', 'demand', 'has_storage', 'connected_mw', 'queued_mw', 'stages',
      'first_date', 'last_date', 'gate', 'status', 'built', 'repd_ref', 'repd_match', 'repd_site', 'repd_status', 'repd_authority', 'repd_planning_ref', 'repd_mw',
      'repd_expiry', 'repd_cfd', 'x', 'y', 'cfd_ids', 'cfd_names', 'cfd_match', 'cfd_round', 'cfd_status', 'cfd_start', 'cfd_mw']
with open(f'{OUT}/projects.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, pf); w.writeheader(); w.writerows(projects)
sf = ['site', 'to', 'n_projects', 'n_queued', 'customers', 'connected_mw', 'queued_mw', 'gate2_mw', 'gate1_mw', 'nogate_mw', 'mixedgate_mw', 'wait_years', 'first_date', 'last_date', 'x', 'y', 'loc_q', 'region', 'loc_basis']
with open(f'{OUT}/sites.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, sf, extrasaction='ignore'); w.writeheader(); w.writerows(sites.values())
json.dump(dict(projects=projects, sites=[{k: v for k, v in s.items() if k != 'projects'} for s in sites.values()]), open(f'{OUT}/table.json', 'w'))

zones = json.load(open(ZONES))
outline = []
for f in zones['features']:
    if not f['properties']['Name_1'].startswith('Z'): continue
    g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        ring = [TO_OSGB.transform(lon, lat) for lon, lat in poly[0]]
        ring = [[round(x / 100) * 100, round(y / 100) * 100] for x, y in ring]
        dd = [ring[0]]
        for q in ring[1:]:
            if q != dd[-1]: dd.append(q)
        if len(dd) >= 4: outline.append(dd)
json.dump(outline, open(f'{OUT}/outline.json', 'w'), separators=(',', ':'))
print('outline rings', len(outline), 'points', sum(len(r) for r in outline))
# ---------- platform data ----------
yr = collections.defaultdict(lambda: collections.Counter())
for r in tec:
    if r['Project Status'] == 'Built': continue
    d = pdate(r['MW Effective From']); mw = num(r['MW Increase / Decrease'])
    if not mw: continue
    y = 'No date' if not d else ('2026 or earlier' if d.year <= 2026 else str(d.year))
    yr[y][r['Gate'].strip() or 'none'] += mw
def wavg(pp):
    w = [(p['queued_mw'], max(0, (dt.date.fromisoformat(p['first_date']) - TODAY).days / 365.25)) for p in pp if p['first_date'] and p['queued_mw'] > 0]
    return round(sum(a * b for a, b in w) / sum(a for a, _ in w), 1) if w else None
unb = [p for p in projects if not p['built'] and p['queued_mw'] > 0]
TO_NAME = {'NGET': 'England and Wales (NGET)', 'SPT': 'Central and southern Scotland (SPT)', 'SHET': 'Northern Scotland (SHET)', 'OFTO': 'Offshore links (OFTO)'}
plat = dict(
    tec_date=TEC_DATE, built=TODAY.isoformat(),
    head=dict(connected=round(sum(p['connected_mw'] for p in projects)), queued=round(sum(p['queued_mw'] for p in unb)), projects=len(unb), sites=len(set(p['site'] for p in unb)),
              gate2=round(sum(p['queued_mw'] for p in unb if p['gate'] == '2')), gate1=round(sum(p['queued_mw'] for p in unb if p['gate'] == '1')), nogate=round(sum(p['queued_mw'] for p in unb if p['gate'] == '')),
              n_gate2=sum(1 for p in unb if p['gate'] == '2'), n_gate1=sum(1 for p in unb if p['gate'] == '1'), n_nogate=sum(1 for p in unb if p['gate'] == ''),
              storage=round(sum(p['queued_mw'] for p in unb if p['has_storage'])), wait=wavg(unb), wait_g2=wavg([p for p in unb if p['gate'] == '2']), wait_g1=wavg([p for p in unb if p['gate'] == '1']),
              repd_matched=sum(1 for p in unb if p['repd_ref'])),
    years=[dict(y=y, g2=round(v['2']), g1=round(v['1']), none=round(v['none'])) for y, v in sorted(yr.items(), key=lambda kv: (kv[0] == 'No date', kv[0] != '2026 or earlier', kv[0]))],
    regions=[dict(name=TO_NAME[t], queued=round(sum(p['queued_mw'] for p in unb if p['to'] == t)), connected=round(sum(p['connected_mw'] for p in projects if p['to'] == t)),
                  n=sum(1 for p in unb if p['to'] == t), wait=wavg([p for p in unb if p['to'] == t])) for t in ('NGET', 'SPT', 'SHET', 'OFTO')],
    tech=[dict(name=k, mw=round(v), n=sum(1 for p in unb if p['tech'] == k)) for k, v in collections.Counter({k: sum(p['queued_mw'] for p in unb if p['tech'] == k) for k in set(p['tech'] for p in unb)}).most_common()],
    sites=[], cfd=[])
for s_ in sorted(sites.values(), key=lambda s: -s['queued_mw']):
    pp = sorted([p for p in s_['projects'] if not p['built'] and p['queued_mw'] > 0], key=lambda p: (p['first_date'] or '9999', -p['queued_mw']))
    if not pp: continue
    plat['sites'].append(dict(n=s_['site'], to=s_['to'], x=s_['x'], y=s_['y'], b=s_['loc_basis'], lq=s_['loc_q'], rg=s_['region'], c=round(s_['connected_mw']), q=round(s_['queued_mw']),
        g2=round(s_['gate2_mw']), g1=round(s_['gate1_mw']), gn=round(s_['nogate_mw']), w=wavg(pp), k=len(set(p['customer'] for p in pp)),
        t=[[k, round(v)] for k, v in s_['tech_mw'].items()][:4],
        p=[[p['name'], p['customer'], p['tech'], round(p['queued_mw'], 1), p['first_date'], p['status'], p['gate'], p['repd_status']] for p in pp]))
for p in sorted(projects, key=lambda p: p['name']):
    if p['cfd_ids'] and not p['built']:
        plat['cfd'].append(dict(name=p['name'], customer=p['customer'], site=p['site'], tech=p['tech'], mw=p['queued_mw'], date=p['first_date'], gate=p['gate'], status=p['status'],
                                cfd_names=p['cfd_names'], cfd_ids=p['cfd_ids'], cfd_round=p['cfd_round'], cfd_status=p['cfd_status'], cfd_start=p['cfd_start'], cfd_mw=p['cfd_mw'], match=p['cfd_match']))
LIVE = {'Operational': 'o', 'Awaiting Construction': 'c', 'Under Construction': 'c', 'Application Submitted': 'p', 'Appeal Lodged': 'p'}
plan = {'o': [], 'c': [], 'p': []}
for r in repd:
    k = LIVE.get(r['Development Status (short)'].strip())
    if not k or r['Country'] == 'Northern Ireland' or r['Mounting Type for Solar'] == 'Roof' or num(r['Installed Capacity (MWelec)']) < 1: continue
    try: plan[k] += [round(float(r['X-coordinate'].replace(',', '')) / 100), round(float(r['Y-coordinate'].replace(',', '')) / 100)]
    except ValueError: pass
plat['plan'] = plan; plat['repd_date'] = 'Q3 2026'
print('planning points', {k: len(v) // 2 for k, v in plan.items()})
json.dump(plat, open(f'{OUT}/platform.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print('platform.json bytes', os.path.getsize(f'{OUT}/platform.json'), 'sites', len(plat['sites']), 'cfd rows', len(plat['cfd']))
print(json.dumps(plat['head'])); print(json.dumps(plat['regions'])); print(json.dumps(plat['years']))
# ---------- report ----------
un = [p for p in projects if not p['built']]
G = lambda x: round(x / 1000, 1)
print('projects', len(projects), 'unbuilt', len(un), 'sites', len(sites))
print('connected GW', G(sum(p['connected_mw'] for p in projects)), 'queued GW', G(sum(p['queued_mw'] for p in projects)))
for g in ('2', '1', '', '1/2'):
    pp = [p for p in un if p['gate'] == g]; print('  gate', g or 'blank', len(pp), 'projects', G(sum(p['queued_mw'] for p in pp)), 'GW')
tm = collections.Counter(); tn = collections.Counter()
for p in un: tm[p['tech']] += p['queued_mw']; tn[p['tech']] += 1
for k, v in tm.most_common(): print(f'  {k:34s} {tn[k]:5d} {G(v):7.1f} GW')
print('storage-involving queued GW', G(sum(p['queued_mw'] for p in un if p['has_storage'])), 'demand-flag projects', sum(1 for p in un if p['demand']), G(sum(p['queued_mw'] for p in un if p['demand'])))
m = [p for p in projects if p['repd_ref']]; print('REPD matched', len(m), 'of', len(projects), '| unbuilt matched', len([p for p in un if p['repd_ref']]), 'of', len(un))
print('  match kinds', collections.Counter(re.sub(r' \(.*', '', p['repd_match']) for p in m))
c = [p for p in projects if p['cfd_ids']]; print('CfD matched projects', len(c), 'of CfD transmission units', sum(1 for x in cfd if x['Transmission_or_Distribution_connection'] == 'Transmission'))
loc = [s for s in sites.values() if s['x'] != '']; ql = sum(s['queued_mw'] for s in loc); qa = sum(s['queued_mw'] for s in sites.values())
print('sites located', len(loc), 'of', len(sites), '| queued MW located', round(100 * ql / qa), '%', collections.Counter(s['loc_q'] for s in loc))
