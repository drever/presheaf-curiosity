import sys, json, time, random
import und
from und import *
from und2 import learn_w
import e2
from e2 import R, maxn, NS, NTEST, make_world, gen_comp
V = {'plain100': lambda tr: learn_u(tr, R, 20, maxn, False, mode='hier', topc=100, maxe=10),
     'sub5': lambda tr: learn_w(tr, R, 20, maxn, False, use_glue=False, maxs=5),
     'sub5glue': lambda tr: learn_w(tr, R, 20, maxn, False, use_glue=True, maxs=5),
     'sub3glue': lambda tr: learn_w(tr, R, 20, maxn, False, use_glue=True, maxs=3)}
def main(world, seed):
    und.SYMS = set(); sym = world == 'sym'; rng = random.Random(1000 + seed); perm, motifs, nrel = make_world(rng, sym)
    allc = [gen_comp(rng, perm, motifs, nrel, sym) for _ in range(max(NS) + NTEST)]; test = allc[max(NS):]; out = {'world': world, 'seed': seed, 'res': {}}
    for n in NS:
        res = {}
        for nm, f in V.items():
            t0 = time.time(); D = f(allc[:n]); res[nm] = {'k': len(D), 'test': total_u(test, D, R, maxn, False) / len(test), 'time': time.time() - t0}
        out['res'][n] = res
    json.dump(out, open(f'e6_{world}_{seed}.json', 'w')); print('fertig', world, seed, flush=True)
if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]))
