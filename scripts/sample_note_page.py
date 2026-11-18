"""Write site/sample-landowner-note.html: a worked sample of the £495 landowner grid note.

A snapshot dated 18 November 2026. Register figures: NESO TEC Register file of 16 November 2026.
Local figures: Northern Powergrid heat map data (last processed 27 July 2026), read 18 November 2026.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from site_shell import shell
import html
E = html.escape

d = json.load(open('out/platform.json'))
S = {s['n']: s for s in d['sites']}
MON = 'January February March April May June July August September October November December'.split()
fd = lambda s: f"{int(s[8:10])} {MON[int(s[5:7]) - 1]} {s[:4]}" if s else 'No date'


def firm(n):
    n = n.title()
    for a, b in ((' Llp', ' LLP'), (' Uk ', ' UK '), (' Uk', ' UK'), ('Rwe ', 'RWE ')):
        n = n.replace(a, b)
    return n


def site_row(name, dist):
    s = S[name]
    ds = sorted(p[4] for p in s['p'] if p[4])
    span = f"{ds[0][:4]} to {ds[-1][:4]}" if ds[0][:4] != ds[-1][:4] else ds[0][:4]
    return (f"<tr><td><b>{E(name)}</b></td><td>{dist}</td><td class=n>{s['q']:,}</td><td class=n>{len(s['p'])}</td>"
            f"<td class=n>{s['g2']:,}</td><td>{span}</td></tr>")


cb = ['Creyke Beck 400kV Substation', 'Creyke Beck GSP', 'Creyke Beck 132kV']
nh = [n for n in S if 'North Humber Connection Node' in n]
nh_q = sum(S[n]['q'] for n in nh)
nh_n = sum(len(S[n]['p']) for n in nh)
nh_d = sorted(p[4] for n in nh for p in S[n]['p'] if p[4])
q400 = S[cb[0]]

projects = []
for n in cb:
    for p in S[n]['p']:
        projects.append((p[4], n, p))
projects.sort()
prow = ''.join(f"<tr><td><b>{E(p[0])}</b><span class=dev>{E(firm(p[1]))}</span></td><td>{E(n.replace(' Substation', ''))}</td>"
               f"<td class=n>{p[3]:,.0f}</td><td>{E(p[2])}</td><td>{'Gate ' + p[6] if p[6] else 'Not shown'}</td><td>{E(fd(p[4]))}</td><td>{E(p[5])}</td></tr>"
               for _, n, p in projects)

LOCAL = [  # Northern Powergrid heat map data, read 18 Nov 2026 (data last processed 27 Jul 2026)
    ('Creyke Beck', 'Grid supply point, 132 kV', '0.0', 323.3, 'Green', 314.8, 'Green'),
    ('Beverley 132/33kV', 'Bulk supply point, 33 kV', '2.2', 57.0, 'Red', 23.6, 'Red'),
    ('Southwood Road', 'Primary, 11 kV', '2.9', 2.2, 'Red', 9.5, 'Red'),
    ('Endike Lane', 'Primary, 11 kV', '2.9', 23.9, 'Red', 11.4, 'Red'),
    ('Spark Mill Lane', 'Primary, 11 kV', '4.0', 15.7, 'Red', 7.3, 'Red'),
    ('County Road North', 'Primary, 11 kV', '5.1', 13.3, 'Green', 6.6, 'Green'),
]
lrow = ''.join(f"<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{c} km</td><td class=n>{g:.1f}</td><td><span class='rag {gc[0]}'>{gc}</span></td><td class=n>{dm:.1f}</td><td><span class='rag {dc[0]}'>{dc}</span></td></tr>"
               for a, b, c, g, gc, dm, dc in LOCAL)

body = f"""
<section class="page-head"><div class="wrap">
  <p class="eyebrow">Sample landowner grid note</p>
  <h1>Land near Creyke Beck, East Riding of Yorkshire</h1>
  <p class="lead">A worked example of our £495 landowner grid note, built from real public data. There is no client and no named landowner: the land is a notional field next to Creyke Beck substation, near Cottingham. A real note follows the same six sections and arrives within three working days.</p>
</div></section>

