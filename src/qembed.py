"""Quotient eines Multiplizierers (ohne Bus) als typisiertes Z^2-Gitter einbetten; Kosten der Einbettungsbeschreibung (Rechtecke + Buendeltabelle + Ausnahmen)."""
import pickle
from collections import Counter, defaultdict, deque
import netlist; netlist.HB = '/tmp/claude-0/genbench/'
import und; from und import *
from e38 import comp_np
from netlist import Labeler
from latt import learn_rule, _coords
from core import LOG
und.SYMS = set()
Dfull, recs, D0 = pickle.load(open('../results/e38_cells.pkl', 'rb'))
_L = Labeler(); _comps = {}
def get_comp(k):
    if not _comps: 
        for kk in (16, 24, 32): _comps[kk] = comp_np(f'mul{kk}', _L)
    return _comps[k]
def quotient(k):
    c = get_comp(k); inst, raw = cover_u(c, Dfull); memb = defaultdict(list)
    for kk, (pi, ids, mm) in enumerate(inst):
        for u, n in mm: memb[n].append((kk, pi, u))
    Eq = {}
    for n, Mb in memb.items():
        for i in range(len(Mb)):
            for j in range(i + 1, len(Mb)):
                a, b = Mb[i], Mb[j]
                if a[0] == b[0]: continue
                x, y = (a, b) if (a[1], a[2]) <= (b[1], b[2]) else (b, a); Eq[(x[0], y[0], (x[1], x[2], y[1], y[2]))] = 1
    return list(Eq), {i: pi for i, (pi, _, _) in enumerate(inst)}, len(inst), raw
def embed(Q, ptype, N):
    cell = Counter(ptype.values()).most_common(1)[0][0]
    pairs_of = defaultdict(set)
    for a, b, kk in Q: pairs_of[kk].add((a, b))
    bid = {}; groups = {}
    for kk, ps in pairs_of.items(): bid[kk] = groups.setdefault(frozenset(ps), len(groups))
    QB = list({(a, b, bid[kk]) for a, b, kk in Q}); core = {i for i in range(N) if ptype[i] == cell}
    cidx = {x: j for j, x in enumerate(sorted(core))}; ces = [(cidx[a], bb, cidx[b]) for a, b, bb in QB if a in core and b in core]
    gens = learn_rule(ces); gl = [set(ls) for ls, _ in gens]
    co_idx, conf = _coords(gl, [(1, 0), (0, 1), (1, 1)][:len(gl)], ces, len(core)); inv_c = {j: x for x, j in cidx.items()}
    coord = {inv_c[j]: p for j, p in co_idx.items()}; occ = defaultdict(list)
    for x, p in coord.items(): occ[p].append(x)
    disp = {}
    for a, b, bb in QB:
        if a in coord and b in coord and ptype[a] == cell and ptype[b] == cell: disp.setdefault(bb, (coord[b][0] - coord[a][0], coord[b][1] - coord[a][1]))
    bpairs = defaultdict(list); adj = defaultdict(list)
    for a, b, bb in QB: bpairs[bb].append((a, b)); adj[a].append((b, bb, 1)); adj[b].append((a, bb, -1))
    cands = sorted([(du, dv) for du in range(-3, 4) for dv in range(-3, 4) if (du, dv) != (0, 0)], key=lambda d: (abs(d[0]) + abs(d[1]), d))
    q = deque(sorted(coord)); coll = 0
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
                        elif a2 in coord or b2 in coord:
                            p2 = (coord[a2][0] + dd[0], coord[a2][1] + dd[1]) if a2 in coord else (coord[b2][0] - dd[0], coord[b2][1] - dd[1])
                            if p2 in occ: sc -= 5
                            elif p2 not in tg: tg.add(p2); sc += 1
                    if best is None or sc > best[0]: best = (sc, dd)
                d = best[1]; disp[bb] = d
            p = (cx[0] + s * d[0], cx[1] + s * d[1])
            if p in occ: coll += 1; continue
            coord[y] = p; occ[p].append(y); q.append(y)
    byb = defaultdict(Counter)
    for a, b, bb in QB:
        if a in coord and b in coord: byb[bb][(coord[b][0] - coord[a][0], coord[b][1] - coord[a][1])] += 1
    exc = sum(sum(c.values()) - max(c.values()) for c in byb.values()) + sum(1 for a, b, bb in QB if a not in coord or b not in coord)
    return {'coord': coord, 'occ': occ, 'bundles': len(groups), 'exceptions': exc, 'collisions': coll, 'unplaced': N - len(coord), 'edges': len(QB), 'cell': cell}
def rectangles(coord, ptype):
    """Greedy-Zerlegung in typkonstante Rechtecke, bestes Shear s in {-1,0,1}."""
    best = None
    for s in (-1, 0, 1):
        site = {(u + s * v, v): ptype[x] for x, (u, v) in coord.items()}; todo = set(site); n = 0
        while todo:
            u0, v0 = min(todo, key=lambda p: (p[1], p[0])); t = site[(u0, v0)]; w = 0
            while (u0 + w, v0) in todo and site[(u0 + w, v0)] == t: w += 1
            h = 1
            while all((u0 + i, v0 + h) in todo and site[(u0 + i, v0 + h)] == t for i in range(w)): h += 1
            for i in range(w):
                for j in range(h): todo.discard((u0 + i, v0 + j))
            n += 1
        if best is None or n < best[0]: best = (n, s)
    return best
