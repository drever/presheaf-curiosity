import sys, json, time, random, os
import und
from und import *
from molcommon import load_mols, sample_comps, canon_bond
from mol_big import gspan_mol
from mol_sel import greedy_select
from mol_subdue import run_subdue

def main(k, seed, maxv, N=300):
    tr = load_mols('mol/solubility.train.sdf'); te = load_mols('mol/solubility.test.sdf')
    keys = sorted({(bt, el[x], el[y]) for ms in (tr, te) for n, bonds, el in ms for a, bt, b in bonds for x, y in [canon_bond(el, a, b, bt)]})
    relid = {t: i for i, t in enumerate(keys)}; R = len(keys); und.SYMS = {i for t, i in relid.items() if t[1] == t[2]}
    rng = random.Random(seed); train = sample_comps(tr, int(.7 * N), k, rng, relid); test = sample_comps(te, N - int(.7 * N), k, rng, relid)
    maxn = k + 1; ntr = len(train)
    out = {'k': k, 'seed': seed, 'ntr': ntr, 'nte': len(test), 'm': {}}
    def ev(nm, D, tm):
        dbits = total_u([], D, R, maxn)
        trb = total_u(train, D, R, maxn, False)
        out['m'][nm] = {'k': len(D), 'max_edges': max([len(p) for p in D] or [0]), 'dict': dbits, 'train': trb / ntr,
                        'test': total_u(test, D, R, maxn, False) / len(test), 'time': tm}
        print(' ', nm, len(D), round(out['m'][nm]['test'], 1), round(tm, 1), 's', flush=True)
    for topc in (6, 30, 100):
        for mode in ('hier', 'grow'):
            if mode == 'grow' and topc != 30: continue
            t0 = time.time(); D = learn_u(train, R, 20, maxn, True, mode=mode, topc=topc, maxe=max(10, k)); ev(f'{mode}{topc}', D, time.time() - t0)
    t0 = time.time(); D = learn_u(train, R, 40, maxn, True, mode='hier', topc=30, maxe=max(10, k)); ev('hier30_K40', D, time.time() - t0)
    t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.10 * ntr)), maxv, f'{__import__("tempfile").gettempdir()}/mf_{k}_{seed}.gsp'); tg = time.time() - t0
    t0 = time.time(); D = greedy_select(train, C, R, maxn, 20, 30); ev('gspan_mdl30', D, tg + time.time() - t0)
    t0 = time.time(); pats, info = run_subdue(train, 40, 500, max(10, k), 4); tm = time.time() - t0
    Dall = []; seen = set()
    for p in pats:
        kk = canon_u(p, True)
        if kk not in seen: seen.add(kk); Dall.append(p)
    for n in (20, 40):
        Dn = Dall[:n]
        trn = [total_u(train, Dn[:m], R, maxn) for m in range(len(Dn) + 1)]
        ns = min(range(len(trn)), key=lambda m: trn[m])
        ev(f'subdue{n}_all', Dn, tm); ev(f'subdue{n}_mdl', Dn[:ns], tm)
    json.dump(out, open(f'mf_{k}_{seed}.json', 'w')); print('fertig', k, seed, flush=True)

if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
