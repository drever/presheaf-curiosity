"""Are the learned patterns a stable "basis" of the data, and how steep is their "spectrum"?   (lab notebook, section 14)

Loose analogy with PCA: components should be a property of the data, not of the sample (stability), and a few of them
should carry most of the effect (spectrum).

Set-up per seed: repaired split of c6288 into regions A and B (split.gate_walk_split). Four dictionaries with the usual
learner settings, each from 100 windows: A1 and A2 (two independent window draws of A), B1 (windows of B), and X from
another circuit (c880) as a reference for "different data". Fresh evaluation windows: 100 of A and 100 of B.

Stability measures for a pair of dictionaries (D, D'):
  shared      number of patterns with identical canonical form, and Jaccard index
  used_shared share of pattern-covered edges of the evaluation windows that D covers with patterns that also occur in D'
  cross       bits/window when the evaluation windows are coded with D' instead of D (interface costs, no dictionary cost)
Spectrum for A1: evaluation bits/window on B with the first k patterns in the order the learner added them, k = 0..K,
and the number of edges each pattern covers in the final cover.

Expectations, written before the first run:
  E1  A1 versus B1 is about as similar as A1 versus A2 (sampling noise explains the difference): used_shared within 10
      percentage points of each other.
  E2  used_shared(A1, B1) is at least 70%, and coding B with A1 costs at most 10% more than coding B with B1.
  E3  the dictionary from c880 shares little: used_shared(A1, X) below 30%.
  E4  the spectrum is steep: half of the total saving on B is reached with at most 3 patterns, 90% with at most 10.

Control (added 18 November 2026, expectations written before its first run): `python basis.py SEED rewired` runs the same
measurement on c6288 after a label- and degree-preserving rewiring (rewire() below): repeated swaps of the targets of two
edges with the same label (a->b, c->d  becomes  a->d, c->b), 20 swaps per edge, no self-loops and no repeated pairs.
Every node keeps its gate type, its in- and out-degree and its label counts; the cells of the multiplier are destroyed.
Expectations for the control, compared with the original circuit on the same seeds:
  C1  compression is much weaker: bits/window on B with the dictionary from A at least 30% higher.
  C2  the spectrum is flatter at the top but the first pattern still gives a large share (it is a two-edge NOR chain, which
      label statistics alone produce): k_for_90pct larger than in the original.
  C3  stability of the working core stays high (used_shared A1|B1 on B at least 80%), because small chains and stars recur
      in any graph with these labels and degrees. If C3 holds, the stability measured in section 14 is NOT evidence of
      cell structure, only the compression level and the large patterns are.
Usage: python basis.py SEED [rewired]   ->  ../results/basis_SEED.json or basis_rewired_SEED.json"""
import sys, json, random, collections
import und
from und import *
from und3 import learn_h, dict_bits_h
from netlist import *
from iface import total_iface
import split as SP
NN = 31; MAXN = 32; R = 64; seed = int(sys.argv[1]); N = 100; rewired = len(sys.argv) > 2 and sys.argv[2] == 'rewired'

from rewire import rewire
und.SYMS = set(); und.TWIN_MAX = 6; L = Labeler()
E0 = load_bench('c6288')
if rewired:
    E0, swaps = rewire(E0, random.Random(8900 + seed))
    assert collections.Counter(u for u, _, _ in E0) == collections.Counter(u for u, _, _ in load_bench('c6288'))
    assert collections.Counter((v, l) for _, v, l in E0) == collections.Counter((v, l) for _, v, l in load_bench('c6288'))
sp = SP.gate_walk_split(E0, random.Random(900 + seed)); rng = random.Random(7900 + seed)
other = [e for e in load_bench('c880') if not SP.is_input_edge(e)]
def win(es, k): return [to_comp(w, rng, NN) for w in windows_from(es, rng, k, nmax=20, labeler=L)]
tr = {'A1': win(sp['A'], N), 'A2': win(sp['A'], N), 'B1': win(sp['B'], N), 'X': win(other, N)}
ev = {'A': win(sp['A'], N), 'B': win(sp['B'], N)}
learn = lambda T: learn_h(T, R, 40, MAXN, False, mode='hier', topc=30, maxe=12, objective='hier')
D = {k: learn(v) for k, v in tr.items()}; keys = {k: [canon_u(p, False) for p in d] for k, d in D.items()}
bits = lambda cs, d: total_iface(cs, d, R, MAXN, False) / len(cs)

def usage(cs, d):
    """edges covered per pattern index in the greedy cover of the windows"""
    u = collections.Counter()
    for c in cs:
        for pi, ids, mm in cover_u(c, d)[0]: u[pi] += len(d[pi])
    return u

out = {'seed': seed, 'rewired': rewired, 'patterns': {k: len(d) for k, d in D.items()}, 'sizes': {k: sorted(len(p) for p in d) for k, d in D.items()},
       'dict_bits': {k: dict_bits_h(d, R, MAXN) for k, d in D.items()}, 'empty': {e: bits(cs, []) for e, cs in ev.items()}, 'pairs': {}, 'own': {}}
for a in D:
    for e, cs in ev.items(): out['own'][f'{a}_on_{e}'] = bits(cs, D[a])
for a, b, e in (('A1', 'A2', 'A'), ('A1', 'A2', 'B'), ('A1', 'B1', 'A'), ('A1', 'B1', 'B'), ('B1', 'A1', 'B'), ('A1', 'X', 'A'), ('X', 'A1', 'A')):
    sa, sb = set(keys[a]), set(keys[b]); u = usage(ev[e], D[a]); tot = sum(u.values())
    out['pairs'][f'{a}|{b}|on_{e}'] = {'shared': len(sa & sb), 'jaccard': len(sa & sb) / len(sa | sb), 'used_shared': sum(n for pi, n in u.items() if keys[a][pi] in sb) / tot if tot else None,
                                       'covered_share': tot / sum(len(c.E) for c in ev[e]), 'bits_with_first': bits(ev[e], D[a]), 'bits_with_second': bits(ev[e], D[b])}
d = D['A1']; curve = [bits(ev['B'], d[:k]) for k in range(len(d) + 1)]; u = usage(ev['B'], d); total = curve[0] - min(curve)
out['spectrum'] = {'heldout_bits_by_k': curve, 'pattern_sizes_in_order': [len(p) for p in d], 'edges_covered_by_pattern': [u.get(i, 0) for i in range(len(d))],
                   'k_for_half': next(k for k, v in enumerate(curve) if curve[0] - v >= 0.5 * total), 'k_for_90pct': next(k for k, v in enumerate(curve) if curve[0] - v >= 0.9 * total)}
print(json.dumps({'seed': seed, 'patterns': out['patterns'], 'pairs': {k: {x: round(y, 3) if isinstance(y, float) else y for x, y in v.items()} for k, v in out['pairs'].items()},
                  'k_half': out['spectrum']['k_for_half'], 'k_90': out['spectrum']['k_for_90pct'], 'curve': [round(x, 1) for x in curve]}), flush=True)
json.dump(out, open(f'../results/basis_rewired_{seed}.json' if rewired else f'../results/basis_{seed}.json', 'w'), indent=1)
