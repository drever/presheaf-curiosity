"""Test C (Version 2): Makro mit Loch, Fuellung = Teilgraph-Muster aus einer eigenen Fuellbibliothek (top-down gelernt).
Loch = (Rahmenmuster A aus Glue-Woerterbuch D, Knotenpaar p<q). Fuellung: Teilgraph, der nur an a=m[p], b=m[q] am Rahmen haengt (<= maxF Kanten),
kanonisch mit markierten Anschluessen. Optionen: Bibliotheksfuellung, 'leer' (triviale Fuellung = initiales Objekt unter I), 'sonst'.
Kosten Option: -log2 p; eingesetzte Fuellung kostet keinen Index und keine Zeiger."""
import math, collections
import und
from und import embed_u, canon_u
from core import LOG
from iface import lcomb

def components(c, A_ids, A_V, skip=frozenset()):
    """Zusammenhangskomponenten der Nicht-Rahmen-Kanten ueber aeussere Knoten; liefert Liste (Kanten, T) mit T = beruehrte Rahmenknoten."""
    par = {}
    def find(x):
        while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
        return x
    es = [e for e in c.E if e[0] not in A_ids and e[0] not in skip]
    for e in es:
        u, v = e[1], e[3]
        if u not in A_V and v not in A_V: par[find(u)] = find(v)
    groups = {}
    for e in es:
        u, v = e[1], e[3]
        key = ('x', find(u)) if u not in A_V else (('x', find(v)) if v not in A_V else ('d', e[0]))
        g = groups.setdefault(key, [[], set()]); g[0].append(e); g[1] |= {x for x in (u, v) if x in A_V}
    return [(g[0], g[1]) for g in groups.values()]

def filler_of(comps, a, b, maxF):
    """None = groesse/mehrdeutig, [] = leer, sonst Kantenliste."""
    ks = [es for es, T in comps if T == {a, b}]
    if not ks: return None if any({a, b} < T for es, T in comps) else []
    if len(ks) > 1 or len(ks[0]) > maxF: return None
    return ks[0]

def filler_pattern(es, a, b):
    loc = {a: 0, b: 1}
    for _, u, r, v in es:
        for x in (u, v):
            if x not in loc: loc[x] = len(loc)
    return [(loc[u], r, loc[v]) for _, u, r, v in es]

def filler_key(pat, R):
    n = 2 + max([max(u, v) for u, _, v in pat] + [1])
    e = list(pat) + [(n, R + 1, 0), (n + 1, R + 2, 1)]
    return canon_u(e, bool(und.SYMS))

def match_filler(c, pat, a, b, forbid, used):
    """Einbettung von pat mit 0->a, 1->b; innere Knoten injektiv, nicht in forbid; Kanten nicht in used."""
    m = {0: a, 1: b}; inv = {a, b}; ch = []; syms = und.SYMS
    def rec(i):
        if i == len(pat): return True
        u, r, v = pat[i]; sym = r in syms
        if u in m: cand = c.out[m[u]] + (c.inn[m[u]] if sym else [])
        elif v in m: cand = c.inn[m[v]] + (c.out[m[v]] if sym else [])
        else: return False
        for e in cand:
            if e[2] != r or e[0] in used or e[0] in ch: continue
            for ma, mb in [(e[1], e[3])] + ([(e[3], e[1])] if sym else []):
                if (u in m and m[u] != ma) or (v in m and m[v] != mb): continue
                new = []; ok = True
                if u not in m:
                    if ma in inv or ma in forbid: continue
                    m[u] = ma; inv.add(ma); new.append(u)
                if v not in m:
                    if mb in inv or mb in forbid: ok = False
                    else: m[v] = mb; inv.add(mb); new.append(v)
                if ok:
                    ch.append(e[0])
                    if rec(i + 1): return True
                    ch.pop()
                for x in new: inv.discard(m[x]); del m[x]
        return False
    if not pat: return None
    # Reihenfolge so, dass jede Kante an bereits abgebildeten Knoten haengt
    order = []; rest = list(pat); mapped = {0, 1}
    while rest:
        for k, (u, r, v) in enumerate(rest):
            if u in mapped or v in mapped: order.append(rest.pop(k)); mapped |= {u, v}; break
        else: return None
    pat = order
    return (list(ch), dict(m)) if rec(0) else None

def cover_used(c, D, used0, alive=None):
    used = set(used0); inst = []
    for pi in sorted(alive if alive is not None else range(len(D)), key=lambda i: -len(D[i])):
        while True:
            res = embed_u(D[pi], c, used)
            if not res: break
            ids, m = res; used |= set(ids); inst.append((pi, set(ids), dict(m)))
    return inst, [e[0] for e in c.E if e[0] not in used], used

