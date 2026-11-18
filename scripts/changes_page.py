"""Register changes page: what moved between consecutive NESO TEC Register files.

Usage: python3 scripts/changes_page.py
Reads every register in archive/tec/ plus the newest in inputs/, saves a structured
record of each consecutive pair to data/changes/<new register>.json (kept forever,
so the history survives when old CSVs are pruned), and writes site/changes.html.
"""
import glob, html, json, os, re, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from queue_watch import load, num, date, fdate, reg_date
from site_shell import shell

E = html.escape


def regdt(p):
    m = re.search(r'(\d{1,2})-([a-z]+)-(\d{4})', os.path.basename(p))
    return datetime.strptime(' '.join(m.groups()), '%d %B %Y') if m else datetime.min


def firm(n):
    n = n.title()
    for a, b in ((' Llp', ' LLP'), (' Uk ', ' UK '), (' Uk', ' UK'), (' Plc', ' plc'), (' Ltd', ' Ltd')):
        n = n.replace(a, b)
    return n


def rec(r):
    return {'project': r['Project Name'], 'developer': firm(r['Customer Name']), 'site': r['Connection Site'],
            'tech': r['Plant Type'], 'mw': round(num(r['MW Increase / Decrease']), 1), 'date': r['MW Effective From'],
            'gate': r['Gate'] or '', 'status': r['Project Status']}


def structured(oldp, newp):
    old, new = load(oldp), load(newp)
    out = {'old': reg_date(oldp), 'new': reg_date(newp), 'joined': [], 'left': [], 'dates': [], 'other': []}
    for k in sorted(new.keys() - old.keys()):
        out['joined'].append(rec(new[k]))
    for k in sorted(old.keys() - new.keys()):
        out['left'].append(rec(old[k]))
    for k in sorted(old.keys() & new.keys()):
        a, b = old[k], new[k]
        r = rec(b)
        if a['MW Effective From'] != b['MW Effective From']:
            da, db = date(a['MW Effective From']), date(b['MW Effective From'])
            r2 = dict(r, was=a['MW Effective From'], years=round((db - da).days / 365.25, 1) if da and db else None)
            out['dates'].append(r2)
        bits = []
        if a['Connection Site'] != b['Connection Site']:
            bits.append(f"moved from {a['Connection Site']} to {b['Connection Site']}")
        if num(a['MW Increase / Decrease']) != num(b['MW Increase / Decrease']):
            bits.append(f"size {num(a['MW Increase / Decrease']):,.1f} MW to {num(b['MW Increase / Decrease']):,.1f} MW")
        if (a['Gate'] or '') != (b['Gate'] or ''):
            bits.append(f"Gate {a['Gate'] or 'not shown'} to {b['Gate'] or 'not shown'}")
        if a['Project Status'] != b['Project Status']:
            bits.append(f"status {a['Project Status']} to {b['Project Status']}")
        if bits:
            out['other'].append(dict(r, what='; '.join(bits)))
    return out


def gate(g):
    return f'Gate {g}' if g else 'No Gate shown'


def table(head, rows):
    if not rows:
        return '<p class="none">None.</p>'
    h = ''.join(f'<th{" class=n" if c.startswith("#") else ""}>{E(c.lstrip("#"))}</th>' for c in head)
    body = ''.join('<tr>' + ''.join(f'<td{" class=n" if head[i].startswith("#") else ""}>{v}</td>' for i, v in enumerate(r)) + '</tr>' for r in rows)
    return f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'


def proj(r):
    return f'<b>{E(r["project"])}</b><span class="dev">{E(r["developer"])}</span>'


def block(c):
    dl = sorted(c['dates'], key=lambda r: -(r['years'] or 0))
    later = sum(1 for r in dl if (r['years'] or 0) > 0)
    earlier = sum(1 for r in dl if (r['years'] or 0) < 0)
    summ = (f"{len(c['joined'])} joined, {len(c['left'])} left, {len(dl)} connection date"
            f"{'s' if len(dl) != 1 else ''} moved ({later} later, {earlier} earlier), {len(c['other'])} other change{'s' if len(c['other']) != 1 else ''}.")
    parts = [f'<p class="summ">{summ}</p>',
             '<h3>Connection dates that moved</h3>',
             table(['Project', 'Site', '#MW', 'Was', 'Now', '#Change'],
                   [[proj(r), E(r['site']), f"{r['mw']:,.0f}", E(fdate(r['was'])), E(fdate(r['date'])),
                     (f"{'+' if r['years'] > 0 else ''}{r['years']:.1f} yrs" if r['years'] is not None else 'n/a')] for r in dl]),
             '<h3>Joined the queue</h3>',
             table(['Project', 'Site', 'Technology', '#MW', 'Contracted date', 'Gate'],
                   [[proj(r), E(r['site']), E(r['tech']), f"{r['mw']:,.0f}", E(fdate(r['date'])), gate(r['gate'])] for r in c['joined']]),
             '<h3>Left the register</h3>',
             table(['Project', 'Site', 'Technology', '#MW', 'Was contracted for'],
                   [[proj(r), E(r['site']), E(r['tech']), f"{r['mw']:,.0f}", E(fdate(r['date']))] for r in c['left']]),
             '<h3>Gate, size, site and status changes</h3>',
             table(['Project', 'Site', 'What changed'], [[proj(r), E(r['site']), E(r['what'])] for r in c['other']])]
    return '\n'.join(parts)


