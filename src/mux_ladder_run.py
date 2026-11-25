"""Pattern-cap ladder (docs/prereg-mux-ladder.md). Usage: python mux_ladder_run.py CIRCUIT SEED NMAX MAXE
Same as quip_window.py with HUBS = 0, except that the pattern cap maxe (12 there) and the pattern node cap MAXN
(32 there) are parameters: MAXN = max(32, MAXE + 1). Original docstring of quip_window.py:
NMAX = nodes per window (20 = the setting of quip_run.py); HUBS = 0 (hub fan-out edges left out, as in quip_run.py) or
1 (hub fan-out edges added back to the region that contains their sink; the walk that defines the regions is unchanged).
Gluing only, on the circuit and on its label- and degree-preserving rewiring. Writes ../results/quipw_CIRCUIT_SEED_NMAX_HUBS.json"""
import sys, json, random, time
from collections import Counter
import und
from und3 import learn_h
from netlist import Labeler, windows_from, to_comp
import split as SP, coder2
from rewire import rewire
from quip import load_quip
name = sys.argv[1]; seed = int(sys.argv[2]); NMAX = int(sys.argv[3]); MAXE = int(sys.argv[4]); HUBS = 0
NN = NMAX + 11; MAXN = max(32, MAXE + 1); NTR = 40; NTE = 100        # NN = 31 for NMAX = 20, as in quip_run.py
und.SYMS = set(); und.TWIN_MAX = 6; und.EMBED_BUDGET = 2000; und.CANON_UNDIRECTED = True
E = load_quip(name); L = Labeler(); R = max(64, len({l for *_, l in E}))
LD = lambda T: learn_h(T, R, 40, MAXN, False, mode='hier', topc=30, maxe=MAXE, objective='hier')
out = {'name': name, 'seed': seed, 'nmax': NMAX, 'hubs': HUBS, 'maxe': MAXE, 'MAXN': MAXN, 'NN': NN, 'edges': len(E), 'R': R, 'times': {}}

def regions(E, s):
    sp = SP.hub_walk_split(E, random.Random(900 + s)); A, B = list(sp['A']), list(sp['B'])
    if HUBS:
        outd = Counter(e[0] for e in E)
        for e in E:
            if not SP.is_input_edge(e) and outd[e[0]] > 8: (A if e[1] in sp['SA'] else B).append(e)
    return A, B, {'cut': sp['cut'], 'A_edges': len(A), 'B_edges': len(B), 'label_tv': SP.label_tv(A, B)}

def code(te, model):
    b, info = coder2.encode(te, model, R, 'boundary'); v = coder2.verify(te, b, info)
    return {'data_bits_per_window': sum(info['per_comp_bits']) / len(te), 'dict_bits': info['dict_bits'], 'verified': all(v.values())}

for tag, EE in (('circuit', E), ('control', rewire(E, random.Random(8900 + seed))[0])):
    A, B, info = regions(EE, seed); rng = random.Random(10900 + seed)
    tr = [to_comp(w, rng, NN) for w in windows_from(A, rng, NTR, nmax=NMAX, labeler=L)]
    te = [to_comp(w, rng, NN) for w in windows_from(B, rng, NTE, nmax=NMAX, labeler=L)]
    r = {'split': info, 'test_edges_per_window': sum(len(c.E) for c in te) / len(te)}
    r['empty'] = code(te, coder2.model_plain([]))
    t0 = time.time(); Dg = LD(tr); out['times'][tag] = round(time.time() - t0)
    r['glue'] = code(te, coder2.model_plain(Dg)); r['glue']['patterns'] = len(Dg); r['glue']['pattern_edges'] = sorted((len(p) for p in Dg), reverse=True)
    r['share_of_empty'] = r['glue']['data_bits_per_window'] / r['empty']['data_bits_per_window']
    out[tag] = r
out['gap'] = out['control']['share_of_empty'] - out['circuit']['share_of_empty']
print(json.dumps({k: out[k] for k in ('name', 'seed', 'nmax', 'maxe', 'gap', 'times')} | {t: round(out[t]['share_of_empty'], 3) for t in ('circuit', 'control')}), flush=True)
json.dump(out, open(f'../results/ladder_{name}_{seed}_{NMAX}_{MAXE}.json', 'w'), indent=1)
