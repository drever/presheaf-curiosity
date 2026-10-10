import sys, json, time, random
import und
from und import *
from molcommon import load_mols, sample_comps, canon_bond
from mol_big import gspan_mol

def greedy_select(train, cands, R, maxn, K, topc):
    D = []; L = total_u(train, D, R, maxn); left = list(cands)
    for _ in range(K):
        best, bL = None, L
        for p in left[:topc]:
            Ln = total_u(train, D + [p], R, maxn)
            if Ln < bL: best, bL = p, Ln
        if best is None: break
        D.append(best); left.remove(best); L = bL
    return D

def main(k, seed, maxv, N=300):
    tr = load_mols('mol/solubility.train.sdf'); te = load_mols('mol/solubility.test.sdf')
    keys = sorted({(bt, el[x], el[y]) for ms in (tr, te) for n, bonds, el in ms for a, bt, b in bonds for x, y in [canon_bond(el, a, b, bt)]})
    relid = {t: i for i, t in enumerate(keys)}; R = len(keys); und.SYMS = {i for t, i in relid.items() if t[1] == t[2]}
    rng = random.Random(seed); train = sample_comps(tr, int(.7 * N), k, rng, relid); test = sample_comps(te, N - int(.7 * N), k, rng, relid)
    maxn = k + 1
    t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(float(__import__("os").environ.get("MINSUP","0.10")) * len(train))), maxv, f'/tmp/ms_{k}_{seed}.gsp'); tg = time.time() - t0
    out = {'k': k, 'seed': seed, 'ncand': len(C), 'nfound': nf, 'm': {}}
    for topc in (6, 30):
        t0 = time.time(); D = greedy_select(train, C, R, maxn, 20, topc)
        out['m'][f'gspan_mdl_{topc}'] = {'k': len(D), 'max_edges': max([len(p) for p in D] or [0]), 'test': total_u(test, D, R, maxn, False) / len(test),
                                          'dict': total_u([], D, R, maxn), 'time': time.time() - t0 + tg}
    json.dump(out, open(f'ms_{k}_{seed}.json', 'w')); print('fertig', k, seed, len(C), flush=True)

if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
