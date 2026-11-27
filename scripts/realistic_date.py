"""Realistic connection dates, learned from our own register history.

Compares the earliest archived TEC register copy with the newest weekly copy (about two years apart),
for every project that was waiting to connect in the earlier copy. Groups projects by technology and by
how far away their contracted date was (under 2 years, 2 to 5 years, 5 years or more), and measures:
share whose date moved a month or more later, median move when it did, and share that left the register.
model() returns the table; assess(tech, date_iso, today) gives one project's date risk and likely date.
"""
import csv, glob, os, statistics as st, datetime as dt, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_N = 15


def tech_class(pt):
    p = (pt or '').lower()
    if 'offshore' in p: return 'Offshore wind'
    if 'wind' in p: return 'Onshore wind'
    if pt.strip() in ('Energy Storage System', 'Battery storage'): return 'Battery storage'
    if 'storage' in p and ('pv' in p or 'solar' in p): return 'Solar + storage'
    if 'pv' in p or 'solar' in p: return 'Solar'
    return 'Other'


def horizon(years):
    return 'under 2 years' if years < 2 else ('2 to 5 years' if years < 5 else '5 years or more')


def _pdate(s):
    s = (s or '').strip()
    for f in ('%Y-%m-%d', '%d/%m/%Y'):
        try: return dt.datetime.strptime(s[:10], f).date()
        except ValueError: pass
    return None


def _load(f):
    out = {}
    for r in csv.DictReader(open(f, encoding='utf-8-sig')):
        out.setdefault(r['Project Number'], (r, _pdate(r['MW Effective From'])))
    return out


def _fdate(f):
    return dt.date.fromisoformat(os.path.basename(f)[13:23])


_M = None


def model():
    global _M
    if _M: return _M
    files = sorted(glob.glob(os.path.join(ROOT, 'archive/tec-weekly/tec-register-20*.csv')))
    fa, fb = files[0], files[-1]
    A, B = _load(fa), _load(fb)
    ref = _fdate(fa)
    groups = collections.defaultdict(lambda: {'n': 0, 'left': 0, 'moves': []})
    for pid, (r, d) in A.items():
        if d is None or (float(r['MW Connected'] or 0) > 0 and float(r['MW Increase / Decrease'] or 0) <= 0):
            continue
        h = horizon((d - ref).days / 365.25)
        for key in ((tech_class(r['Plant Type']), h), ('All', h)):
            g = groups[key]; g['n'] += 1
            if pid not in B: g['left'] += 1; continue
            d2 = B[pid][1]
            if d2: g['moves'].append((d2 - d).days / 30.44)
    table = {}
    for key, g in groups.items():
        v = g['moves']
        if not v: continue
        later = [x for x in v if x >= 1]
        table[key] = {'n': g['n'], 'stayed': len(v), 'later_share': len(later) / len(v),
                      'median_later': st.median(later) if later else 0.0, 'left_share': g['left'] / g['n']}
    _M = {'from': ref.isoformat(), 'to': _fdate(fb).isoformat(), 'table': table}
    return _M


def assess(tech, date_iso, today=None):
    d = _pdate(date_iso)
    if not d: return None
    today = today or dt.date.today()
    if d < today: return None
    m = model()
    h = horizon((d - today).days / 365.25)
    t = tech_class(tech) if tech not in ('Offshore wind', 'Onshore wind', 'Battery storage', 'Solar + storage', 'Solar', 'Other') else tech
    g = m['table'].get((t, h))
    basis = f'{t.lower()} projects'
    if not g or g['stayed'] < MIN_N:
        g = m['table'].get(('All', h)); basis = 'all projects'
    if not g: return None
    p = g['later_share']
    risk = 'High' if p >= 0.5 else ('Medium' if p >= 0.25 else 'Low')
    likely = d + dt.timedelta(days=round(g['median_later'] * 30.44)) if p >= 0.5 else d
    return {'risk': risk, 'likely': likely.isoformat(), 'later_share': round(p, 2), 'median_later_months': round(g['median_later'], 1),
            'left_share': round(g['left_share'], 2), 'sample': g['stayed'], 'basis': f'{basis} {h} from their date'}


if __name__ == '__main__':
    m = model(); print(m['from'], '->', m['to'])
    for k, v in sorted(m['table'].items()): print(k, v)
    print(assess('Battery storage', '2028-10-30'))
