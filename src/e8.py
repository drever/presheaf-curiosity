import sys, json, time, random
import und
from und import *
from und2 import learn_best
import e2
from e2 import R, maxn, NS, NTEST, make_world, gen_comp
def main(world, seed):
    und.SYMS = set(); sym = world == 'sym'; rng = random.Random(1000 + seed); perm, motifs, nrel = make_world(rng, sym)
    allc = [gen_comp(rng, perm, motifs, nrel, sym) for _ in range(max(NS) + NTEST)]; test = allc[max(NS):]; out = {'world': world, 'seed': seed, 'res': {}}
    for n in NS:
        t0 = time.time(); D, w = learn_best(allc[:n], R, 20, maxn, False, return_which=True)
        out['res'][n] = {'k': len(D), 'which': w, 'test': total_u(test, D, R, maxn, False) / len(test), 'time': time.time() - t0}
    json.dump(out, open(f'e8_{world}_{seed}.json', 'w')); print('fertig', world, seed, flush=True)
if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]))
