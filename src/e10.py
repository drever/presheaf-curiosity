import sys, json, time, random
import und
from und import *
from und2 import learn_best
import e2
from e2 import R, P, maxn, NS, NTEST, make_world, gen_comp, quotient, est_mdl, costq
def main(world, seed):
    und.SYMS = set(); sym = world == 'sym'; rng = random.Random(1000 + seed); perm, motifs, nrel = make_world(rng, sym)
    true_sig = {}
    if sym:
        for c in range(P): true_sig[perm[c]] = perm[c + P]; true_sig[perm[c + P]] = perm[c]
    allc = [gen_comp(rng, perm, motifs, nrel, sym) for _ in range(max(NS) + NTEST)]; test = allc[max(NS):]; out = {'world': world, 'seed': seed, 'res': {}}
    for n in NS:
        train = allc[:n]; res = {}
        def run(nm, sig):
            q = quotient(train, sig); D = learn_best(q, R - len(sig) // 2, 20, maxn, False)
            res[nm] = {'k': len(D), 'test': costq(quotient(test, sig), D, sig, False), 'pairs': len(sig) // 2, 'right': sum(1 for r, s in sig.items() if true_sig.get(r) == s) // 2}
        run('new', {}); run('new_est', est_mdl(train))
        if sym: run('new_oracle', true_sig)
        out['res'][n] = res
    json.dump(out, open(f'e10_{world}_{seed}.json', 'w')); print('fertig', world, seed, flush=True)
if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]))
