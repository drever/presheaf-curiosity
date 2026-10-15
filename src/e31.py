import sys, os, json, random, time
seed = int(sys.argv[1]); NTR = int(sys.argv[2]); world = sys.argv[3] if len(sys.argv) > 3 else 'd2'   # d2 | d1 (Kontrolle: Unterloch immer leer)
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import Comp, LOG
import holes2 as H2, holes3 as H3m
NNr = 31; Rr = 64; MAXEr = 12; und.SYMS = set(); rng = random.Random(31000 + seed)
NMID = int(os.environ.get('NMID', 4)); NLEAF = int(os.environ.get('NLEAF', 8)); MAXF = 8; maxn = NNr + 1; R = Rr
def make_frame():
    k = 6; es = set()
    for v in range(1, k):
        u = rng.randrange(v); es.add((u, v) if rng.random() < .5 else (v, u))
    while len(es) < k + 1:
        a, b = rng.sample(range(k), 2)
        if (a, b) not in es and (b, a) not in es: es.add((a, b))
    edges = [(a, rng.randrange(Rr), b) for a, b in sorted(es)]; pairs = []
    while len(pairs) < 2:
        a, b = rng.sample(range(k), 2)
        if all((a, b) != p and (b, a) != p for p in pairs) and (a, b) not in es and (b, a) not in es: pairs.append((a, b))
    return k, edges, pairs
def make_leaf():
    m = rng.choice([1, 2]); inner = list(range(2, 2 + m)); es = [(0, inner[0], rng.randrange(Rr))]
    for x, y in zip(inner, inner[1:]): es.append((x, y, rng.randrange(Rr)))
    es.append((inner[-1], 1, rng.randrange(Rr)))
    if m == 2: es.append((0, inner[1], rng.randrange(Rr)))
    return m, es
def make_mid(): return [(0, 2, rng.randrange(Rr)), (3, 1, rng.randrange(Rr)), (2, 1, rng.randrange(Rr))]   # Knoten 0,1 Ports; 2,3 Unterloch-Paar
frames = [make_frame() for _ in range(3)]; mids = [make_mid() for _ in range(NMID)]; leaves = [make_leaf() for _ in range(NLEAF)]
def gen():
    E = {}; used = set()
    def add(u, v, r):
        if u != v and (u, v) not in E and (v, u) not in E: E[(u, v)] = r
    for _ in range(2):
        k, fe, pairs = rng.choice(frames); nodes = rng.sample([x for x in range(NNr) if x not in used], k); used |= set(nodes)
        for a, r, b in fe: add(nodes[a], nodes[b], r)
        for (a, b) in pairs:
            if rng.random() < 0.15: continue
            me = rng.choice(mids); free = [x for x in range(NNr) if x not in used]; i2, i3 = rng.sample(free, 2); used |= {i2, i3}
            mp = {0: nodes[a], 1: nodes[b], 2: i2, 3: i3}
            for s, t, r in me: add(mp[s], mp[t], r)
            if world == 'd2' and rng.random() >= 0.2:
                m, ge = rng.choice(leaves); free = [x for x in range(NNr) if x not in used]; inner = rng.sample(free, m); used |= set(inner)
                lp = {0: i2, 1: i3}
                for t, x in enumerate(inner): lp[2 + t] = x
                for s, t, r in ge: add(lp[s], lp[t], r)
    for _ in range(4):
        u, v = rng.sample(range(NNr), 2)
        if (u, v) not in E and (v, u) not in E: E[(u, v)] = rng.randrange(Rr)
    return Comp(NNr, [(u, r, v) for (u, v), r in E.items()])
train = [gen() for _ in range(NTR)]; tests = [gen() for _ in range(100)]; tag = f'{world}_{seed}_n{NTR}'
KD = int(os.environ.get('KD', 40))
LDm = lambda comps, Rx=R: learn_h(comps, Rx, KD, maxn, False, mode='hier', topc=30, maxe=MAXEr, objective='hier')
t0 = time.time(); res = {}
D = LDm(train); dglue = dict_bits_h(D, R, maxn)
tg = H2.total(tests, D, [], {}, R, 'iface', MAXF)
cst, D2, H, lib, alive, hb, rd = H2.refine(train, D, R, 'iface', LDm, MAXF, rounds=int(os.environ.get('ROUNDS', 2)), maxn=maxn)
dflat = dict_bits_h([D2[j] for j in sorted(alive)], R, maxn) + hb
tf = H2.total(tests, D2, H, lib, R, 'iface', MAXF, alive)
res.update(k_dict=len(D), glue=tg, dict_glue=dglue, flat=tf, dict_flat=dflat, n_holes=len(H), flat_round=rd)
r3 = H3m.build_depth2(train, D2, H, lib, alive, R, 'iface', LDm, MAXF, maxn) if H else None
if r3:
    Hh, lib3, b3, info = r3
    td = H2.total(tests, D2, Hh, lib3, R, 'iface', MAXF, alive)
    dd2 = dict_bits_h([D2[j] for j in sorted(alive)], R, maxn) + b3
    trf = H2.total(train, D2, H, lib, R, 'iface', MAXF, alive) * NTR + dflat; trd = H2.total(train, D2, Hh, lib3, R, 'iface', MAXF, alive) * NTR + dd2
    res.update(d2=td, dict_d2=dd2, train_flat=trf, train_d2=trd, info=info)
    res['d2_chosen'] = trd < trf
else: res.update(d2=None)
res['time'] = round(time.time() - t0)
print(tag, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in res.items()}, flush=True)
json.dump(res, open(f'../results/e31_{tag}.json', 'w'), default=str)
