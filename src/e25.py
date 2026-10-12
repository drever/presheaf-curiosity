import sys, os, json, random, time
which = sys.argv[1]; n = int(sys.argv[2]); seed = int(sys.argv[3])
if which == 'streets': os.environ['SYM'] = '1'
import und, und4
from repair import learn, cost, dict_cost
if which == 'c6288':
    from netlist import *
    NN = 31; R = 64; und.SYMS = set(); syms = set(); rng = random.Random(100 + seed); L = Labeler()
    def win(nm, k): return [to_comp(x, rng, NN) for x in windows_from(load_bench(nm), rng, k, nmax=20, labeler=L)]
    train = win('c6288', n); tests = {'in': win('c6288', 100)}
    for c in ['c1355', 'c499', 'c880', 'c1908']: tests[c] = win(c, 100)
else:
    from streets import *
    from e19 import load, R
    und.SYMS = set(range(NLAB)); syms = set(range(NLAB)); rng = random.Random(11 + seed)
    tr_all = load('barcelona', rng, n + 100); train, te = tr_all[:n], tr_all[n:]
    tests = {'in': te}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
t0 = time.time(); rules = learn(train, R, syms)
r = {'k': len(rules), 'time': round(time.time() - t0), 'dict_bits': dict_cost(rules, R), 'train': cost(train, rules, R, syms)}
for t, c in tests.items(): r[t] = cost(c, rules, R, syms)
print(which, seed, {a: round(b, 1) for a, b in r.items()}, flush=True)
json.dump(r, open(f'../results/e25_{which}_{n}_{seed}.json', 'w'))
