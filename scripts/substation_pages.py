"""Build one public page per grid connection site, for grid.benzene-group.com (GitHub Pages, docs/).

Usage: python3 -I scripts/substation_pages.py [QUEUE_MAP_HTML]
Reads the data object embedded in the published queue map (default published/queue-map.html),
history/events.csv (date moves) and data/headroom.json (local network capacity).
Writes docs/: index.html, substations/<slug>/index.html, sitemap.xml, robots.txt, llms.txt, CNAME, .nojekyll.
Every figure comes from those files. No hand-typed numbers.
"""
import csv, html, json, math, os, re, sys, datetime as dt, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import realistic_date as RD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'published/queue-map.html')
OUT = os.path.join(ROOT, 'docs')
HOST = 'https://grid.benzene-group.com'
MAIN = 'https://www.benzene-group.com'
E = html.escape

s = open(SRC, encoding='utf-8').read()
i = s.index('const D = ') + len('const D = ')
D, _ = json.JSONDecoder().raw_decode(s[i:])
TEC_DATE = D['tec_date']
TODAY = dt.date.today().isoformat()

HR = json.load(open(os.path.join(ROOT, 'data/headroom.json'), encoding='utf-8'))
OPS = HR['ops']

moves = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(ROOT, 'history/events.csv'), encoding='utf-8')):
    if r['kind'] != 'date' or not r['months']:
        continue
    m = float(r['months'])
    if abs(m) >= 1.0:
        moves[r['site']].append(r)
EV_FIRST = min((r['week'] for v in moves.values() for r in v), default='')


def slug(n):
    n = re.sub(r'\b(\d+(\.\d+)?(/\d+)*kv)\b', lambda m: m.group(1), n.lower())
    return re.sub(r'[^a-z0-9]+', '-', n).strip('-')[:80]


def fdate(iso):
    if not iso:
        return 'no date'
    try:
        d = dt.date.fromisoformat(iso[:10])
        return f'{d.day} {d.strftime("%b %Y")}'
    except ValueError:
        return iso


def fmw(x):
    return f'{x:,.0f}' if x >= 10 else f'{x:,.1f}'.rstrip('0').rstrip('.')


def wk(iso):
    d = dt.date.fromisoformat(iso)
    return f'{d.day} {d.strftime("%b %Y")}'


TO_NAME = {'NGET': 'National Grid Electricity Transmission (England and Wales)', 'SPT': 'SP Transmission (southern Scotland)',
           'SHET': 'SSEN Transmission (northern Scotland)', 'OFTO': 'an offshore transmission owner'}

sites = [x for x in D['sites'] if x.get('q', 0) > 0 or x.get('c', 0) > 0]
seen = collections.Counter()
for x in sites:
    b = slug(x['n'])
    seen[b] += 1
    x['slug'] = b if seen[b] == 1 else f'{b}-{seen[b]}'
    x['short'] = re.sub(r'\s+(Substation|GSP)$', '', x['n'])

