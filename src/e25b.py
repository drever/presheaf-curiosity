import sys, os, json, random
which = sys.argv[1]; n = int(sys.argv[2]); seed = int(sys.argv[3])
if which == 'streets': os.environ['SYM'] = '1'
import und, und4
from und3 import learn_h, dict_bits_h
from iface import total_iface
from repair import learn, cost, dict_cost
if which == 'c6288':
    from netlist import *
    NN = 31; R = 64; maxn = NN + 1; und.SYMS = set(); syms = set(); rng = random.Random(100 + seed); L = Labeler(); MAXE = 12
    train = [to_comp(x, rng, NN) for x in windows_from(load_bench('c6288'), rng, n, nmax=20, labeler=L)]
else:
    from streets import *
    from e19 import load, R, NN, maxn, MAXE
    und.SYMS = set(range(NLAB)); und4.UND = True; syms = set(range(NLAB)); rng = random.Random(11 + seed)
    train = load('barcelona', rng, n + 100)[:n]
out = {}
for nm, mode in (('glue', 'hier'), ('grow', 'grow')):
    D = learn_h(train, R, 40, maxn, which == 'streets', mode=mode, topc=30, maxe=MAXE, objective='hier')
    out[nm] = {'k': len(D), 'dict': dict_bits_h(D, R, maxn), 'train_if': total_iface(train, D, R, maxn, False) }
rules = learn(train, R, syms)
out['repair'] = {'k': len(rules), 'dict': dict_cost(rules, R), 'train_if': cost(train, rules, R, syms) * n}
for k, v in out.items(): v['total_per_window'] = (v['dict'] + v['train_if']) / n
print(which, seed, json.dumps({k: {a: round(b, 1) for a, b in v.items()} for k, v in out.items()}), flush=True)
json.dump(out, open(f'../results/e25b_{which}_{n}_{seed}.json', 'w'))
