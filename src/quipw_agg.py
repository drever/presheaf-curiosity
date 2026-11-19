"""Evaluation of docs/prereg-quip-window.md (W1, W2, H1). Usage: python quipw_agg.py"""
import json
C = ('mux32_16bit', 'mux64_16bit', 'mux8_64bit'); r = {}
for c in C:
    for s in (0, 1):
        for n in (20, 40, 60):
            for h in (0, 1):
                d = json.load(open(f'../results/quipw_{c}_{s}_{n}_{h}.json'))
                ok = all(d[t][m]['verified'] for t in ('circuit', 'control') for m in ('empty', 'glue'))
                r[(c, s, n, h)] = d['gap']
                print(f"{c:12s} s{s} n{n:2d} hubs{h} circuit {d['circuit']['share_of_empty']:.3f} control {d['control']['share_of_empty']:.3f} gap {d['gap']:+.3f} "
                      f"tv {d['circuit']['split']['label_tv']:.2f} pat {d['circuit']['glue']['patterns']:2d} maxpat {max(d['circuit']['glue']['pattern_edges'] + [0]):2d} verified {ok}")
W1 = {(c, s): r[(c, s, 60, 0)] - r[(c, s, 20, 0)] for c in C[:2] for s in (0, 1)}
W2 = {(C[2], s): r[(C[2], s, 60, 0)] - r[(C[2], s, 20, 0)] for s in (0, 1)}
H1 = {(c, s): r[(c, s, 20, 1)] - r[(c, s, 20, 0)] for c in C[:2] for s in (0, 1)}
print('W1', {f'{c} s{s}': round(v, 3) for (c, s), v in W1.items()}, '->', 'holds' if all(v >= 0.10 for v in W1.values()) else 'fails')
print('W2', {f'{c} s{s}': round(v, 3) for (c, s), v in W2.items()}, '->', 'holds' if all(abs(v) < 0.10 for v in W2.values()) else 'fails')
print('H1', {f'{c} s{s}': round(v, 3) for (c, s), v in H1.items()}, '->', 'holds' if all(v >= 0.10 for v in H1.values()) else 'fails')
json.dump({'gaps': {' '.join(map(str, k)): v for k, v in r.items()}, 'W1': {f'{c} {s}': v for (c, s), v in W1.items()},
           'W2': {f'{c} {s}': v for (c, s), v in W2.items()}, 'H1': {f'{c} {s}': v for (c, s), v in H1.items()}}, open('../results/quipw_agg.json', 'w'), indent=1)
