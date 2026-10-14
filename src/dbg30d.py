import sys, collections, os
os.environ['NTR'] = '120'; os.environ['KD'] = '80'
sys.argv = ['e30.py', 'syn', '0']
src = open('e30.py').read().split("res['k_dict']")[0]
exec(src)
cands, lib = H2.find_candidates(train, D, R, 5)
print('cands', len(cands), 'lib', len(lib))
cands = sorted(cands, key=lambda h: -h['score'])[:8]
base = H2.total(train, D, [], lib, R, 'iface', 5) * len(train)
print('base', round(base))
Vs = {i: len({x for a, _, b in D[i] for x in (a, b)}) for i in range(len(D))}
for h in cands:
    t = H2.total(train, D, [h], lib, R, 'iface', 5) * len(train)
    print(h['key'], len(D[h['key'][0]]), 'nfil', len(h['fil']), 'score', h['score'], 'probs', {str(o)[:10]: round(p, 2) for o, p in h['prob'].items() if o[0] != 'f'}, 'delta', round(t - base), 'dict', round(H2.hole_bits(h, len(D), Vs[h['key'][0]])))
