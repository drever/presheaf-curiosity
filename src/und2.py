import itertools
from und import *
from und import cover_u, canon_u, total_u
from core import LOG, normalize, order_pattern, dict_bits
import und

def learn_v(train, R, K, maxn, und_flag, topc=30, patience=3, maxe=10, rank='gain', prune=True):
    D = []; keys = set(); L = total_u(train, D, R, maxn)
    ln = LOG(maxn); rawc = 2 * ln + LOG(R)
    for it in range(K):
        cnt = {}
        for c in train:
            inst, raw = cover_u(c, D); pieces = []
            for pi, ids, mm in inst:
                mp = dict(mm); pieces.append((frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]), set(mp.values())))
            for e in raw:
                t = (c.E[e][1], c.E[e][2], c.E[e][3]); pieces.append((frozenset([t]), {t[0], t[2]}))
            cand = [(p,) for p in pieces] + [(p, q) for p, q in itertools.combinations(pieces, 2) if p[1] & q[1]]
            for grp in cand:
                es = frozenset().union(*[g[0] for g in grp])
                if len(es) > maxe: continue
                pat = normalize(es); k = canon_u(pat, und_flag)
                if k in keys: continue
                cnt.setdefault(k, [0, pat])[0] += 1
        scored = []
        for n_, pat in cnt.values():
            e = len(pat); v = len({x for a, r, b in pat for x in (a, b)})
            if rank == 'gain':
                save = e * rawc - (LOG(len(D) + 2) + v * ln); s = n_ * save - (2 + e * rawc)
            else: s = n_ * e
            if s > 0: scored.append((s, pat))
        scored.sort(key=lambda x: -x[0])
        best, bL = None, L
        for b in range(patience):
            for s, pat in scored[b * topc:(b + 1) * topc]:
                try: op = tuple(order_pattern(pat))
                except ValueError: continue
                Ln = total_u(train, D + [op], R, maxn)
                if Ln < bL: best, bL = op, Ln
            if best is not None: break
        if best is None: break
        D.append(best); keys.add(canon_u(best, und_flag)); L = bL
    if prune:
        improved = True
        while improved and D:
            improved = False
            for i in range(len(D)):
                t = D[:i] + D[i + 1:]; Lt = total_u(train, t, R, maxn)
                if Lt < L: D, L, improved = t, Lt, True; break
    return D

def subgraph_pool(train, und_flag, maxs, maxe_cap=10):
    pool = {}
    for ci, c in enumerate(train):
        E = [(a, r, b) for _, a, r, b in c.E]; nodes = [{a, b} for a, r, b in E]
        cur = {frozenset([i]) for i in range(len(E))}; seen_c = set()
        for size in range(1, maxs + 1):
            nxt = set()
            for s in cur:
                if size >= 2:
                    es = [E[i] for i in s]; pat = normalize(es); k = canon_u(pat, und_flag)
                    if k not in seen_c:
                        seen_c.add(k); pool.setdefault(k, [0, pat])[0] += 1
                if size < maxs:
                    vs = set().union(*[nodes[i] for i in s])
                    for j in range(len(E)):
                        if j not in s and nodes[j] & vs: nxt.add(s | {j})
            cur = nxt
    return pool

