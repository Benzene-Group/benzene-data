"""One-off: split the single-page site/index.html into index, how-it-works and pricing pages.

Usage (repo root): python3 -I scripts/split_pages.py
Reads site/index.html, writes site/index.html, site/how-it-works.html, site/pricing.html.
"""
import re

SRC = 'site/index.html'
h = open(SRC, encoding='utf-8').read()


def cut(start_pat, end_pat):
    s = h.index(start_pat)
    e = h.index(end_pat, s)
    return h[s:e]


head_end = h.index('<nav>')
head = h[:head_end]
nav_end = h.index('</nav>') + len('</nav>')
hero = cut('<header class="hero">', '<section id="why">')
sec = {}
order = ['why', 'gates', 'who', 'latest', 'pricing', 'how', 'contact']
for i, k in enumerate(order):
    start = h.index(f'<section id="{k}"')
    end = h.index(f'<section id="{order[i + 1]}"') if i + 1 < len(order) else h.index('<footer>')
    sec[k] = h[start:end]
footer = cut('<footer>', '<script>')
script_start = h.index('<script>', h.index('<footer>'))
ld_start = h.index('<script type="application/ld+json">')
script = h[script_start:ld_start]
ld = h[ld_start:h.index('</body>')]

# Make the shared script safe on pages without every element
script = script.replace("document.getElementById('minimap').innerHTML = m + '</g>';",
                        "var mmEl = document.getElementById('minimap'); if (mmEl) mmEl.innerHTML = m + '</g>';")
script = script.replace("document.getElementById('chart').innerHTML = g;",
                        "var chEl = document.getElementById('chart'); if (chEl) chEl.innerHTML = g;")
script = script.replace("document.getElementById('ctaBtn').addEventListener(",
                        "(document.getElementById('ctaBtn') || { addEventListener: function () {} }).addEventListener(")
script = script.replace("document.getElementById('emailInput').addEventListener(",
                        "(document.getElementById('emailInput') || { addEventListener: function () {} }).addEventListener(")
script = script.replace("o = document.getElementById('cOut');\n", "o = document.getElementById('cOut');\n  if (!m) return;\n", 1)
for needle in ("if (mmEl)", "if (chEl)", "addEventListener: function", "if (!m) return;"):
    assert needle in script, needle

LOGO = re.search(r'<svg width="34".*?</svg>', h[head_end:nav_end], re.S).group(0)


def nav(active):
    links = [('/queue-map.html', 'Queue map', 'map'), ('/how-it-works.html', 'How it works', 'how'), ('/pricing.html', 'Services and pricing', 'pricing')]
    a = ''.join(f'\n      <a href="{u}"{" aria-current=\"page\"" if k == active else ""}>{t}</a>' for u, t, k in links)
    return (f'<nav>\n  <div class="wrap nav-inner">\n    <a href="/" class="logo" aria-label="Benzene home">\n      {LOGO}\n      Benzene\n    </a>\n'
            f'    <div class="nav-links">{a}\n      <a href="#contact" class="btn">Free substation check</a>\n    </div>\n  </div>\n</nav>\n')


FOOT_LINKS = ('<nav class="foot-links" aria-label="Site"><a href="/">Home</a><a href="/queue-map.html">Queue map</a>'
              '<a href="/how-it-works.html">How it works</a><a href="/pricing.html">Services and pricing</a></nav>')
footer = footer.replace('<div class="wrap">', '<div class="wrap">' + FOOT_LINKS, 1)

EXTRA_CSS = ('a.sig { color: inherit; text-decoration: none; transition: border-color .15s }\n'
             'a.sig:hover { border-color: var(--accent) }\n'
             'a.sig .go { font: 500 14px var(--sans); color: var(--accent); margin-top: auto }\n'
             '.nav-links a[aria-current="page"] { color: var(--fg); font-weight: 500 }\n'
             '.foot-links { display: flex; flex-wrap: wrap; gap: 6px 18px; width: 100%; margin-bottom: 8px }\n'
             '.foot-links a { color: var(--fg-2); text-decoration: none }\n'
             '.page-head { padding-block: 48px 8px; border-bottom: 0 }\n')
head = head.replace('</style>', EXTRA_CSS + '</style>', 1)

