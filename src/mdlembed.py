"""Einbettung direkt nach Beschreibungslaenge (zweiseitig exakt: vorhergesagte Kanten vs. tatsaechliche Kanten).
Modell: Buendeltabelle (Labels + Verschiebung), Knotenplaetze (Kernregion + Laeufe), Ausnahmen (fehlende/zusaetzliche Kanten, unplatzierte Knoten)."""
import math, random
from collections import Counter, defaultdict, deque
from core import LOG
import qembed as QE
DIRS = [(a, b) for a in range(-2, 3) for b in range(0, 3) if (b > 0 or a > 0)]
def runs_cost(sites, cellt, W, T):
    """Kernregion (Parallelogramm, Shear -1..1) + gierige Laeufe fuer den Rest."""
    core = [p for p, t in sites.items() if t == cellt]; best = None
    for s in (-1, 0, 1):
        pts = [(u + s * v, v) for u, v in core]; us = [p[0] for p in pts]; vs = [p[1] for p in pts]
        miss = (max(us) - min(us) + 1) * (max(vs) - min(vs) + 1) - len(core) if core else 0
        if best is None or miss < best: best = miss
    bits = 6 * LOG(W) + best * 2 * LOG(W) + LOG(T)
    nc = {p: t for p, t in sites.items() if t != cellt}; todo = set(nc); nr = 0
    while todo:
        b = None
        for p in todo:
            for d in DIRS:
                q = (p[0] - d[0], p[1] - d[1])
                if q in todo and nc[q] == nc[p]: continue
                n = 0; q = p
                while q in todo and nc[q] == nc[p]: n += 1; q = (q[0] + d[0], q[1] + d[1])
                if b is None or n > b[0]: b = (n, p, d)
        n, p, d = b; nr += 1
        for i in range(n): todo.discard((p[0] + i * d[0], p[1] + i * d[1]))
    return bits + nr * (LOG(T) + 2 * LOG(W) + LOG(len(DIRS)) + LOG(W)), nr
def model_cost(E, ptype, N, disp, nlab, T, labc, runs=True):
    QB = E['QB']; coord, _, info = QE.place(QB, E['core_coord'], disp, N); cellt = E['cell']
    sites = {coord[x]: ptype[x] for x in coord}; us = [p[0] for p in coord.values()]; vs = [p[1] for p in coord.values()]; W = max(max(us) - min(us), max(vs) - min(vs)) + 2
    typ_of = defaultdict(Counter); act = defaultdict(set)
    for a, b, bb in QB: typ_of[bb][(ptype[a], ptype[b])] += 1; act[bb].add((a, b))
    extra = miss = 0; bundle_bits = 0.0; bytype = defaultdict(list)
    for x in coord: bytype[ptype[x]].append(x)
    for bb, A in act.items():
        d = disp.get(bb)
        if d is None: extra += len(A); continue
        bundle_bits += labc * nlab[bb] + 2 + 2 * LOG(7)
        ta, tb = typ_of[bb].most_common(1)[0][0]; P = set()
        for x in bytype[ta]:
            y = sites.get((coord[x][0] + d[0], coord[x][1] + d[1]))
            if y is not None and y == tb:
                for yy in [z for z in QE_occ(coord, (coord[x][0] + d[0], coord[x][1] + d[1]))]: P.add((x, yy))
        miss += len(P - A); extra += len(A - P)
    unplaced = N - len(coord)
    rb, nr = runs_cost(sites, cellt, W, T) if runs else (0, 0)
    n = LOG(N); exc = (extra + miss) * (2 * n + labc) + unplaced * (LOG(T) + 2 * LOG(W))
    return bundle_bits + rb + exc, {'bundle_bits': round(bundle_bits), 'site_bits': round(rb), 'exception_bits': round(exc), 'extra': extra, 'miss': miss, 'unplaced': unplaced, 'runs': nr}
_occ_cache = {}
def QE_occ(coord, p):
    key = id(coord)
    if key not in _occ_cache or _occ_cache[key][0] is not coord:
        inv = defaultdict(list)
        for x, q in coord.items(): inv[q].append(x)
        _occ_cache.clear(); _occ_cache[key] = (coord, inv)
    return _occ_cache[key][1].get(p, [])
def optimize(E, ptype, N, rounds=3, rad=3, verbose=True):
    T = len(set(ptype.values())); labs = defaultdict(set)
    for kk, bb in E['bid'].items(): labs[bb].add(kk)
    nlab = {bb: len(v) for bb, v in labs.items()}; labc = 2 * LOG(T) + 2 * LOG(20)
    core_b = set()
    for a, b, bb in E['QB']:
        if a in E['core'] and b in E['core']: core_b.add(bb)
    disp = dict(E['disp']); cur, br = model_cost(E, ptype, N, disp, nlab, T, labc); start = cur
    d2 = dict(disp)                                   # Alternativstart: Mehrheitsverschiebung je Buendel, iteriert
    for _ in range(5):
        co, _, _ = QE.place(E['QB'], E['core_coord'], d2, N); mj = defaultdict(Counter)
        for a, b, bb in E['QB']:
            if a in co and b in co: mj[bb][(co[b][0] - co[a][0], co[b][1] - co[a][1])] += 1
        nd = dict(d2)
        for bb, c in mj.items():
            if bb not in core_b: nd[bb] = c.most_common(1)[0][0]
        if nd == d2: break
        d2 = nd
    c2, br2 = model_cost(E, ptype, N, d2, nlab, T, labc)
    if verbose: print('  majority start', round(c2), br2, flush=True)
    if c2 < cur: disp, cur, br = d2, c2, br2
    if verbose: print('  start', round(cur), br, flush=True)
    cands = [(du, dv) for du in range(-rad, rad + 1) for dv in range(-rad, rad + 1) if (du, dv) != (0, 0)] + [None]
    order = sorted({bb for _, _, bb in E['QB']} - core_b, key=lambda b: -nlab[b])
    for rd in range(rounds):
        improved = False
        for bb in order:
            old = disp.get(bb); bestc = (cur, old)
            for dd in cands:
                if dd == old: continue
                if dd is None: disp.pop(bb, None)
                else: disp[bb] = dd
                c, _ = model_cost(E, ptype, N, disp, nlab, T, labc)
                if c < bestc[0] - 1e-9: bestc = (c, dd)
            if bestc[1] is None: disp.pop(bb, None)
            else: disp[bb] = bestc[1]
            if bestc[0] < cur - 1e-9: cur = bestc[0]; improved = True
        if verbose: print('  round', rd, round(cur), flush=True)
        if not improved: break
    cur, br = model_cost(E, ptype, N, disp, nlab, T, labc)
    return cur, br, disp, start
