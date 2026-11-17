"""Small find-and-replace pairs that turn the live map page into the new one.

Usage: python3 -I scripts/map_pairs.py published/queue-map.html out/index.html out/map_pairs.json
The live page must equal the first file exactly. The pairs are verified to reproduce the new page.
"""
import difflib, json, re, sys

a = open(sys.argv[1], encoding='utf-8').read()
b = open(sys.argv[2], encoding='utf-8').read()
split = lambda s: re.split(r'(?<=\}),(?=\{)', s)   # one token per JSON object boundary
ta, tb = split(a), split(b)
pa = [0]
for t in ta: pa.append(pa[-1] + len(t) + 1)
pb = [0]
for t in tb: pb.append(pb[-1] + len(t) + 1)
blocks = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
    if tag == 'equal':
        continue
    s = [pa[i1], min(pa[i2], len(a)), pb[j1], min(pb[j2], len(b))]
    if blocks and s[0] - blocks[-1][1] < 300:
        blocks[-1][1], blocks[-1][3] = s[1], s[3]
    else:
        blocks.append(s)
# refine each block to the characters that actually changed
fine = []
for a1, a2, b1, b2 in blocks:
    sa, sb = a[a1:a2], b[b1:b2]
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sa, sb, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        s2 = [a1 + i1, a1 + i2, b1 + j1, b1 + j2]
        if fine and s2[0] - fine[-1][1] < 120:
            fine[-1][1], fine[-1][3] = s2[1], s2[3]
        else:
            fine.append(s2)
blocks = fine
pairs = []
for a1, a2, b1, b2 in blocks:
    c = 40
    while a.count(a[max(0, a1 - c):a2 + c]) != 1:
        c += 40
    lead = a1 - max(0, a1 - c)
    pairs.append([a[a1 - lead:a2 + c], b[b1 - lead:b2 + c]])
s = a
for o, n in pairs:
    assert s.count(o) == 1
    s = s.replace(o, n)
assert s == b, 'pairs do not reproduce the new page'
json.dump({'start_len': len(a), 'end_len': len(b), 'pairs': pairs}, open(sys.argv[3], 'w'), ensure_ascii=False)
print(json.dumps({'pairs': len(pairs), 'bytes': len(json.dumps(pairs, ensure_ascii=False))}))
