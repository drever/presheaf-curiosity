import sys, json, time, random
import und
from und import *
from core import Comp, dict_bits
from und3 import learn_h, dict_bits_h
from und4 import *

R = 12; NN = 30; maxn = NN + 1; MAXE = 24

def chain(rng, lo, length):
    return [(i, rng.choice(lo), i + 1) for i in range(length)]

def make_world(rng):
    H = []; V = []
    while len(H) < 5:
        c = chain(rng, list(range(0, 6)), rng.choice([2, 3]))
        if c not in H: H.append(c)
    while len(V) < 5:
        c = chain(rng, list(range(6, 12)), rng.choice([2, 3]))
        if c not in V: V.append(c)
    pairs = [(i, j) for i in range(5) for j in range(5)]; rng.shuffle(pairs)
    return H, V, pairs[:15], pairs[15:]      # gesehene / ungesehene Paare (60% / 40%)

def gen_comp(rng, H, V, pairs, ngrid=2, nnoise=4):
    E = {}
    for _ in range(ngrid):
        i, j = rng.choice(pairs); g = prod_pattern(H[i], V[j]); k = 1 + max(max(a, b) for a, _, b in g)
        nodes = rng.sample(range(NN), k)
        for a, r, b in g:
            u, v = nodes[a], nodes[b]
            if (u, v) not in E and (v, u) not in E and u != v: E[(u, v)] = r
    for _ in range(nnoise):
        u, v = rng.sample(range(NN), 2)
        if (u, v) not in E and (v, u) not in E: E[(u, v)] = rng.randrange(R)
    return Comp(NN, [(u, r, v) for (u, v), r in E.items()])

def main(n, seed, K=40):
    und.SYMS = set(); rng = random.Random(7000 + seed); H, V, seen, unseen = make_world(rng)
    train = [gen_comp(rng, H, V, seen) for _ in range(n)]
    te_seen = [gen_comp(rng, H, V, seen) for _ in range(100)]; te_unseen = [gen_comp(rng, H, V, unseen) for _ in range(100)]
    out = {'n': n, 'seed': seed, 'm': {}}
    def ev(nm, Dtrain_cover, dict_cost, tm, extra=None):
        out['m'][nm] = {'k': len(Dtrain_cover), 'train': total_u(train, Dtrain_cover, R, maxn, False) / n, 'dict': dict_cost, 'test_seen': total_u(te_seen, Dtrain_cover, R, maxn, False) / 100,
                        'test_unseen': total_u(te_unseen, Dtrain_cover, R, maxn, False) / 100, 'time': tm}
        if extra: out['m'][nm].update(extra)
        print(n, seed, nm, len(Dtrain_cover), {a: round(b, 1) for a, b in out['m'][nm].items() if a.startswith('test') or a == 'dict'}, round(tm), 's', flush=True)
    cross = lambda A, B: (min(r for _, r, _ in A) < 6) != (min(r for _, r, _ in B) < 6)
    t0 = time.time(); D0, F, Dp, Deff = learn_prod(train, R, K, maxn, MAXE); tm = time.time() - t0
    _, _, Dpc, Deffc = learn_prod(train, R, K, maxn, MAXE, cross=cross)
    ev('none', [], 0, 0)
    ev('glue_hier', D0, dict_bits_h(D0, R, maxn), tm)
    ev('glue_hier_prodcost', D0, dict_bits_hp(D0, R, maxn), tm)
    ev('prod_closure', Deff, dict_bits_h(Dp, R, maxn) + sum(LOG(len(Dp) + 1) + 1 for _ in F), tm, {'nfactors': len(F), 'nexplicit': len(Dp), 'nimplicit': len(Deff) - len(Dp)})
    ev('prod_closure_cross', Deffc, dict_bits_h(Dpc, R, maxn), tm, {'nexplicit': len(Dpc), 'nimplicit': len(Deffc) - len(Dpc)})
    pure = lambda p: len({r < 6 for _, r, _ in p}) == 1
    t0 = time.time(); _, Fd, Dpd, Deffd = learn_prod_data(train, R, K, maxn, MAXE, cross=cross, pure=pure, topk=20); tmd = time.time() - t0
    ev('prod_data_cross', Deffd, dict_bits_h(Dpd, R, maxn) + sum(LOG(len(Dpd) + 1) + 1 for _ in Fd), tmd, {'nfactors': len(Fd), 'nexplicit': len(Dpd)})
    Fo = [tuple(order_pattern(normalize(c))) for c in H + V]
    Dpo, Deffo = effective_dict(D0, Fo, MAXE, cross)
    ev('oracle_closure', Deffo, dict_bits_h(Dpo, R, maxn) + len(Fo) * (LOG(len(Dpo) + 1) + 1), 0, {'nexplicit': len(Dpo)})
    t0 = time.time(); Dg = learn_h(train, R, K, maxn, False, mode='grow', topc=30, maxe=MAXE, objective='hier'); ev('grow_hier', Dg, dict_bits_h(Dg, R, maxn), time.time() - t0)
    json.dump(out, open(f'e17_{n}_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
