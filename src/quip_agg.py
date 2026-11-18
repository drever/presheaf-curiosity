"""Evaluation of the Quip measurement against P1-P5 of docs/prereg-quip.md. Usage: python quip_agg.py"""
import json, glob, os
from quip import CIRCUITS
rows = {}
for c in CIRCUITS:
    for f in glob.glob(f'../results/quip_{c}_[0-9].json'):
        d = json.load(open(f))
        if 'circuit' in d and 'control' in d: rows[(c, d['seed'])] = d
seeds = sorted({s for _, s in rows}); res = {'P1': [], 'P2': [], 'P3': [], 'P4': [], 'table': []}
print(f"{'circuit':16s} seed |  empty   glue  product  holes | glue/empty  control glue/empty | factors holes | shared use circuit/control | verified")
for c in CIRCUITS:
    for s in seeds:
        if (c, s) not in rows: continue
        d = rows[(c, s)]; a = d['circuit']; k = d['control']
        g = a['glue']['data_bits_per_window']; p = a['product']['data_bits_per_window']; h = a['holes']['data_bits_per_window']
        ver = all(x['verified'] for x in (a['empty'], a['glue'], a['product'], a['holes'], k['empty'], k['glue']))
        tv = a['split']['label_tv']
        print(f"{c:16s} {s:4d} tv={tv:.2f} | {a['empty']['data_bits_per_window']:6.1f} {g:6.1f} {p:7.1f} {h:6.1f} | {a['share_of_empty']:9.3f}  {k['share_of_empty']:17.3f} | {a['product']['factors']:7d} {a['holes']['holes']:5d} | {a['shared_use'] or 0:8.3f} / {k['shared_use'] or 0:5.3f} | {ver}")
        res['table'].append({'circuit': c, 'seed': s, 'empty': a['empty']['data_bits_per_window'], 'glue': g, 'product': p, 'holes': h, 'share': a['share_of_empty'], 'control_share': k['share_of_empty'],
                             'factors': a['product']['factors'], 'holes_found': a['holes']['holes'], 'shared_use': a['shared_use'], 'control_shared_use': k['shared_use'], 'verified': ver, 'label_tv': tv,
                             'dict_bits': {m: a[m]['dict_bits'] for m in ('glue', 'product', 'holes')}})
        res['P1'].append(k['share_of_empty'] - a['share_of_empty'] >= 0.10)
        res['P2'].append((a['product']['factors'] > 0, (g - p) / g))
        res['P3'].append((a['holes']['holes'] > 0, (g - h) / g))
        if s == 0: res['P4'].append((a['shared_use'] or 0) > (k['shared_use'] or 0))
n = len(res['P1'])
print(f"P1 control at least 10 points worse in every circuit and seed: {sum(res['P1'])}/{n} -> {'holds' if all(res['P1']) else 'fails'}")
fac = {t['circuit'] for t in res['table'] if t['factors'] > 0}; mx = max(x for _, x in res['P2'])
print(f"P2 factors selected in {len(fac)} circuits {sorted(fac)}; largest saving of product over gluing {mx:.1%} -> {'holds' if len(fac) <= 2 and mx <= 0.05 else 'fails'}")
hc = {t['circuit'] for t in res['table'] if t['holes_found'] > 0}; mh = max(x for _, x in res['P3'])
print(f"P3 holes found in {sorted(hc)}; largest saving of holes over gluing {mh:.1%} -> {'holds' if hc and mh <= 0.05 else 'fails'}")
print(f"P4 shared use higher on circuit than control (seed 0): {sum(res['P4'])}/{len(res['P4'])} -> {'holds' if sum(res['P4']) >= 8 else 'fails'}")
for f in sorted(glob.glob('../results/quip_size_*.json')):
    d = json.load(open(f)); print('P5', os.path.basename(f), {n: round(d[n]['ratio'], 3) for n in ('barrel32', 'barrel64')}, '->', 'holds' if all(d[n]['ratio'] <= 1.10 for n in ('barrel32', 'barrel64')) else 'fails')
json.dump(res, open('../results/quip_agg.json', 'w'), indent=1)
