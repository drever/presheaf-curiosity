import sys, json, time, itertools
from collections import Counter
import und
from und import *
from core import order_pattern, normalize
from cells import whole_comp

def merge_round(comp, D, maxe, mincount):
    inst, raw = cover_u(comp, D); pieces = []
    for pi, ids, mm in inst:
        mp = dict(mm); pieces.append((frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]), set(mp.values())))
    cnt = {}
    for p, q in itertools.combinations(pieces, 2):
        if not (p[1] & q[1]): continue
        es = p[0] | q[0]
        if len(es) > maxe or len(es) <= max(len(p[0]), len(q[0])): continue
        pat = normalize(es); k = canon_u(pat, False); cnt.setdefault(k, [0, pat])[0] += 1
    byscore = sorted(cnt.values(), key=lambda x: -x[0] * len(x[1]))[:8]; bysize = sorted([v for v in cnt.values() if v[0] >= mincount], key=lambda x: (-len(x[1]), -x[0]))[:8]
    seen = set(); cands = []
    for n_, pat in byscore + bysize:
        k = canon_u(pat, False)
        if k not in seen: seen.add(k); cands.append((n_, pat))
    L0 = total_u([comp], D, 64, comp.n + 1); best = None
    for n_, pat in cands:
        try: op = tuple(order_pattern(pat))
        except ValueError: continue
        Ln = total_u([comp], D + [op], 64, comp.n + 1)
        if Ln < L0 and (best is None or Ln < best[0]): best = (Ln, op, n_)
    return (best[1], best[2], L0 - best[0]) if best else (None, 0, 0)

if __name__ == '__main__':
    und.SYMS = set(); comp, nodes, L = whole_comp()
    D = [tuple(tuple(e) for e in p) for p in json.load(open('cells_D1b.json'))['D']]
    for rd in range(4):
        t0 = time.time(); p, n_, gain = merge_round(comp, D, 24, 100)
        if p is None: print('no more candidates', flush=True); break
        D.append(p); print('round', rd, 'new pattern edges', len(p), 'count', n_, 'gain bits', round(gain), round(time.time() - t0), 's', flush=True)
    inst, raw = cover_u(comp, D)
    print('final instances', Counter((pi, len(D[pi])) for pi, _, _ in inst).most_common(8), 'raw', len(raw), flush=True)
    json.dump({'D': [list(p) for p in D]}, open('cells_D2.json', 'w'))
