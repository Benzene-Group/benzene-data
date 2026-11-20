"""Write site/sample-data-centre-brief.html: a worked sample of the data centre power brief.

A snapshot dated 20 November 2026. Register figures: NESO TEC Register file of 16 November 2026.
Local figures: Northern Powergrid heat map data (last processed 27 July 2026) and SSEN Distribution
Headroom Dashboard Data (March 2026), both read 19 November 2026. Approved for publication by Ben, 20 Nov 2026.
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from site_shell import shell
from sample_note_css import CSS
import html
E = html.escape

REG = list(csv.DictReader(open('inputs/tec-register-16-november-2026.csv', encoding='utf-8-sig')))
MON = 'January February March April May June July August September October November December'.split()


def fd(d):
    return f"{int(d[:2])} {MON[int(d[3:5]) - 1]} {d[6:]}" if d else ''


def tech(p):
    t = p.replace('PV Array (Photo Voltaic/solar)', 'Solar').replace('Energy Storage System', 'Storage').replace('Wind Offshore', 'Offshore wind')
    t = t.replace('OCGT (Open Cycle Gas Turbine)', 'Gas turbine (OCGT)').replace('CCGT (Combined Cycle Gas Turbine)', 'Gas (CCGT)')
    t = t.replace('CHP (Combined Heat and Power)', 'CHP').replace('Oil & AGT (Advanced Gas Turbine)', 'Oil and gas turbine')
    return t.replace(';', ', ')


AREAS = [('Blyth', 'Blyth, Northumberland'), ('Ratcliffe', 'Ratcliffe-on-Soar, Nottinghamshire'), ('Didcot', 'Didcot, Oxfordshire')]
S = {}
for key, label in AREAS:
    rs = [r for r in REG if key.lower() in r['Connection Site'].lower()]
    q = [r for r in rs if float(r['MW Increase / Decrease'] or 0) > 0]
    gate = {}
    for r in q:
        gate[r['Gate'] or ''] = gate.get(r['Gate'] or '', 0) + float(r['MW Increase / Decrease'])
    dates = sorted(r['MW Effective From'][6:] + r['MW Effective From'][3:5] for r in q)
    S[key] = dict(label=label, rows=rs, q=q, con=sum(float(r['MW Connected'] or 0) for r in rs),
                  qmw=sum(float(r['MW Increase / Decrease']) for r in q), gate=gate,
                  first=dates[0], last=dates[-1])

ym = lambda s: f"{MON[int(s[4:]) - 1][:3]} {s[:4]}"
num = lambda x: f"{x:,.2f}".rstrip('0').rstrip('.')


def gate_txt(g):
    parts = []
    for k, lab in (('2', 'Gate 2'), ('1', 'Gate 1'), ('', 'No Gate shown')):
        if g.get(k):
            parts.append(f"{lab}: {num(g[k])}")
    return '<br>'.join(parts)


summary = ''.join(
    f"<tr><td><b>{E(S[k]['label'])}</b></td><td class=n>{len(S[k]['rows'])}</td><td class=n>{num(S[k]['con'])}</td>"
    f"<td class=n>{num(S[k]['qmw'])}</td><td>{gate_txt(S[k]['gate'])}</td><td>{ym(S[k]['first'])} to {ym(S[k]['last'])}</td></tr>"
    for k, _ in AREAS)


def proj_rows(k):
    out = []
    for r in sorted(S[k]['rows'], key=lambda r: (float(r['MW Increase / Decrease'] or 0) <= 0, r['MW Effective From'][6:] + r['MW Effective From'][3:5])):
        inc = float(r['MW Increase / Decrease'] or 0)
        name = r['Project Name'].split('\t')[-1].strip()
        mw = f"{num(inc)} queued" + (f" (plus {num(float(r['MW Connected']))} connected)" if float(r['MW Connected'] or 0) else '') if inc > 0 else f"{num(float(r['MW Connected']))} connected"
        out.append(f"<tr><td><b>{E(name)}</b><span class=dev>{E(r['Connection Site'].title().replace('Kv', 'kV').replace('Gsp', 'GSP').replace('Gis', 'GIS').replace('Ratcliffe-On-Soar', 'Ratcliffe-on-Soar'))}</span></td>"
                   f"<td class=n>{mw}</td><td>{E(tech(r['Plant Type']))}</td><td>{'Gate ' + r['Gate'] if r['Gate'] else ('' if inc <= 0 else 'Not shown')}</td>"
                   f"<td>{fd(r['MW Effective From']) if inc > 0 else ''}</td><td>{E(r['Project Status'])}</td></tr>")
    return ''.join(out)


LOCAL = {
    'Blyth': ('Northern Powergrid', 'Heat map data, last processed 27 July 2026', 'MW', [
        ('Blyth', 'Grid supply point, 132 kV', 'At the GSP', 0.0, 'Amber', 45.8, 'Amber'),
        ('Blyth', 'Grid supply point, 66 kV', 'At the GSP', 0.0, 'Green', 0.0, 'Green'),
        ('Maddison Street', 'Primary, 11 kV', '1.7 km', 0.0, 'Green', 0.0, 'Green'),
        ('Wansbeck', 'Primary, 11 kV', '2.1 km', 0.0, 'Amber', 0.0, 'Amber'),
        ('Reservoir', 'Primary, 20 kV', '4.2 km', 0.0, 'Amber', 0.0, 'Green'),
        ('Ashington', 'Primary, 11 kV', '4.3 km', 0.0, 'Red', 0.0, 'Amber')]),
    'Didcot': ('SSEN Distribution', 'Headroom Dashboard Data, March 2026', 'MVA', [
        ('Milton', 'Primary, 33 kV', '0.9 km', 0.0, 'Red', 0.0, 'Red'),
        ('Drayton', 'Bulk supply point, 132 kV', '4.3 km', 0.0, 'Red', 0.0, 'Red'),
        ('Fulscot', 'Primary, 33 kV', '4.3 km', 0.0, 'Red', 0.0, 'Red'),
        ('Culham', 'Primary, 132 kV', '4.8 km', 0.0, 'Red', 15.5, 'Green'),
        ('Winsmore Lane', 'Primary, 33 kV', '5.3 km', 0.0, 'Red', 0.0, 'Red'),
        ('Harwell', 'Primary, 132 kV', '6.0 km', 0.0, 'Red', 39.1, 'Green')]),
}


def local_table(k):
    op, src, unit, rows = LOCAL[k]
    body = ''.join(f"<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{c}</td><td class=n>{g:.1f}</td><td><span class='rag {gc[0]}'>{gc}</span></td>"
                   f"<td class=n>{dm:.1f}</td><td><span class='rag {dc[0]}'>{dc}</span></td></tr>" for a, b, c, g, gc, dm, dc in rows)
    return (f"<div class=\"tw\"><table><thead><tr><th>Substation</th><th>Type</th><th>Distance</th><th class=n>Generation headroom MW</th><th>Rating</th>"
            f"<th class=n>Demand headroom {unit}</th><th>Rating</th></tr></thead><tbody>{body}</tbody></table></div>"
            f"<p class=\"small\">{op}, {src}, read 19 November 2026, shown as published. Distances are straight-line and approximate.</p>")


b, r, d = S['Blyth'], S['Ratcliffe'], S['Didcot']
body = f"""
<section class="page-head"><div class="wrap">
  <p class="eyebrow">Sample data centre power brief</p>
  <h1>A 100 MW data centre: Blyth, Ratcliffe-on-Soar or Didcot?</h1>
  <p class="lead">A worked example of our data centre power brief, built from real public data. There is no client. We picked three areas near transmission substations as examples of different kinds of location; nothing here says a data centre is planned at any of them. A real brief compares up to three sites of your choosing and arrives within seven working days.</p>