CSS = """
:root{--ink:#0f1b2a;--teal:#1a8aa6;--teal2:#0f6e86;--mute:#6b7280;--line:#e5e7eb;--bg:#f7f9fb}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:#fff}
a{color:var(--teal2)}header,main,footer{max-width:960px;margin:0 auto;padding:0 18px}
header{display:flex;align-items:center;gap:12px;padding-top:16px;padding-bottom:12px;border-bottom:1px solid var(--line);flex-wrap:wrap}
header img{width:32px;height:32px}header .b{font-weight:700;font-size:18px;text-decoration:none;color:var(--ink)}
header nav{margin-left:auto;display:flex;gap:14px;font-size:14px;flex-wrap:wrap}
h1{font-size:28px;line-height:1.2;margin:26px 0 6px}h2{font-size:20px;margin:30px 0 8px}
.sub{color:var(--mute);margin:0 0 18px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.k{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px}.k b{display:block;font-size:22px}.k span{font-size:13px;color:var(--mute)}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--bg);font-weight:600}td.n,th.n{text-align:right;white-space:nowrap}.late{color:#b42318}.early{color:#067647}
.cta{background:var(--ink);color:#fff;border-radius:12px;padding:20px;margin:30px 0}.cta a{color:#9be3f2}.cta h2{margin-top:0;color:#fff}
.btn{display:inline-block;background:var(--teal);color:#fff!important;text-decoration:none;padding:9px 14px;border-radius:8px;font-weight:600;margin:6px 8px 0 0}
.note{font-size:13px;color:var(--mute)}footer{border-top:1px solid var(--line);margin-top:40px;padding-top:14px;padding-bottom:30px;font-size:13px;color:var(--mute)}
input[type=search]{width:100%;padding:10px;border:1px solid var(--line);border-radius:8px;font-size:16px;margin:8px 0 14px}
ul.cols{columns:2;padding-left:18px}@media(max-width:600px){ul.cols{columns:1}h1{font-size:24px}}
"""


def page(title, desc, path, body, jsonld=None):
    url = HOST + path
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ''
    return f"""<!DOCTYPE html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Benzene"><meta property="og:image" content="{MAIN}/brand/email-mark.png">
<link rel="icon" href="{MAIN}/favicon.svg"><style>{CSS}</style>{ld}</head><body>
<header><img src="{MAIN}/favicon.svg" alt=""><a class="b" href="{MAIN}/">Benzene</a>
<nav><a href="{HOST}/">All substations</a><a href="{MAIN}/queue-map.html">Queue map</a><a href="{MAIN}/changes.html">Register changes</a><a href="{MAIN}/pricing.html">Services and pricing</a></nav></header>
<main>{body}</main>
<footer><p>Benzene: UK grid connection intelligence. <a href="{MAIN}/">benzene-group.com</a> · <a href="mailto:info@benzene-group.com">info@benzene-group.com</a></p>
<p>Queue data: NESO Transmission Entry Capacity (TEC) register of {E(TEC_DATE)}, used under the NESO Open Data Licence. Date moves: our weekly copies of the register. Local capacity: {E('; '.join(o['credit'] + ' (' + o['date'] + ')' for o in OPS))}.
This page is information, not engineering, legal or investment advice.</p>
<p>Benzene Company Ltd, registered in England and Wales, company number 17593082.</p></footer></body></html>"""


def nearest_sites(x, k=5):
    if not x.get('x'):
        return []
    d = [(math.hypot(o['x'] - x['x'], o['y'] - x['y']), o) for o in sites if o is not x and o.get('x')]
    return [o for dist, o in sorted(d, key=lambda t: t[0])[:k] if dist < 60000]


def headroom(x, k=6, km=20):
    if not x.get('x'):
        return []
    out = []
    for r in HR['rows']:
        dd = math.hypot(r[4] - x['x'], r[5] - x['y'])
        if dd <= km * 1000:
            out.append((dd, r))
    return sorted(out, key=lambda t: t[0])[:k]


