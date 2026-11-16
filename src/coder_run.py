"""Write c6288 with our coder and read it back. Usage: python coder_run.py full|gates SEED"""
import sys, random, json
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import Comp
from netlist import *
from iface import total_iface, total_old
import split as SP, coder
cond = sys.argv[1]; seed = int(sys.argv[2]); maxn = 32
und.SYMS = set(); und.TWIN_MAX = 6; L = Labeler(); rng = random.Random(100 + seed)
E = load_bench('c6288')
if cond == 'gates': E = [e for e in E if not SP.is_input_edge(e)]
train = [to_comp(x, rng, 31) for x in windows_from(E, rng, 40, nmax=20, labeler=L)]
D = learn_h(train, 64, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier')
out = {'cond': cond, 'seed': seed, 'edges': len(E), 'patterns': len(D), 'runs': []}
for numbering in ('name', 'anonymous'):
    nodes = sorted({x for u, v, _ in E for x in (u, v)}, key=lambda x: (len(x), x))
    if numbering == 'anonymous': random.Random(seed).shuffle(nodes)
    ix = {x: i for i, x in enumerate(nodes)}; es = sorted(E)
    if numbering == 'anonymous': random.Random(seed + 1).shuffle(es)      # random edge order as well
    whole = Comp(len(nodes), [(ix[u], L(l), ix[v]) for u, v, l in es])
    for R in (64, len(L.ids)):
        model = {'boundary': total_iface([whole], D, R, maxn, True), 'all': total_old([whole], D, R, maxn, True)}
        for mode in ('boundary', 'all'):
            b, info = coder.encode(whole, D, R, mode); v = coder.verify(whole, b, info, mode); info.pop('fresh_order')
            r = {'numbering': numbering, 'R': R, 'mode': mode, 'file_bits': 8 * len(b), 'model_bits': round(model[mode]), **{k: round(x) if isinstance(x, float) else x for k, x in info.items()}, 'verify': v}
            out['runs'].append(r); print(json.dumps(r), flush=True)
json.dump(out, open(f'../results/coder_{cond}_{seed}.json', 'w'), indent=1)
