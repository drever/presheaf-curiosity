import sys, json, time, random, signal
import und
from und import *
from netlist import *
from mol_big import gspan_mol
from mol_sel import greedy_select
import mol_subdue
NN = 31; maxn = NN + 1; NMAX = 20; R = 64

def main(seed, n=40, tmax=500, maxv=17):
    und.SYMS = set(); rng = random.Random(100 + seed)       # gleiche Reihenfolge wie e21 -> gleiche Fenster
    L = Labeler()
    def win(nm, k): return [to_comp(x, rng, NN) for x in windows_from(load_bench(nm), rng, k, nmax=NMAX, labeler=L)]
    train = win('c6288', n); tests = {'in:c6288': win('c6288', 100)}
    for c in ('c1355', 'c499', 'c880', 'c1908'): tests[c] = win(c, 100)
    res = {}
    def ev(nm, D, extra=None):
        r = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'train': total_u(train, D, R, maxn, False) / len(train)}
        for t, c in tests.items(): r[t] = total_u(c, D, R, maxn, False) / len(c)
        if extra: r.update(extra)
        res[nm] = r; print(seed, nm, {a: round(b, 1) for a, b in r.items()}, flush=True)
    def handler(sig, frm): raise TimeoutError()
    signal.signal(signal.SIGALRM, handler)
    for minfrac in (0.2,):
        nm = f'gspan_minsup{minfrac}_maxv{maxv}'
        try:
            signal.alarm(tmax); t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(minfrac * n)), maxv, f'/tmp/e22_{seed}_{minfrac}.gsp')
            D = greedy_select(train, C, R, maxn, 40, 30); signal.alarm(0); ev(nm, D, {'ncand': len(C), 'time': time.time() - t0})
        except TimeoutError: res[nm] = {'timeout': True}; print(seed, nm, 'timeout', flush=True)
    try:
        signal.alarm(tmax); t0 = time.time(); pats, info = mol_subdue.run_subdue(train, 20, 100, 12, 4); signal.alarm(0)
        D = []; seen = set()
        for p in pats:
            kk = canon_u(p, False)
            if kk not in seen: seen.add(kk); D.append(p)
        trn = [total_u(train, D[:m], R, maxn, False) for m in range(0, len(D) + 1)]; nstar = min(range(len(trn)), key=lambda m: trn[m])
        ev('subdue_mdl', D[:nstar], {'time': time.time() - t0, 'nraw': len(pats), 'nstar': nstar}); ev('subdue_full', D)
    except TimeoutError: res['subdue'] = {'timeout': True}; print(seed, 'subdue timeout', flush=True)
    json.dump({'seed': seed, 'm': res}, open(f'e22_maxv{maxv}_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), tmax=int(sys.argv[3]) if len(sys.argv) > 3 else 500, maxv=int(sys.argv[2]) if len(sys.argv) > 2 else 17)
