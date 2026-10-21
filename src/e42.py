"""c6288: Quotient (Bundel-Einbettung wie in 4n) -> typisiertes Z^2-Gitter? Rechtecke, Ausnahmen, Bus."""
import json, sys
from collections import Counter, defaultdict
import und; from und import *
from cells import whole_comp
from quotient import build_quotient
import qembed as QE
from core import LOG
import netlist; netlist.HB = '/tmp/dl/hdl-benchmarks/iscas85/bench/'
und.SYMS = set(); comp, nodes, L = whole_comp()
D = [tuple(tuple(e) for e in p) for p in json.load(open('cells_D2.json'))['D']]
pis = {n for n in range(comp.n) if not comp.inn[n]}
E, nsup, inst, raw = build_quotient(comp, D, pis)
ptype = {i: (inst[i][0] if i < len(inst) else -1) for i in range(nsup)}
Q = [(a, b, k) for a, b, k in E]
print('quotient nodes', nsup, 'edges', len(Q), 'patterns', Counter(ptype.values()).most_common(6))
Em = QE.embed(Q, ptype, nsup)
print({k: v for k, v in Em.items() if k not in ('coord', 'occ')})
coord, disp2, sc, info = QE.refine(Em, nsup); print('after refine', sc, info); Em['coord'] = coord
coord = Em['coord']; nrect, shear = QE.rectangles(coord, ptype); print('rectangles', nrect, 'shear', shear)
us = [p[0] for p in coord.values()]; vs = [p[1] for p in coord.values()]; occ = Em['occ']
syms = {pi: chr(ord('a') + j) for j, pi in enumerate(sorted({ptype[x] for x in coord if ptype[x] != Em['cell']}))}
for v in range(min(vs), max(vs) + 1):
    print(f'{v:3d} ' + ''.join(('#' if ptype[occ[(u, v)][0]] == Em['cell'] else syms[ptype[occ[(u, v)][0]]]) if (u, v) in occ else '.' for u in range(min(us), max(us) + 1)))
print({s: (p, len(D[p]) if p >= 0 else 0) for p, s in syms.items()})
# Bus: Ziele jedes Eingangs auf Linien?
memb = defaultdict(list)
for kk, (pi, ids, mm) in enumerate(inst):
    for u, n in mm: memb[n].append(kk)
bus = defaultdict(list)
for e, u, r, v in comp.E:
    if u in pis: bus[u].append(v)
cell = Em['cell']; stats = Counter(); offs = defaultdict(list); explained = 0
for p, tg in bus.items():
    pts = sorted({coord[kk] for n in tg for kk in memb[n] if ptype[kk] == cell and kk in coord})
    if len(pts) >= 3:
        ds = Counter((b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])); d, cnt = ds.most_common(1)[0]; stats[(d, cnt == len(pts) - 1)] += 1; offs[d].append((pts[0], len(pts))); explained += len(pts)
    else: stats[('short', len(pts))] += 1
print('PIs', len(bus), 'bus edges', sum(len(v) for v in bus.values()), 'direction/collinear', dict(stats), 'cell targets on lines', explained)
for d, lst in offs.items():
    cr = sorted({p[0] * d[1] - p[1] * d[0] for p, _ in lst}); print('   direction', d, 'lines', len(lst), 'gaps', dict(Counter(b - a for a, b in zip(cr, cr[1:]))))
# Kosten
n = LOG(nsup); R = 100
o = {'quotient_edges': len(Q), 'raw': len(Q) * (2 * n + LOG(R)), 'bundles': Em['bundles'], 'rectangles': nrect, 'exceptions': Em['exceptions'], 'unplaced': Em['unplaced'], 'collisions': Em['collisions']}
types = len(set(ptype.values())); o['embedding_model'] = o['bundles'] * (2 * LOG(types) + 2 * LOG(8) + 6) + nrect * (LOG(types) + 4 * LOG(60)) + o['exceptions'] * (2 * n + LOG(R)) + 55
print(o); json.dump(o, open('../results/e42.json', 'w'))
# --- Laeufe entlang von 4 Richtungen fuer alle Nicht-Kernzellen, Kern = ein Parallelogramm ---
site = {p: ptype[xs[0]] for p, xs in occ.items() if xs}
site = {coord[x]: ptype[x] for x in coord}; cellt = Em['cell']
noncore = {p: t for p, t in site.items() if t != cellt}; todo = set(noncore); nruns = 0; lens = []
dirs = [(a, b) for a in range(-2, 3) for b in range(0, 3) if (b > 0 or a > 0)]
while todo:
    best = None
    for p in todo:
        for d in dirs:
            if (p[0] - d[0], p[1] - d[1]) in todo and noncore[(p[0] - d[0], p[1] - d[1])] == noncore[p]: continue     # nur Laufanfang
            n = 0; q = p
            while q in todo and noncore[q] == noncore[p]: n += 1; q = (q[0] + d[0], q[1] + d[1])
            if best is None or n > best[0]: best = (n, p, d)
    n, p, d = best; nruns += 1; lens.append(n)
    for i in range(n): todo.discard((p[0] + i * d[0], p[1] + i * d[1]))
print('non-core cells', len(noncore), 'runs (4 directions, greedy longest first)', nruns, 'lengths', sorted(lens, reverse=True)[:25])
byb = defaultdict(Counter)
for a, b, bb in Em['QB']:
    if a in coord and b in coord: byb[bb][(coord[b][0] - coord[a][0], coord[b][1] - coord[a][1])] += 1
inc = {bb: c for bb, c in byb.items() if len(c) > 1}
print('bundles with >1 displacement', len(inc), 'inconsistent edges (non-majority)', sum(sum(c.values()) - max(c.values()) for c in inc.values()))
for bb, c in sorted(inc.items(), key=lambda kv: -sum(kv[1].values()))[:8]: print('  bundle', bb, dict(c))
o['runs'] = nruns; o['inconsistent_after_refine'] = sum(sum(c.values()) - max(c.values()) for c in inc.values())
o['model_with_runs'] = o['bundles'] * (2 * LOG(types) + 2 * LOG(8) + 6) + (1 + nruns) * (LOG(types) + 2 * LOG(60) + 2 + LOG(30)) + o['inconsistent_after_refine'] * (2 * n + LOG(R)) + 55
print(o); json.dump(o, open('../results/e42.json', 'w'))
