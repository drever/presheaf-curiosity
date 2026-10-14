"""Test C: Makros mit Loch, dessen Fuellung ein Teilgraph-Muster aus dem Woerterbuch ist (Loch = Schnittstelle aus zwei Anschlussknoten).
Ausgangspunkt: Glue-Woerterbuch D und seine Ueberdeckung. Ein Loch ist (Rahmenmuster A, Knoten p,q). Kandidaten: Instanzen B, die nur an
den zwei Knoten p,q am Rahmen haengen (sauberer Anschluss). Loch-Modell: Option = Fuellmuster (mit Anschlussreihenfolge), 'leer' (triviale
Fuellung) oder 'sonst'. Kosten: -log2 p(Option); eingesetzte Fuellung kostet sonst nichts (kein Index, keine Zeiger), ihre Anschluss-
knoten sind intern. Vergleich mit getrenntem Kodieren (Iface- bzw. relative Adressierung)."""
import math, collections, itertools
import und
from und import cover_u
from core import LOG
from iface import lcomb

class Unit:
    __slots__ = ('pi', 'ids', 'mp', 'V', 'inv')
    def __init__(s, pi, ids, mm):
        s.pi = pi; s.ids = set(ids); s.mp = dict(mm); s.V = set(s.mp.values()); s.inv = {v: k for k, v in s.mp.items()}

def get_units(c, D):
    inst, raw = cover_u(c, D)
    return [Unit(pi, ids, mm) for pi, ids, mm in inst], raw

def boundary(c, idset, nodes):
    return {v for v in nodes if any(e[0] not in idset for e in c.out[v]) or any(e[0] not in idset for e in c.inn[v])}

def clean_attach(c, A, B):
    """B haengt sauber an A: gemeinsame Knoten genau zwei, B hat sonst keinen Kontakt. Liefert (p,q,s,t) oder None."""
    if len(B.ids) >= len(A.ids): return None
    S = A.V & B.V
    if len(S) != 2: return None
    if not boundary(c, B.ids, B.V) <= S: return None
    a, b = sorted(S, key=lambda v: A.inv[v]); return A.inv[a], A.inv[b], B.inv[a], B.inv[b]

def candidates(train_units, train_comps):
    cnt = collections.defaultdict(collections.Counter); nA = collections.Counter()
    for c, (units, raw) in zip(train_comps, train_units):
        for A in units: nA[A.pi] += 1
        for A in units:
            for B in units:
                if A is B: continue
                r = clean_attach(c, A, B)
                if r: cnt[(A.pi, r[0], r[1])][(B.pi, r[2], r[3])] += 1
    return cnt, nA

def make_hole(key, fillcnt, nA_pi, min_c=2):
    fil = {f: n for f, n in fillcnt.items() if n >= min_c}
    other = sum(n for f, n in fillcnt.items() if f not in fil); filled = sum(fillcnt.values())
    empty = max(0, nA_pi - filled)
    if len(fil) + (empty > 0) < 2: return None
    opts = {('f',) + f: n for f, n in fil.items()}; opts[('empty',)] = empty; opts[('other',)] = other
    tot = sum(opts.values()); 
    prob = {o: (n + 0.5) / (tot + 0.5 * len(opts)) for o, n in opts.items()}
    return {'key': key, 'fil': set(fil), 'prob': prob, 'nopt': len(opts)}

def hole_dict_bits(h, ND, V):
    return 2 * LOG(max(2, V)) + h['nopt'] * (LOG(ND + 1) + 2 * LOG(max(2, V)) + 6)

def window_cost(c, units, raw, D, holes, R, mode):
    """mode: 'iface' (Zeiger log n) oder 'rel' (relative Adressierung gegen schon platzierte Knoten, min mit iface)."""
    n = LOG(c.n); ND = len(D); bykey = collections.defaultdict(list)
    for h in holes: bykey[h['key'][0]].append(h)
    absorbed = {}; frames = {}; opt_bits = 0.0
    for i, A in enumerate(units):
        if i in absorbed or A.pi not in bykey: continue
        for h in bykey[A.pi]:
            _, p, q = h['key']; chosen = None; seen_other = False
            for j, B in enumerate(units):
                if j == i or j in absorbed or j in frames: continue
                r = clean_attach(c, A, B)
                if r and (r[0], r[1]) == (p, q):
                    if (B.pi, r[2], r[3]) in h['fil']: chosen = (j, ('f', B.pi, r[2], r[3])); break
                    seen_other = True
            if chosen: absorbed[chosen[0]] = i; frames[i] = True; opt_bits += -LOG(h['prob'][chosen[1]])
            elif seen_other: opt_bits += -LOG(h['prob'][('other',)])
            else: opt_bits += -LOG(h['prob'][('empty',)])
    members = collections.defaultdict(list)
    for j, i in absorbed.items(): members[i].append(j)
    total = len(raw) * (2 * n + LOG(R)) + opt_bits; seen = set()
    for i, A in enumerate(units):
        if i in absorbed: continue
        ids = set(A.ids); V = set(A.V); extra = set()
        for j in members[i]: ids |= units[j].ids; extra |= units[j].V
        bset = boundary(c, ids, V | extra) & (V | extra)
        # Knoten, die nur im eingesetzten Fuellmuster liegen, aber Aussenkontakt haben, muessen ebenfalls adressiert werden
        k = len(bset); Vn = len(V)
        old = LOG(ND + 1) + Vn * n; new = LOG(ND + 1) + LOG(Vn + 1) + lcomb(Vn, k) + k * n
        u = min(old, new)
        if mode == 'rel':
            rel = LOG(ND + 1) + LOG(Vn + 1) + lcomb(Vn, k) + sum(1 + (LOG(max(2, len(seen))) if v in seen else n) for v in bset)
            u = min(u, rel)
        total += u + 1; seen |= V | extra
    return total

def total_cost(comps, covers, D, holes, R, mode):
    return sum(window_cost(c, u, r, D, holes, R, mode) for c, (u, r) in zip(comps, covers)) / len(comps)

def learn_holes(train, covers, D, R, mode, maxh=6):
    cnt, nA = candidates(covers, train)
    cands = [h for h in (make_hole(k, f, nA[k[0]]) for k, f in cnt.items()) if h]
    Vsize = {i: len({x for a, _, b in D[i] for x in (a, b)}) for i in range(len(D))}
    chosen = []; cur = total_cost(train, covers, D, chosen, R, mode) * len(train)
    while cands and len(chosen) < maxh:
        best = None
        for h in cands:
            t = total_cost(train, covers, D, chosen + [h], R, mode) * len(train) + sum(hole_dict_bits(x, len(D), Vsize[x['key'][0]]) for x in chosen + [h])
            base = cur + sum(hole_dict_bits(x, len(D), Vsize[x['key'][0]]) for x in chosen)
            if best is None or t - base < best[0]: best = (t - base, h)
        if best[0] >= 0: break
        chosen.append(best[1]); cands.remove(best[1]); cur = total_cost(train, covers, D, chosen, R, mode) * len(train)
    dbits = sum(hole_dict_bits(x, len(D), Vsize[x['key'][0]]) for x in chosen)
    return chosen, dbits
