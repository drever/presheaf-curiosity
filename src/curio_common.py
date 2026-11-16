"""Shared pieces of the curiosity experiment (docs/prereg-curiosity.md): data, candidate patterns, rank correlation."""
import random, itertools, collections
import und
from und import *
from und3 import total_h
from core import Comp
from netlist import *
from iface import total_iface
import split as SP

NN = 31; MAXN = 32; R = 64; MAXE = 12; TOPC = 30; KDICT = 40


def setup(seed, npool=200, ntest=100):
    """Pool windows from region A and test windows from region B of the repaired split, as Comp objects."""
    und.SYMS = set(); und.TWIN_MAX = 6; L = Labeler()
    sp = SP.gate_walk_split(load_bench('c6288'), random.Random(900 + seed)); rng = random.Random(3900 + seed)
    pool = []; seen = set()
    while len(pool) < npool:
        for w in windows_from(sp['A'], rng, npool, nmax=20, labeler=L):
            k = frozenset(SP.nodes_of(w))
            if k not in seen and len(pool) < npool: seen.add(k); pool.append(w)
    test = windows_from(sp['B'], rng, ntest, nmax=20, labeler=L)
    assert not (SP.nodes_of(sp['A']) & SP.nodes_of(sp['B']))
    return [to_comp(w, rng, NN) for w in pool], [to_comp(w, rng, NN) for w in test], L


def unlearnable(pool, seed, frac=0.3):
    """Replace a random `frac` of the pool by windows of the same size with random endpoints and labels from the pool's label frequencies."""
    rng = random.Random(4900 + seed); labs = [e[2] for c in pool for e in c.E]
    idx = sorted(rng.sample(range(len(pool)), int(round(frac * len(pool))))); out = list(pool)
    for i in idx:
        c = pool[i]; nodes = sorted({x for e in c.E for x in (e[1], e[3])}); es = {}
        while len(es) < len(c.E):
            a, b = rng.sample(nodes, 2)
            if (a, b) not in es and (b, a) not in es: es[(a, b)] = rng.choice(labs)
        out[i] = Comp(c.n, [(a, r, b) for (a, b), r in es.items()])
    return out, set(idx)


def candidates(c, D, keys=()):
    """Candidate glue patterns in one window under dictionary D, exactly as one round of und3.learn_h forms them.
    Returns {canonical key: ordered pattern}."""
    inst, raw = cover_u(c, D); pieces = []; out = {}
    for pi, ids, mm in inst:
        mp = dict(mm); pieces.append((frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]), set(mp.values())))
    for e in raw:
        t = (c.E[e][1], c.E[e][2], c.E[e][3]); pieces.append((frozenset([t]), {t[0], t[2]}))
    for grp in [(p,) for p in pieces] + [(p, q) for p, q in itertools.combinations(pieces, 2) if p[1] & q[1]]:
        es = frozenset().union(*[g[0] for g in grp])
        if len(es) > MAXE: continue
        pat = normalize(es)
        try: k = canon_u(pat, False)
        except ValueError: continue
        if k in keys: continue
        out.setdefault(k, [0, pat])[0] += 1
    return out


def ranked_candidates(train, D, keys):
    """The candidates the learner would evaluate in this round: top TOPC by count times size. List of (count, ordered pattern, key)."""
    cnt = {}
    for c in train:
        for k, (n, pat) in candidates(c, D, keys).items():
            cnt.setdefault(k, [0, pat])[0] += n
    res = []
    for k, (n, pat) in sorted(cnt.items(), key=lambda x: -x[1][0] * len(x[1][1]))[:TOPC]:
        try: res.append((n, tuple(order_pattern(pat)), k))
        except ValueError: continue
    return res


def learn_traced(train, on_round=None):
    """und3.learn_h (mode 'hier', objective 'hier') with a hook: on_round(round, D, candidates, pool_gains) before the best candidate is added."""
    D = []; keys = set(); Lc = total_h(train, D, R, MAXN)
    for it in range(KDICT):
        cands = ranked_candidates(train, D, keys)
        gains = [Lc - total_h(train, D + [op], R, MAXN) for _, op, _ in cands]
        if on_round: on_round(it, D, cands, gains)
        if not cands or max(gains) <= 0: break
        j = max(range(len(cands)), key=lambda i: gains[i])          # first best, as in learn_h
        D.append(cands[j][1]); keys.add(cands[j][2]); Lc -= gains[j]
    return D


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
            for t in range(i, j + 1): r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rk(x), rk(y); n = len(a); ma, mb = sum(a) / n, sum(b) / n
    sa = sum((u - ma) ** 2 for u in a) ** .5; sb = sum((u - mb) ** 2 for u in b) ** .5
    return None if sa == 0 or sb == 0 else sum((u - ma) * (v - mb) for u, v in zip(a, b)) / (sa * sb)
