"""Queue watch: compare two NESO TEC Register files and report what changed at watched sites.

Usage:
  python3 scripts/queue_watch.py OLD.csv NEW.csv watch/watchlist.json OUT_DIR
  python3 scripts/queue_watch.py OLD.csv NEW.csv --all OUT_DIR      (every site with a change)

watchlist.json:
  {"customers": [{"name": "Acme Solar", "email": "x@acme.co.uk",
                  "sites": ["Berkswell GSP"], "projects": ["PRO-003804"]}]}

Writes one plain-text alert per customer (or per site with --all) and changes.json.
Alerts are drafts for Ben to send. No em or en dashes in any output.
"""
import csv, json, os, re, sys
from collections import defaultdict
from datetime import datetime

def load(path):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    out, seen = {}, defaultdict(int)
    for r in rows:
        base = (r['Project ID'] or r['Project Number'] or r['Project Name'], r['Stage'] or '')
        seen[base] += 1
        out[base + (seen[base],)] = r
    return out

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def date(v):
    try:
        return datetime.strptime(v, '%d/%m/%Y')
    except (TypeError, ValueError):
        return None

def fdate(v):
    d = date(v)
    return d.strftime('%-d %B %Y') if d else (v or 'no date')

def reg_date(path):
    m = re.search(r'(\d{1,2})-([a-z]+)-(\d{4})', os.path.basename(path))
    return f"{int(m.group(1))} {m.group(2).capitalize()} {m.group(3)}" if m else os.path.basename(path)

def queued(r):
    return max(num(r['MW Increase / Decrease']), 0.0) if r['Project Status'] != 'Built' else 0.0

def label(r):
    s = f"{r['Project Name']} ({r['Customer Name'].title()}, {r['Plant Type']}"
    s += f", stage {r['Stage']})" if r['Stage'] else ')'
    return s

def diff(old, new):
    """Return {site: [change dicts]} plus per-site before/after summaries."""
    changes = defaultdict(list)
    for k in new.keys() - old.keys():
        r = new[k]
        changes[r['Connection Site']].append({'kind': 'joined', 'row': r,
            'text': f"New in the queue: {label(r)}, {num(r['MW Increase / Decrease']):,.0f} MW, contracted for {fdate(r['MW Effective From'])}."})
    for k in old.keys() - new.keys():
        r = old[k]
        changes[r['Connection Site']].append({'kind': 'left', 'row': r,
            'text': f"Left the register: {label(r)}, {num(r['MW Increase / Decrease']):,.0f} MW, which was contracted for {fdate(r['MW Effective From'])}."})
    for k in old.keys() & new.keys():
        a, b = old[k], new[k]
        site = b['Connection Site']
        if a['Connection Site'] != b['Connection Site']:
            changes[a['Connection Site']].append({'kind': 'moved_out', 'row': b,
                'text': f"Moved to {b['Connection Site']}: {label(b)}."})
            changes[site].append({'kind': 'moved_in', 'row': b,
                'text': f"Moved here from {a['Connection Site']}: {label(b)}, {num(b['MW Increase / Decrease']):,.0f} MW."})
            continue
        if a['MW Effective From'] != b['MW Effective From']:
            da, db = date(a['MW Effective From']), date(b['MW Effective From'])
            way = 'later' if (da and db and db > da) else 'earlier' if (da and db) else 'changed'
            changes[site].append({'kind': 'date_' + way, 'row': b,
                'text': f"Date {way}: {label(b)} moved from {fdate(a['MW Effective From'])} to {fdate(b['MW Effective From'])}."})
        if num(a['MW Increase / Decrease']) != num(b['MW Increase / Decrease']):
            changes[site].append({'kind': 'mw', 'row': b,
                'text': f"Size changed: {label(b)} went from {num(a['MW Increase / Decrease']):,.1f} MW to {num(b['MW Increase / Decrease']):,.1f} MW."})
        if (a['Gate'] or '') != (b['Gate'] or ''):
            changes[site].append({'kind': 'gate', 'row': b,
                'text': f"Gate changed: {label(b)} went from {a['Gate'] or 'no Gate shown'} to {b['Gate'] or 'no Gate shown'}."})
        if a['Project Status'] != b['Project Status']:
            changes[site].append({'kind': 'status', 'row': b,
                'text': f"Status changed: {label(b)} went from {a['Project Status']} to {b['Project Status']}."})
    return changes

