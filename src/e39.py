"""Rand als typisiertes Gitter: Einbettung aller Quotientenknoten (PI-Kanten entfernt) in Z^2 mit je Kantenbuendel festem Verschiebungsvektor."""
import sys, pickle
from collections import Counter, defaultdict, deque
import netlist; import paths; netlist.HB = paths.GEN
import und; from und import *
from e38 import comp_np
from netlist import Labeler
from latt import learn_rule, _coords
und.SYMS = set()
Dfull, recs, D0 = pickle.load(open('../results/e38_cells.pkl', 'rb'))
k = int(sys.argv[1]) if len(sys.argv) > 1 else 16
L = Labeler(); comps = {kk: comp_np(f'mul{kk}', L) for kk in (16, 24, 32)}; c = comps[k]
inst, raw = cover_u(c, Dfull)
cell = max(range(len(Dfull)), key=lambda i: sum(1 for pi, _, _ in inst if pi == i) * (len(Dfull[i]) >= 15))
memb = defaultdict(list)
for kk, (pi, ids, mm) in enumerate(inst):
    for u, n in mm: memb[n].append((kk, pi, u))
Eq = {}
for n, Mb in memb.items():
    for i in range(len(Mb)):
        for j in range(i + 1, len(Mb)):
            a, b = Mb[i], Mb[j]
            if a[0] == b[0]: continue
            x, y = (a, b) if (a[1], a[2]) <= (b[1], b[2]) else (b, a); Eq[(x[0], y[0], (x[1], x[2], y[1], y[2]))] = 1
Q = list(Eq); N = len(inst); ptype = {i: pi for i, (pi, _, _) in enumerate(inst)}
print('quotient nodes', N, 'edges', len(Q), 'cell pattern', cell)
# Buendel: Labels (Portpaare) die immer auf denselben Knotenpaaren liegen
pairs_of = defaultdict(set)
for a, b, kk in Q: pairs_of[kk].add((a, b))
bid = {}; groups = {}
for kk, ps in pairs_of.items(): bid[kk] = groups.setdefault(frozenset(ps), len(groups))
QB = list({(a, b, bid[kk]) for a, b, kk in Q}); print('bundles', len(groups))
core = {i for i in range(N) if ptype[i] == cell}
cidx = {x: j for j, x in enumerate(sorted(core))}; ces = [(cidx[a], b_, cidx[b]) for a, b, b_ in QB if a in core and b in core]
gens = learn_rule(ces); print('core generators', [(ls, len(f)) for ls, f in gens]); gl = [set(ls) for ls, _ in gens]
# Koordinaten des Kerns per BFS aus den Erzeugern (Verschiebung des dritten = (1,1))
co_idx, conf = _coords(gl, [(1, 0), (0, 1), (1, 1)][:len(gl)], ces, len(core)); print('core coords', len(co_idx), 'conflicts', conf)
inv_c = {j: x for x, j in cidx.items()}; coord = {inv_c[j]: p for j, p in co_idx.items()}
occ = defaultdict(list)
for x, p in coord.items(): occ[p].append(x)
disp = {}
for a, b, bb in QB:
    if a in coord and b in coord: disp.setdefault(bb, (coord[b][0] - coord[a][0], coord[b][1] - coord[a][1]))
bpairs = defaultdict(list)
for a, b, bb in QB: bpairs[bb].append((a, b))
adj = defaultdict(list)
for a, b, bb in QB: adj[a].append((b, bb, 1)); adj[b].append((a, bb, -1))
cands = sorted([(du, dv) for du in range(-3, 4) for dv in range(-3, 4) if (du, dv) != (0, 0)], key=lambda d: (abs(d[0]) + abs(d[1]), d))
q = deque(sorted(coord)); coll = 0; placed_by_choice = 0
while q:
    x = q.popleft(); cx = coord[x]
    for y, bb, s in sorted(adj[x]):
        if y in coord: continue
        if bb in disp: d = disp[bb]
        else:
            best = None
            for dd in cands:
                sc = 0; tg = set()
                for a2, b2 in bpairs[bb]:
                    if a2 in coord and b2 in coord: sc += 1000 * ((coord[b2][0] - coord[a2][0], coord[b2][1] - coord[a2][1]) == dd)
                    elif a2 in coord:
                        p2 = (coord[a2][0] + dd[0], coord[a2][1] + dd[1])
                        if p2 in occ: sc -= 5
                        elif p2 not in tg: tg.add(p2); sc += 1
                    elif b2 in coord:
                        p2 = (coord[b2][0] - dd[0], coord[b2][1] - dd[1])
                        if p2 in occ: sc -= 5
                        elif p2 not in tg: tg.add(p2); sc += 1
                if best is None or sc > best[0]: best = (sc, dd)
            d = best[1]; disp[bb] = d; placed_by_choice += 1
        p = (cx[0] + s * d[0], cx[1] + s * d[1])
        if p in occ: coll += 1; continue
        coord[y] = p; occ[p].append(y); q.append(y)
print('embedded', len(coord), 'of', N, 'collisions', coll, 'bundles with chosen disp', placed_by_choice, 'of', len(groups))
bad = [(a, b, bb) for a, b, bb in QB if a in coord and b in coord and (coord[b][0] - coord[a][0], coord[b][1] - coord[a][1]) != disp.get(bb)]
print('inconsistent edges', len(bad), 'of', len(QB))
us = [p[0] for p in coord.values()]; vs = [p[1] for p in coord.values()]
sym = {pi: chr(ord('a') + j) for j, pi in enumerate(sorted({ptype[x] for x in coord if ptype[x] != cell}))}
for v in range(min(vs), max(vs) + 1):
    print(f'{v:3d} ' + ''.join(('#' if ptype[occ[(u, v)][0]] == cell else sym[ptype[occ[(u, v)][0]]]) if (u, v) in occ else '.' for u in range(min(us), max(us) + 1)))
print({sym[p]: (p, len(Dfull[p])) for p in sym})
byb = defaultdict(Counter)
for a, b, bb in QB:
    if a in coord and b in coord: byb[bb][(coord[b][0] - coord[a][0], coord[b][1] - coord[a][1])] += 1
inc = {bb: c for bb, c in byb.items() if len(c) > 1}
print('bundles with >1 displacement:', len(inc), 'of', len(byb))
tys = {bb: Counter((ptype[a], ptype[b]) for a, b, b2 in QB if b2 == bb).most_common(1)[0][0] for bb in inc}
for bb, c in sorted(inc.items(), key=lambda kv: -sum(kv[1].values()))[:12]: print(' bundle', bb, 'types', tys[bb], dict(c))
bb_bad = Counter(bb for a, b, bb in bad); print('bad by bundle', bb_bad.most_common(6)); 
for bb, _ in bb_bad.most_common(3): print(bb, 'disp', disp.get(bb), 'actual', dict(byb[bb]))
