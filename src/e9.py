import sys, json, time, random
import und
from und import *
from und2 import learn_best
from kg_final import load, sample
def main(seed):
    und.SYMS = set(); k = 5; maxn = 6; tr, R = load('kinships'); comps = sample(tr, 300, k, random.Random(seed)); cut = int(.7 * len(comps)); train_all, test = comps[:cut], comps[cut:]
    out = {'seed': seed, 'res': {}}
    for n in (20, 60, 210):
        t0 = time.time(); D, w = learn_best(train_all[:n], R, 20, maxn, False, maxs=4, return_which=True)
        out['res'][n] = {'k': len(D), 'which': w, 'test': total_u(test, D, R, maxn, False) / len(test), 'time': time.time() - t0}
        print(seed, n, out['res'][n], flush=True)
    json.dump(out, open(f'e9_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]))
