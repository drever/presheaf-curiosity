import itertools, collections, pynauty
from core import LOG, normalize, order_pattern, dict_bits
SYMS = set()

def canon_u(edges, und):
    vs = sorted({x for e in edges for x in (e[0], e[2])}); nv = len(vs); ix = {v: i for i, v in enumerate(vs)}
    N = nv + len(edges); adj = collections.defaultdict(list); color = [0] * nv
    for j, (a, r, b) in enumerate(edges):
        w = nv + j; color.append(r + 1)
        if und and r in SYMS: adj[ix[a]].append(w); adj[ix[b]].append(w)
        else: adj[ix[a]].append(w); adj[w].append(ix[b])
    cl = collections.defaultdict(set)
    for v, c in enumerate(color): cl[c].add(v)
    g = pynauty.Graph(N, directed=True, adjacency_dict=dict(adj), vertex_coloring=[cl[c] for c in sorted(cl)])
    lab = pynauty.canon_label(g)
    return (pynauty.certificate(g), tuple(color[lab[i]] for i in range(N)))

def embed_u(pat, comp, used):
    m = {}; inv = set(); ch = []
    def rec(i):
        if i == len(pat): return True
        u, r, v = pat[i]; sym = r in SYMS
        if u in m: cand = comp.out[m[u]] + (comp.inn[m[u]] if sym else [])
        elif v in m: cand = comp.inn[m[v]] + (comp.out[m[v]] if sym else [])
        else: cand = comp.byrel[r]
        for e in cand:
            if e[2] != r or e[0] in used or e[0] in ch: continue
            for ma, mb in [(e[1], e[3])] + ([(e[3], e[1])] if sym else []):
                if (u in m and m[u] != ma) or (v in m and m[v] != mb): continue
                new = []; ok = True
                if u not in m:
                    if ma in inv: continue
                    m[u] = ma; inv.add(ma); new.append(u)
                if v not in m:
                    if mb in inv: ok = False
                    else: m[v] = mb; inv.add(mb); new.append(v)
                if ok:
                    ch.append(e[0])
                    if rec(i + 1): return True
                    ch.pop()
                for x in new: inv.discard(m[x]); del m[x]
        return False
    return (list(ch), dict(m)) if rec(0) else None

def cover_u(comp, D):
    used = set(); inst = []
    for pi in sorted(range(len(D)), key=lambda i: -len(D[i])):
        while True:
            res = embed_u(D[pi], comp, used)
            if not res: break
            ids, m = res; used |= set(ids); inst.append((pi, tuple(ids), tuple(sorted(m.items()))))
    return inst, [e[0] for e in comp.E if e[0] not in used]

def total_u(comps, D, R, maxn, with_dict=True):
    s = 0
    for c in comps:
        inst, raw = cover_u(c, D); n = LOG(c.n)
        s += len(raw) * (2 * n + LOG(R)) + sum(LOG(len(D) + 1) + len(mm) * n for _, _, mm in inst)
    return s + (dict_bits(D, R, maxn) if with_dict else 0)

def learn_u(train, R, K, maxn, und, mode='hier', topc=6, maxe=10):
    D = []; keys = set(); L = total_u(train, D, R, maxn)
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
                pat = normalize(es); k = canon_u(pat, und)
                if k in keys: continue
                cnt.setdefault(k, [0, pat])[0] += 1
        cands = sorted(cnt.values(), key=lambda x: -x[0] * len(x[1]))[:topc]
        best, bL = None, L
        for n_, pat in cands:
            try: op = tuple(order_pattern(pat))
            except ValueError: continue
            Ln = total_u(train, D + [op], R, maxn)
            if Ln < bL: best, bL = op, Ln
        if best is None: break
        D.append(best); keys.add(canon_u(best, und)); L = bL
    return D
