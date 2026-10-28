import sys, json, time, random, signal
import und
from und import *
import e12
from e12 import R, maxn, make_lib, gen_comp
from mol_big import gspan_mol
from mol_sel import greedy_select
def main(depth, n, seed, maxv, tmax):
    und.SYMS = set(); rng = random.Random(5000 + 100 * depth + seed); lib = make_lib(rng, depth)
    allc = [gen_comp(rng, lib) for _ in range(n + 100)]; train, test = allc[:n], allc[n:]
    def handler(sig, frm): raise TimeoutError()
    signal.signal(signal.SIGALRM, handler); res = {}
    try:
        signal.alarm(tmax); t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.2 * n)), maxv, f'{__import__("tempfile").gettempdir()}/e13_{depth}_{n}_{seed}.gsp'); signal.alarm(0)
        D = greedy_select(train, C, R, maxn, 40, 30); res = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'test': total_u(test, D, R, maxn, False) / len(test), 'time': time.time() - t0, 'ncand': len(C)}
    except TimeoutError: res = {'timeout': True}
    print(depth, n, seed, maxv, res, flush=True); json.dump(res, open(f'e13_{depth}_{n}_{seed}_{maxv}.json', 'w'))
if __name__ == '__main__': main(*[int(x) for x in sys.argv[1:]])
