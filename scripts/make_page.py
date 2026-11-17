import csv, glob, json, sys
import numpy as np

out = sys.argv[1]
d = json.load(open(f'{out}/platform.json')); o = json.load(open(f'{out}/outline.json'))
for s in d['sites']:
    s['p'] = [p[:7] for p in s['p']]; s.pop('t', None); s.pop('k', None); s.pop('w', None)

# Area for each site, inferred from its map position: the most common region among the
# nearest planning database records. Scotland is split by transmission owner. Sites with no
# map position get "Offshore" or "Not placed". Stored as one index list so data stays compact.
REN = {'Eastern': 'East of England', 'Yorkshire and Humber': 'Yorkshire and the Humber'}
repd = sorted(glob.glob('inputs/REPD_Publication_*.csv'))[-1]
pts, regs = [], []
for r in csv.DictReader(open(repd, encoding='cp1252', errors='replace')):
    g = r['Region'].strip()
    if g in ('', 'Offshore', 'Northern Ireland'):
        continue
    try:
        pts.append((float(r['X-coordinate']), float(r['Y-coordinate']))); regs.append(REN.get(g, g))
    except ValueError:
        pass
P = np.array(pts)
names, idx = [], []
def area(s):
    if s['x'] == '':
        return 'Offshore' if any(w in s['n'].lower() for w in ('offshore', 'platform')) else 'Not placed'
    dd = ((P[:, 0] - s['x']) ** 2 + (P[:, 1] - s['y']) ** 2)
    near = np.argsort(dd)[:7]
    votes = {}
    for k in near:
        votes[regs[k]] = votes.get(regs[k], 0) + 1
    g = max(votes, key=votes.get)
    if g == 'Scotland':
        g = 'North of Scotland' if s['to'] == 'SHET' else 'South of Scotland'
    return g
for s in d['sites']:
    a = area(s)
    if a not in names:
        names.append(a)
    idx.append(names.index(a))
areas = {'areas': names, 'ar': idx}

t = open('scripts/template.html', encoding='utf-8').read()
js = lambda x: json.dumps(x, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
t = t.replace('/*DATA*/', js(d)).replace('/*OUTLINE*/', js(o)).replace('/*AREAS*/', js(areas)).replace('/*NI*/', js(json.load(open(f'{out}/ni.json'))))
open(f'{out}/index.html', 'w', encoding='utf-8').write(t)
print('index.html bytes', len(t.encode()))
