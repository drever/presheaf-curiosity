import sys, json, time, random
import und
from und import *
from core import Comp
from und2 import learn_x

R = 12; NN = 24; maxn = NN + 1

def make_lib(rng, depth, L=6):
    lib = [[(0, rng.randrange(R), 1), (1, rng.randrange(R), 2)] for _ in range(L)]   # Basis: 2-Kanten-Pfade
    lib = [[(a, r, b) for a, r, b in m] for m in lib]
    for _ in range(depth):
        new = []
        for _ in range(L):
            m1, m2 = rng.sample(lib, 2)
            n1 = 1 + max(max(a, b) for a, _, b in m1); n2 = 1 + max(max(a, b) for a, _, b in m2)
            s1 = rng.randrange(n1); s2 = rng.randrange(n2)          # ein gemeinsamer Knoten
            mp = {}; nxt = n1
            for v in range(n2):
                if v == s2: mp[v] = s1
                else: mp[v] = nxt; nxt += 1
            new.append(list(m1) + [(mp[a], r, mp[b]) for a, r, b in m2])
        lib = new
    return lib

def gen_comp(rng, lib, nmot=3, nnoise=4):
    E = {}
    for _ in range(nmot):
        m = rng.choice(lib); k = 1 + max(max(a, b) for a, _, b in m)
        nodes = rng.sample(range(NN), k)
        for a, r, b in m:
            u, v = nodes[a], nodes[b]
            if (u, v) not in E and (v, u) not in E and u != v: E[(u, v)] = r
    for _ in range(nnoise):
        u, v = rng.sample(range(NN), 2)
        if (u, v) not in E and (v, u) not in E: E[(u, v)] = rng.randrange(R)
    return Comp(NN, [(u, r, v) for (u, v), r in E.items()])

def main(depth, n, seed, K=40):
    und.SYMS = set(); rng = random.Random(5000 + 100 * depth + seed); lib = make_lib(rng, depth)
    msize = sorted(len(m) for m in lib)
    allc = [gen_comp(rng, lib) for _ in range(n + 100)]; train, test = allc[:n], allc[n:]
    out = {'depth': depth, 'n': n, 'seed': seed, 'motif_sizes': msize, 'm': {}}
    def ev(nm, D, tm): out['m'][nm] = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'test': total_u(test, D, R, maxn, False) / len(test), 'dict': total_u([], D, R, maxn), 'time': tm}; print(depth, n, seed, nm, len(D), round(out['m'][nm]['test'], 1), round(tm), 's', flush=True)
    ev('none', [], 0)
    for nm, mode, tc in (('hier30', 'hier', 30), ('grow30', 'grow', 30)):
        t0 = time.time(); ev(nm, learn_u(train, R, K, maxn, False, mode=mode, topc=tc, maxe=18), time.time() - t0)
    for nm, tc in (('hier100', 100),):
        t0 = time.time(); ev(nm, learn_u(train, R, K, maxn, False, mode='hier', topc=tc, maxe=18), time.time() - t0)
    t0 = time.time(); ev('grow100', learn_u(train, R, K, maxn, False, mode='grow', topc=100, maxe=18), time.time() - t0)
    import signal
    from mol_big import gspan_mol
    from mol_sel import greedy_select
    from mol_subdue import run_subdue
    def handler(sig, frm): raise TimeoutError()
    signal.signal(signal.SIGALRM, handler)
    try:
        signal.alarm(240); t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.2 * n)), 12, f'/tmp/e12_{depth}_{n}_{seed}.gsp'); signal.alarm(0)
        ev('gspan_mdl30', greedy_select(train, C, R, maxn, K, 30), time.time() - t0)
    except TimeoutError: out['m']['gspan_mdl30'] = {'timeout': True}; print('gspan timeout', flush=True)
    t0 = time.time(); pats, _ = run_subdue(train, 30, 500, 18, 4); tm = time.time() - t0; Dd = []; seen = set()
    for p in pats:
        kk = canon_u(p, True)
        if kk not in seen: seen.add(kk); Dd.append(p)
    trn = [total_u(train, Dd[:m], R, maxn) for m in range(len(Dd) + 1)]; ns = min(range(len(trn)), key=lambda m: trn[m]); ev('subdue_mdl', Dd[:ns], tm)
    json.dump(out, open(f'e12_{depth}_{n}_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