</div></section>

<section class="note"><div class="wrap">
<div class="paper">
  <p class="meta">20 November 2026 &middot; Prepared by Benzene as a sample &middot; A desk review of public registers and published network data. Not legal advice, an engineering study or a connection offer.</p>

  <h2>1. The short answer</h2>
  <ul>
    <li><b>Blyth.</b> The busiest node of the three: {num(b['qmw'])} MW queued across {len(b['q'])} projects, all offshore wind or storage, dated {b['first'][:4]} to {b['last'][:4]}. It also has the most generation queuing nearby, which matters if you want to talk about co-location or a private wire. <span class="tag c">Confirmed</span> figures, <span class="tag i">Inferred</span> reading.</li>
    <li><b>Ratcliffe-on-Soar.</b> The least crowded: {num(r['qmw'])} MW queued across {len(r['q'])} projects, dated {r['first'][:4]} to {r['last'][:4]}, on a former coal station site that already has 225 MW of storage and gas turbines connected. <span class="tag c">Confirmed</span> figures, <span class="tag i">Inferred</span> reading.</li>
    <li><b>Didcot.</b> {num(d['con'])} MW connected and {num(d['qmw'])} MW queued across {len(d['q'])} entries, dated {d['first'][:4]} to {d['last'][:4]}. The only one of the three with a Gate 2 project (300 MW). The nearest local substations are rated Red for new demand, apart from two 132 kV primaries. <span class="tag c">Confirmed</span></li>
  </ul>
  <p>None of this says whether 100 MW of demand can connect at any of them. NESO's register lists generation and storage, not demand applications. That is a question for NESO and the network operator, and section 6 lists what to ask. <span class="tag i">Inferred</span></p>

  <div class="tw"><table class="kv"><tbody>
    <tr><th>Request modelled</th><td>A 100 MW data centre, comparing three candidate areas</td></tr>
    <tr><th>Client</th><td>None: sample only</td></tr>
    <tr><th>Register data as of</th><td>NESO TEC Register file of 16 November 2026</td></tr>
    <tr><th>Local network data as of</th><td>Northern Powergrid, last processed 27 July 2026; SSEN Distribution, March 2026. National Grid Electricity Distribution not yet covered.</td></tr>
  </tbody></table></div>

  <h2>2. The transmission substations</h2>
  <div class="tw"><table><thead><tr><th>Area</th><th class=n>Register rows</th><th class=n>Connected MW</th><th class=n>Queued MW</th><th>Queued MW by Gate</th><th>Contracted dates (queued)</th></tr></thead><tbody>{summary}</tbody></table></div>
  <p class="small">Confirmed from the NESO TEC Register of 16 November 2026. The counts and sums are ours, over every row whose connection site name contains the area name. "Queued" is the MW increase not yet connected.</p>
  <h3>Blyth</h3>
  <div class="tw"><table><thead><tr><th>Project</th><th class=n>MW</th><th>Technology</th><th>Gate</th><th>Contracted date</th><th>Register status</th></tr></thead><tbody>{proj_rows('Blyth')}</tbody></table></div>
  <h3>Ratcliffe-on-Soar</h3>
  <div class="tw"><table><thead><tr><th>Project</th><th class=n>MW</th><th>Technology</th><th>Gate</th><th>Contracted date</th><th>Register status</th></tr></thead><tbody>{proj_rows('Ratcliffe')}</tbody></table></div>
  <h3>Didcot</h3>
  <div class="tw"><table><thead><tr><th>Project</th><th class=n>MW</th><th>Technology</th><th>Gate</th><th>Contracted date</th><th>Register status</th></tr></thead><tbody>{proj_rows('Didcot')}</tbody></table></div>
  <p class="small">All rows Confirmed from the NESO TEC Register of 16 November 2026, names as the register shows them. Two Didcot storage rows list "Demand" in their plant type; that is battery import, not a data centre. No changes at any of the three areas between the registers of 13 and 16 November.</p>

  <h2>3. The local network</h2>
  <h3>Blyth (Northern Powergrid)</h3>
  {local_table('Blyth')}
  <h3>Didcot (SSEN Distribution)</h3>
  {local_table('Didcot')}
  <h3>Ratcliffe-on-Soar (National Grid Electricity Distribution)</h3>
  <p>Not yet covered. We have asked National Grid Electricity Distribution to confirm the licence terms for its headroom data before we show it. A real brief would say the same, or quote the operator's own map with its date.</p>
  <p><b>What this means.</b> Local substations near Blyth and Didcot show tens of MW of demand headroom at most, and often none. 100 MW is a transmission-scale request: the local network is a guide to how tight the area is, not a route to connection. <span class="tag i">Inferred</span></p>
  <p class="small">Confirmed from each operator's published data, shown as published, with the operator's caveats. Northern Powergrid: Supported by <a href="https://northernpowergrid.opendatasoft.com/p/opendatalicence/" target="_blank" rel="noopener">Northern Powergrid Open Data</a>. SSEN: Contains <a href="https://data.ssen.co.uk/@ssen-distribution/generation-availability-and-network-capacity" target="_blank" rel="noopener">SSEN Distribution data</a>, CC BY 4.0; SSEN gives demand headroom in MVA. Operators work out headroom their own way, so compare within an area rather than across them.</p>

  <h2>4. Generation nearby</h2>
  <p>This sample lists only projects on the same substations and grid supply points (section 2). A real brief adds register projects within about 10 km, for co-location or private wire conversations.</p>

  <h2>5. The rules that apply</h2>
  <ul>
    <li><b>Ofgem's proposed Data Centre Commitment Fee.</b> £237,500 to £712,500 per MW, for projects above 40 MW on the transmission system, and above 40 MW on the distribution system where a Transmission Entry Assessment applies. Held from offer acceptance to energisation, returned if the project proceeds as planned and forfeited if it terminates or fails the requirements. <span class="tag c">Confirmed</span> Ofgem, Curate consultation, 29 July 2026, paragraphs 4.1, 5.1 and 5.3. A proposal: the consultation closed on 16 September 2026 and Ofgem said it intends to decide later in 2026. We had not found a decision by 20 November 2026.</li>
    <li><b>At 100 MW</b> that would be £23.75m to £71.25m, the same at all three areas. <span class="tag i">Inferred</span> 100 &times; £237,500 and 100 &times; £712,500.</li>
    <li><b>The Data Centre Covenant.</b> HM Treasury's policy paper of 28 October 2026 sets five tests. For "strategic" data centres that meet them, the government offers to reserve and reallocate grid connections, identify additional capacity and accelerate connections before 2030. "Strategic data centre" is not yet defined and no MW threshold is given. <span class="tag c">Confirmed</span> GOV.UK, The Data Centre Covenant.</li>
  </ul>

  <h2>6. Questions to put to NESO and the network operator</h2>
  <ol>
    <li>Is there a demand connection point at this substation for 100 MW, and at what voltage?</li>
    <li>What demand is already contracted or applied for at this node? The register will not tell us.</li>
    <li>What reinforcement works are needed, and what are their planned dates?</li>
    <li>Would a non-firm or flexible connection be offered earlier than a firm one?</li>
    <li>Would the 40 MW fee threshold apply to the project as one application, or stage by stage?</li>
  </ol>

  <h2>7. Comparison</h2>
  <div class="tw"><table><thead><tr><th></th><th>Blyth</th><th>Ratcliffe-on-Soar</th><th>Didcot</th></tr></thead><tbody>
    <tr><td><b>Queued MW at node</b> <span class="tag c">Confirmed</span></td><td>{num(b['qmw'])}</td><td>{num(r['qmw'])}</td><td>{num(d['qmw'])}</td></tr>
    <tr><td><b>Gate 2 MW queued</b> <span class="tag c">Confirmed</span></td><td>{num(b['gate'].get('2', 0))}</td><td>{num(r['gate'].get('2', 0))}</td><td>{num(d['gate'].get('2', 0))}</td></tr>
    <tr><td><b>Latest queued date</b> <span class="tag c">Confirmed</span></td><td>{ym(b['last'])}</td><td>{ym(r['last'])}</td><td>{ym(d['last'])}</td></tr>
    <tr><td><b>Connected at node</b> <span class="tag c">Confirmed</span></td><td>{num(b['con'])} MW</td><td>{num(r['con'])} MW</td><td>{num(d['con'])} MW</td></tr>
    <tr><td><b>Best local demand headroom nearby</b> <span class="tag c">Confirmed</span></td><td>45.8 MW (Blyth 132 kV GSP, Amber)</td><td>Not yet covered</td><td>39.1 MVA (Harwell, Green)</td></tr>
    <tr><td><b>Fee at 100 MW, if adopted</b> <span class="tag i">Inferred</span></td><td>£23.75m to £71.25m</td><td>Same</td><td>Same</td></tr>
  </tbody></table></div>

  <h2>8. Sources and limits</h2>
  <div class="tw"><table><thead><tr><th>Source</th><th>Used for</th></tr></thead><tbody>
    <tr><td>NESO TEC Register, file of 16 November 2026</td><td>Sections 1, 2 and 7</td></tr>
    <tr><td>Northern Powergrid heat map data, last processed 27 July 2026</td><td>Section 3, Blyth</td></tr>
    <tr><td>SSEN Distribution, Headroom Dashboard Data, March 2026</td><td>Section 3, Didcot</td></tr>
    <tr><td><a href="https://www.ofgem.gov.uk/sites/default/files/2026-07/Proposed-data-centre-connection-reforms-curate-consultation-document.pdf" target="_blank" rel="noopener">Ofgem, Curate: Demand Connections Reform consultation, 29 July 2026</a></td><td>Section 5, fee</td></tr>
    <tr><td><a href="https://www.gov.uk/government/publications/data-centre-covenant/the-data-centre-covenant" target="_blank" rel="noopener">HM Treasury, The Data Centre Covenant, 28 October 2026</a></td><td>Section 5, Covenant</td></tr>
  </tbody></table></div>
  <p class="small"><span class="tag c">Confirmed</span> read on a primary source. <span class="tag r">Reported</span> taken from a named source we have not checked against the original. <span class="tag i">Inferred</span> our reading of confirmed facts. The register lists generation and storage, not demand, and we have seen no demand offer at these sites. We do not forecast connection dates. Registers change, so findings are correct only as of the dates shown. Not legal advice or an engineering study.</p>
</div>

<div class="qwcta"><p><b>Weighing real sites?</b> A data centre power brief costs £2,950 for up to three sites, or £1,950 for one, and takes seven working days. Or start with a free check: tell us the nearest substation and we will send you what is queued there.</p><a class="btn" href="#contact">Free substation check</a></div>
</div></section>
"""

page = shell('Sample data centre power brief | Benzene',
             'A worked sample of the Benzene data centre power brief: a 100 MW request compared across Blyth, Ratcliffe-on-Soar and Didcot, with the transmission queue, local headroom and the rules that apply.',
             'sample-data-centre-brief.html', body, CSS)
assert '—' not in page and '–' not in page
open('site/sample-data-centre-brief.html', 'w', encoding='utf-8').write(page)
print('written', len(page))
