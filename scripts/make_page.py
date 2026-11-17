import json, sys
out = sys.argv[1]
d = json.load(open(f'{out}/platform.json')); o = json.load(open(f'{out}/outline.json'))
for s in d['sites']:
    s['p'] = [p[:7] for p in s['p']]; s.pop('t', None); s.pop('k', None); s.pop('w', None)
t = open('scripts/template.html', encoding='utf-8').read()
js = lambda x: json.dumps(x, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
t = t.replace('/*DATA*/', js(d)).replace('/*OUTLINE*/', js(o)).replace('/*NI*/', js(json.load(open(f'{out}/ni.json'))))
open(f'{out}/index.html', 'w', encoding='utf-8').write(t)
print('index.html bytes', len(t.encode()))