TECH_ORDER = collections.Counter()
built = []
for x in sites:
    p = sorted(x.get('p', []), key=lambda r: (r[4] or '9999'))
    q = x.get('q', 0)
    n = len(p)
    dates = [r[4] for r in p if r[4]]
    first, last = (min(dates), max(dates)) if dates else ('', '')
    techs = collections.Counter()
    for r in p:
        techs[r[2]] += r[3]
    top_tech = ', '.join(t.lower() for t, _ in techs.most_common(2))
    mv = moves.get(x['n'], [])
    later = sum(1 for r in mv if float(r['months']) > 0)
    earlier = len(mv) - later
    name = x['n']
    short = re.sub(r'\s+(Substation|GSP)$', '', name)
    to = TO_NAME.get(x.get('to', ''), x.get('to', ''))

    desc = (f'{short}: {n} project{"s" if n != 1 else ""} and {fmw(q)} MW waiting to connect in NESO\'s register of {TEC_DATE}'
            + (f', dates from {fdate(first)} to {fdate(last)}' if first else '')
            + (f'. {len(mv)} connection date move{"s" if len(mv) != 1 else ""} of a month or more since {wk(EV_FIRST)}.' if mv else '.'))
    title = f'{short} grid connection queue | Benzene'

    kp = f"""<div class="kpis"><div class="k"><b>{n}</b><span>project{'s' if n != 1 else ''} in the queue</span></div>
<div class="k"><b>{fmw(q)} MW</b><span>waiting to connect</span></div>
<div class="k"><b>{fmw(x.get('c', 0))} MW</b><span>already connected</span></div>
<div class="k"><b>{fmw(x.get('g2', 0))} MW</b><span>holding Gate 2</span></div>
<div class="k"><b>{len(mv)}</b><span>date moves since {wk(EV_FIRST)}</span></div></div>"""

    risks = [RD.assess(r[2], r[4]) for r in p]
    def rcell(a):
        if not a: return '<td>n/a</td><td class=n></td>'
        c = 'late' if a['risk'] == 'High' else ''
        return f"<td class='{c}'>{a['risk']}</td><td class=n>{fdate(a['likely']) if a['likely'] != '' else ''}</td>"
    rows = ''.join(f"<tr><td>{E(r[0])}</td><td>{E(r[1])}</td><td>{E(r[2])}</td><td class=n>{fmw(r[3])}</td><td class=n>{fdate(r[4])}</td>{rcell(a)}<td>{E(r[5])}</td><td>{E(r[6] or 'none')}</td></tr>" for r, a in zip(p, risks))
    hi_mw = sum(r[3] for r, a in zip(p, risks) if a and a['risk'] == 'High')
    x['_risks'] = risks
    qtab = (f'<h2>What sits in the queue</h2><p class="note">Sorted by contracted date. Register of {E(TEC_DATE)}. '
            f'Date risk and likely date come from how similar projects\' dates actually moved over the last two years (<a href="{HOST}/method/">how we work it out</a>).</p>'
            f'<div class="tw"><table><tr><th>Project</th><th>Customer</th><th>Type</th><th class=n>MW</th><th class=n>Contracted date</th><th>Date risk</th><th class=n>Likely date</th><th>Stage</th><th>Gate</th></tr>{rows}</table></div>') if p else ''

    if mv:
        mrows = ''.join(
            f"<tr><td>{wk(r['week'])}</td><td>{E(r['name'])}</td><td class=n>{fdate(r['old'])}</td><td class=n>{fdate(r['new'])}</td>"
            f"<td class='n {'late' if float(r['months']) > 0 else 'early'}'>{'+' if float(r['months']) > 0 else ''}{float(r['months']):.0f} months</td></tr>"
            for r in sorted(mv, key=lambda r: r['week'], reverse=True))
        mtab = (f'<h2>Dates that moved</h2><p>Since {wk(EV_FIRST)}, connection dates here moved by a month or more {len(mv)} time{"s" if len(mv) != 1 else ""}: '
                f'{later} later and {earlier} earlier. An earlier date can mean someone ahead dropped out or the queue was re-ordered.</p>'
                f'<div class="tw"><table><tr><th>Week seen</th><th>Project</th><th class=n>Was</th><th class=n>Now</th><th class=n>Change</th></tr>{mrows}</table></div>')
    else:
        mtab = f'<h2>Dates that moved</h2><p>No connection date here has moved by a month or more since {wk(EV_FIRST)}.</p>'

    hr = headroom(x)
    if hr:
        hrows = ''.join(
            f"<tr><td>{E(r[1])}</td><td>{E(OPS[r[0]]['name'])}</td><td class=n>{d / 1000:.1f} km</td>"
            f"<td class=n>{'' if r[6] is None else fmw(r[6]) + ' MW'}</td><td class=n>{'' if r[8] is None else fmw(r[8]) + ' MW'}</td></tr>"
            for d, r in hr)
        htab = (f'<h2>Local network capacity nearby</h2><p class="note">Nearest distribution substations within 20 km, from each operator\'s published headroom data. '
                f'Location is approximate. Check the operator\'s own map before relying on it.</p>'
                f'<div class="tw"><table><tr><th>Substation</th><th>Operator</th><th class=n>Distance</th><th class=n>Generation headroom</th><th class=n>Demand headroom</th></tr>{hrows}</table></div>')
    else:
        htab = ''

    near = nearest_sites(x)
    ntab = ('<h2>Nearby connection points</h2><ul>' + ''.join(
        f'<li><a href="{HOST}/substations/{o["slug"]}/">{E(o["short"])}</a>: {fmw(o.get("q", 0))} MW waiting</li>' for o in near) + '</ul>') if near else ''

    cta = f"""<div class="cta"><h2>Thinking of connecting near {E(short)}?</h2>
<p>Tell us the site and size. We'll send you what sits ahead of it in the queue, free. It takes a day.</p>
<a class="btn" href="mailto:info@benzene-group.com?subject={E(('Free check: ' + short).replace(' ', '%20'))}">Ask for a free check</a>
<a class="btn" href="{MAIN}/sample-screening-report.html">See a sample report</a>
<p class="note" style="color:#c9d4e0">Paid screening reports from £1,950. Queue watch alerts you when anything here changes.</p></div>"""

    body = (f'<h1>{E(short)}: grid connection queue</h1><p class="sub">{E(name)} · {E(to)} · register of {E(TEC_DATE)}</p>'
            f'<p>{n} project{"s" if n != 1 else ""} with {fmw(q)} MW {"are" if n != 1 else "is"} waiting to connect here'
            + (f' (largest by capacity: {E(top_tech)})' if top_tech else '') + (f'. Contracted dates run from {fdate(first)} to {fdate(last)}.' if first else '.') + '</p>'
            + kp.replace('</div></div>', f'</div><div class="k"><b>{fmw(hi_mw) if p else 0} MW</b><span>at high date risk</span></div></div>', 1) + qtab + mtab + htab + cta + ntab)

    jsonld = {'@context': 'https://schema.org', '@type': 'Dataset', 'name': f'{short} grid connection queue',
              'description': desc, 'url': f'{HOST}/substations/{x["slug"]}/', 'dateModified': TODAY,
              'creator': {'@type': 'Organization', 'name': 'Benzene', 'url': MAIN},
              'isBasedOn': 'https://www.neso.energy/data-portal/transmission-entry-capacity-tec-register',
              'spatialCoverage': {'@type': 'Place', 'name': name}}
    path = f'/substations/{x["slug"]}/'
    os.makedirs(OUT + path, exist_ok=True)
    open(OUT + path + 'index.html', 'w', encoding='utf-8').write(page(title, desc, path, body, jsonld))
    built.append((x, short, q, len(mv)))

