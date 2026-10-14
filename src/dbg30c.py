import sys, collections
sys.argv = ['e30.py', 'syn', '0']
src = open('e30.py').read().split("res['k_dict']")[0]
exec(src)
from holes import get_units
for pi_target in (30, 19):
    ccnt = collections.defaultdict(collections.Counter)
    for c in train:
        units, raw = get_units(c, D)
        for A in units:
            if A.pi != pi_target: continue
            comps = H2.components(c, A.ids, A.V); ps = sorted(A.mp)
            for i, p in enumerate(ps):
                for q in ps[i+1:]:
                    F = H2.filler_of(comps, A.mp[p], A.mp[q], 5)
                    if F is None: ccnt[(p,q)]['big'] += 1
                    elif not F: ccnt[(p,q)]['empty'] += 1
                    else: ccnt[(p,q)][H2.filler_key(H2.filler_pattern(F, A.mp[p], A.mp[q]), R)[0][:4]] += 1
    print('pattern', pi_target, len(D[pi_target]), 'edges')
    for k, v in sorted(ccnt.items(), key=lambda kv: -sum(n for o,n in kv[1].items() if o not in ('empty','big')))[:4]: print(' ', k, dict(v.most_common(6)))
