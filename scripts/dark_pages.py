# One-off: add light/dark theme support to site/*.html (follows the device setting; toggle overrides).
import glob, sys
sys.path.insert(0, 'scripts')
from theme_snippets import HEAD, BTN, JS, logo

LIGHT_EXTRA = """  --nav-bg: rgba(255,255,255,.94); --cta: #13243a; --cta-h: #24405f; --cta-fg: #ffffff;
  --input: #ffffff; --hero-top: #ffffff; --shadow: rgba(19,36,58,.06); --shadow-2: rgba(19,36,58,.1);
  --land: #dde5ee; --gridline: #e1e7ee; --dotring: #ffffff; --err: #b4232f;
  --w1: #f2a7ad; --w2: #e47883; --w3: #cc4a5a; --w4: #a3303f; --w5: #6b1d2a;
  --roi-bg: #13243a; --roi-fg: #ffffff; --roi-p: #e8eef5; --roi-btn-h: #3fd6ef;
  --ring: #07738d; --bond: #009fc0; --hover: #eef3f8;
"""
DARK = """  --bg: #0d1521; --band: #111c2b; --card: #152132;
  --fg: #e7edf5; --fg-2: #b4c1d0; --fg-3: #8b9aad;
  --line: #22324a; --line-2: #34465f;
  --brand: #05c8e8; --accent: #4cc0dc; --accent-bg: #0f3442;
  --g2: #2bb3d4; --g1: #e3a535; --gn: #9d93f2;
  --ok: #4fd29a; --ok-bg: #12382a; --warn: #f0bd5c; --warn-bg: #3a2c10; --inf-bg: #22314a;
  --nav-bg: rgba(13,21,33,.92); --cta: #4cc0dc; --cta-h: #74d2e8; --cta-fg: #0d1521;
  --input: #0f1a28; --hero-top: #111c2b; --shadow: rgba(0,0,0,.35); --shadow-2: rgba(0,0,0,.5);
  --land: #2a3a50; --gridline: #22324a; --dotring: #152132; --err: #ff6b78;
  --w1: #5a2731; --w2: #8c3444; --w3: #c64b5e; --w4: #ec7584; --w5: #ffb4bd;
  --roi-bg: #0a2a35; --roi-fg: #ffffff; --roi-p: #cfe3ec; --roi-btn-h: #74d2e8;
  --ring: #3aa6c0; --bond: #05c8e8; --hover: #1b2a3e;
  color-scheme: dark;
"""
R = [
 ('background: rgba(255,255,255,.94);', 'background: var(--nav-bg);'),
 ('.nav-links a.btn, .nav-links a.btn:hover { color: #fff }', '.nav-links a.btn, .nav-links a.btn:hover { color: var(--cta-fg) }'),
 ('.btn { display: inline-block; background: var(--fg); color: #fff;', '.btn { display: inline-block; background: var(--cta); color: var(--cta-fg);'),
 ('.btn:hover { background: #24405f }', '.btn:hover { background: var(--cta-h) }'),
 ('.btn.alt:hover { background: #fff;', '.btn.alt:hover { background: var(--card);'),
 ('linear-gradient(180deg, #ffffff 0%, var(--bg) 100%)', 'linear-gradient(180deg, var(--hero-top) 0%, var(--bg) 100%)'),
 ('box-shadow: 0 6px 24px rgba(19,36,58,.06)', 'box-shadow: 0 6px 24px var(--shadow)'),
 ('box-shadow: 0 8px 28px rgba(19,36,58,.1)', 'box-shadow: 0 8px 28px var(--shadow-2)'),
 ('background: var(--fg); color: #fff; border-radius: 10px; padding: 20px 24px }', 'background: var(--roi-bg); color: var(--roi-fg); border-radius: 10px; padding: 20px 24px }'),
 ('color: #e8eef5 }', 'color: var(--roi-p) }'),
 ('.roi strong { color: #fff }', '.roi strong { color: var(--roi-fg) }'),
 ('.roi .btn:hover { background: #3fd6ef }', '.roi .btn:hover { background: var(--roi-btn-h) }'),
 ('color: var(--fg); background: #fff }', 'color: var(--fg); background: var(--input) }'),
 ('color: var(--fg); background: #fff; outline: none }', 'color: var(--fg); background: var(--input); outline: none }'),
 ('.cta-btn { background: var(--fg); color: #fff;', '.cta-btn { background: var(--cta); color: var(--cta-fg);'),
 ('.cta-btn:hover { background: #24405f }', '.cta-btn:hover { background: var(--cta-h) }'),
 ('stroke="#157a52"', 'style="stroke:var(--ok)"'),
 ("var C = ['#f2a7ad', '#e47883', '#cc4a5a', '#a3303f', '#6b1d2a'];", "var C = ['var(--w1)', 'var(--w2)', 'var(--w3)', 'var(--w4)', 'var(--w5)'];"),
 ('''fill="#dde5ee" stroke="#dde5ee" stroke-width=".8"/><g fill-opacity=".9" stroke="#fff" stroke-width=".5">''', '''style="fill:var(--land);stroke:var(--land)" stroke-width=".8"/><g fill-opacity=".9" style="stroke:var(--dotring)" stroke-width=".5">'''),
 ('''+ '" fill="' + C[D[i + 3]] + '"/>';''', '''+ '" style="fill:' + C[D[i + 3]] + '"/>';'''),
 ("var cols = ['#0e8fae', '#c27c00', '#7a6ee0']", "var cols = ['var(--g2)', 'var(--g1)', 'var(--gn)']"),
 ('''stroke="#e1e7ee"/>''', '''style="stroke:var(--gridline)"/>'''),
 ('''+ '" fill="' + cols[s[0]] + '"><title>''', '''+ '" style="fill:' + cols[s[0]] + '"><title>'''),
 ("input.style.borderColor = '#b4232f';", "input.style.borderColor = 'var(--err)';"),
]
CSS = """.themebtn { display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 6px; border: 1px solid var(--line-2); background: transparent; color: var(--fg-2); cursor: pointer; padding: 0 }
.themebtn:hover { color: var(--fg); background: var(--hover) }
.themebtn .moon { display: none }
:root[data-theme="dark"] .themebtn .sun { display: none } :root[data-theme="dark"] .themebtn .moon { display: inline }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .themebtn .sun { display: none } :root:not([data-theme="light"]) .themebtn .moon { display: inline } }
"""
for f in sorted(glob.glob('site/*.html')):
    t = open(f, encoding='utf-8').read()
    if 'id="themebtn"' in t:
        print(f, 'already done'); continue
    for a, b in R:
        if a in t:
            t = t.replace(a, b)
    t = t.replace('  color-scheme: light;\n}', LIGHT_EXTRA + '  color-scheme: light;\n}\n@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {\n' + DARK + '} }\n:root[data-theme="dark"] {\n' + DARK + '}', 1)
    t = t.replace('<style>', HEAD + '\n<style>', 1).replace('</style>', CSS + '</style>', 1)
    a = t.index('<nav>'); b = t.index('</nav>', a)
    seg = logo(t[a:b])
    i = seg.index('<a href="#contact" class="btn">') if '<a href="#contact" class="btn">' in seg else seg.index('class="btn"')
    i = seg.rfind('<a ', 0, i + 1) if not seg[i:].startswith('<a ') else i
    seg = seg[:i] + BTN + '\n      ' + seg[i:]
    t = t[:a] + seg + t[b:]
    t = t.replace('</body>', JS + '\n</body>', 1)
    assert '[data-theme="dark"] {' in t, f
    open(f, 'w', encoding='utf-8').write(t)
    left = [x for x in ('#fff ', '#fff;', '#fff"', '#24405f', '#dde5ee', 'rgba(19') if x in t.split('</style>')[0].split('<style>')[1]]
    print(f, 'ok; literals left in CSS:', left)
