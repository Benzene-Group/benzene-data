"""Refresh every register-derived figure on the Benzene homepage and in llms.txt.

Usage: python3 -I update_home.py OUTDIR SITEDIR
  OUTDIR  holds platform.json from build.py
  SITEDIR holds index.html (with <!--f:key--> markers) and llms.template.txt
Writes SITEDIR/index.html and SITEDIR/llms.txt in place and prints a JSON list of changed figures.
"""
import json, math, re, sys

out, site = sys.argv[1:3]
d = json.load(open(f'{out}/platform.json', encoding='utf-8'))
H = d['head']
q = H['queued']

def gw(mw, nd=1):
    return f'{mw / 1000:.{nd}f}'

def yr(label):
    return int(label[:4]) if label[:4].isdigit() else None

later = sum(y['g2'] + y['g1'] + y['none'] for y in d['years'] if yr(y['y']) and yr(y['y']) >= 2031 and y['y'] != '2026 or earlier')
g2_by_2029 = sum(y['g2'] for y in d['years'] if yr(y['y']) and yr(y['y']) <= 2029)
day, month, year = d['tec_date'].split()

F = {
    'queued_gw': f'{round(q / 1000):,}',
    'projects': f"{H['projects']:,}",
    'wait': f"{H['wait']}",
    'pct2031': f'{round(later / q * 100)}',
    'g2share': f"{round(H['gate2'] / q * 100)}",
    'tec_date': d['tec_date'],
    'tec_short': f'{day} {month[:3]} {year}',
    'n_g2': f"{H['n_gate2']:,}", 'gw_g2': gw(H['gate2']), 'wait_g2': f"{H['wait_g2']}",
    'n_g1': f"{H['n_gate1']:,}", 'gw_g1': gw(H['gate1']), 'wait_g1': f"{H['wait_g1']}",
    'n_gn': f"{H['n_nogate']:,}", 'gw_gn': gw(H['nogate']),
    'g2by2029': f"{round(g2_by_2029 / H['gate2'] * 100) if H['gate2'] else 0}",
}

# llms.txt extras
F_llms = dict(F, queued_gw1=gw(q), sites=f"{H['sites']:,}", connected_gw=gw(H['connected']))

# Chart data: years with a date, oldest first
Y = [[y['y'], y['g2'], y['g1'], y['none']] for y in d['years'] if y['y'] != 'No date']
peak = max(a + b + c for _, a, b, c in Y)
top = max(100000, math.ceil(peak / 25000) * 25000)

# Minimap: the 110 sites with most capacity waiting, OSGB metres to the 167 x 307 outline frame
S = sorted([s for s in d['sites'] if isinstance(s['x'], (int, float)) and isinstance(s['y'], (int, float))], key=lambda s: -s['q'])[:110]
qmax, qmin = S[0]['q'], S[-1]['q']
def wbin(w):
    w = w if w is not None else 0
    return 0 if w < 2 else 1 if w < 4 else 2 if w < 6 else 3 if w < 8 else 4
D = []
for s in sorted(S, key=lambda s: s['q']):
    r = 3.2 + 3.3 * (math.sqrt(s['q']) - math.sqrt(qmin)) / ((math.sqrt(qmax) - math.sqrt(qmin)) or 1)
    D += [round(s['x'] / 3990), round(307.3 - s['y'] / 3990), round(r * 10), wbin(s['w'])]

html = open(f'{site}/index.html', encoding='utf-8').read()
changes = []
def sub_f(m):
    k, old = m.group(1), m.group(2)
    new = F[k]
    if new != old:
        changes.append({'figure': k, 'was': old, 'now': new})
    return f'<!--f:{k}-->{new}<!--/f-->'
html, n = re.subn(r'<!--f:(\w+)-->(.*?)<!--/f-->', sub_f, html)
assert n >= 15, f'only {n} figure markers found'
for key, val in (('D', json.dumps(D, separators=(',', ':'))), ('Y', json.dumps(Y, separators=(', ', ', ')).replace('"', "'"))):
    html, k = re.subn(r'/\*' + key + r'\*/.*?/\*/' + key + r'\*/', lambda m: f'/*{key}*/{val}/*/{key}*/', html, flags=re.S)
    assert k == 1, f'marker {key} missing'
html, k = re.subn(r'/\*TOP\*/\d+/\*/TOP\*/', f'/*TOP*/{top}/*/TOP*/', html)
assert k == 1
assert '—' not in html and '–' not in html, 'dash found'
open(f'{site}/index.html', 'w', encoding='utf-8').write(html)

llms = open(f'{site}/llms.template.txt', encoding='utf-8').read().format(**F_llms)
open(f'{site}/llms.txt', 'w', encoding='utf-8').write(llms)
print(json.dumps({'tec_date': d['tec_date'], 'changes': changes, 'chart_top_gw': top // 1000}, indent=1))
