import sys, json, time, random, math, collections
import und
from und import *
from core import Comp, dict_bits
import exp1
from exp1 import R, P, NN, maxn, NTEST, quotient, est_sigma

NS = [5, 10, 20, 40, 80]

def make_world(rng, sym):
    nrel = P if sym else R
    perm = list(range(R)); rng.shuffle(perm); motifs = []
    while len(motifs) < 5:
        k = rng.choice([4, 5]); edges = list({(i, rng.randrange(i)) if rng.random() < .5 else (rng.randrange(i), i) for i in range(1, k)})
        if rng.random() < .7:
            a, b = rng.sample(range(k), 2)
            if (a, b) not in edges and (b, a) not in edges: edges.append((a, b))
        motifs.append([(a, rng.randrange(nrel), b) for a, b in edges])
    return perm, motifs, nrel

def gen_comp(rng, perm, motifs, nrel, sym):
    E = {}
    for _ in range(2):
        m = rng.choice(motifs); nodes = rng.sample(range(NN), max(max(a, b) for a, _, b in m) + 1)
        for a, c, b in m:
            u, v = nodes[a], nodes[b]
            if (u, v) not in E and (v, u) not in E: E[(u, v)] = c
    for _ in range(2):
        u, v = rng.sample(range(NN), 2)
        if (u, v) not in E and (v, u) not in E: E[(u, v)] = rng.randrange(nrel)
    edges = []
    for (u, v), c in E.items():
        if not sym: edges.append((u, perm[c], v))
        else: edges.append((u, perm[c], v) if rng.random() < .5 else (v, perm[c + P], u))
    return Comp(NN, edges)

def costq(comps, D, sig, with_dict):
    Reff = R - len(sig) // 2
    e = sum(1 for c in comps for x in c.E if x[2] in sig) / len(comps)
    return total_u(comps, D, Reff, maxn, False) / len(comps) + e + (dict_bits(D, Reff, maxn) / len(comps) if with_dict else 0)

def fit(train, sig, K=20, topc=30):
    return learn_u(quotient(train, sig), R - len(sig) // 2, K, maxn, False, mode='hier', topc=topc, maxe=10)

def total_train(train, sig, K=10, topc=10):
    q = quotient(train, sig); D = learn_u(q, R - len(sig) // 2, K, maxn, False, mode='hier', topc=topc, maxe=10)
    Reff = R - len(sig) // 2
    return total_u(q, D, Reff, maxn, True) + sum(1 for c in train for x in c.E if x[2] in sig) + 2 * math.log2(R) * (len(sig) // 2)

def profile_ranking(train, sig):
    # Kandidatenpaare nach Profil-Kosinus, nur unter noch ungepaarten Relationen
    import exp1 as E
    F = collections.defaultdict(collections.Counter)
    for c in train:
        for _, a, r, b in c.E:
            for _, a2, t, b2 in c.E:
                if (a2, t, b2) == (a, r, b): continue
                for e, x in ((0, a), (1, b)):
                    if x == a2 or x == b2: F[r][(e, t)] += 1
    keys = sorted({k for f in F.values() for k in f})
    def vec(r, flip): return [F[r][((1 - e) if flip else e, t)] for e, t in keys]
    def cos(u, v):
        nu = math.sqrt(sum(x * x for x in u)); nv = math.sqrt(sum(x * x for x in v))
        return sum(x * y for x, y in zip(u, v)) / (nu * nv) if nu and nv else 0
    rels = [r for r in range(R) if F[r] and r not in sig]
    return sorted(((cos(vec(r, False), vec(s, True)), r, s) for r in rels for s in rels if r < s), reverse=True)

def est_mdl(train, ncand=12, maxpairs=P):
    sig = {}; best = total_train(train, sig)
    for _ in range(maxpairs):
        cands = profile_ranking(train, sig)[:ncand]; pick = None
        for v, r, s in cands:
            t = dict(sig); t[r] = s; t[s] = r; L = total_train(train, t)
            if L < best: best, pick = L, (r, s)
        if pick is None: break
        sig[pick[0]] = pick[1]; sig[pick[1]] = pick[0]
    return sig

def main(world, seed):
    sym = world == 'sym'; rng = random.Random(1000 + seed); perm, motifs, nrel = make_world(rng, sym)
    true_sig = {}
    if sym:
        for c in range(P): true_sig[perm[c]] = perm[c + P]; true_sig[perm[c + P]] = perm[c]
    allc = [gen_comp(rng, perm, motifs, nrel, sym) for _ in range(max(NS) + NTEST)]
    test = allc[max(NS):]; out = {'world': world, 'seed': seed, 'res': {}}
    for n in NS:
        train = allc[:n]; res = {}
        def run(nm, sig, tm=0.0):
            D = fit(train, sig); res[nm] = {'k': len(D), 'test': costq(quotient(test, sig), D, sig, False), 'pairs': len(sig) // 2,
                                          'right': sum(1 for r, s in sig.items() if true_sig.get(r) == s) // 2, 'time': tm}
        run('plain', {})
        sp = est_sigma(train); run('est_profile', sp)
        t0 = time.time(); sm = est_mdl(train); run('est_mdl', sm, time.time() - t0)
        if sym: run('oracle', true_sig)
        out['res'][n] = res
        print(world, seed, n, {k: (round(v['test'], 1), v['pairs'], v['right']) for k, v in res.items()}, round(res['est_mdl']['time']), 's', flush=True)
    json.dump(out, open(f'e2_{world}_{seed}.json', 'w'))

if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]))
