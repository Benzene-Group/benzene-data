"""Build a new site page that shares the look of the existing ones.

shell(title, description, path, body_html, extra_css='') returns a full HTML page:
head, styles, theme script and nav taken from site/how-it-works.html, then
body_html, then the free check contact section, the footer and the shared scripts.
"""
import re

SRC = 'site/how-it-works.html'


def _parts():
    s = open(SRC, encoding='utf-8').read()
    head_end = s.index('</head>')
    head = s[:head_end]
    nav = s[s.index('<nav>'):s.index('</nav>', s.index('<nav>')) + len('</nav>')]
    nav = nav.replace(' aria-current="page"', '')
    contact = s[s.index('<section id="contact"'):s.index('</section>', s.index('<section id="contact"')) + len('</section>')]
    footer = s[s.index('<footer>'):s.index('</footer>') + len('</footer>')]
    # the free check form handler: from the ctaBtn line to the end of that statement
    i = s.index("(document.getElementById('ctaBtn')")
    j = s.index('\n});', i) + len('\n});')
    cta_js = s[i:j]
    tail_scripts = re.findall(r"<script>\(function\(\)\{var b=document.getElementById\('(?:themebtn|sharebtn)'\).*?</script>", s)
    return head, nav, contact, footer, cta_js, tail_scripts


def shell(title, description, path, body_html, extra_css=''):
    head, nav, contact, footer, cta_js, tails = _parts()
    url = 'https://www.benzene-group.com/' + path
    head = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', head)
    for prop in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
        head = re.sub(rf'(<meta {prop} content=")[^"]*(")', lambda m: m.group(1) + description + m.group(2), head)
    for prop in ('property="og:title"', 'name="twitter:title"'):
        head = re.sub(rf'(<meta {prop} content=")[^"]*(")', lambda m: m.group(1) + title + m.group(2), head)
    head = re.sub(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + url + m.group(2), head)
    head = re.sub(r'(<meta property="og:url" content=")[^"]*(")', lambda m: m.group(1) + url + m.group(2), head)
    if extra_css:
        head += '<style>\n' + extra_css + '\n</style>\n'
    page = (head + '</head>\n<body>\n\n' + nav + '\n\n' + body_html + '\n\n' + contact + '\n\n' + footer +
            '\n\n<script>\n' + cta_js + '\n</script>\n' + '\n'.join(tails) + '\n</body>\n</html>\n')
    assert '—' not in page and '–' not in page, 'em or en dash in page'
    import json, os
    if os.environ.get('SHELL_PARTS'):
        os.makedirs(os.environ['SHELL_PARTS'], exist_ok=True)
        json.dump({'title': title, 'description': description, 'path': path, 'body': body_html, 'css': extra_css},
                  open(os.path.join(os.environ['SHELL_PARTS'], path + '.json'), 'w'), ensure_ascii=False)
    return page
