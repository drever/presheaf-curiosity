"""Test B: Anti-Unifikation auf Makros mit variablen Labels (Loechern) und Rauschen.
Welt: M Makros (zufaellige zusammenhaengende Graphen), jede Kante entweder fest (ein Label) oder Loch (Label aus kleinem Alphabet).
Rauschen: pf = Label-Austausch pro Kante, pd = Kante fehlt, Clutter-Kanten.
Methoden: exakt (glue auf echten Labels), AU (Formen aus label-geloeschten Graphen lernen, dann je Musterkante
Labelverteilung = lgg/Anti-Unifikation der Vorkommen, Kosten -log2 p), shape_raw (Formen + log R je Label), RePair-Baseline."""
import sys, json, random, time, math, collections
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import Comp, LOG, order_pattern
from iface import total_iface, inst_bits
import repair as rp
NN = 31; maxn = NN + 1; R = 64; MAXE = 12

def make_world(rng, M=4, k=6, frac_hole=0.5, A=4):
    W = []
    while len(W) < M:
        nodes = list(range(k)); es = set()
        for v in range(1, k):
            u = rng.randrange(v); es.add((u, v) if rng.random() < .5 else (v, u))
        while len(es) < k + 1:
            a, b = rng.sample(nodes, 2)
            if (a, b) not in es and (b, a) not in es: es.add((a, b))
        spec = []
        for a, b in sorted(es):
            if rng.random() < frac_hole: spec.append((a, b, ('hole', rng.sample(range(R), A))))
            else: spec.append((a, b, ('fix', rng.randrange(R))))
        W.append((k, spec))
    return W

def gen(rng, W, pf, pd, ninst=2, nclutter=4):
    E = {}
    for _ in range(ninst):
        k, spec = rng.choice(W); nodes = rng.sample(range(NN), k)
        for a, b, (kind, x) in spec:
            if rng.random() < pd: continue
            lab = x if kind == 'fix' else rng.choice(x)
            if rng.random() < pf: lab = rng.randrange(R)
            u, v = nodes[a], nodes[b]
            if u != v and (u, v) not in E and (v, u) not in E: E[(u, v)] = lab
    for _ in range(nclutter):
        u, v = rng.sample(range(NN), 2)
        if (u, v) not in E and (v, u) not in E: E[(u, v)] = rng.randrange(R)
    return Comp(NN, [(u, r, v) for (u, v), r in E.items()])

def erase(c): return Comp(c.n, [(a, 0, b) for _, a, r, b in c.E])

def fit_labels(train, D):
    counts = collections.defaultdict(lambda: collections.defaultdict(collections.Counter)); N = collections.Counter()
    for c in train:
        inst, raw = cover_u(erase(c), D)
        for pi, ids, mm in inst:
            N[pi] += 1
            for j, eid in enumerate(ids): counts[pi][j][c.E[eid][2]] += 1
    return counts, N

def label_bits(cnt, Nn, lab, uniform):
    if uniform: return LOG(R)
    u = len(cnt)
    if Nn == 0 or u == 0: return LOG(R)
    if lab in cnt: return -LOG(cnt[lab] / (Nn + u))
    return -LOG((u / (Nn + u)) / max(1, R - u))

def cost_shape(comps, D, counts, N, uniform=False):
    s = 0
    for c in comps:
        ec = erase(c); inst, raw = cover_u(ec, D); n = LOG(c.n)
        s += len(raw) * (2 * n + LOG(R))
        for pi, ids, mm in inst:
            o, w, k, V = inst_bits(ec, D, pi, ids, mm, n); s += min(o, w) + 1
            for j, eid in enumerate(ids): s += label_bits(counts[pi][j], N[pi], c.E[eid][2], uniform)
    return s / len(comps)

def label_dict_bits(D, counts, N, uniform):
    if uniform: return 0
    return sum(len(cnt) * (LOG(R) + LOG(N[pi] + 1)) for pi in range(len(D)) for cnt in counts[pi].values())

def run(seed, n, pf, pd, fh, A=4, M=4):
    und.SYMS = set(); rng = random.Random(9000 + seed); W = make_world(rng, M=M, frac_hole=fh, A=A)
    train = [gen(rng, W, pf, pd) for _ in range(n)]; test = [gen(rng, W, pf, pd) for _ in range(100)]
    res = {}
    def put(nm, held, d, k, tm):
        res[nm] = {'held': held, 'dict': d, 'k': k, 'amort': held + d / 100, 'time': round(tm)}
    put('none', sum(len(c.E) * (2 * LOG(c.n) + LOG(R)) for c in test) / 100, 0, 0, 0)
    t0 = time.time(); D = learn_h(train, R, 40, maxn, False, mode='hier', topc=30, maxe=MAXE, objective='hier')
    put('exact', total_iface(test, D, R, maxn, False) / 100, dict_bits_h(D, R, maxn), len(D), time.time() - t0)
    t0 = time.time(); Ds = learn_h([erase(c) for c in train], 1, 40, maxn, False, mode='hier', topc=30, maxe=MAXE, objective='hier')
    counts, N = fit_labels(train, Ds); ds = dict_bits_h(Ds, 1, maxn); tm = time.time() - t0
    put('shape_raw', cost_shape(test, Ds, counts, N, True), ds, len(Ds), tm)
    put('AU', cost_shape(test, Ds, counts, N, False), ds + label_dict_bits(Ds, counts, N, False), len(Ds), tm)
    Dt = [tuple(order_pattern([(a, 0, b) for a, b, _ in spec])) for k, spec in W]
    ct, Nt = fit_labels(train, Dt)
    put('AU_oracle', cost_shape(test, Dt, ct, Nt, False), dict_bits_h(Dt, 1, maxn) + label_dict_bits(Dt, ct, Nt, False), len(Dt), 0)
    t0 = time.time(); rules = rp.learn(train, R, set(), K=300)
    put('repair', rp.cost(test, rules, R, set()), rp.dict_cost(rules, R), len(rules), time.time() - t0)
    return res

if __name__ == '__main__':
    seed, n, pf, pd, fh = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    r = run(seed, n, pf, pd, fh)
    for k, v in r.items(): print(seed, pf, pd, fh, k, {a: round(b, 1) for a, b in v.items()}, flush=True)
    json.dump(r, open(f'../results/e27_{seed}_{n}_{pf}_{pd}_{fh}.json', 'w'))
