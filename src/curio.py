"""Curiosity experiment (docs/prereg-curiosity.md): does choosing the next data by predicted description-length gain
beat random order and "most expensive first"?
Usage: python curio.py SEED clean|noise random|gain|surprise|oracle   ->  ../results/curio_SEED_COND_ARM.json"""
import sys, json, time, random
from curio_common import *
from und3 import learn_h, dict_bits_h
seed = int(sys.argv[1]); cond = sys.argv[2]; arm = sys.argv[3]; BATCH = 5; ROUNDS = 12; ORACLE_SUB = 30
pool, test, L = setup(seed); noise = set()
if cond == 'noise': pool, noise = unlearnable(pool, seed)
learn = lambda T: learn_h(T, R, KDICT, MAXN, False, mode='hier', topc=TOPC, maxe=MAXE, objective='hier')
heldout = lambda D: total_iface(test, D, R, MAXN, False) / len(test)

def scores(T, D, remaining):
    """Predicted gain and current cost (surprise) of every remaining pool window."""
    keys = {canon_u(p, False) for p in D}; base_T = total_h(T, D, R, MAXN); base_0 = total_h([], D, R, MAXN); redT = {}; dictc = {}; pred = {}; cost = {}
    for i in remaining:
        w = pool[i]; cost[i] = total_iface([w], D, R, MAXN, False); base_w = total_h([w], D, R, MAXN); best_Tw = 0.0; best_T = 0.0
        for k, (n, pat) in candidates(w, D, keys).items():
            try: op = tuple(order_pattern(pat))
            except ValueError: continue
            if k not in redT:
                redT[k] = base_T - total_h(T, D + [op], R, MAXN); dictc[k] = total_h([], D + [op], R, MAXN) - base_0
            dw = base_w - total_h([w], D + [op], R, MAXN) + dictc[k]            # data bits saved on w alone
            best_Tw = max(best_Tw, redT[k] + dw); best_T = max(best_T, redT[k])
        pred[i] = max(0.0, best_Tw - best_T)
    return pred, cost

T = []; D = []; remaining = list(range(len(pool))); order = list(range(len(pool))); random.Random(5900 + seed).shuffle(order); orng = random.Random(6900 + seed)
# additivity of the objective over windows (used by the estimator)
assert abs(total_h(pool[:3], [], R, MAXN) - sum(total_h([w], [], R, MAXN) for w in pool[:3]) + 2 * total_h([], [], R, MAXN)) < 1e-6
log = {'seed': seed, 'cond': cond, 'arm': arm, 'noise_windows': sorted(noise), 'heldout_round0': heldout([]), 'rounds': []}; t0 = time.time()
for rd in range(1, ROUNDS + 1):
    pred, cost = scores(T, D, remaining); extra = {}
    if arm == 'random': chosen = [i for i in order if i in set(remaining)][:BATCH]
    elif arm == 'gain': chosen = sorted(remaining, key=lambda i: (-pred[i], i))[:BATCH]
    elif arm == 'surprise': chosen = sorted(remaining, key=lambda i: (-cost[i], i))[:BATCH]
    else:
        sub = sorted(orng.sample(remaining, min(ORACLE_SUB, len(remaining)))); real = {i: heldout(learn(T + [pool[i]])) for i in sub}
        chosen = sorted(sub, key=lambda i: (real[i], i))[:BATCH]; extra = {'oracle_heldout_if_added': {str(i): round(v, 2) for i, v in real.items()}}
    T += [pool[i] for i in chosen]; remaining = [i for i in remaining if i not in set(chosen)]; D = learn(T); h = heldout(D)
    log['rounds'].append({'round': rd, 'chosen': chosen, 'chosen_noise': sum(i in noise for i in chosen), 'heldout_bits_per_window': h, 'dict_bits': dict_bits_h(D, R, MAXN), 'patterns': len(D),
                          'train_total': total_h(T, D, R, MAXN), 'pred_gain': {str(i): round(v, 2) for i, v in pred.items()}, 'cost': {str(i): round(v, 2) for i, v in cost.items()},
                          'dictionary': [[list(e) for e in p] for p in D], 'time': round(time.time() - t0), **extra})
    print(seed, cond, arm, 'round', rd, 'heldout', round(h, 1), 'patterns', len(D), 'noise chosen', log['rounds'][-1]['chosen_noise'], 't', round(time.time() - t0), flush=True)
log['auc'] = sum(r['heldout_bits_per_window'] for r in log['rounds']) / ROUNDS
json.dump(log, open(f'../results/curio_{seed}_{cond}_{arm}.json', 'w'))
