"""Eingangsbus: liegen die Ziele jedes Eingangs (PI) auf einer Gitterlinie, und bilden die Linien eine arithmetische Folge?"""
import sys
from qembed import *
from netlist import load_bench
from collections import Counter, defaultdict
for k in (16, 24, 32):
    Q, ptype, N, raw = quotient(k); E = embed(Q, ptype, N); coord = E['coord']; cell = E['cell']
    c = get_comp(k); En = [e for e in load_bench(f'mul{k}') if e[2][0] != 'IN']; names = sorted({x for u, v, _ in En for x in (u, v)}); ix = {x: i for i, x in enumerate(names)}
    inst, _ = cover_u(c, Dfull); memb = defaultdict(list)
    for kk, (pi, ids, mm) in enumerate(inst):
        for u, n in mm: memb[n].append(kk)
    bus = defaultdict(list)
    for u, v, l in load_bench(f'mul{k}'):
        if l[0] == 'IN' and v in ix: bus[u].append(ix[v])
    lines = {}; stats = Counter(); offs = defaultdict(list)
    for pi_, tg in bus.items():
        pts = sorted({coord[kk] for n in tg for kk in memb[n] if ptype[kk] == cell and kk in coord})
        miss = sum(1 for n in tg if not any(ptype[kk] == cell for kk in memb[n]))
        if len(pts) >= 3:
            ds = Counter((b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])); d, cnt = ds.most_common(1)[0]
            stats[(d, cnt == len(pts) - 1)] += 1; offs[d].append((pts[0], len(pts)))
        else: stats[('short', len(pts))] += 1
    print(k, 'PIs', len(bus), 'edges', sum(len(v) for v in bus.values()), 'direction/collinear', dict(stats))
    for d, lst in offs.items():
        cr = sorted({p[0] * d[1] - p[1] * d[0] for p, _ in lst}); gaps = Counter(b - a for a, b in zip(cr, cr[1:])); print('   direction', d, 'lines', len(lst), 'offsets', len(cr), 'gap histogram', dict(gaps))
    exp = sum(n for lst in offs.values() for _, n in lst); tot = sum(len(v) for v in bus.values())
    print('   bus edges explained by lines', exp, 'of', tot, 'remaining', tot - exp)
