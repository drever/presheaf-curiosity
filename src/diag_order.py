"""Diagnostic: how much do gluing and the RePair re-implementation depend on the order of edges inside a window?\nUsage: python diag_order.py COND SEED, COND in full | gates | full_shuf | gates_shuf | gates_intr (whole c6288, 40 training and 100 fresh windows, in-sample).\nfull = with input edges, gates = without; default order = sorted by node name; shuf = random order; intr = order from the graph alone."""
import sys, random, time, json
import und
from und import *
from und3 import learn_h, dict_bits_h
from netlist import *
from iface import total_iface
import repair as RP
import split as SP
NN = 31; maxn = 32; R = 64
cond = sys.argv[1]; seed = int(sys.argv[2]); tw = None if 'notwin' in cond else 6
und.SYMS = set(); und.TWIN_MAX = tw; L = Labeler(); rng = random.Random(100 + seed)
E = load_bench('c6288')
if cond.startswith('gates'): E = [e for e in E if not SP.is_input_edge(e)]
def win(k):
    ws = windows_from(E, rng, k, nmax=20, labeler=L)
    if 'shuf' in cond:
        r2 = random.Random(7 + seed)
        for w in ws: r2.shuffle(w)
    if 'intr' in cond:   # order from the graph alone: label, then degrees of the end nodes inside the window; ties in random order
        import collections
        r2 = random.Random(7 + seed)
        for w in ws:
            r2.shuffle(w); deg = collections.Counter(x for u, v, _ in w for x in (u, v))
            w.sort(key=lambda e: (e[2], deg[e[0]], deg[e[1]]))
    return [to_comp(x, rng, NN) for x in ws]
train = win(40); test = win(100)
out = {'cond': cond, 'seed': seed, 'edges_per_window': sum(len(c.E) for c in test) / 100}
out['empty'] = total_iface(test, [], R, maxn, False) / 100
t = time.time(); D = learn_h(train, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier')
out['glue'] = total_iface(test, D, R, maxn, False) / 100; out['glue_k'] = len(D); out['glue_dict'] = dict_bits_h(D, R, maxn)
for K in (40, 80):
    rules = RP.learn(train, R, set(), K=K); out[f'repair{K}'] = RP.cost(test, rules, R, set()); out[f'repair{K}_k'] = len(rules); out[f'repair{K}_dict'] = RP.dict_cost(rules, R)
print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in out.items()}), flush=True)
