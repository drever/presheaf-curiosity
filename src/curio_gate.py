"""Gate of the curiosity experiment (docs/prereg-curiosity.md, precondition 3 and second amendment):
does the in-sample gain of a candidate pattern predict its gain on held-out windows?
Usage: python curio_gate.py SEED   ->  ../results/curio_gate_SEED.json"""
import sys, json, time
from curio_common import *
from und3 import learn_h
seed = int(sys.argv[1]); pool, test, L = setup(seed); rounds = []; t0 = time.time()

def hook(it, D, cands, gains):
    base = total_h(test, D, R, MAXN); held = [base - total_h(test, D + [op], R, MAXN) for _, op, _ in cands]
    rho = spearman(gains, held) if len(cands) >= 5 else None
    rounds.append({'round': it, 'n_cand': len(cands), 'spearman': rho, 'pool_gain': [round(g, 2) for g in gains], 'heldout_gain': [round(h, 2) for h in held],
                   'sizes': [len(op) for _, op, _ in cands], 'counts': [n for n, _, _ in cands]})
    print(seed, 'round', it, 'cands', len(cands), 'rho', None if rho is None else round(rho, 3), flush=True)

D = learn_traced(pool, hook)
ref = learn_h(pool, R, KDICT, MAXN, False, mode='hier', topc=TOPC, maxe=MAXE, objective='hier')
rhos = sorted(r['spearman'] for r in rounds if r['spearman'] is not None)
out = {'seed': seed, 'patterns': len(D), 'same_as_learn_h': [list(map(list, p)) for p in D] == [list(map(list, p)) for p in ref], 'rounds_used': len(rhos),
       'median_spearman': rhos[len(rhos) // 2] if len(rhos) % 2 else (rhos[len(rhos) // 2 - 1] + rhos[len(rhos) // 2]) / 2, 'time': round(time.time() - t0), 'rounds': rounds}
print(json.dumps({k: v for k, v in out.items() if k != 'rounds'}), flush=True)
json.dump(out, open(f'../results/curio_gate_{seed}.json', 'w'), indent=1)