START = '''<section id="start">
  <div class="wrap">
    <p class="eyebrow">Start here</p>
    <h2>Three ways in</h2>
    <div class="signals">
      <a class="sig" href="/queue-map.html">
        <span class="when">Free tool</span>
        <div class="big">Queue map</div>
        <p>Every transmission connection site in Britain: how much is waiting, the Gate 1 and Gate 2 split, and the contracted dates.</p>
        <span class="go">Open the map &rarr;</span>
      </a>
      <a class="sig" href="/how-it-works.html">
        <span class="when">Explained</span>
        <div class="big">How it works</div>
        <p>Why a grid date costs money, what Gate 1 and Gate 2 really mean, and where every figure we publish comes from.</p>
        <span class="go">Read how it works &rarr;</span>
      </a>
      <a class="sig" href="/pricing.html">
        <span class="when">Services</span>
        <div class="big">From &pound;0</div>
        <p>Start with a free substation check. Take a fixed-fee screening report when you need the full picture.</p>
        <span class="go">See services and pricing &rarr;</span>
      </a>
    </div>
  </div>
</section>

'''


def page_head(title, h1, lead):
    return (f'<section class="page-head">\n  <div class="wrap">\n    <p class="eyebrow">{title}</p>\n    <h1>{h1}</h1>\n'
            f'    <p class="lead">{lead}</p>\n  </div>\n</section>\n\n')


def relink(body):
    for a in ('why', 'gates', 'how'):
        body = body.replace(f'href="#{a}"', f'href="/how-it-works.html#{a}"')
    for a in ('pricing', 'who'):
        body = body.replace(f'href="#{a}"', f'href="/pricing.html#{a}"')
    return body


def bands(parts):
    out = []
    for i, p in enumerate(parts):
        if p.startswith('<section id="contact"'):
            out.append(p)
            continue
        p = re.sub(r'^<section id="(\w+)"(?: class="band")?>', lambda m: f'<section id="{m.group(1)}"' + (' class="band">' if i % 2 else '>'), p)
        out.append(p)
    return out


def head_for(path, title, desc):
    url = 'https://www.benzene-group.com/' + ('' if path == 'index.html' else path)
    x = head
    x = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', x)
    x = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + desc, x)
    x = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + url, x)
    x = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1) + url, x)
    x = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + title, x)
    x = re.sub(r'(<meta name="twitter:title" content=")[^"]*', lambda m: m.group(1) + title, x)
    x = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + desc, x)
    x = re.sub(r'(<meta name="twitter:description" content=")[^"]*', lambda m: m.group(1) + desc, x)
    return x


pages = {
    'index.html': (head_for('index.html', 'Benzene | UK Grid Connection Intelligence', re.search(r'<meta name="description" content="([^"]*)', head).group(1)),
                   None, [hero] + bands([START, sec['latest'], sec['contact']]), True),
    'how-it-works.html': (head_for('how-it-works.html', 'How it works | Benzene',
                                   "Why a grid connection date costs money, what Gate 1 and Gate 2 mean in NESO's register, and how Benzene sources and checks every figure."),
                          'how', [page_head('How it works', 'Why grid dates matter, and how we check them',
                                            'What a late connection costs, what the labels in the national register really mean, and where every figure we publish comes from.')]
                          + bands([sec['why'], sec['gates'], sec['how'], sec['contact']]), False),
    'pricing.html': (head_for('pricing.html', 'Services and pricing | Benzene',
                              'Free substation checks and fixed-fee grid connection screening reports for UK developers, land agents, lawyers and investors.'),
                     'pricing', [page_head('Services and pricing', 'From a free check to a full screening report',
                                           'Pick the question you are trying to answer, then the level of detail you need.')]
                     + bands([sec['who'], sec['pricing'], sec['contact']]), False),
}

for path, (hd, active, body, with_ld) in pages.items():
    content = hd + '<body>\n\n' + nav(active) + '\n' + relink(''.join(body)) + footer + script + (ld if with_ld else '') + '</body>\n</html>\n'
    assert '\u2014' not in content and '\u2013' not in content, path
    open(f'site/{path}', 'w', encoding='utf-8').write(content)
    print(path, len(content), len(re.findall(r'<!--f:\w+-->', content)), 'markers')