# index
by_to = collections.defaultdict(list)
for x, short, q, m in built:
    by_to[TO_NAME.get(x.get('to', ''), x.get('to', '') or 'Other')].append((short, x['slug'], q, m))
top_moves = sorted(built, key=lambda t: (-t[3], -t[2]))[:15]
top_q = sorted(built, key=lambda t: -t[2])[:15]
li = lambda t: f'<li><a href="{HOST}/substations/{t[0]["slug"]}/">{E(t[1])}</a>: {fmw(t[2])} MW waiting' + (f', {t[3]} date moves' if t[3] else '') + '</li>'
lists = ''.join(f'<h2>{E(k)} ({len(v)})</h2><ul class="cols">' + ''.join(
    f'<li data-n="{E(a.lower())}"><a href="{HOST}/substations/{b}/">{E(a)}</a></li>' for a, b, q, m in sorted(v)) + '</ul>' for k, v in sorted(by_to.items(), key=lambda kv: -len(kv[1])))
h = D['head']
body = (f'<h1>Every grid connection point in Great Britain</h1><p class="sub">One page per site in NESO\'s register of {E(TEC_DATE)}: who is queuing, for how much, until when, and which dates have moved.</p>'
        f'<div class="kpis"><div class="k"><b>{len(built):,}</b><span>connection points</span></div><div class="k"><b>{h["projects"]:,}</b><span>projects</span></div>'
        f'<div class="k"><b>{h["queued"] / 1000:,.0f} GW</b><span>waiting to connect</span></div><div class="k"><b>{h["connected"] / 1000:,.0f} GW</b><span>connected</span></div></div>'
        '<input type="search" id="q" placeholder="Find a substation, e.g. Walpole" aria-label="Find a substation">'
        '<h2>Most date moves</h2><ul>' + ''.join(li(t) for t in top_moves) + '</ul>'
        '<h2>Biggest queues</h2><ul>' + ''.join(li(t) for t in top_q) + '</ul>' + lists +
        """<script>document.getElementById('q').addEventListener('input',function(){var v=this.value.toLowerCase();document.querySelectorAll('li[data-n]').forEach(function(l){l.style.display=l.dataset.n.indexOf(v)>-1?'':'none'})})</script>""")
