"""Why does 'grow' stop? Re-implements the learn_h loop for mode='grow' with diagnostics at the stopping round."""
import sys, random, itertools, json
import und
from und import *
import und3
from und3 import total_h, learn_h
from netlist import *
from iface import total_iface
import split as SP
NN = 31; maxn = 32; R = 64
cond = sys.argv[1]; seed = int(sys.argv[2]); topc = int(sys.argv[3]) if len(sys.argv) > 3 else 30
und.SYMS = set(); und.TWIN_MAX = 6; L = Labeler(); rng = random.Random(100 + seed)
E = [e for e in load_bench('c6288') if not SP.is_input_edge(e)]
def win(k):
    ws = windows_from(E, rng, k, nmax=20, labeler=L)
    if 'shuf' in cond:
        r2 = random.Random(7 + seed)
        for w in ws: r2.shuffle(w)
    return [to_comp(x, rng, NN) for x in ws]
train = win(40); test = win(100)
def run(mode, topc):
    D = []; keys = set(); Lc = total_h(train, D, R, maxn); trace = []
    for it in range(40):
        cnt = {}
        for c in train:
            inst, raw = cover_u(c, D); pieces = []
            for pi, ids, mm in inst:
                mp = dict(mm); pieces.append((frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]), set(mp.values())))
            for e in raw:
                t = (c.E[e][1], c.E[e][2], c.E[e][3]); pieces.append((frozenset([t]), {t[0], t[2]}))
            cand = [(p,) for p in pieces] + [(p, q) for p, q in itertools.combinations(pieces, 2) if p[1] & q[1] and (mode == 'hier' or len(p[0]) == 1 or len(q[0]) == 1)]
            for grp in cand:
                es = frozenset().union(*[g[0] for g in grp])
                if len(es) > 12: continue
                pat = normalize(es)
                try: k = canon_u(pat, False)
                except ValueError: continue
                if k in keys: continue
                cnt.setdefault(k, [0, pat])[0] += 1
        allc = sorted(cnt.values(), key=lambda x: -x[0] * len(x[1]))
        res = []
        for rank, (n_, pat) in enumerate(allc[:max(topc, 150)]):
            try: op = tuple(order_pattern(pat))
            except ValueError: continue
            res.append((total_h(train, D + [op], R, maxn) - Lc, rank, n_, len(pat), op))
        top = [r for r in res if r[1] < topc]
        best = min(top, default=None)
        if best is None or best[0] >= 0:
            beyond = sorted(r for r in res if r[1] >= topc and r[0] < 0)[:3]
            trace.append({'stop_round': it, 'n_cand': len(allc), 'best_in_top': None if best is None else (round(best[0], 1), best[1], best[2], best[3]),
                          'improving_beyond_top': [(round(r[0], 1), r[1], r[2], r[3]) for r in beyond], 'sizes_in_D': sorted(len(p) for p in D)})
            break
        D.append(best[4]); keys.add(canon_u(best[4], False)); Lc = best[0] + Lc
    return D, trace
for mode in ('grow', 'hier'):
    D, tr = run(mode, topc)
    print(json.dumps({'cond': cond, 'mode': mode, 'topc': topc, 'k': len(D), 'train_total_h': round(total_h(train, D, R, maxn) / 40, 1), 'test_iface': round(total_iface(test, D, R, maxn, False) / 100, 1), 'stop': tr}), flush=True)
