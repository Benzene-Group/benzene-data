"""Keep the weekly archive and the history files up to date after each refresh.

1. Copy every inputs/tec-register-<d>-<month>-<yyyy>.csv into archive/tec-weekly/tec-register-YYYY-MM-DD.csv if missing.
2. Rebuild history/ (events, date moves) with scripts/history.py.
3. Rebuild history/outcomes.csv: projects that connected between copies, with the contracted date they held
   just before connecting, so we can measure how accurate contracted dates really were.
Run: python3 -I scripts/history_sync.py   (substation_pages.py runs it first)
"""
import csv, datetime as dt, glob, os, re, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARC = os.path.join(ROOT, 'archive/tec-weekly')
added = []
for f in glob.glob(os.path.join(ROOT, 'inputs/tec-register-*.csv')):
    m = re.search(r'tec-register-(\d{1,2})-([a-z]+)-(\d{4})\.csv$', f)
    if not m: continue
    d = dt.datetime.strptime(' '.join(m.groups()), '%d %B %Y').date()
    dst = os.path.join(ARC, f'tec-register-{d.isoformat()}.csv')
    if not os.path.exists(dst):
        shutil.copyfile(f, dst); added.append(os.path.basename(dst))
subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'scripts/history.py'), ARC, os.path.join(ROOT, 'history')], check=True, stdout=subprocess.DEVNULL)

def pdate(s):
    s = (s or '').strip()
    for f in ('%Y-%m-%d', '%d/%m/%Y'):
        try: return dt.datetime.strptime(s[:10], f).date()
        except ValueError: pass
    return None

def load(f):
    out = {}
    for r in csv.DictReader(open(f, encoding='utf-8-sig')):
        try: mc = float(r['MW Connected'] or 0)
        except ValueError: mc = 0.0
        out.setdefault(r['Project Number'], (r, mc, pdate(r['MW Effective From'])))
    return out

files = sorted(glob.glob(os.path.join(ARC, 'tec-register-20*.csv')))
rows, prev, pdatef = [], None, None
for f in files:
    cur = load(f); fd = os.path.basename(f)[13:23]
    if prev:
        for pid, (r, mc, d) in cur.items():
            if pid in prev and prev[pid][1] <= 0 and mc > 0:
                c = prev[pid][2]
                gap = round((dt.date.fromisoformat(fd) - c).days / 30.44, 1) if c else ''
                rows.append({'pid': pid, 'name': r['Project Name'], 'site': r['Connection Site'], 'type': r['Plant Type'],
                             'mw_connected': mc, 'contracted_before': c.isoformat() if c else '', 'seen_connected_between': f'{pdatef} and {fd}',
                             'months_after_contracted': gap})
    prev, pdatef = cur, fd
with open(os.path.join(ROOT, 'history/outcomes.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=['pid', 'name', 'site', 'type', 'mw_connected', 'contracted_before', 'seen_connected_between', 'months_after_contracted'])
    w.writeheader(); w.writerows(rows)
print('archive added', added, 'outcomes', len(rows))
