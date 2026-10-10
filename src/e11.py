import sys, json, time, random
import und
from und import *
from und2 import learn_best
from kg_final import load, sample
from e4 import qd, reff
def main(seed):
    und.SYMS = set(); k = 5; maxn = 6; tr, R = load('kinships'); comps = sample(tr, 300, k, random.Random(seed)); cut = int(.7 * len(comps)); train_all, test = comps[:cut], comps[cut:]
    old = json.load(open(f'e4_{seed}.json')); out = {'seed': seed, 'res': {}}
    for n in (20, 60, 210):
        pairs = old['res'][str(n)]['closure100']['pairs']; sig = {}
        for r, s in pairs: sig[r] = s; sig[s] = r
        q, ex = qd(train_all[:n], sig); Re = reff(R, sig); t0 = time.time()
        D = learn_best(q, Re, 20, maxn, False, maxs=4); qt, ext = qd(test, sig)
        out['res'][n] = {'k': len(D), 'pairs': len(pairs), 'test': (total_u(qt, D, Re, maxn, False) + ext) / len(test), 'time': time.time() - t0}
        print(seed, n, out['res'][n], flush=True)
    json.dump(out, open(f'e11_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]))
