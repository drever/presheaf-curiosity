import sys, json, time, random, collections
import pandas as pd
import und
from und import *
from core import Comp
from mol_big import gspan_mol
from mol_sel import greedy_select
from mol_subdue import run_subdue

def load(name):
    t = pd.read_csv(f'kgdata/{name}/train.txt', sep='\t', header=None)
    rels = {r: i for i, r in enumerate(sorted(t[1].unique()))}
    ents = {e: i for i, e in enumerate(sorted(set(t[0]) | set(t[2])))}
    return {(ents[a], rels[r], ents[b]) for a, r, b in t.values}, len(rels)

def sample(tr, N, k, rng):
    nb = collections.defaultdict(set)
    for a, r, b in tr: nb[a].add(b); nb[b].add(a)
    ents = list(nb); seen = set(); comps = []; tries = 0
    while len(comps) < N and tries < 50 * N:
        tries += 1
        S = [rng.choice(ents)]
        while len(S) < k:
            cand = [x for u in S for x in nb[u] if x not in S]
            if not cand: break
            S.append(rng.choice(cand))
        if len(S) < k: continue
        key = frozenset(S)
        if key in seen: continue
        seen.add(key); ix = {v: i for i, v in enumerate(S)}
        comps.append(Comp(k, [(ix[a], r, ix[b]) for a, r, b in tr if a in ix and b in ix]))
    return comps

def main(name, seed, maxv, k=5, N=300):
    und.SYMS = set()
    tr, R = load(name); rng = random.Random(seed); comps = sample(tr, N, k, rng)
    cut = int(.7 * len(comps)); train, test = comps[:cut], comps[cut:]; ntr = len(train); maxn = k + 1
    out = {'name': name, 'seed': seed, 'ntr': ntr, 'nte': len(test), 'edges': sum(len(c.E) for c in comps) / len(comps), 'm': {}}
    def ev(nm, D, tm):
        out['m'][nm] = {'k': len(D), 'max_edges': max([len(p) for p in D] or [0]), 'dict': total_u([], D, R, maxn), 'train': total_u(train, D, R, maxn, False) / ntr,
                        'test': total_u(test, D, R, maxn, False) / len(test), 'time': tm}
        print(' ', nm, len(D), round(out['m'][nm]['test'], 1), round(tm, 1), 's', flush=True)
    for topc in (6, 30, 100):
        for mode in ('hier', 'grow'):
            if mode == 'grow' and topc != 30: continue
            t0 = time.time(); D = learn_u(train, R, 20, maxn, True, mode=mode, topc=topc, maxe=10); ev(f'{mode}{topc}', D, time.time() - t0)
    t0 = time.time(); D = learn_u(train, R, 40, maxn, True, mode='hier', topc=30, maxe=10); ev('hier30_K40', D, time.time() - t0)
    t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.10 * ntr)), maxv, f'{__import__("tempfile").gettempdir()}/kg_{name}_{seed}.gsp'); tg = time.time() - t0
    out['ncand'] = len(C); out['nfound'] = nf
    t0 = time.time(); D = greedy_select(train, C, R, maxn, 20, 30); ev('gspan_mdl30', D, tg + time.time() - t0)
    t0 = time.time(); pats, info = run_subdue(train, 40, 500, 10, 4); tm = time.time() - t0
    Dall = []; seen = set()
    for p in pats:
        kk = canon_u(p, True)
        if kk not in seen: seen.add(kk); Dall.append(p)
    for n in (20, 40):
        Dn = Dall[:n]; trn = [total_u(train, Dn[:m], R, maxn) for m in range(len(Dn) + 1)]
        ns = min(range(len(trn)), key=lambda m: trn[m])
        ev(f'subdue{n}_all', Dn, tm); ev(f'subdue{n}_mdl', Dn[:ns], tm)
    json.dump(out, open(f'kf_{name}_{seed}.json', 'w')); print('fertig', name, seed, flush=True)

if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
