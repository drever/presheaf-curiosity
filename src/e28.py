"""Test B auf echten Daten: AU-Modell (Formen aus label-geloeschten Fenstern + Labelverteilung je Musterkante) gegen exaktes glue und RePair."""
import sys, os, json, random, time
which = sys.argv[1]; seed = int(sys.argv[2])
if which == 'streets': os.environ['SYM'] = '1'
import und, und4
import e27
from e27 import *
if which == 'c6288':
    from netlist import *
    NNr = 31; Rr = 64; n = 40; und.SYMS = set(); rng = random.Random(100 + seed); L = Labeler()
    def win(nm, k): return [to_comp(x, rng, NNr) for x in windows_from(load_bench(nm), rng, k, nmax=20, labeler=L)]
    train = win('c6288', n); tests = {'in': win('c6288', 100)}; MAXEr = 12; syms = set(); erased_syms = set()
else:
    from streets import *
    from e19 import load, R as Rr, NN as NNr, MAXE as MAXEr
    n = 50; und.SYMS = set(range(NLAB)); und4.UND = True; syms = set(range(NLAB)); erased_syms = {0}; rng = random.Random(500 + seed)
    allw = load('barcelona', rng, n + 130); train = allw[:n]; tests = {'in': allw[n + 30:]}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
e27.R = Rr; e27.NN = NNr; e27.maxn = NNr + 1
import iface; iface_R = Rr
maxn = NNr + 1; R = Rr
res = {}
def put(nm, held, d, k): res[nm] = {'held': held, 'dict': d, 'k': k, 'amort': sum(held.values()) / len(held) + d / 100}; res[nm]['mean'] = sum(held.values()) / len(held)
und.SYMS = syms
D = learn_h(train, R, 40, maxn, which == 'streets', mode='hier', topc=30, maxe=MAXEr, objective='hier')
put('exact', {t: total_iface(c, D, R, maxn, False) / len(c) for t, c in tests.items()}, dict_bits_h(D, R, maxn), len(D))
und.SYMS = erased_syms
Ds = learn_h([erase(c) for c in train], 1, 40, maxn, which == 'streets', mode='hier', topc=30, maxe=MAXEr, objective='hier')
counts, N = fit_labels(train, Ds); ds = dict_bits_h(Ds, 1, maxn)
put('shape_raw', {t: cost_shape(c, Ds, counts, N, True) for t, c in tests.items()}, ds, len(Ds))
put('AU', {t: cost_shape(c, Ds, counts, N, False) for t, c in tests.items()}, ds + label_dict_bits(Ds, counts, N, False), len(Ds))
und.SYMS = syms
rules = rp.learn(train, R, syms, K=300)
put('repair', {t: rp.cost(c, rules, R, syms) for t, c in tests.items()}, rp.dict_cost(rules, R), len(rules))
for k, v in res.items(): print(which, seed, k, {a: (round(b, 1) if not isinstance(b, dict) else {x: round(y, 1) for x, y in b.items()}) for a, b in v.items()}, flush=True)
json.dump(res, open(f'../results/e28_{which}_{seed}.json', 'w'))