<section class="note"><div class="wrap">
<div class="paper">
  <p class="meta">18 November 2026 &middot; Prepared by Benzene as a sample &middot; A desk review of public registers. Not a valuation, legal advice or an engineering study.</p>

  <h2>1. The short answer</h2>
  <p>The transmission queue here is long. <b>{q400['q']:,} MW</b> is queued at Creyke Beck 400kV across {len(q400['p'])} projects, none of it holding Gate 2, with contracted dates running from 2028 to 2039. <span class="tag c">Confirmed</span></p>
  <p>The local network looks different. Northern Powergrid shows 323 MW of generation headroom at its Creyke Beck grid supply point, rated Green, but rates the nearest 33 kV and most nearby 11 kV substations Red for new generation. <span class="tag c">Confirmed</span></p>
  <p>A large scheme needing a transmission connection here would join the back of a long queue. A smaller scheme on the local network would be judged mainly on Northern Powergrid's capacity, and the nearest substations are the constrained ones. Only a connection offer settles either. <span class="tag i">Inferred</span></p>

  <div class="tw"><table class="kv"><tbody>
    <tr><th>Land</th><td>Notional field next to Creyke Beck substation, near Cottingham (sample only)</td></tr>
    <tr><th>Use being proposed</th><td>Solar and battery storage, size not given</td></tr>
    <tr><th>Proposed buyer or developer</th><td>Not shared</td></tr>
    <tr><th>Register data as of</th><td>NESO TEC Register file of 16 November 2026</td></tr>
    <tr><th>Local network data as of</th><td>Northern Powergrid heat map data, last processed 27 July 2026</td></tr>
  </tbody></table></div>

  <h2>2. The grid near the land</h2>
  <h3>Transmission connection points</h3>
  <div class="tw"><table><thead><tr><th>Connection site</th><th>Distance</th><th class=n>MW waiting</th><th class=n>Projects</th><th class=n>Gate 2 MW</th><th>Contracted dates</th></tr></thead><tbody>
    {site_row(cb[0], 'At the land')}{site_row(cb[1], 'At the land')}{site_row(cb[2], 'At the land')}{site_row('Birkhill Wood 400kV Substation', 'About 3 km, position approximate')}
    <tr><td><b>North Humber Connection Nodes</b><span class=dev>{len(nh)} future nodes</span></td><td>Locations not given in the register</td><td class=n>{nh_q:,}</td><td class=n>{nh_n}</td><td class=n>0</td><td>{nh_d[0][:4]} to {nh_d[-1][:4]}</td></tr>
  </tbody></table></div>
  <p class="small">All rows Confirmed from the NESO TEC Register of 16 November 2026. Distances are straight-line and approximate; cable routes are longer.</p>
  <h3>Local network (Northern Powergrid)</h3>
  <div class="tw"><table><thead><tr><th>Substation</th><th>Type</th><th>Distance</th><th class=n>Generation headroom MW</th><th>Rating</th><th class=n>Demand headroom MW</th><th>Rating</th></tr></thead><tbody>{lrow}</tbody></table></div>
  <p class="small">Confirmed from Northern Powergrid's heat map data, shown as published, with the operator's caveats. Supported by <a href="https://northernpowergrid.opendatasoft.com/p/opendatalicence/" target="_blank" rel="noopener">Northern Powergrid Open Data</a>. A substation can show headroom in MW and still be rated Red where a constraint further up the network applies.</p>
  <p><b>What this means.</b> Every project queued at Creyke Beck 400kV is Gate 1 or shows no Gate, so some of it may fall away as NESO applies its readiness tests. We cannot say how much. <span class="tag i">Inferred</span></p>

  <h2>3. Who else is queuing here</h2>
  <div class="tw"><table><thead><tr><th>Project</th><th>Site</th><th class=n>MW</th><th>Technology</th><th>Gate</th><th>Contracted date</th><th>Register status</th></tr></thead><tbody>{prow}</tbody></table></div>
  <p class="small">All rows Confirmed from the NESO TEC Register of 16 November 2026. The developer names are as the register shows them.</p>

  <h2>4. What this means for an option</h2>
  <p>Facts first, then our reading. None of this is advice on option terms.</p>
  <ul>
    <li><b>Gate 2 land test.</b> NESO's guidance says an option agreement used as Gate 2 land evidence needs a minimum term of three years from the date it was signed, unless an exception applies. <span class="tag c">Confirmed</span> NESO's lease pro forma sets a default lease term of 20 years from the date the option is exercised. <span class="tag r">Reported</span></li>
    <li><b>Timing.</b> Contracted dates at Creyke Beck run to 2039. If a developer's plan depends on a new transmission connection here, its date could fall after a three to five year option has run. Ask how the two line up. <span class="tag i">Inferred</span></li>
    <li><b>Local headroom.</b> The grid supply point shows headroom; the nearer 33 kV and 11 kV substations are mostly rated Red. Ask which one the developer would connect to.</li>
  </ul>

  <h2>5. Questions to put to the developer</h2>
  <ol>
    <li>Which substation do you plan to connect to, and do you hold a connection offer or have you applied?</li>
    <li>If you hold an offer, what is its Gate status and its connection date?</li>
    <li>Is the plan a transmission connection at Creyke Beck, or a local connection through Northern Powergrid?</li>
    <li>If local, what has Northern Powergrid said about the Red ratings at Beverley and the nearby 11 kV substations?</li>
    <li>What happens to the option payments if the connection date moves?</li>
  </ol>

  <h2>6. Sources and limits</h2>
  <div class="tw"><table><thead><tr><th>Source</th><th>Used for</th></tr></thead><tbody>
    <tr><td>NESO TEC Register, file of 16 November 2026</td><td>Sections 1 to 3</td></tr>
    <tr><td>Northern Powergrid heat map data (Heat Map Data, Table), last processed 27 July 2026</td><td>Section 2, local network</td></tr>
    <tr><td>NESO, Connections Reform: Supporting your resubmission after initial checks, September 2025</td><td>Section 4, option term</td></tr>
    <tr><td>NESO, Pro Forma: Option Agreement, Lease Agreement or Existing Land Lease</td><td>Section 4, lease term</td></tr>
  </tbody></table></div>
  <p class="small"><span class="tag c">Confirmed</span> read on a primary source. <span class="tag r">Reported</span> taken from a named source we have not checked against the original document. <span class="tag i">Inferred</span> our reading of confirmed facts. This note uses public data only. Registers change, so findings are correct only as of the dates shown. It does not forecast whether or when a project on this land would connect.</p>
