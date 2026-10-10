import sys, json, time, random, math, collections
import und
from und import *
from core import Comp

P = 6; R = 2 * P; NN = 8; maxn = NN + 1; BASE_N = [5, 10, 20, 40, 80]; NTEST = 100

def make_world(rng):
    perm = list(range(R)); rng.shuffle(perm)      # versteckte Zuordnung: kanonische Relation c -> (perm[c], perm[c+P]) = (vor, rueck)
    motifs = []
    while len(motifs) < 5:
        k = rng.choice([4, 5]); edges = {(i, rng.randrange(i)) if rng.random() < .5 else (rng.randrange(i), i) for i in range(1, k)}
        edges = list(edges)
        if rng.random() < .7:
            a, b = rng.sample(range(k), 2)
            if (a, b) not in edges and (b, a) not in edges: edges.append((a, b))
        motifs.append([(a, rng.randrange(P), b) for a, b in edges])
    return perm, motifs

def gen_comp(rng, perm, motifs):
    E = {}  # (a,b) -> c  (kanonisch, gerichtet)
    for _ in range(2):
        m = rng.choice(motifs); nodes = rng.sample(range(NN), max(max(a, b) for a, _, b in m) + 1)
        for a, c, b in m:
            u, v = nodes[a], nodes[b]
            if (u, v) not in E and (v, u) not in E: E[(u, v)] = c
    for _ in range(2):
        u, v = rng.sample(range(NN), 2)
        if (u, v) not in E and (v, u) not in E: E[(u, v)] = rng.randrange(P)
    edges = []
    for (u, v), c in E.items():
        edges.append((u, perm[c], v) if rng.random() < .5 else (v, perm[c + P], u))
    return Comp(NN, edges)

def quotient(comps, sigma):
    out = []
    for c in comps:
        es = []
        for _, a, r, b in c.E:
            s = sigma.get(r, r)
            es.append((a, r, b) if r <= s else (b, s, a))
        out.append(Comp(c.n, es))
    return out

def est_sigma(train):
    F = collections.defaultdict(collections.Counter)
    for c in train:
        for _, a, r, b in c.E:
            for _, a2, t, b2 in c.E:
                if (a2, t, b2) == (a, r, b): continue
                for e, x in ((0, a), (1, b)):
                    if x == a2 or x == b2: F[r][(e, t)] += 1
    keys = sorted({k for f in F.values() for k in f}); 
    def vec(r, flip):
        return [F[r][((1 - e) if flip else e, t)] for e, t in keys]
    def cos(u, v):
        nu = math.sqrt(sum(x * x for x in u)); nv = math.sqrt(sum(x * x for x in v))
        return sum(x * y for x, y in zip(u, v)) / (nu * nv) if nu and nv else 0
    rels = [r for r in range(R) if F[r]]
    sc = sorted(((cos(vec(r, False), vec(s, True)), r, s) for r in rels for s in rels if r < s), reverse=True)
    used = set(); sig = {}
    for v, r, s in sc:
        if r in used or s in used: continue
        used |= {r, s}; sig[r] = s; sig[s] = r
    return sig

def cost(comps, D, Reff, extra_bits):
    return total_u(comps, D, Reff, maxn, False) / len(comps) + extra_bits

def main(seed):
    rng = random.Random(seed); perm, motifs = make_world(rng)
    true_sig = {}
    for c in range(P): true_sig[perm[c]] = perm[c + P]; true_sig[perm[c + P]] = perm[c]
    allc = [gen_comp(rng, perm, motifs) for _ in range(max(BASE_N) + NTEST)]
    test = allc[max(BASE_N):]; out = {'seed': seed, 'res': {}}
    eavg = sum(len(c.E) for c in test) / len(test)
    for n in BASE_N:
        train = allc[:n]; res = {}
        def run(nm, tr, te, Reff, extra, topc):
            t0 = time.time(); D = learn_u(tr, Reff, 20, maxn, False, mode='hier', topc=topc, maxe=10)
            res[nm] = {'k': len(D), 'test': cost(te, D, Reff, extra), 'train': cost(tr, D, Reff, extra), 'dict': dict_bits(D, Reff, maxn), 'time': time.time() - t0}
        res['none'] = {'test': cost(test, [], R, 0)}
        run('plain30', train, test, R, 0, 30); run('plain100', train, test, R, 0, 100)
        qtr, qte = quotient(train, true_sig), quotient(test, true_sig)
        run('oracle100', qtr, qte, R // 2, eavg, 100)
        es = est_sigma(train); correct = sum(1 for r, s in es.items() if true_sig.get(r) == s) / max(1, len(es))
        run('est100', quotient(train, es), quotient(test, es), R // 2, eavg, 100); res['est100']['pair_acc'] = correct
        out['res'][n] = res
        print(seed, n, {k: round(v['test'], 1) for k, v in res.items()}, 'acc', round(correct, 2), flush=True)
    json.dump(out, open(f'e1_{seed}.json', 'w'))

if __name__ == '__main__': main(int(sys.argv[1]))