desc = f'Grid connection queue for every connection point in Great Britain: {h["projects"]:,} projects in NESO\'s register of {TEC_DATE}, with date moves and local capacity.'
open(OUT + '/index.html', 'w', encoding='utf-8').write(page('Grid connection queue by substation, Great Britain | Benzene', desc, '/', body,
     {'@context': 'https://schema.org', '@type': 'DataCatalog', 'name': 'Benzene grid connection queue by substation', 'url': HOST + '/', 'creator': {'@type': 'Organization', 'name': 'Benzene', 'url': MAIN}}))

M = RD.model()
mrows = ''.join(f"<tr><td>{E(k[0])}</td><td>{E(k[1])}</td><td class=n>{v['stayed']}</td><td class=n>{round(100*v['later_share'])}%</td><td class=n>{v['median_later']:.0f} months</td><td class=n>{round(100*v['left_share'])}%</td></tr>"
                for k, v in sorted(M['table'].items(), key=lambda kv: (kv[0][0] == 'All', kv[0][0], ['under 2 years','2 to 5 years','5 years or more'].index(kv[0][1]))))
mbody = (f'<h1>How we work out a realistic connection date</h1><p class="sub">Learned from our own copies of NESO\'s register, {wk(M["from"])} to {wk(M["to"])}.</p>'
         '<p>A contracted connection date is a promise, not a forecast. So we checked how those promises have actually held up. We took every project waiting to connect in our earliest copy of the register, grouped them by technology and by how far away their contracted date was, and looked at where each one stood two years later: same date, moved later, moved earlier, or gone from the register.</p>'
         '<p>For any project today, we find its group and report three things. <b>Date risk</b>: High if half or more of similar projects moved a month or more later, Medium from a quarter, otherwise Low. <b>Likely date</b>: the contracted date plus the typical move, when the risk is High; otherwise the contracted date. <b>Dropout</b>: the share of similar projects that left the register. Where a group is small, we use all technologies together.</p>'
         '<p>The pattern is clear. Dates within two years slip far more often than dates further out, so a project\'s risk rises as its date gets closer.</p>'
         f'<div class="tw"><table><tr><th>Technology</th><th>Contracted date was</th><th class=n>Projects still listed</th><th class=n>Moved later</th><th class=n>Typical move</th><th class=n>Left the register</th></tr>{mrows}</table></div>'
         '<p class="note">This is a statistical view from public records, not a forecast for any single project and not engineering advice. It ignores project-specific facts like works already started. A screening report reads those properly.</p>')