def learn_w(train, R, K, maxn, und_flag, topc=30, maxs=5, patience=2, maxe=10, use_glue=True):
    D = []; keys = set(); L = total_u(train, D, R, maxn)
    ln = LOG(maxn); rawc = 2 * ln + LOG(R)
    pool = subgraph_pool(train, und_flag, maxs)
    def gscore(n_, pat, dl):
        e = len(pat); v = len({x for a, r, b in pat for x in (a, b)})
        return n_ * (e * rawc - (LOG(dl + 2) + v * ln)) - (2 + e * rawc)
    for it in range(K):
        cands = {}
        for k, (n_, pat) in pool.items():
            if k in keys: continue
            s = gscore(n_, pat, len(D))
            if s > 0: cands[k] = (s, pat)
        if use_glue:
            cnt = {}
            for c in train:
                inst, raw = cover_u(c, D); pieces = []
                for pi, ids, mm in inst:
                    mp = dict(mm); pieces.append((frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]), set(mp.values())))
                for e in raw:
                    t = (c.E[e][1], c.E[e][2], c.E[e][3]); pieces.append((frozenset([t]), {t[0], t[2]}))
                for p, q in itertools.combinations(pieces, 2):
                    if not (p[1] & q[1]): continue
                    es = p[0] | q[0]
                    if len(es) > maxe: continue
                    pat = normalize(es); k = canon_u(pat, und_flag)
                    if k in keys: continue
                    cnt.setdefault(k, [0, pat])[0] += 1
            for k, (n_, pat) in cnt.items():
                s = gscore(n_, pat, len(D))
                if s > 0 and (k not in cands or cands[k][0] < s): cands[k] = (s, pat)
        scored = sorted(cands.values(), key=lambda x: -x[0])
        best, bL = None, L
        for b in range(patience):
            for s, pat in scored[b * topc:(b + 1) * topc]:
                try: op = tuple(order_pattern(pat))
                except ValueError: continue
                Ln = total_u(train, D + [op], R, maxn)
                if Ln < bL: best, bL = op, Ln
            if best is not None: break
        if best is None: break
        D.append(best); keys.add(canon_u(best, und_flag)); L = bL
    return D

def learn_x(train, R, K, maxn, und_flag, topc=50, maxs=4, patience=2, maxe=10):
    D = []; keys = set(); L = total_u(train, D, R, maxn)
    ln = LOG(maxn); rawc = 2 * ln + LOG(R)
    pool = subgraph_pool(train, und_flag, maxs)
    def gscore(n_, pat, dl):
        e = len(pat); v = len({x for a, r, b in pat for x in (a, b)})
        return n_ * (e * rawc - (LOG(dl + 2) + v * ln)) - (2 + e * rawc)
    for it in range(K):
        cands = {k: [n_, pat] for k, (n_, pat) in pool.items() if k not in keys}
        cnt = {}
        for c in train:
            inst, raw = cover_u(c, D); pieces = []
            for pi, ids, mm in inst:
                mp = dict(mm); pieces.append((frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]), set(mp.values())))
            for e in raw:
                t = (c.E[e][1], c.E[e][2], c.E[e][3]); pieces.append((frozenset([t]), {t[0], t[2]}))
            for grp in [(p,) for p in pieces] + list(itertools.combinations(pieces, 2)):
                if len(grp) == 2 and not (grp[0][1] & grp[1][1]): continue
                es = frozenset().union(*[g[0] for g in grp])
                if len(es) > maxe: continue
                pat = normalize(es); k = canon_u(pat, und_flag)
                if k in keys: continue
                cnt.setdefault(k, [0, pat])[0] += 1
        for k, (n_, pat) in cnt.items():
            if k not in cands or cands[k][0] < n_: cands[k] = [n_, pat]
        items = list(cands.values())
        A = sorted(items, key=lambda x: -gscore(x[0], x[1], len(D)))
        B = sorted(items, key=lambda x: -x[0] * len(x[1]))
        best, bL = None, L; tried = set()
        for b in range(patience):
            for lst in (A, B):
                for n_, pat in lst[b * topc:(b + 1) * topc]:
                    if pat in tried: continue
                    tried.add(pat)
                    try: op = tuple(order_pattern(pat))
                    except ValueError: continue
                    Ln = total_u(train, D + [op], R, maxn)
                    if Ln < bL: best, bL = op, Ln
            if best is not None: break
        if best is None: break
        D.append(best); keys.add(canon_u(best, und_flag)); L = bL
    return D

def learn_best(train, R, K, maxn, und_flag, maxs=5, return_which=False):
    D1 = learn_u(train, R, K, maxn, und_flag, mode='hier', topc=100, maxe=10)
    D2 = learn_x(train, R, K, maxn, und_flag, maxs=maxs)
    L1, L2 = total_u(train, D1, R, maxn), total_u(train, D2, R, maxn)
    D, w = (D1, 'glue') if L1 <= L2 else (D2, 'pool')
    return (D, w) if return_which else D
