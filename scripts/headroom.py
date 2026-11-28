import os
"""Combine distribution network capacity heat maps into data/headroom.json for the queue map.

Inputs (inputs/headroom/), downloaded from each operator's open data portal:
  ukpn-capacity-heatmap.json   UK Power Networks, LTDS Capacity Heatmap (CC BY 4.0)
  spen-heatmaps.json           SP Energy Networks, distribution capacity heatmaps SPD and SPM (CC BY 4.0)
  enwl-heatmaps.json           Electricity North West, primary and BSP heat maps (CC BY 4.0)
  ssen-headroom-dashboard.json SSEN Distribution, Headroom Dashboard Data March 2026 (CC BY 4.0), from data-api.ssen.co.uk
Northern Powergrid stays live on the map (fetched in the browser), so it is not in this file.

Output rows: [operator index, name, type (G grid supply, B bulk supply, P primary),
              kV, easting, northing, generation MW, generation rating, demand MW, demand rating]
Ratings are the operator's own traffic light (G, A, R) or '' where the operator publishes none.
"""
import json, re
from pyproj import Transformer

T = Transformer.from_crs('EPSG:4326', 'EPSG:27700', always_xy=True)
OPS = [
    {'id': 'UKPN', 'name': 'UK Power Networks', 'area': 'London, the South East and the East of England',
     'credit': 'Contains UK Power Networks data, CC BY 4.0', 'url': 'https://ukpowernetworks.opendatasoft.com/explore/dataset/ukpn-capacity-heatmap/', 'date': '19 October 2026'},
    {'id': 'SPEN', 'name': 'SP Energy Networks', 'area': 'central and southern Scotland, Merseyside, Cheshire and North Wales',
     'credit': 'Contains SP Energy Networks data, CC BY 4.0', 'url': 'https://spenergynetworks.opendatasoft.com/', 'date': '9 and 12 June 2026'},
    {'id': 'ENWL', 'name': 'Electricity North West', 'area': 'the North West of England',
     'credit': 'Contains Electricity North West data, CC BY 4.0', 'url': 'https://electricitynorthwest.opendatasoft.com/', 'date': '29 October 2026'},
    {'id': 'SSEN', 'name': 'SSEN Distribution', 'area': 'the north of Scotland and central southern England',
     'credit': 'Contains SSEN Distribution data, CC BY 4.0', 'url': 'https://data.ssen.co.uk/@ssen-distribution/generation-availability-and-network-capacity', 'date': '11 March 2026'},
]


def rag(v):
    v = (v or '').strip().lower()
    return {'green': 'G', 'amber': 'A', 'red': 'R'}.get(v, '')


def mw(v):
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return None


def kv(v):
    nums = [float(x) for x in re.findall(r'[\d.]+', str(v or ''))]
    return max(nums) if nums else None


def en(lat, lon):
    e, n = T.transform(float(lon), float(lat))
    return round(e), round(n)


def main():
    rows = []
    for r in json.load(open('inputs/headroom/ukpn-capacity-heatmap.json')):
        if r.get('latitude') is None:
            continue
        e, n = en(r['latitude'], r['longitude'])
        rows.append([0, r['name'], 'P', kv(r.get('voltages')), e, n, mw(r['generationavailablecapacity']), rag(r['generationconstraint']),
                     mw(r['demandavailablecapacity']), rag(r['demandconstraint'])])
    s = json.load(open('inputs/headroom/spen-heatmaps.json'))
    for r in s['spd']:
        if r.get('latitude') is None:
            continue
        e, n = en(r['latitude'], r['longitude'])
        rows.append([1, r['name'].title(), 'P', kv(r.get('voltage')), e, n, mw(r['generationavailablecapacity']), rag(r['generationconstraint']),
                     mw(r['demandavailablecapacity']), rag(r['demandconstraint'])])
    for r in s['spm']:
        if r.get('lat') is None:
            continue
        e, n = en(r['lat'], r['lon'])
        rows.append([1, (r.get('site_name') or r['name']).title(), 'B' if r['type'] == 'BSP' else 'P', kv(r.get('voltage')), e, n,
                     mw(r['generationavailablecapacity']), rag(r['generationconstraint']), mw(r['demandavailablecapacity']), rag(r['demandconstraint'])])
    w = json.load(open('inputs/headroom/enwl-heatmaps.json'))
    for key, t in (('bsp', 'B'), ('pry', 'P')):
        for r in w[key]:
            g = r.get('geo_point_2d')
            if not g:
                continue
            e, n = en(g['lat'], g['lon'])
            num = r.get('bsp_number') if key == 'bsp' else r.get('pry_number')
            rows.append([2, f"{'Bulk supply point' if t == 'B' else 'Primary substation'} {num}", t, r.get('voltage_kv'), e, n,
                         mw(r['generation_headroom_non_firm_inverter_based_mw']), '', mw(r['demand_headroom_firm_mw']), ''])
    for r in json.load(open('inputs/headroom/ssen-headroom-dashboard.json')):
        if r.get('lat') is None:
            continue
        e, n = en(r['lat'], r['lon'])
        rows.append([3, r['n'], {'GSP': 'G', 'BSP': 'B'}.get(r['t'], 'P'), kv(r.get('kv')), e, n, mw(r['g']), rag(r['gr']), mw(r['d']), rag(r['dr'])])
    out = {'ops': OPS, 'rows': rows}
    json.dump(out, open('data/headroom.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    # keep a dated copy of every refresh: a headroom history nobody else keeps
    import datetime as _dt
    os.makedirs('data/headroom-history', exist_ok=True)
    json.dump(out, open(f'data/headroom-history/{_dt.date.today().isoformat()}.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    from collections import Counter
    print(len(rows), 'rows', dict(Counter(r[0] for r in rows)), 'ratings', dict(Counter(r[7] for r in rows)))


if __name__ == '__main__':
    main()