</div>

<div class="qwcta"><p><b>Want one for a real piece of land?</b> A landowner grid note costs £495 for one site and takes three working days. Or start with a free check: tell us the nearest substation and we will send you what is queued there.</p><a class="btn" href="#contact">Free substation check</a></div>
</div></section>
"""

CSS = """
.note { padding-block: 8px 56px }
.paper { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: clamp(18px, 4vw, 40px); max-width: 920px }
.paper h2 { font-size: 22px; margin: 30px 0 10px }
.paper h2:first-of-type { margin-top: 14px }
.paper h3 { font-size: 16px; margin: 18px 0 8px; font-weight: 600 }
.paper p, .paper li { color: var(--fg-2); max-width: 72ch; margin-bottom: 10px }
.paper ul, .paper ol { padding-left: 20px }
.paper b { color: var(--fg) }
.meta { font: 12.5px var(--mono); color: var(--fg-3) !important }
.small { font-size: 13px; color: var(--fg-3) !important }
.tw { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; margin: 10px 0 12px }
.tw table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 520px }
.tw th { text-align: left; font: 600 11px var(--mono); letter-spacing: .05em; text-transform: uppercase; color: var(--fg-3); padding: 9px 11px; border-bottom: 1px solid var(--line); vertical-align: bottom }
.tw td { padding: 9px 11px; border-bottom: 1px solid var(--line); vertical-align: top; color: var(--fg-2) }
.tw tr:last-child td, .tw tr:last-child th { border-bottom: 0 }
.tw td b { color: var(--fg); font-weight: 600; display: block }
.tw .dev { display: block; font-size: 12.5px; color: var(--fg-3) }
.tw .n { text-align: right; font-family: var(--mono); white-space: nowrap }
.kv { min-width: 0 !important }
.kv th { width: 34%; text-transform: none; letter-spacing: 0; font: 600 13px var(--sans, inherit); color: var(--fg-2) }
.rag { font: 600 11px var(--mono); padding: 2px 7px; border-radius: 4px }
.rag.G { background: var(--ok-bg); color: var(--ok) }
.rag.A { background: var(--warn-bg); color: var(--warn) }
.rag.R { background: var(--err-bg, var(--warn-bg)); color: var(--err, var(--warn)) }
.qwcta { margin-top: 28px; max-width: 920px; padding: 20px; border: 1px solid var(--line); border-radius: 10px; background: var(--card); display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: center; justify-content: space-between }
.qwcta p { max-width: 60ch; color: var(--fg-2) }
"""

page = shell('Sample landowner grid note | Benzene',
             'A worked sample of the Benzene landowner grid note for land near Creyke Beck: the transmission queue, local network headroom and the questions to ask a developer.',
             'sample-landowner-note.html', body, CSS)
open('site/sample-landowner-note.html', 'w', encoding='utf-8').write(page)
print('written', len(page))