os.makedirs(OUT + '/method', exist_ok=True)
open(OUT + '/method/index.html', 'w', encoding='utf-8').write(page('How we work out a realistic grid connection date | Benzene',
     'How often UK grid connection dates actually slip, by technology and time to connection, from two years of NESO register copies.', '/method/', mbody))
urls = [HOST + '/', HOST + '/method/'] + [f'{HOST}/substations/{x["slug"]}/' for x, *_ in built]
open(OUT + '/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + ''.join(f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls) + '</urlset>\n')
open(OUT + '/robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {HOST}/sitemap.xml\n')
open(OUT + '/llms.txt', 'w').write(
    f'# Benzene grid connection queue by substation\n\nOne page per grid connection point in Great Britain, built from NESO\'s TEC register of {TEC_DATE}, '
    f'our weekly copies of it since {wk(EV_FIRST)}, and distribution operators\' published headroom data.\n\n'
    f'- Index: {HOST}/\n- Main site: {MAIN}/\n- Services and pricing: {MAIN}/pricing.html\n- Contact: info@benzene-group.com\n')
open(OUT + '/CNAME', 'w').write('grid.benzene-group.com\n')
open(OUT + '/.nojekyll', 'w').write('')
for p in (OUT + '/index.html',):
    assert '—' not in open(p, encoding='utf-8').read()

# machine-readable feed for the Benzene Grid MCP server and anyone else: docs/api/queue.json
import pyproj
_T = pyproj.Transformer.from_crs('EPSG:27700', 'EPSG:4326', always_xy=True)
def _ll(x, y):
    lon, lat = _T.transform(x, y)
    return round(lat, 5), round(lon, 5)
api_sites = []
for x, short, q, m in built:
    lat, lon = _ll(x['x'], x['y']) if x.get('x') else (None, None)
    api_sites.append({'name': x['n'], 'short': short, 'slug': x['slug'], 'to': x.get('to', ''), 'lat': lat, 'lon': lon,
                      'queued_mw': round(q, 1), 'connected_mw': round(x.get('c', 0), 1), 'gate2_mw': round(x.get('g2', 0), 1),
                      'projects': [dict(zip(['project', 'customer', 'type', 'mw', 'date', 'stage', 'gate'], r)) | {'date_risk': RD.assess(r[2], r[4])} for r in sorted(x.get('p', []), key=lambda r: r[4] or '9999')],
                      'url': f'{HOST}/substations/{x["slug"]}/'})
api_moves = [{'week': r['week'], 'site': r['site'], 'project': r['name'], 'customer': r['cust'], 'type': r['type'], 'mw': r['mw'],
              'gate': r['gate'], 'old': r['old'], 'new': r['new'], 'months': float(r['months'])} for v in moves.values() for r in v]
api_hr = []
for r in HR['rows']:
    lat, lon = _ll(r[4], r[5])
    api_hr.append([r[1], OPS[r[0]]['name'], r[2], r[3], lat, lon, r[6], r[8]])
os.makedirs(OUT + '/api', exist_ok=True)
json.dump({'register_date': TEC_DATE, 'built': TODAY, 'moves_since': EV_FIRST, 'head': D['head'], 'sites': api_sites,
           'moves': sorted(api_moves, key=lambda m: m['week'], reverse=True),
           'headroom_fields': ['substation', 'operator', 'type', 'kv', 'lat', 'lon', 'generation_headroom_mw', 'demand_headroom_mw'],
           'headroom': api_hr, 'headroom_credits': [o['credit'] + ' (' + o['date'] + ')' for o in OPS],
           'licence': 'Queue data from NESO TEC register, NESO Open Data Licence. Headroom data credited per operator. Compiled by Benzene, benzene-group.com.'},
          open(OUT + '/api/queue.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('api bytes', os.path.getsize(OUT + '/api/queue.json'))

print('pages', len(built), 'register', TEC_DATE, 'moves window from', EV_FIRST)
