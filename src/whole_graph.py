"""Whole-circuit description length under our cost model, to set beside real compressors on the same graph.
A dictionary is learned on 40 windows (as everywhere else) and then used to cover the WHOLE c6288 graph as one component.
Usage: python whole_graph.py full|gates SEED"""
import sys, random, json, time
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import Comp, LOG
from netlist import *
from iface import total_iface
import repair as RP
import split as SP
cond = sys.argv[1]; seed = int(sys.argv[2]); R = 64; maxn = 32
und.SYMS = set(); und.TWIN_MAX = 6; L = Labeler(); rng = random.Random(100 + seed)
E = load_bench('c6288')
if cond == 'gates': E = [e for e in E if not SP.is_input_edge(e)]
train = [to_comp(x, rng, 31) for x in windows_from(E, rng, 40, nmax=20, labeler=L)]
nodes = sorted({x for u, v, _ in E for x in (u, v)}); r2 = random.Random(seed); r2.shuffle(nodes); ix = {x: i for i, x in enumerate(nodes)}
whole = Comp(len(nodes), [(ix[u], L(l), ix[v]) for u, v, l in sorted(E)])
out = {'cond': cond, 'seed': seed, 'nodes': len(nodes), 'edges': len(E), 'labels': len(L.ids)}
out['raw_model_bits'] = total_iface([whole], [], R, maxn, False)
t = time.time(); D = learn_h(train, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier')
out['glue_bits'] = total_iface([whole], D, R, maxn, False); out['glue_dict_bits'] = dict_bits_h(D, R, maxn); out['glue_k'] = len(D); out['glue_time'] = round(time.time() - t)
rules = RP.learn(train, R, set(), K=80)
out['repair_reimpl_sorted_bits'] = RP.cost([whole], rules, R, set()); out['repair_reimpl_dict_bits'] = RP.dict_cost(rules, R)
print(json.dumps({k: (round(v) if isinstance(v, float) else v) for k, v in out.items()}), flush=True)
json.dump(out, open(f'../results/whole_graph_{cond}_{seed}.json', 'w'))