CSS = """
.chg { padding-block: 8px 56px }
.chg h2 { margin-top: 8px }
.chg h3 { font-size: 18px; margin: 28px 0 10px; font-weight: 600 }
.summ { font-size: 17px; color: var(--fg-2); max-width: 70ch }
.tw { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--card) }
.tw table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 560px }
.tw th { text-align: left; font: 600 11.5px var(--mono); letter-spacing: .05em; text-transform: uppercase; color: var(--fg-3); padding: 10px 12px; border-bottom: 1px solid var(--line) }
.tw td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; color: var(--fg-2) }
.tw tr:last-child td { border-bottom: 0 }
.tw td b { color: var(--fg); font-weight: 600; display: block }
.tw .dev { font-size: 12.5px; color: var(--fg-3) }
.tw .n { text-align: right; font-family: var(--mono); white-space: nowrap }
.none { color: var(--fg-3) }
.chg details { margin-top: 28px; border-top: 1px solid var(--line); padding-top: 18px }
.chg details summary { cursor: pointer; font-weight: 600 }
.qwcta { margin-top: 36px; padding: 20px; border: 1px solid var(--line); border-radius: 10px; background: var(--card); display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: center; justify-content: space-between }
.qwcta p { max-width: 60ch; color: var(--fg-2) }
.srcline { margin-top: 24px; font-size: 13px; color: var(--fg-3); max-width: 75ch }
"""


def main():
    regs = sorted(glob.glob('archive/tec/*.csv') + glob.glob('inputs/tec-register-*.csv'), key=regdt)
    os.makedirs('data/changes', exist_ok=True)
    for a, b in zip(regs, regs[1:]):
        out = f"data/changes/{os.path.basename(b).replace('.csv', '.json')}"
        if not os.path.exists(out):
            json.dump(structured(a, b), open(out, 'w'), indent=1)
    hist = sorted(glob.glob('data/changes/*.json'), key=regdt, reverse=True)
    if not hist:
        print('no register pairs yet'); return
    cs = [json.load(open(p)) for p in hist]
    latest = cs[0]
    body = [f'<section class="page-head"><div class="wrap"><p class="eyebrow">Register changes</p>',
            '<h1>What changed in the grid queue</h1>',
            f'<p class="lead">NESO republishes its whole connection register twice a week. We compare each file with the one before and list every project that joined, left, or moved its date. Latest comparison: the register of {E(latest["new"])} against {E(latest["old"])}.</p></div></section>',
            '<section class="chg"><div class="wrap">',
            f'<h2>{E(latest["old"])} to {E(latest["new"])}</h2>', block(latest)]
    for c in cs[1:8]:
        body.append(f'<details><summary>{E(c["old"])} to {E(c["new"])}</summary>{block(c)}</details>')
    body.append('<div class="qwcta"><p><b>Want this for your own sites?</b> Queue watch emails you after every new register with what changed at the substations or projects you pick. £99 a month per site, five sites for the price of four.</p><a class="btn" href="/pricing.html#queue-watch">Start queue watch</a></div>')
    body.append('<p class="srcline"><span class="tag c">Confirmed</span> Every row comes from NESO\'s TEC Register files named above, compared line by line. Transmission connections only. A project can appear as leaving and joining if NESO renumbers it. Dates are the contracted dates in the register, not forecasts.</p>')
    body.append('</div></section>')
    inner = '<!--CHG-->\n' + '\n'.join(body) + '\n<!--/CHG-->'
    os.makedirs('out', exist_ok=True)
    open('out/changes_body.html', 'w', encoding='utf-8').write(inner)
    page = shell('Grid queue changes | Benzene',
                 'Every project that joined, left or moved its connection date between NESO TEC Register files, compared line by line.',
                 'changes.html', inner, CSS)
    open('site/changes.html', 'w', encoding='utf-8').write(page)
    print(f'site/changes.html written: {len(cs)} comparison(s), latest {latest["old"]} to {latest["new"]}')


if __name__ == '__main__':
    main()
