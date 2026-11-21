"""Six-month (and longer) history of the NESO TEC register from weekly snapshots.

Usage: python3 -I history.py <snapshot_dir> <out_dir> [start YYYY-MM-DD]
Snapshots named tec-register-YYYY-MM-DD.csv (date = download date).
"""
import csv, datetime, json, os, re, sys
from collections import Counter, defaultdict

src, out = sys.argv[1], sys.argv[2]
start = sys.argv[3] if len(sys.argv) > 3 else '2026-05-19'
os.makedirs(out, exist_ok=True)

def nd(s):
    s = (s or '').strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def nf(s):
    try:
        return round(float(s), 2)
    except (TypeError, ValueError):
        return 0.0

files = sorted(f for f in os.listdir(src) if re.match(r'tec-register-\d{4}-\d{2}-\d{2}\.csv$', f))
files = [f for f in files if f[13:23] >= start]
snaps = []
for f in files:
    with open(os.path.join(src, f), encoding='utf-8-sig') as fh:
        rows = {}
        for r in csv.DictReader(fh):
            rows[r['Project Number'].strip()] = {
                'name': r['Project Name'].strip(), 'cust': r['Customer Name'].strip(),
                'site': r['Connection Site'].strip(), 'date': nd(r['MW Effective From']),
                'mw': nf(r['Cumulative Total Capacity (MW)']), 'status': r['Project Status'].strip(),
                'type': r['Plant Type'].strip(), 'to': r['HOST TO'].strip(), 'gate': r.get('Gate', '').strip(),
                'agree': r['Agreement Type'].strip(), 'pid': r['Project Number'].strip(), 'stage': r['Stage'],
            }
    snaps.append((f[13:23], rows))

events = []  # every change between consecutive snapshots
weekly = []
for (d0, a), (d1, b) in zip(snaps, snaps[1:]):
    c = Counter()
    for k in b.keys() - a.keys():
        events.append(dict(week=d1, kind='joined', **{x: b[k][x] for x in ('pid', 'stage', 'name', 'cust', 'site', 'type', 'to', 'mw', 'gate')}, new=str(b[k]['date'])))
        c['joined'] += 1
    for k in a.keys() - b.keys():
        events.append(dict(week=d1, kind='left', **{x: a[k][x] for x in ('pid', 'stage', 'name', 'cust', 'site', 'type', 'to', 'mw', 'gate')}, old=str(a[k]['date'])))
        c['left'] += 1
    for k in a.keys() & b.keys():
        x, y = a[k], b[k]
        base = {z: y[z] for z in ('pid', 'stage', 'name', 'cust', 'site', 'type', 'to', 'mw', 'gate')}
        if x['date'] != y['date'] and x['date'] and y['date']:
            m = round((y['date'] - x['date']).days / 30.44, 1)
            events.append(dict(week=d1, kind='date', old=str(x['date']), new=str(y['date']), months=m, **base))
            c['later' if m > 0 else 'earlier'] += 1
        if x['gate'] != y['gate']:
            events.append(dict(week=d1, kind='gate', old=x['gate'], new=y['gate'], **base)); c['gate'] += 1
        if x['mw'] != y['mw']:
            events.append(dict(week=d1, kind='mw', old=x['mw'], new=y['mw'], **base)); c['mw'] += 1
        if x['site'] != y['site']:
            events.append(dict(week=d1, kind='site', old=x['site'], new=y['site'], **base)); c['site'] += 1
        if x['status'] != y['status']:
            events.append(dict(week=d1, kind='status', old=x['status'], new=y['status'], **base)); c['status'] += 1
    weekly.append(dict(week=d1, prev=d0, **c))

# Net change per project-stage across the whole window (first seen vs last seen)
first, last = snaps[0][1], snaps[-1][1]
net = []
for k in first.keys() & last.keys():
    x, y = first[k], last[k]
    if x['date'] and y['date'] and x['date'] != y['date']:
        net.append(dict(pid=y['pid'], stage=y['stage'], name=y['name'], cust=y['cust'], site=y['site'], type=y['type'], to=y['to'], mw=y['mw'], gate=y['gate'], old=str(x['date']), new=str(y['date']), months=round((y['date'] - x['date']).days / 30.44, 1)))

def wcsv(name, rows, cols):
    with open(os.path.join(out, name), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

ecols = ['week', 'kind', 'pid', 'stage', 'name', 'cust', 'site', 'type', 'to', 'mw', 'gate', 'old', 'new', 'months']
wcsv('events.csv', events, ecols)
wcsv('net_date_changes.csv', sorted(net, key=lambda r: -abs(r['months'])), ecols[2:])
wcsv('weekly.csv', weekly, ['prev', 'week', 'joined', 'left', 'later', 'earlier', 'gate', 'mw', 'site', 'status'])

# Developer view: projects with any date change, gate change, or join in the window
dev = defaultdict(lambda: dict(projects=set(), later=0, earlier=0, gate=0, joined=0, left=0, mw_moved=0.0, sites=set(), latest=''))
for e in events:
    d = dev[e['cust']]
    if e['kind'] == 'date':
        d['projects'].add(e['name']); d['sites'].add(e['site']); d['latest'] = max(d['latest'], e['week'])
        d['later' if e['months'] > 0 else 'earlier'] += 1; d['mw_moved'] += e['mw']
    elif e['kind'] in ('gate', 'joined', 'left'):
        d[e['kind']] += 1; d['projects'].add(e['name']); d['latest'] = max(d['latest'], e['week'])
drows = [dict(customer=c, projects=len(v['projects']), date_later=v['later'], date_earlier=v['earlier'], gate_changes=v['gate'], joined=v['joined'], left=v['left'], mw_on_moved_rows=round(v['mw_moved'], 1), sites='; '.join(sorted(v['sites']))[:300], latest_change=v['latest'], example_projects='; '.join(sorted(v['projects']))[:300]) for c, v in dev.items()]
drows.sort(key=lambda r: (-(r['date_later'] + r['date_earlier']), -r['projects']))
wcsv('developers.csv', drows, list(drows[0].keys()) if drows else ['customer'])

# Substation view
sub = defaultdict(lambda: dict(later=0, earlier=0, months=[], projects=set()))
for e in events:
    if e['kind'] == 'date':
        s = sub[e['site']]; s['later' if e['months'] > 0 else 'earlier'] += 1; s['months'].append(e['months']); s['projects'].add(e['pid'])
srows = [dict(site=k, moves=v['later'] + v['earlier'], later=v['later'], earlier=v['earlier'], projects=len(v['projects']), avg_months=round(sum(v['months']) / len(v['months']), 1), net_months=round(sum(v['months']), 1)) for k, v in sub.items()]
srows.sort(key=lambda r: -r['moves'])
wcsv('substations.csv', srows, list(srows[0].keys()) if srows else ['site'])

summary = dict(snapshots=[d for d, _ in snaps], first=snaps[0][0], last=snaps[-1][0], rows_first=len(first), rows_last=len(last),
               kinds=Counter(e['kind'] for e in events), date_later=sum(1 for e in events if e['kind'] == 'date' and e['months'] > 0),
               date_earlier=sum(1 for e in events if e['kind'] == 'date' and e['months'] < 0),
               net_rows_changed=len(net), net_later=sum(1 for r in net if r['months'] > 0), net_earlier=sum(1 for r in net if r['months'] < 0),
               developers_with_date_moves=sum(1 for r in drows if r['date_later'] + r['date_earlier'] > 0))
json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1, default=str)
print(json.dumps(summary, indent=1, default=str))
