"""Grid Delay Index and Slippage Index page for grid.benzene-group.com/delay-index/.
Run after substation_pages.py (imports its page shell). Figures computed from history/events.csv
(weekly copies) and realistic_date.model() (two-year comparison). No hand-typed numbers.
"""
import csv, collections, datetime as dt, os, sys, statistics as st
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import realistic_date as RD
import substation_pages as SP  # rebuilds pages too; reuse its shell and constants
E, HOST, OUT = SP.E, SP.HOST, SP.OUT

ev = [r for r in csv.DictReader(open(os.path.join(SP.ROOT, 'history/events.csv'), encoding='utf-8'))
      if r['kind'] == 'date' and r['months'] and abs(float(r['months'])) >= 1.0]
bym = collections.defaultdict(lambda: {'later': 0, 'earlier': 0, 'mw_later': 0.0, 'months_later': 0.0})
for r in ev:
    m = r['week'][:7]; v = float(r['months']); b = bym[m]
    if v > 0:
        b['later'] += 1; b['mw_later'] += float(r['mw'] or 0); b['months_later'] += v
    else:
        b['earlier'] += 1
months = sorted(bym)
latest = months[-1]
L = bym[latest]
later_all = [float(r['months']) for r in ev if float(r['months']) > 0]
tot_later, tot_earlier = len(later_all), len(ev) - len(later_all)
M = RD.model()
near = {k[0]: v for k, v in M['table'].items() if k[1] == 'under 2 years' and v['stayed'] >= RD.MIN_N and k[0] != 'All'}
alln = M['table'][('All', 'under 2 years')]

def mname(m):
    d = dt.date.fromisoformat(m + '-01'); return d.strftime('%B %Y')

rows = ''.join(f"<tr><td>{mname(m)}</td><td class=n>{bym[m]['later']}</td><td class=n>{bym[m]['earlier']}</td><td class=n>{SP.fmw(bym[m]['mw_later'])} MW</td><td class=n>{bym[m]['months_later']:,.0f}</td></tr>" for m in reversed(months))
nrows = ''.join(f"<tr><td>{E(k)}</td><td class=n>{v['stayed']}</td><td class=n>{round(100*v['later_share'])}%</td><td class=n>{v['median_later']:.0f} months</td></tr>" for k, v in sorted(near.items(), key=lambda kv: -kv[1]['later_share']))
body = (f'<h1>Grid Delay Index</h1><p class="sub">How often Great Britain\'s grid connection dates move, from our weekly copies of NESO\'s register. Updated with each new register.</p>'
        f'<div class="kpis"><div class="k"><b>{L["later"]}</b><span>dates pushed later in {mname(latest)}</span></div>'
        f'<div class="k"><b>{SP.fmw(L["mw_later"])} MW</b><span>of projects pushed later in {mname(latest)}</span></div>'
        f'<div class="k"><b>{len(ev)}</b><span>moves of a month or more since {SP.wk(SP.EV_FIRST)}</span></div>'
        f'<div class="k"><b>{round(100*alln["later_share"])}%</b><span>of projects within two years of their date moved later (two-year view)</span></div></div>'
        f'<h2>Month by month</h2><p>Each row counts connection dates that moved by a month or more between weekly copies of the register. {tot_later} moved later and {tot_earlier} earlier since {SP.wk(SP.EV_FIRST)}; the typical later move was {st.median(later_all):.0f} months.</p>'
        f'<div class="tw"><table><tr><th>Month seen</th><th class=n>Later</th><th class=n>Earlier</th><th class=n>MW pushed later</th><th class=n>Months of delay added</th></tr>{rows}</table></div>'
        f'<h2>The two-year view: near dates slip most</h2><p>We compared every project waiting in our register copy of {SP.wk(M["from"])} with where it stood on {SP.wk(M["to"])}. Of projects whose contracted date was under two years away, {round(100*alln["later_share"])}% had moved a month or more later, typically by {alln["median_later"]:.0f} months, and {round(100*alln["left_share"])}% had left the register.</p>'
        f'<div class="tw"><table><tr><th>Technology</th><th class=n>Projects</th><th class=n>Moved later</th><th class=n>Typical move</th></tr>{nrows}</table></div>'
        f'<p>Every project on our <a href="{HOST}/">substation pages</a> now shows a date risk and a likely date built from this. <a href="{HOST}/method/">How we work it out</a>.</p>'
        f'<div class="cta"><h2>Is your date one of them?</h2><p>Tell us the project or site. We\'ll send you what sits ahead of it and how its date compares, free.</p>'
        f'<a class="btn" href="mailto:info@benzene-group.com?subject=Free%20check">Ask for a free check</a><a class="btn" href="{SP.MAIN}/sample-screening-report.html">See a sample report</a></div>'
        '<p class="note">Journalists: you are welcome to quote these figures with credit to Benzene and a link to this page. Questions to info@benzene-group.com.</p>')
os.makedirs(OUT + '/delay-index', exist_ok=True)
open(OUT + '/delay-index/index.html', 'w', encoding='utf-8').write(SP.page('Grid Delay Index: how often UK grid connection dates move | Benzene',
     f'{len(ev)} grid connection date moves of a month or more since {SP.wk(SP.EV_FIRST)}; {round(100*alln["later_share"])}% of near-term projects moved later over two years.', '/delay-index/', body))
sm = open(OUT + '/sitemap.xml').read()
if '/delay-index/' not in sm:
    sm = sm.replace('</urlset>', f'<url><loc>{HOST}/delay-index/</loc><lastmod>{SP.TODAY}</lastmod></url>\n</urlset>')
    open(OUT + '/sitemap.xml', 'w').write(sm)
print('delay index', latest, L, len(ev))
