import sys, json, time, random
import und
from und import *
from molcommon import load_mols, sample_comps, canon_bond
from mol_big import gspan_mol

def residual_counts(train, D, cands, exclude):
    used_sets = []
    for c in train:
        inst, raw = cover_u(c, D)
        used_sets.append(set(range(len(c.E))) - set(raw))
    sc = []
    for idx, p in enumerate(cands):
        if idx in exclude: continue
        n = 0
        for c, u0 in zip(train, used_sets):
            used = set(u0)
            while True:
                res = embed_u(p, c, used)
                if not res: break
                used |= set(res[0]); n += 1
        sc.append((n * len(p), idx))
    sc.sort(reverse=True)
    return sc

def greedy_adaptive(train, cands, R, maxn, K, topc):
    D = []; L = total_u(train, D, R, maxn); chosen = set()
    for _ in range(K):
        sc = residual_counts(train, D, cands, chosen)
        best, bL, bi = None, L, None
        for s, idx in sc[:topc]:
            if s == 0: break
            Ln = total_u(train, D + [cands[idx]], R, maxn)
            if Ln < bL: best, bL, bi = cands[idx], Ln, idx
        if best is None: break
        D.append(best); chosen.add(bi); L = bL
    return D

def main(k, seed, maxv, N=300):
    tr = load_mols('mol/solubility.train.sdf'); te = load_mols('mol/solubility.test.sdf')
    keys = sorted({(bt, el[x], el[y]) for ms in (tr, te) for n, bonds, el in ms for a, bt, b in bonds for x, y in [canon_bond(el, a, b, bt)]})
    relid = {t: i for i, t in enumerate(keys)}; R = len(keys); und.SYMS = {i for t, i in relid.items() if t[1] == t[2]}
    rng = random.Random(seed); train = sample_comps(tr, int(.7 * N), k, rng, relid); test = sample_comps(te, N - int(.7 * N), k, rng, relid)
    maxn = k + 1
    C, nf = gspan_mol(train, None, max(2, int(.10 * len(train))), maxv, f'{__import__("tempfile").gettempdir()}/ma_{k}_{seed}.gsp')
    t0 = time.time(); D = greedy_adaptive(train, C, R, maxn, 20, 30); tm = time.time() - t0
    out = {'k': k, 'seed': seed, 'ncand': len(C), 'ad': {'k': len(D), 'max_edges': max([len(p) for p in D] or [0]),
           'test': total_u(test, D, R, maxn, False) / len(test), 'dict': total_u([], D, R, maxn), 'time': tm}}
    json.dump(out, open(f'ma_{k}_{seed}.json', 'w')); print('fertig', k, seed, round(tm, 1), 's', flush=True)

if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
