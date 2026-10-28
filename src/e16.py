import sys, json, time, random
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import dict_bits
from molcommon import load_mols, sample_comps, canon_bond
from mol_big import gspan_mol
from mol_sel import greedy_select
from mol_subdue import run_subdue

def main(k, seed, maxv, which, N=300, K=40):
    tr = load_mols('mol/solubility.train.sdf'); te = load_mols('mol/solubility.test.sdf')
    keys = sorted({(bt, el[x], el[y]) for ms in (tr, te) for n_, bonds, el in ms for a, bt, b in bonds for x, y in [canon_bond(el, a, b, bt)]})
    relid = {t: i for i, t in enumerate(keys)}; R = len(keys); und.SYMS = {i for t, i in relid.items() if t[1] == t[2]}
    rng = random.Random(seed); train = sample_comps(tr, int(.7 * N), k, rng, relid); test = sample_comps(te, N - int(.7 * N), k, rng, relid)
    maxn = k + 1; n = len(train); out = {'k': k, 'seed': seed, 'n': n, 'K': K, 'm': {}}
    def ev(nm, D, tm, sort=False):
        if sort: D = sorted(D, key=len)
        out['m'][nm] = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'train': total_u(train, D, R, maxn, False) / n, 'test': total_u(test, D, R, maxn, False) / len(test),
                        'dict_flat': dict_bits(D, R, maxn), 'dict_h': dict_bits_h(D, R, maxn), 'time': tm}
        print(k, seed, nm, len(D), round(out['m'][nm]['test'], 1), round(out['m'][nm]['dict_flat']), round(out['m'][nm]['dict_h']), round(tm), 's', flush=True)
        json.dump(out, open(f'e16_{k}_{seed}.json', 'w'))
    for nm in which:
        t0 = time.time()
        if nm in ('hier_flat', 'hier_hier', 'grow_flat', 'grow_hier'):
            mode, obj = nm.split('_'); ev(nm, learn_h(train, R, K, maxn, True, mode=mode, topc=30, maxe=max(10, k), objective=obj), time.time() - t0)
        elif nm == 'gspan':
            C, nf = gspan_mol(train, None, max(2, int(.10 * n)), maxv, f'{__import__("tempfile").gettempdir()}/e16_{k}_{seed}.gsp'); ev(nm, greedy_select(train, C, R, maxn, K, 30), time.time() - t0, sort=True)
        elif nm == 'subdue':
            pats, _ = run_subdue(train, 40, 500, max(10, k), 4); tm = time.time() - t0; Dd = []; seen = set()
            for p in pats:
                kk = canon_u(p, True)
                if kk not in seen: seen.add(kk); Dd.append(p)
            trn = [total_u(train, Dd[:m], R, maxn) for m in range(len(Dd) + 1)]; ns = min(range(len(trn)), key=lambda m: trn[m]); ev(nm, Dd[:ns], tm, sort=True)
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4].split(','))