def bnd(c, idset, nodes):
    return {v for v in nodes if any(e[0] not in idset for e in c.out[v]) or any(e[0] not in idset for e in c.inn[v])}

def unit_bits(c, ids, V, nodes_all, n, ND, mode, seen):
    k_set = bnd(c, ids, nodes_all); k = len(k_set); Vn = len(V)
    old = LOG(ND + 1) + Vn * n; new = LOG(ND + 1) + LOG(Vn + 1) + lcomb(Vn, k) + k * n; u = min(old, new)
    if mode == 'rel':
        rel = LOG(ND + 1) + LOG(Vn + 1) + lcomb(Vn, k) + sum(1 + (LOG(max(2, len(seen))) if v in seen else n) for v in k_set)
        u = min(u, rel)
    return u + 1

def window_cost(c, D, H, lib, R, mode, maxF, alive=None):
    n = LOG(c.n); ND = len(D) if alive is None else len(alive); used = set(); seen = set(); bits = 0.0
    bykey = collections.defaultdict(list)
    for h in H: bykey[h['key'][0]].append(h)
    for pi in sorted(bykey, key=lambda i: -len(D[i])):
        while True:
            res = embed_u(D[pi], c, used)
            if not res: break
            ids, m = res; A_ids = set(ids); A_V = set(m.values()); fill_ids = set(); fill_V = set()
            for h in bykey[pi]:
                _, p, q = h['key']; a, b = m[p], m[q]; got = None
                for f in h['fil']:
                    r = match_filler(c, lib[f], a, b, A_V - {a, b}, used | A_ids | fill_ids)
                    if r: got = (f, r); break
                if got:
                    fill_ids |= set(got[1][0]); fill_V |= set(got[1][1].values()); bits += -LOG(h['prob'][('f', got[0])])
                else:
                    F = filler_of(components(c, A_ids | fill_ids, A_V), a, b, 99)
                    bits += -LOG(h['prob'][('empty',)] if F == [] else h['prob'][('other',)])
            used |= A_ids | fill_ids
            bits += unit_bits(c, A_ids | fill_ids, A_V, A_V | fill_V, n, ND, mode, seen); seen |= A_V | fill_V
    inst, raw, used = cover_used(c, D, used, alive)
    for pi, ids, m in inst:
        V = set(m.values()); bits += unit_bits(c, ids, V, V, n, ND, mode, seen); seen |= V
    return bits + len(raw) * (2 * n + LOG(R))

def total(comps, D, H, lib, R, mode, maxF, alive=None): return sum(window_cost(c, D, H, lib, R, mode, maxF, alive) for c in comps) / len(comps)

def hole_bits(h, ND, V): return 2 * LOG(max(2, V)) + h['nopt'] * (LOG(ND + 1) + 2 * LOG(max(2, V)) + 6) + sum(2 + 2 * len(x) for x in [])

def find_candidates(train, D, R, maxF, minF=2, minframe=4):
    from holes import get_units
    cnt = collections.defaultdict(collections.Counter); nA = collections.Counter(); lib = {}
    for c in train:
        for pi in range(len(D)):
            if len(D[pi]) < minframe: continue
            used = set()
            while True:
                res = embed_u(D[pi], c, used)
                if not res: break
                ids, m = res; used |= set(ids); A_ids = set(ids); A_V = set(m.values())
                nA[pi] += 1; ps = sorted(m); comps = components(c, A_ids, A_V)
                for i, p in enumerate(ps):
                    for q in ps[i + 1:]:
                        a, b = m[p], m[q]; F = filler_of(comps, a, b, maxF)
                        if F is None: cnt[(pi, p, q)][('big',)] += 1
                        elif not F: cnt[(pi, p, q)][('empty',)] += 1
                        else:
                            pat = filler_pattern(F, a, b); k = filler_key(pat, R); lib.setdefault(k, pat); cnt[(pi, p, q)][('f', k)] += 1
    cands = []
    for key, cn in cnt.items():
        fil = {o[1]: n for o, n in cn.items() if o[0] == 'f' and n >= minF}
        other = sum(n for o, n in cn.items() if (o[0] == 'f' and o[1] not in fil) or o[0] == 'big'); empty = cn.get(('empty',), 0)
        if not fil or len(fil) + (empty >= minF) < 2: continue
        opts = {('f', f): n for f, n in fil.items()}; opts[('empty',)] = empty; opts[('other',)] = other
        tot = sum(opts.values()); prob = {o: (n + 0.5) / (tot + 0.5 * len(opts)) for o, n in opts.items()}
        cands.append({'key': key, 'fil': set(fil), 'prob': prob, 'nopt': len(opts), 'score': sum(fil.values())})
    return cands, lib

