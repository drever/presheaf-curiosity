"""Held-out test on c6288, repaired split (supersedes heldout.py, whose results are kept as a record).

What changed against heldout.py:
  1. The walk that cuts the netlist in two does not pass through primary inputs (split.gate_walk_split). The 512 input
     fan-out edges are in neither region.
  2. Region A is cut once more by the same walk into a training part and a test part that share no node, so a "new" window
     of A cannot overlap a training window.
  3. The learned dictionaries and the cost of every single test window are saved, so that two methods can be compared
     window by window (the test windows are the same for all methods).
  4. The three random streams (split, inner split, windows) are separate, so changing the number of windows does not move
     the split.

Usage: python heldout2.py SEED [TRAIN_WINDOWS=40] [TEST_WINDOWS=100]
Writes ../results/heldout2_SEED.json. Bits per window, lower is better, no dictionary cost, as in heldout.py."""
import sys, os, json, time, random, platform
import und
from und import *
from und3 import learn_h
from netlist import *
from iface import total_iface
import repair as RP
import split as SP

NN = 31; maxn = NN + 1; R = 64; TRAIN_FRAC = 0.5
seed = int(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 40; kt = int(sys.argv[3]) if len(sys.argv) > 3 else 100
und.SYMS = set(); und.TWIN_MAX = 6; L = Labeler()
E = load_bench('c6288')
sp = SP.gate_walk_split(E, random.Random(900 + seed))
inner = SP.inner_split(sp['A'], random.Random(1900 + seed), TRAIN_FRAC)
rng = random.Random(2900 + seed)
regions = {'A_train': inner['train'], 'A_new': inner['test'], 'B_heldout': sp['B']}
for name, es in regions.items(): print(name, SP.describe(es), flush=True)
print('cut A|B', sp['cut'], 'cut inside A', inner['cut'], 'input edges left out', sp['input_edges'], flush=True)

raw = {'A_train': windows_from(regions['A_train'], rng, n, nmax=20, labeler=L)}
for t in ('A_new', 'B_heldout'): raw[t] = windows_from(regions[t], rng, kt, nmax=20, labeler=L)
train_nodes = set().union(*[SP.nodes_of(w) for w in raw['A_train']])
for t in ('A_new', 'B_heldout'):
    assert not any(SP.nodes_of(w) & train_nodes for w in raw[t]), 'a test window shares a node with a training window'
comps = {t: [to_comp(w, rng, NN) for w in ws] for t, ws in raw.items()}
train = comps['A_train']; tests = {t: comps[t] for t in ('A_new', 'B_heldout')}

res = {'script': 'heldout2.py', 'seed': seed, 'python': platform.python_version(), 'PYTHONHASHSEED': os.environ.get('PYTHONHASHSEED'),
       'R': R, 'labels_seen': len(L.ids), 'train_frac': TRAIN_FRAC,
       'split': {'cut_A_B': sp['cut'], 'cut_inside_A': inner['cut'], 'input_edges_left_out': sp['input_edges'], **{t: SP.describe(es) for t, es in regions.items()}},
       'windows': {t: [{'nodes': sorted(SP.nodes_of(w)), 'edges': len(w)} for w in ws] for t, ws in raw.items()},
       'methods': {}}

def per_window(cs, D=None, rules=None):
    if D is not None: return [total_iface([c], D, R, maxn, False) for c in cs]
    return [RP.cost([c], rules, R, set()) for c in cs]

def ev(name, D=None, rules=None, tm=0):
    r = {'k': len(D if D is not None else rules), 'time': round(tm), 'per_window': {}}
    if D is not None: r['patterns'] = [[list(e) for e in p] for p in D]
    else: r['rules'] = [repr(k) for k in rules]
    for t, cs in tests.items():
        pw = per_window(cs, D, rules); r['per_window'][t] = pw; r[t] = sum(pw) / len(pw) if pw else None
    res['methods'][name] = r
    print(seed, name, {'k': r['k'], 'time': r['time'], **{t: (round(r[t], 1) if r[t] is not None else None) for t in tests}}, flush=True)

ev('none', D=[])
t0 = time.time(); ev('glue', D=learn_h(train, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier'), tm=time.time() - t0)
t0 = time.time(); ev('grow', D=learn_h(train, R, 40, maxn, False, mode='grow', topc=30, maxe=12, objective='hier'), tm=time.time() - t0)
t0 = time.time(); ev('repair_reimpl', rules=RP.learn(train, R, set(), K=80), tm=time.time() - t0)

# glue against grow on the same windows. The windows of one region overlap each other, so they are not independent draws:
# the counts below describe these windows and are not a significance test.
res['paired_glue_minus_grow'] = {}
for t in tests:
    a = res['methods']['glue']['per_window'][t]; b = res['methods']['grow']['per_window'][t]; d = [x - y for x, y in zip(a, b)]
    res['paired_glue_minus_grow'][t] = {'windows': len(d), 'mean_difference': sum(d) / len(d) if d else None,
                                         'glue_lower': sum(x < 0 for x in d), 'equal': sum(x == 0 for x in d), 'glue_higher': sum(x > 0 for x in d)}
    print(seed, 'glue minus grow', t, res['paired_glue_minus_grow'][t], flush=True)
json.dump(res, open(f'../results/heldout2_{seed}.json', 'w'), indent=1)
