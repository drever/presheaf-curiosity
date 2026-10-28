import sys, json, time, random, signal
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import dict_bits
import e12
from e12 import R, maxn, make_lib, gen_comp
from mol_big import gspan_mol
from mol_sel import greedy_select
from mol_subdue import run_subdue

def main(depth, n, seed, K=40):
    und.SYMS = set(); rng = random.Random(5000 + 100 * depth + seed); lib = make_lib(rng, depth)
    allc = [gen_comp(rng, lib) for _ in range(300 + 100)]; train, test = allc[:n], allc[300:]
    out = {'depth': depth, 'n': n, 'seed': seed, 'm': {}}
    def ev(nm, D, tm, sort=False):
        if sort: D = sorted(D, key=len)
        out['m'][nm] = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'train': total_u(train, D, R, maxn, False) / n, 'test': total_u(test, D, R, maxn, False) / len(test),
                        'dict_flat': dict_bits(D, R, maxn), 'dict_h': dict_bits_h(D, R, maxn), 'time': tm}
        print(depth, n, seed, nm, len(D), round(out['m'][nm]['test'], 1), round(out['m'][nm]['dict_flat']), round(out['m'][nm]['dict_h']), flush=True)
    for nm, mode, obj in (('hier_flat', 'hier', 'flat'), ('hier_hier', 'hier', 'hier'), ('grow_flat', 'grow', 'flat'), ('grow_hier', 'grow', 'hier')):
        t0 = time.time(); ev(nm, learn_h(train, R, K, maxn, False, mode=mode, topc=30, maxe=18, objective=obj), time.time() - t0)
    if depth <= 2:
        def handler(sig, frm): raise TimeoutError()
        signal.signal(signal.SIGALRM, handler)
        try:
            signal.alarm(240); t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.2 * n)), 20, f'{__import__("tempfile").gettempdir()}/e14_{depth}_{n}_{seed}.gsp'); signal.alarm(0)
            ev('gspan_mdl', greedy_select(train, C, R, maxn, K, 30), time.time() - t0, sort=True)
        except TimeoutError: out['m']['gspan_mdl'] = {'timeout': True}
        t0 = time.time(); pats, _ = run_subdue(train, 30, 500, 18, 4); tm = time.time() - t0; Dd = []; seen = set()
        for p in pats:
            kk = canon_u(p, True)
            if kk not in seen: seen.add(kk); Dd.append(p)
        trn = [total_u(train, Dd[:m], R, maxn) for m in range(len(Dd) + 1)]; ns = min(range(len(trn)), key=lambda m: trn[m]); ev('subdue_mdl', Dd[:ns], tm, sort=True)
    json.dump(out, open(f'e14_{depth}_{n}_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
