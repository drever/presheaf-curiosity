"""Evaluation of docs/prereg-mux-ladder.md (L1, L2 and descriptive rows). Usage: python ladder_agg.py"""
import json, os
NS = (2, 4, 8, 16); CAPS = (12, 32, 64); FIT = {4: 32, 8: 32, 16: 64}
g = {}; rows = []
for N in NS:
    for c in CAPS:
        for s in (0, 1):
            f = f'../results/ladder_ladder_mux{N}_16bit_{s}_60_{c}.json'
            if not os.path.exists(f): print(f'mux{N} cap {c} seed {s}: not finished'); continue
            d = json.load(open(f))
            ok = all(d[t][m]['verified'] for t in ('circuit', 'control') for m in ('empty', 'glue'))
            g[(N, c, s)] = d['gap']
            rows.append({'N': N, 'cap': c, 'seed': s, 'circuit': d['circuit']['share_of_empty'], 'control': d['control']['share_of_empty'], 'gap': d['gap'],
                         'max_pattern_edges': max(d['circuit']['glue']['pattern_edges'] + [0]), 'patterns': d['circuit']['glue']['patterns'],
                         'label_tv': d['circuit']['split']['label_tv'], 'times': d['times'], 'verified': ok})
            r = rows[-1]
            print(f"mux{N:<2d} cap {c:2d} seed {s}: circuit {r['circuit']:.3f} control {r['control']:.3f} gap {r['gap']:+.3f} "
                  f"maxpat {r['max_pattern_edges']:2d} pat {r['patterns']:2d} tv {r['label_tv']:.2f} t {r['times']} verified {ok}")
def m(N, c):
    v = [g[(N, c, s)] for s in (0, 1) if (N, c, s) in g]
    return sum(v) / len(v) if len(v) == 2 else None
L1 = {N: (m(N, FIT[N]) - m(N, 12)) if None not in (m(N, FIT[N]), m(N, 12)) else None for N in FIT}
L2 = {N: (m(N, 64) - m(N, 12)) if None not in (m(N, 64), m(N, 12)) else None for N in FIT}
print('mean gap by N and cap:', {f'mux{N} cap{c}': round(m(N, c), 3) for N in NS for c in CAPS if m(N, c) is not None})
print('L1 (gap at fitting cap - gap at 12, >= +0.10):', {N: round(v, 3) for N, v in L1.items() if v is not None},
      '->', 'holds' if all(v is not None and v >= 0.10 for v in L1.values()) else 'fails')
print('L2 (|gap at 64 - gap at 12| < 0.05):', {N: round(v, 3) for N, v in L2.items() if v is not None},
      '->', 'holds' if all(v is not None and abs(v) < 0.05 for v in L2.values()) else 'fails')
json.dump({'rows': rows, 'L1': L1, 'L2': L2}, open('../results/ladder_agg.json', 'w'), indent=1)