def contains(Dj, Di):
    from core import Comp
    vs = sorted({x for a, _, b in Dj for x in (a, b)}); ix = {v: k for k, v in enumerate(vs)}
    return embed_u(Di, Comp(len(vs), [(ix[a], r, ix[b]) for a, r, b in Dj]), set()) is not None

def learn(train, D, R, mode, maxF=5, maxh=6, topc=20, maxn=32):
    from und3 import dict_bits_h
    cands, lib = find_candidates(train, D, R, maxF)
    cands = sorted(cands, key=lambda h: -h['score'])[:topc]
    Vs = {i: len({x for a, _, b in D[i] for x in (a, b)}) for i in range(len(D))}
    def hb(H): return sum(hole_bits(h, len(D), Vs[h['key'][0]]) + sum(2 + 3 * len(lib[f]) * LOG(8) for f in h['fil']) for h in H)
    def cost(H, alive): return total(train, D, H, lib, R, mode, maxF, alive) * len(train) + hb(H) + dict_bits_h([D[j] for j in sorted(alive)], R, maxn)
    groups = collections.defaultdict(list)
    for h in cands: groups[h['key'][0]].append(h)
    glist = []
    for pi, hs in groups.items():
        hs = sorted(hs, key=lambda h: -h['score']); top = hs[0]['score']
        glist.append((pi, [h for h in hs if h['score'] >= 0.4 * top][:3]))
    alive = set(range(len(D))); chosen = []; cur = cost(chosen, alive)
    while glist and len(chosen) < maxh:
        best = None
        for gi, (pi, hs) in enumerate(glist):
            sup = {j for j in alive if j != pi and len(D[j]) > len(D[pi]) and contains(D[j], D[pi])}
            for al in (alive, alive - sup):
                if pi not in al: continue
                t = cost(chosen + hs, al)
                if best is None or t < best[0]: best = (t, gi, al)
        if best is None or best[0] >= cur: break
        cur, gi, alive = best; chosen += glist[gi][1]; glist.pop(gi)
    return chosen, lib, alive, hb(chosen)

def strip_window(c, D, H, lib, maxF, alive=None):
    """Entfernt die von Loechern absorbierten Fuellkanten aus dem Fenster (fuer das Neulernen des Woerterbuchs ohne Kombinationsmuster)."""
    from core import Comp
    used = set(); gone = set(); bykey = collections.defaultdict(list)
    for h in H: bykey[h['key'][0]].append(h)
    for pi in sorted(bykey, key=lambda i: -len(D[i])):
        while True:
            res = embed_u(D[pi], c, used)
            if not res: break
            ids, m = res; A_ids = set(ids); A_V = set(m.values()); fill = set()
            for h in bykey[pi]:
                _, p, q = h['key']; a, b = m[p], m[q]
                for f in h['fil']:
                    r = match_filler(c, lib[f], a, b, A_V - {a, b}, used | A_ids | fill)
                    if r: fill |= set(r[0]); break
            used |= A_ids | fill; gone |= fill
    return Comp(c.n, [(e[1], e[2], e[3]) for e in c.E if e[0] not in gone])

def refine(train, D0, R, mode, learn_D, maxF=5, rounds=3, maxn=32):
    """Abwechselnd: Fuellkanten abziehen -> Woerterbuch neu lernen -> Loecher neu lernen. Waehlt die Runde mit den kleinsten Trainingskosten (inkl. Woerterbuch)."""
    from und3 import dict_bits_h
    def full_cost(D, H, lib, alive, hbits):
        return total(train, D, H, lib, R, mode, maxF, alive) * len(train) + hbits + dict_bits_h([D[j] for j in sorted(alive)], R, maxn)
    best = (full_cost(D0, [], {}, set(range(len(D0))), 0), D0, [], {}, set(range(len(D0))), 0, 0)
    D = D0; H, lib, alive, hbits = learn(train, D, R, mode, maxF, maxn=maxn)
    for rd in range(1, rounds + 1):
        cst = full_cost(D, H, lib, alive, hbits)
        print('  round', rd - 1, 'holes', len(H), 'alive', len(alive), 'train total', round(cst), 'baseline', round(best[0]), flush=True)
        if cst < best[0]: best = (cst, D, H, lib, alive, hbits, rd - 1)
        if not H: break
        stripped = [strip_window(c, D, H, lib, maxF) for c in train]
        D = learn_D(stripped)
        H, lib, alive, hbits = learn(train, D, R, mode, maxF, maxn=maxn)
    cst = full_cost(D, H, lib, alive, hbits)
    print('  round', rounds, 'holes', len(H), 'alive', len(alive), 'train total', round(cst), flush=True)
    if cst < best[0]: best = (cst, D, H, lib, alive, hbits, rounds)
    return best
