import sys, collections
sys.argv = ['e30.py', 'syn', '0']
src = open('e30.py').read().split("res['k_dict']")[0]
exec(src)
cands, lib = H2.find_candidates(train, D, R, MAXF)
print('cands', len(cands), 'lib', len(lib))
from holes import get_units
cnt = collections.Counter()
for c in train:
    units, raw = get_units(c, D)
    for A in units:
        if len(D[A.pi]) >= 4: cnt[A.pi] += 1
print('frame-ish instances', sum(cnt.values()), 'patterns', len(cnt), [(i, len(D[i]), n) for i, n in cnt.most_common(8)])
ccnt = collections.defaultdict(collections.Counter)
for c in train:
    units, raw = get_units(c, D)
    for A in units:
        if A.pi != 30: continue
        ps = sorted(A.mp)
        for i, p in enumerate(ps):
            for q in ps[i+1:]:
                a, b = A.mp[p], A.mp[q]; F = H2.filler_of(H2.components(c, A.ids, A.V), a, b, 5)
                if F is None: ccnt[(p,q)]['big'] += 1
                elif not F: ccnt[(p,q)]['empty'] += 1
                else: ccnt[(p,q)][H2.filler_key(H2.filler_pattern(F, a, b), R)[0][:6]] += 1
for k, v in sorted(ccnt.items(), key=lambda kv: -sum(kv[1].values()))[:30]:
    if len(v) > 1 and not (len(v)==1): print(k, dict(v.most_common(5)))
