"""Do the computed code lengths of the product and hole models match actual files?   (lab notebook, section 16)
Worlds of section 4 ("Result step 1", e17: product world; section 4h, e30: hole world), test windows written with coder2.
Usage: python coder2_check.py product SEED [N=50]   |   python coder2_check.py holes SEED"""
import sys, os, json, random, time
import und
from und import *
from core import Comp, LOG
import coder2
which = sys.argv[1]; seed = int(sys.argv[2]); out = {'world': which, 'seed': seed}
if which == 'product':
    import e17
    from und3 import learn_h, dict_bits_h
    from und4 import learn_prod_auto
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 50; R = e17.R; maxn = e17.maxn
    und.SYMS = set(); rng = random.Random(7000 + seed); H, V, seen, unseen = e17.make_world(rng)
    train = [e17.gen_comp(rng, H, V, seen) for _ in range(n)]
    tests = {'seen': [e17.gen_comp(rng, H, V, seen) for _ in range(100)], 'unseen': [e17.gen_comp(rng, H, V, unseen) for _ in range(100)]}
    t0 = time.time(); D0, F, Dp, Deff, col = learn_prod_auto(train, R, 40, maxn, e17.MAXE); out['learn_time'] = round(time.time() - t0)
    models = {'glue': (coder2.model_plain(D0), D0, dict_bits_h(D0, R, maxn)),
              'product': (coder2.model_product(Dp, F, col, e17.MAXE), Deff, dict_bits_h(Dp, R, maxn) + sum(LOG(len(Dp) + 1) + 1 for _ in F))}
    out['factors'] = len(F); out['factors_in_Dp'] = sum(any(tuple(f) == tuple(p) for p in Dp) for f in F); out['explicit'] = len(Dp); out['effective'] = len(Deff)
    assert coder2.effective(models['product'][0]) == list(Deff) or len(coder2.effective(models['product'][0])) == len(Deff)
    for name, (m, Dcov, dmodel) in models.items():
        for t, cs in tests.items():
            b, info = coder2.encode(cs, m, R, 'all'); v = coder2.verify(cs, b, info)
            out[f'{name}_{t}'] = {'model_bits_per_window': total_u(cs, Dcov, R, maxn, False) / len(cs), 'file_data_bits_per_window': sum(info['per_comp_bits']) / len(cs),
                                  'model_dict_bits': dmodel, 'file_dict_bits': info['dict_bits'], 'file_bytes': info['bytes'], 'verify': v}
else:
    sys.argv = ['e30.py', 'syn', str(seed)]; os.environ.update({'NTR': '120', 'NGAD': '6', 'KD': '80', 'ROUNDS': '2'})
    src = open('e30.py').read().split("maxn = NNr + 1; R = Rr; res = {}")[0]; g = {}; exec(src, g)
    import holes2 as H2
    from und3 import learn_h
    train, tests, R, MAXE, MAXF = g['train'], g['tests']['in'], g['Rr'], g['MAXEr'], g['MAXF']; maxn = g['NNr'] + 1
    LD = lambda comps: learn_h(comps, R, 80, maxn, False, mode='hier', topc=30, maxe=MAXE, objective='hier')
    t0 = time.time(); D = LD(train); cst, D2, holes, lib, alive, dbits, rd = H2.refine(train, D, R, 'iface', LD, MAXF, rounds=2, maxn=maxn); out['learn_time'] = round(time.time() - t0)
    from und3 import dict_bits_h
    out['holes'] = len(holes); out['fillers'] = sorted(len(h['fil']) for h in holes)
    models = {'glue': (coder2.model_plain(D), lambda cs: H2.total(cs, D, [], {}, R, 'iface', MAXF), dict_bits_h(D, R, maxn)),
              'holes': (coder2.model_holes(D2, holes, lib, alive), lambda cs: H2.total(cs, D2, holes, lib, R, 'iface', MAXF, alive), dbits + dict_bits_h([D2[j] for j in sorted(alive)], R, maxn))}
    for name, (m, mf, dmodel) in models.items():
        b, info = coder2.encode(tests, m, R, 'boundary'); v = coder2.verify(tests, b, info); info.pop('fresh_order')
        out[f'{name}_test'] = {'model_bits_per_window': mf(tests), 'file_data_bits_per_window': sum(info['per_comp_bits']) / len(tests), 'model_dict_bits': dmodel,
                               'file_dict_bits': info['dict_bits'], 'file_bytes': info['bytes'], 'units': info['units'], 'option_counts': info['option_counts'], 'verify': v}
print(json.dumps({k: ({a: (round(b, 1) if isinstance(b, float) else b) for a, b in v.items()} if isinstance(v, dict) else v) for k, v in out.items()}), flush=True)
json.dump(out, open(f'../results/coder2_{which}_{seed}.json', 'w'), indent=1, default=str)
