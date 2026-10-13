import sys, os, json, random, time
which = sys.argv[1]; seed = int(sys.argv[2])
if which == 'streets': os.environ['SYM'] = '1'
import und, und4
import e27
from e27 import *
from hybrid import *
if which == 'syn':
    pf, pd, fh = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    und.SYMS = set(); rng = random.Random(9000 + seed); W = make_world(rng, frac_hole=fh)
    train = [gen(rng, W, pf, pd) for _ in range(40)]; tests = {'in': [gen(rng, W, pf, pd) for _ in range(100)]}
    Rr, NNr, MAXEr, sym = R, NN, MAXE, False; tag = f'syn_{seed}_{pf}_{pd}_{fh}'
elif which == 'c6288':
    from netlist import *
    NNr = 31; Rr = 64; und.SYMS = set(); rng = random.Random(100 + seed); L = Labeler()
    def win(nm, k): return [to_comp(x, rng, NNr) for x in windows_from(load_bench(nm), rng, k, nmax=20, labeler=L)]
    train = win('c6288', 40); tests = {'in': win('c6288', 100)}; MAXEr = 12; sym = False; tag = f'c6288_{seed}'
else:
    from streets import *
    from e19 import load, R as Rr, NN as NNr, MAXE as MAXEr
    und.SYMS = set(range(NLAB)); und4.UND = True; rng = random.Random(500 + seed); sym = True
    allw = load('barcelona', rng, 180); train = allw[:50]; tests = {'in': allw[80:]}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
    tag = f'streets_{seed}'
e27.R = Rr; e27.NN = NNr; maxn = NNr + 1; R = Rr
res = {}
def put(nm, held, d, k): res[nm] = {'held': held, 'dict': d, 'k': k, 'mean': sum(held.values()) / len(held), 'amort': sum(held.values()) / len(held) + d / 100}
t0 = time.time()
Dex = learn_h(train, R, 40, maxn, sym, mode='hier', topc=30, maxe=MAXEr, objective='hier')
put('exact', {t: total_iface(c, Dex, R, maxn, False) / len(c) for t, c in tests.items()}, dict_bits_h(Dex, R, maxn), len(Dex))
Ds = learn_h([erase(c) for c in train], 1, 40, maxn, sym, mode='hier', topc=30, maxe=MAXEr, objective='hier')
counts, N = fit_labels(train, Ds); ds = dict_bits_h(Ds, 1, maxn)
put('AU', {t: cost_shape(c, Ds, counts, N, False) for t, c in tests.items()}, ds + label_dict_bits(Ds, counts, N, False), len(Ds))
counts2, N2, uE, uS = learn_hybrid(train, Dex, Ds, R)
Dex2, Ds2, c3, N3 = prune_dicts(Dex, Ds, uE, uS, counts2, N2)
d = dict_bits_h(Dex2, R, maxn) + dict_bits_h(Ds2, 1, maxn) + label_dict_bits(Ds2, c3, N3, False)
put('hybrid', {t: cost_hybrid(c, Dex2, Ds2, c3, N3, R) for t, c in tests.items()}, d, len(Dex2) + len(Ds2))
res['hybrid']['k_exact'] = len(Dex2); res['hybrid']['k_shape'] = len(Ds2); res['time'] = round(time.time() - t0)
for k, v in res.items(): print(tag, k, v if not isinstance(v, dict) else {a: (round(b, 1) if isinstance(b, float) else b) for a, b in v.items() if a != 'held'}, flush=True)
json.dump(res, open(f'../results/e29_{tag}.json', 'w'))
