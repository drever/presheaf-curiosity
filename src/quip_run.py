"""Pre-registered measurement on the Quip circuits (docs/prereg-quip.md). Usage: python quip_run.py CIRCUIT SEED
Writes ../results/quip_CIRCUIT_SEED.json"""
import sys, json, random, time, collections
import und
from und import *
from und3 import learn_h
from und4 import learn_prod_auto
import holes2 as H2
from netlist import Labeler, windows_from, to_comp
import split as SP, coder2
from rewire import rewire
from quip import load_quip
name = sys.argv[1]; seed = int(sys.argv[2]); NN = 31; MAXN = 32; NTR = 40; NTE = 100
und.SYMS = set(); und.TWIN_MAX = 6
E = load_quip(name); L = Labeler(); R = max(64, len({l for *_, l in E}))
LD = lambda T: learn_h(T, R, 40, MAXN, False, mode='hier', topc=30, maxe=12, objective='hier')
out = {'circuit': name, 'seed': seed, 'edges': len(E), 'R': R, 'times': {}}

def windows(E, s):
    sp = SP.gate_walk_split(E, random.Random(900 + s)); rng = random.Random(10900 + s)
    tr = [to_comp(w, rng, NN) for w in windows_from(sp['A'], rng, NTR, nmax=20, labeler=L)]
    te = [to_comp(w, rng, NN) for w in windows_from(sp['B'], rng, NTE, nmax=20, labeler=L)]
    trB = [to_comp(w, rng, NN) for w in windows_from(sp['B'], rng, NTR, nmax=20, labeler=L)]
    return tr, te, trB, {'cut': sp['cut'], 'A_edges': len(sp['A']), 'B_edges': len(sp['B'])}

def code(te, model):
    b, info = coder2.encode(te, model, R, 'boundary'); v = coder2.verify(te, b, info)
    return {'data_bits_per_window': sum(info['per_comp_bits']) / len(te), 'dict_bits': info['dict_bits'], 'bytes': info['bytes'], 'units': info['units'],
            'instances': info['instances'], 'raw_edges': info['raw_edges'], 'verified': all(v.values())}

def shared_use(te, DA, DB):
    kb = {canon_u(p, False) for p in DB}; ka = [canon_u(p, False) for p in DA]; tot = sh = 0
    for c in te:
        for pi, ids, mm in cover_u(c, DA)[0]:
            tot += len(ids); sh += len(ids) * (ka[pi] in kb)
    return sh / tot if tot else None

for tag, EE in (('circuit', E), ('control', rewire(E, random.Random(8900 + seed))[0])):
    tr, te, trB, info = windows(EE, seed); r = {'split': info, 'test_edges_per_window': sum(len(c.E) for c in te) / len(te)}
    r['empty'] = code(te, coder2.model_plain([]))
    t0 = time.time(); Dg = LD(tr); out['times'][tag + '_glue'] = round(time.time() - t0)
    r['glue'] = code(te, coder2.model_plain(Dg)); r['glue']['patterns'] = len(Dg); r['glue']['max_pattern'] = max([len(p) for p in Dg] + [0])
    DB = LD(trB); r['shared_use'] = shared_use(te, Dg, DB)
    r['jaccard'] = len({canon_u(p, False) for p in Dg} & {canon_u(p, False) for p in DB}) / max(1, len({canon_u(p, False) for p in Dg} | {canon_u(p, False) for p in DB}))
    r['share_of_empty'] = r['glue']['data_bits_per_window'] / r['empty']['data_bits_per_window']
    if tag == 'circuit':
        t0 = time.time(); _, F, Dp, Deff, col = learn_prod_auto(tr, R, 40, MAXN, 24, D0=Dg); out['times']['product'] = round(time.time() - t0)
        r['product'] = code(te, coder2.model_product(Dp, F, col, 24)); r['product'].update({'factors': len(F), 'factor_sizes': [len(f) for f in F], 'implicit': len(Deff) - len(Dp)})
        t0 = time.time(); cst, D2, holes, lib, alive, dbits, rd = H2.refine(tr, Dg, R, 'iface', LD, 5, rounds=2, maxn=MAXN); out['times']['holes'] = round(time.time() - t0)
        r['holes'] = code(te, coder2.model_holes(D2, holes, lib, alive) if holes else coder2.model_plain(Dg))
        r['holes'].update({'holes': len(holes), 'fillers': [len(h['fil']) for h in holes]})
    out[tag] = r
    print(json.dumps({'circuit': name, 'seed': seed, tag: {k: (round(v['data_bits_per_window'], 1) if isinstance(v, dict) and 'data_bits_per_window' in v else (round(v, 3) if isinstance(v, float) else v)) for k, v in r.items() if k != 'split'}}), flush=True)
json.dump(out, open(f'../results/quip_{name}_{seed}.json', 'w'), indent=1)
