"""Twice-weekly refresh: fetch the newest NESO TEC register, rebuild, and decide whether it is safe to publish.

Usage (from the repo root): python3 -I scripts/refresh.py
Writes:
  inputs/<new register>.csv   the downloaded register
  out/                        build output (out/index.html is the queue map page)
  site/index.html, site/llms.txt   homepage and llms.txt with refreshed figures
  out/refresh.json            status: no_new_register | ready | hold, plus every change
A figure moving by more than 10% sets status to hold: a person checks before anything is published.
"""
import glob, json, os, re, subprocess, sys, urllib.request

API = 'https://api.neso.energy/api/3/action/package_show?id=transmission-entry-capacity-tec-register'
HOLD_PCT = 10.0
NUMERIC = ['queued_gw', 'projects', 'wait', 'pct2031', 'g2share', 'n_g2', 'gw_g2', 'wait_g2',
           'n_g1', 'gw_g1', 'wait_g1', 'n_gn', 'gw_gn', 'g2by2029']


def run(*args):
    r = subprocess.run([sys.executable, '-I', *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'{args[0]} failed:\n{r.stderr}')
    return r.stdout


def write(status, **kw):
    os.makedirs('out', exist_ok=True)
    json.dump(dict(status=status, **kw), open('out/refresh.json', 'w'), indent=1)
    print(json.dumps(dict(status=status, **kw), indent=1))


pkg = json.load(urllib.request.urlopen(API, timeout=60))['result']
res = next(r for r in pkg['resources'] if (r.get('format') or '').upper() == 'CSV')
url = res['url']
name = url.rsplit('/', 1)[-1]
if not re.match(r'tec-register-\d{1,2}-[a-z]+-\d{4}\.csv$', name):
    sys.exit(f'unexpected register file name: {name}')

current = sorted(glob.glob('inputs/tec-register-*.csv'), key=os.path.getmtime)
if os.path.exists(f'inputs/{name}'):
    write('no_new_register', register=name)
    sys.exit(0)

# The CSV download redirects to a storage host outside the allowlist, so read the same
# rows through NESO's datastore API and write them back in the published CSV layout.
rows, fields, off = [], None, 0
while True:
    q = f"https://api.neso.energy/api/3/action/datastore_search?resource_id={res['id']}&limit=1000&offset={off}"
    r = json.load(urllib.request.urlopen(q, timeout=60))['result']
    fields = fields or [f['id'] for f in r['fields'] if f['id'] != '_id']
    rows += r['records']
    off += 1000
    if off >= r['total']:
        break
if len(rows) != r['total'] or 'Project Name' not in fields or len(rows) < 1000:
    sys.exit(f'register looks wrong: {len(rows)} rows, fields {fields}')

def cell(v):
    if v is None:
        return ''
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else repr(v)
    v = str(v)
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})(?:T00:00:00)?', v)
    return f'{m.group(3)}/{m.group(2)}/{m.group(1)}' if m else v

import csv
with open(f'inputs/{name}', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(fields)
    for rec in rows:
        w.writerow([cell(rec[k]) for k in fields])

repd = sorted(glob.glob('inputs/REPD_Publication_*.csv'))[-1]
run('scripts/build.py', f'inputs/{name}', repd, 'inputs/cfd_contract_portfolio_status.csv', 'out', 'reference/pypsa-gb')
import shutil
shutil.copy('reference/ni.json', 'out/ni.json')
run('scripts/make_page.py', 'out')
upd = json.loads(run('scripts/update_home.py', 'out', 'site'))

moves, hold = [], []
for c in upd['changes']:
    if c['figure'] in NUMERIC:
        was, now = float(c['was'].replace(',', '')), float(c['now'].replace(',', ''))
        pct = (now - was) / was * 100 if was else 100.0
        c['pct'] = round(pct, 1)
        if abs(pct) > HOLD_PCT:
            hold.append(c)
    moves.append(c)

for old in current:
    if old != f'inputs/{name}':
        os.remove(old)

# Payloads for publishing: homepage figures and blocks, llms.txt, and the map page edits
h = open('site/index.html', encoding='utf-8').read()
F = dict(re.findall(r'<!--f:(\w+)-->(.*?)<!--/f-->', h))
B = {k: re.search(r'/\*' + k + r'\*/(.*?)/\*/' + k + r'\*/', h, re.S).group(1) for k in ('D', 'Y', 'TOP')}
json.dump({'F': F, 'B': B, 'llms': open('site/llms.txt', encoding='utf-8').read()},
          open('out/home.json', 'w', encoding='utf-8'), ensure_ascii=False)
run('scripts/map_pairs.py', 'published/queue-map.html', 'out/index.html', 'out/map_pairs.json')

write('hold' if hold else 'ready', register=name, tec_date=upd['tec_date'], changes=moves,
      held_figures=hold, map_bytes=os.path.getsize('out/index.html'))
