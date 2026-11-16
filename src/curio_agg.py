"""Evaluation of the curiosity experiment exactly as fixed in docs/prereg-curiosity.md. Usage: python curio_agg.py"""
import json, glob, os, statistics as st
runs = {}
for f in glob.glob('../results/curio_[0-9]_*_*.json'):
    d = json.load(open(f)); runs[(d['seed'], d['cond'], d['arm'])] = d
seeds = sorted({k[0] for k in runs}); out = {}
def curve(s, c, a): return [r['heldout_bits_per_window'] for r in runs[(s, c, a)]['rounds']]
def auc(s, c, a, lo=1, hi=12): return st.mean(curve(s, c, a)[lo - 1:hi])
def paired(c, a, b, lo=1, hi=12):
    ss = [s for s in seeds if (s, c, a) in runs and (s, c, b) in runs]; d = [auc(s, c, a, lo, hi) - auc(s, c, b, lo, hi) for s in ss]
    return {'seeds': ss, 'diff_per_seed': [round(x, 2) for x in d], 'mean': round(st.mean(d), 2), 'positive': sum(x > 0 for x in d), 'n': len(d)}
for c in ('clean', 'noise'):
    print(f'== {c} pool: mean held-out bits/window over rounds 1-12 (AUC), per seed')
    for a in ('random', 'gain', 'surprise', 'oracle'):
        v = [(s, auc(s, c, a)) for s in seeds if (s, c, a) in runs]
        if v: print(f'  {a:9s}', ' '.join(f'{x:6.1f}' for _, x in v), '| mean', round(st.mean(x for _, x in v), 1), '| round 12:', ' '.join(f'{curve(s, c, a)[-1]:6.1f}' for s, _ in v))
    out[c] = {'random_minus_gain': paired(c, 'random', 'gain'), 'surprise_minus_gain': paired(c, 'surprise', 'gain'), 'random_minus_surprise': paired(c, 'random', 'surprise'),
              'random_minus_gain_rounds1to4': paired(c, 'random', 'gain', 1, 4), 'random_minus_gain_rounds5to12': paired(c, 'random', 'gain', 5, 12)}
    for k, v in out[c].items(): print('  ', k, v)
    print('   mean curve per arm:')
    for a in ('random', 'gain', 'surprise', 'oracle'):
        ss = [s for s in seeds if (s, c, a) in runs]
        if ss: print(f'     {a:9s}', ' '.join(f'{st.mean(curve(s, c, a)[r] for s in ss):6.1f}' for r in range(12)), f'(n={len(ss)})')
print('== noise pool: unlearnable windows among the 60 chosen (pool share 30% = 18 expected at random)')
out['noise_chosen'] = {}
for a in ('random', 'gain', 'surprise'):
    v = [sum(r['chosen_noise'] for r in runs[(s, 'noise', a)]['rounds']) for s in seeds if (s, 'noise', a) in runs]; out['noise_chosen'][a] = v; print(f'  {a:9s}', v)
h1 = out['clean']['random_minus_gain']; h2 = out['noise']['surprise_minus_gain']
out['H1_gain_beats_random_clean'] = h1['mean'] > 0 and h1['positive'] >= 4
out['H2_gain_beats_surprise_noise'] = h2['mean'] > 0 and h2['positive'] >= 4 and st.mean(out['noise_chosen']['gain']) < st.mean(out['noise_chosen']['surprise'])
print('H1 (gain beats random, clean pool):', out['H1_gain_beats_random_clean']); print('H2 (gain beats surprise, pool with unlearnable windows):', out['H2_gain_beats_surprise_noise'])
json.dump(out, open('../results/curio_agg.json', 'w'), indent=1)
