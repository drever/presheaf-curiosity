import sys, os, json, random, time
os.environ['SYM'] = '1'
import und, und4
from und import *
from und3 import learn_h, dict_bits_h
from streets import *
from e19 import load, R, NN, maxn, MAXE
from iface import total_iface
import repair as rp
seed = int(sys.argv[1]); n = 50; NEVAL = 100
und.SYMS = set(range(NLAB)); und4.UND = True; syms = set(range(NLAB)); rng = random.Random(500 + seed)
allw = load('barcelona', rng, n + 130); train, val, te = allw[:n], allw[n:n + 30], allw[n + 30:]
tests = {'barcelona': te}
for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
out = {}
def rec(nm, held, dct, k, tm):
    r = {'k': k, 'dict': dct, 'time': round(tm)}; r.update(held)
    r['mean'] = sum(held.values()) / len(held); r['amortised'] = r['mean'] + dct / NEVAL
    out[nm] = r; print(seed, nm, {a: round(b, 1) for a, b in r.items()}, flush=True)
for nm, mode in (('glue', 'hier'), ('grow', 'grow')):
    t0 = time.time(); D = learn_h(train, R, 40, maxn, True, mode=mode, topc=30, maxe=MAXE, objective='hier')
    rec(nm, {t: total_iface(c, D, R, maxn, False) / len(c) for t, c in tests.items()}, dict_bits_h(D, R, maxn), len(D), time.time() - t0)
t0 = time.time(); rules = rp.learn(train, R, syms, K=300); tl = time.time() - t0
def ev(rules): return {t: rp.cost(c, rules, R, syms) for t, c in tests.items()}
rec('rp_full', ev(rules), rp.dict_cost(rules, R), len(rules), tl)
t0 = time.time(); pr = rp.prune(train, rules, R, syms, LOG(NN)); rec('rp_prune', ev(pr), rp.dict_cost(pr, R), len(pr), time.time() - t0)
def best_prefix(rs):
    best = None
    for K in sorted({0, 5, 10, 15, 20, 30, 40, 60, 80, 120, len(rs)}):
        if K > len(rs): continue
        sub = rs[:K]; crit = rp.cost(val, sub, R, syms) + rp.dict_cost(sub, R) / NEVAL
        if best is None or crit < best[0]: best = (crit, K)
    return best[1]
K1 = best_prefix(rules); rec('rp_val', ev(rules[:K1]), rp.dict_cost(rules[:K1], R), K1, 0)
K2 = best_prefix(pr); rec('rp_prune_val', ev(pr[:K2]), rp.dict_cost(pr[:K2], R), K2, 0)
json.dump(out, open(f'../results/e26_{seed}.json', 'w'))
