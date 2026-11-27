"""Evaluation of docs/prereg-slices.md (S1, S2, S3 and descriptive rows). Usage: python slices_agg.py"""
import json, os
C = ['ladder_mux4_16bit', 'ladder_mux8_16bit', 'ladder_mux16_16bit', 'ladder_mux32_16bit', 'ladder_mux64_16bit', 'mux8_64bit', 'mux8_128bit', 'barrel16', 'barrel32', 'barrel64']
R = {}
for c in C:
    for s in (0, 1):
        f = f'../results/slices_{c}_{s}.json'
        if not os.path.exists(f): print(c, s, 'not finished'); continue
        d = json.load(open(f)); R[(c, s)] = d
        ok = all(d[t][m]['verified'] for t in ('intact', 'shuffled', 'rewired', 'global_shuffle') for m in ('plain', 'decomposed')) and all(v['verified'] for v in d['forced'].values())
        sv = {t: d[t]['saving_share'] * 100 for t in ('intact', 'shuffled', 'rewired', 'global_shuffle')}
        att = {t: d[t]['decomposed']['parts'].get('copies', 0) for t in ('intact', 'shuffled')}
        fz = {k: round(v['parts'].get('copies', 0)) for k, v in d['forced'].items()}
        print(f"{c:20s} s{s} plain {d['intact']['plain']['bits']:8.0f} | saving intact {sv['intact']:5.1f}% shuffled {sv['shuffled']:5.1f}% rewired {sv['rewired']:5.1f}% global {sv['global_shuffle']:5.1f}% "
              f"| attach bits intact {att['intact']:6.0f} shuffled {att['shuffled']:6.0f} same choice {d['same_choice_intact_shuffled']} forced {fz} | verified {ok}")
m = lambda c, s, t: R[(c, s)][t]['saving_share'] * 100
k = 'ladder_mux16_16bit'
if all((k, s) in R for s in (0, 1)):
    S1 = all(m(k, s, 'intact') >= 10 and m(k, s, 'shuffled') >= 10 and m(k, s, 'rewired') <= 2 for s in (0, 1))
    S2 = all(m(k, s, 'intact') - m(k, s, 'shuffled') >= 1 for s in (0, 1))
    print('S1', 'holds' if S1 else 'fails', [(round(m(k, s, 'intact'), 1), round(m(k, s, 'shuffled'), 1), round(m(k, s, 'rewired'), 1)) for s in (0, 1)])
    print('S2', 'holds' if S2 else 'fails', [round(m(k, s, 'intact') - m(k, s, 'shuffled'), 2) for s in (0, 1)])
L = [c for c in C if c.startswith('ladder')]
if all((c, 0) in R for c in L):
    iv = {c: m(c, 0, 'intact') for c in L}
    print('S3 intact savings (seed-independent):', {c.split('_')[1]: round(v, 1) for c, v in iv.items()},
          '->', 'holds (mux32 below mux16 and mux64)' if iv['ladder_mux32_16bit'] < min(iv['ladder_mux16_16bit'], iv['ladder_mux64_16bit']) else 'fails')
json.dump({f'{c} {s}': {t: R[(c, s)][t]['saving_share'] for t in ('intact', 'shuffled', 'rewired', 'global_shuffle')} for (c, s) in R}, open('../results/slices_agg.json', 'w'), indent=1)