def summary(rows, site):
    rs = [r for r in rows.values() if r['Connection Site'] == site and queued(r) > 0]
    mw = sum(queued(r) for r in rs)
    dates = [date(r['MW Effective From']) for r in rs if date(r['MW Effective From'])]
    g2 = sum(queued(r) for r in rs if (r['Gate'] or '').strip() == '2')
    return {'projects': len({r['Project ID'] for r in rs}), 'mw': mw, 'gate2_mw': g2,
            'earliest': min(dates).strftime('%B %Y') if dates else 'n/a',
            'latest': max(dates).strftime('%B %Y') if dates else 'n/a'}

ORDER = ['left', 'moved_out', 'date_earlier', 'gate', 'joined', 'moved_in', 'date_later', 'date_changed', 'mw', 'status']

def site_block(site, ch, old, new):
    a, b = summary(old, site), summary(new, site)
    lines = [site, '-' * len(site)]
    delta = b['mw'] - a['mw']
    pj = f"{b['projects']} project{'s' if b['projects'] != 1 else ''}"
    lines.append(f"Waiting to connect: {b['mw']:,.0f} MW across {pj} "
                 f"({'up' if delta > 0 else 'down'} {abs(delta):,.0f} MW since the last register)." if round(delta) else
                 f"Waiting to connect: {b['mw']:,.0f} MW across {pj} (no change in total).")
    span = f"all contracted for {b['earliest']}" if b['earliest'] == b['latest'] else f"contracted dates run from {b['earliest']} to {b['latest']}"
    lines.append(f"Holding Gate 2: {b['gate2_mw']:,.0f} MW; {span}.")
    if not ch:
        lines.append('No projects joined, left or changed date here.')
    else:
        lines.append('')
        lines.append('What changed:')
        for c in sorted(ch, key=lambda c: ORDER.index(c['kind'])):
            lines.append('* ' + c['text'])
    good = [c for c in ch if c['kind'] in ('left', 'moved_out', 'date_later')]
    if good:
        lines.append('')
        lines.append(f"Why it matters: {'these changes free' if len(good) > 1 else 'this change frees'} up room or pushes a competitor back. A smaller or later queue ahead of you can help your own date, "
                     "though NESO decides the order. [Inferred]")
    return '\n'.join(lines)

def alert(customer, sites, changes, old, new, od, nd):
    out = [f"Subject: Queue watch: {', '.join(sites[:2])}{' and more' if len(sites) > 2 else ''}, register of {nd}", '',
           f"Hello{(' ' + customer['first_name']) if customer.get('first_name') else ''},", '',
           f"NESO published a new connection register ({nd}). Here is what changed at the "
           f"site{'s' if len(sites) > 1 else ''} you watch, compared with the register of {od}.", '']
    for s in sites:
        out += [site_block(s, changes.get(s, []), old, new), '']
    out += ["Source: NESO TEC Register, files of " + od + " and " + nd + ". Transmission connections only. "
            "Figures are Confirmed from the register; anything marked Inferred is our reading.", '',
            "Best regards,", "Benzene", "info@benzene-group.com", "www.benzene-group.com"]
    text = '\n'.join(out)
    assert '—' not in text and '–' not in text
    return text

def main():
    oldp, newp, wl, outd = sys.argv[1:5]
    old, new = load(oldp), load(newp)
    od, nd = reg_date(oldp), reg_date(newp)
    changes = diff(old, new)
    os.makedirs(outd, exist_ok=True)
    json.dump({s: [c['text'] for c in v] for s, v in changes.items()}, open(f'{outd}/changes.json', 'w'), indent=1)
    if wl == '--all':
        customers = [{'name': s, 'sites': [s]} for s in sorted(changes)]
    else:
        customers = json.load(open(wl))['customers']
    for c in customers:
        sites = list(c.get('sites', []))
        for pid in c.get('projects', []):
            for r in list(new.values()) + list(old.values()):
                if r['Project Number'] == pid and r['Connection Site'] not in sites:
                    sites.append(r['Connection Site'])
        slug = re.sub(r'[^a-z0-9]+', '-', c['name'].lower()).strip('-')
        open(f'{outd}/{slug}.txt', 'w').write(alert(c, sites, changes, old, new, od, nd))
    n = sum(len(v) for v in changes.values())
    print(f'{n} changes at {len(changes)} sites; {len(customers)} alerts written to {outd}')

if __name__ == '__main__':
    main()
