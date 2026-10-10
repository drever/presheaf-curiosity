import itertools, math
import und
from und import cover_u, canon_u, total_u, embed_u
from core import Comp, LOG, normalize, order_pattern, dict_bits

def pat_cost_h(p, earlier, R, maxn):
    """Bits fuer Muster p, wenn es aus frueheren Mustern (Verweis) und einzelnen Kanten zusammengeklebt wird.
    Kostet nie mehr als die flache Kantenliste."""
    edge = 2 * LOG(maxn) + LOG(R)
    flat = 2 + len(p) * edge
    if not earlier: return flat
    vs = sorted({x for a, r, b in p for x in (a, b)}); ix = {v: i for i, v in enumerate(vs)}
    comp = Comp(len(vs), [(ix[a], r, ix[b]) for a, r, b in p])
    inst, raw = cover_u(comp, earlier)
    if not inst: return flat
    seen_v = set(); bits = 2
    parts = [(LOG(len(earlier)), {v for _, v in mm}) for _, ids, mm in inst] + [(edge, {comp.E[e][1], comp.E[e][3]}) for e in raw]
    # Kantenkosten fuer Rohkanten: Referenz auf Knoten wird ueber Klebe-Kosten unten bezahlt -> nur Relation + Marker
    parts = [(LOG(len(earlier)), {v for _, v in mm}) for _, ids, mm in inst] + [(LOG(R), {comp.E[e][1], comp.E[e][3]}) for e in raw]
    for c, vset in parts:
        bits += c
        for v in vset:
            bits += 1                                   # neu oder identifiziert?
            if v in seen_v: bits += LOG(max(2, len(seen_v)))   # mit welchem bisherigen Knoten
        seen_v |= vset
    return min(flat, bits)

def dict_bits_h(D, R, maxn):
    return sum(pat_cost_h(p, D[:k], R, maxn) for k, p in enumerate(D))

def total_h(comps, D, R, maxn, with_dict=True):
    return total_u(comps, D, R, maxn, False) + (dict_bits_h(D, R, maxn) if with_dict else 0)

def learn_h(train, R, K, maxn, und_flag, mode='hier', topc=30, maxe=10, objective='hier'):
    f = total_h if objective == 'hier' else total_u
    D = []; keys = set(); L = f(train, D, R, maxn)
    for it in range(K):
        cnt = {}
        for c in train:
            inst, raw = cover_u(c, D); pieces = []
            for pi, ids, mm in inst:
                mp = dict(mm); pieces.append((frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]), set(mp.values())))
            for e in raw:
                t = (c.E[e][1], c.E[e][2], c.E[e][3]); pieces.append((frozenset([t]), {t[0], t[2]}))
            cand = [(p,) for p in pieces] + [(p, q) for p, q in itertools.combinations(pieces, 2)
                    if p[1] & q[1] and (mode == 'hier' or len(p[0]) == 1 or len(q[0]) == 1)]
            for grp in cand:
                es = frozenset().union(*[g[0] for g in grp])
                if len(es) > maxe: continue
                pat = normalize(es); k = canon_u(pat, und_flag)
                if k in keys: continue
                cnt.setdefault(k, [0, pat])[0] += 1
        cands = sorted(cnt.values(), key=lambda x: -x[0] * len(x[1]))[:topc]
        best, bL = None, L
        for n_, pat in cands:
            try: op = tuple(order_pattern(pat))
            except ValueError: continue
            Ln = f(train, D + [op], R, maxn)
            if Ln < bL: best, bL = op, Ln
        if best is None: break
        D.append(best); keys.add(canon_u(best, und_flag)); L = bL
    return D
