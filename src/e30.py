import sys, os, json, random, time
which = sys.argv[1]; seed = int(sys.argv[2])
if which == 'streets': os.environ['SYM'] = '1'
import und, und4
from und import *
from und3 import learn_h, dict_bits_h
from core import Comp, LOG
from iface import total_iface
from holes import *
import holes2 as H2
MAXF = 5
if which == 'syn':
    fh_empty = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
    NNr = 31; Rr = 64; MAXEr = 12; sym = False; und.SYMS = set(); rng = random.Random(12000 + seed)
    def make_frame():
        k = 6; es = set()
        for v in range(1, k):
            u = rng.randrange(v); es.add((u, v) if rng.random() < .5 else (v, u))
        while len(es) < k + 1:
            a, b = rng.sample(range(k), 2)
            if (a, b) not in es and (b, a) not in es: es.add((a, b))
        edges = [(a, rng.randrange(Rr), b) for a, b in sorted(es)]
        pairs = []
        while len(pairs) < 2:
            a, b = rng.sample(range(k), 2)
            if (a, b) not in [(x, y) for x, y in pairs] and (b, a) not in [(x, y) for x, y in pairs] and (a, b) not in es and (b, a) not in es: pairs.append((a, b))
        return k, edges, pairs
    def make_gadget():
        m = rng.choice([1, 2]); inner = list(range(2, 2 + m)); es = [(0, inner[0], rng.randrange(Rr))]
        for x, y in zip(inner, inner[1:]): es.append((x, y, rng.randrange(Rr)))
        es.append((inner[-1], 1, rng.randrange(Rr)))
        if m == 2: es.append((0, inner[1], rng.randrange(Rr)))
        else: es.append((inner[0], 1 if False else 0, rng.randrange(Rr))) if False else None
        return m, es
    frames = [make_frame() for _ in range(3)]; NGAD = int(os.environ.get('NGAD', 6)); gadgets = [make_gadget() for _ in range(NGAD)]
    def gen():
        E = {}; gused = set()
        for _ in range(2):
            k, fe, pairs = rng.choice(frames); nodes = rng.sample([x for x in range(NNr) if x not in gused], k); used = set(nodes) | gused; gused |= set(nodes)
            def add(u, v, r):
                if u != v and (u, v) not in E and (v, u) not in E: E[(u, v)] = r
            for a, r, b in fe: add(nodes[a], nodes[b], r)
            for (a, b) in pairs:
                if rng.random() < fh_empty: continue
                m, ge = rng.choice(gadgets); free = [x for x in range(NNr) if x not in used]; inner = rng.sample(free, m); used |= set(inner); gused |= set(inner)
                mp = {0: nodes[a], 1: nodes[b]}
                for t, x in enumerate(inner): mp[2 + t] = x
                for s, t, r in ge: add(mp[s], mp[t], r)
        for _ in range(4):
            u, v = rng.sample(range(NNr), 2)
            if (u, v) not in E and (v, u) not in E: E[(u, v)] = rng.randrange(Rr)
        return Comp(NNr, [(u, r, v) for (u, v), r in E.items()])
    NTR = int(os.environ.get('NTR', 40)); train = [gen() for _ in range(NTR)]; tests = {'in': [gen() for _ in range(100)]}; tag = f'syn_{seed}_{fh_empty}_g{NGAD}'
elif which == 'c6288':
    from netlist import *
    NNr = 31; Rr = 64; und.SYMS = set(); rng = random.Random(100 + seed); L = Labeler(); sym = False
    def win(nm, k): return [to_comp(x, rng, NNr) for x in windows_from(load_bench(nm), rng, k, nmax=20, labeler=L)]
    train = win('c6288', 40); tests = {'in': win('c6288', 100)}; MAXEr = 12; tag = f'c6288_{seed}'
else:
    from streets import *
    from e19 import load, R as Rr, NN as NNr, MAXE as MAXEr
    und.SYMS = set(range(NLAB)); und4.UND = True; rng = random.Random(500 + seed); sym = True
    allw = load('barcelona', rng, 180); train = allw[:50]; tests = {'in': allw[80:]}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
    tag = f'streets_{seed}'
maxn = NNr + 1; R = Rr; res = {}
t0 = time.time()
D = learn_h(train, R, int(os.environ.get('KD', 40)), maxn, sym, mode='hier', topc=30, maxe=MAXEr, objective='hier')
res['k_dict'] = len(D); res['dict_bits'] = dict_bits_h(D, R, maxn)
res['check_total_iface'] = [total_iface(tests['in'], D, R, maxn, False) / len(tests['in']), H2.total(tests['in'], D, [], {}, R, 'iface', MAXF)]
LD = lambda comps: learn_h(comps, R, int(os.environ.get('KD', 40)), maxn, sym, mode='hier', topc=30, maxe=MAXEr, objective='hier')
for mode in ('iface', 'rel'):
    cst, D2, holes, lib, alive, dbits, rd = H2.refine(train, D, R, mode, LD, MAXF, rounds=int(os.environ.get('ROUNDS', 3)), maxn=maxn)
    r = {'round': rd, 'n_holes': len(holes), 'hole_dict_bits': dbits, 'train_cost_total': cst, 'holes': [{'key': h['key'], 'nfill': len(h['fil'])} for h in holes]}
    r['glue'] = {t: H2.total(cs, D, [], {}, R, mode, MAXF) for t, cs in tests.items()}
    r['holes_model'] = {t: H2.total(cs, D2, holes, lib, R, mode, MAXF, alive) for t, cs in tests.items()}
    r['mean_glue'] = sum(r['glue'].values()) / len(r['glue']); r['mean_holes'] = sum(r['holes_model'].values()) / len(r['holes_model'])
    r['k_alive'] = len(alive); r['dict_bits_alive'] = dict_bits_h([D2[j] for j in sorted(alive)], R, maxn)
    res[mode] = r
res['time'] = round(time.time() - t0)
print(tag, 'dict', res['k_dict'], 'check', [round(x, 1) for x in res['check_total_iface']], 'time', res['time'])
for mode in ('iface', 'rel'):
    r = res[mode]; print(' ', mode, 'holes', r['n_holes'], 'alive', r['k_alive'], 'dict', round(r['dict_bits_alive'] + r['hole_dict_bits']), 'vs', round(res['dict_bits']), 'glue', round(r['mean_glue'], 1), 'holes', round(r['mean_holes'], 1), flush=True)
json.dump(res, open(f'../results/e30_{tag}.json', 'w'), default=str)
