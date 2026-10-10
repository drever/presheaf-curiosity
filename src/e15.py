import sys, json, time, random, signal
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import dict_bits
from kg_final import load, sample
from mol_big import gspan_mol
from mol_sel import greedy_select
from mol_subdue import run_subdue

def main(name, seed, N, K, which):
    und.SYMS = set(); k = 5; maxn = k + 1
    tr, R = load(name); comps = sample(tr, N, k, random.Random(seed)); cut = int(.7 * len(comps)); train, test = comps[:cut], comps[cut:]; n = len(train)
    out = {'name': name, 'seed': seed, 'n': n, 'nte': len(test), 'K': K, 'm': {}}
    def ev(nm, D, tm, sort=False):
        if sort: D = sorted(D, key=len)
        out['m'][nm] = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'train': total_u(train, D, R, maxn, False) / n, 'test': total_u(test, D, R, maxn, False) / len(test),
                        'dict_flat': dict_bits(D, R, maxn), 'dict_h': dict_bits_h(D, R, maxn), 'time': tm}
        print(name, seed, nm, len(D), round(out['m'][nm]['test'], 1), round(out['m'][nm]['dict_flat']), round(out['m'][nm]['dict_h']), round(tm), 's', flush=True)
        json.dump(out, open(f'e15_{name}_{seed}.json', 'w'))
    for nm in which:
        t0 = time.time()
        if nm in ('hier_flat', 'hier_hier', 'grow_flat', 'grow_hier'):
            mode, obj = nm.split('_'); ev(nm, learn_h(train, R, K, maxn, False, mode=mode, topc=30, maxe=10, objective=obj), time.time() - t0)
        elif nm == 'gspan':
            C, nf = gspan_mol(train, None, max(2, int(.10 * n)), 8, f'/tmp/e15_{name}_{seed}.gsp'); ev(nm, greedy_select(train, C, R, maxn, K, 30), time.time() - t0, sort=True)
        elif nm == 'subdue':
            pats, _ = run_subdue(train, 40, 500, 10, 4); tm = time.time() - t0; Dd = []; seen = set()
            for p in pats:
                kk = canon_u(p, True)
                if kk not in seen: seen.add(kk); Dd.append(p)
            trn = [total_u(train, Dd[:m], R, maxn) for m in range(len(Dd) + 1)]; ns = min(range(len(trn)), key=lambda m: trn[m]); ev(nm, Dd[:ns], tm, sort=True)
if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5].split(','))
