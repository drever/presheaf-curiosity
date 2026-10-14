import sys
sys.argv = ['e30.py', 'syn', sys.argv[1] if len(sys.argv) > 1 else '0']
src = open('e30.py').read().split("res['k_dict']")[0].replace("D = learn_h(", "D = [] if True else learn_h(")
exec(src)
from core import order_pattern
D = [tuple(order_pattern(fe)) for k, fe, pairs in frames] + [tuple(order_pattern([(s, r, t) for s, t, r in ge])) for m, ge in gadgets]
lib = {}; H = []
for fi, (k, fe, pairs) in enumerate(frames):
    for (a, b) in pairs:
        p, q = min(a, b), max(a, b); fil = set(); prob = {}
        for gi, (m, ge) in enumerate(gadgets):
            pat = [(s, r2, t) for s, t, r2 in [(x, y, r) for x, y, r in ge]]
            if a > b: sw = {0: 1, 1: 0}; pat = [(sw.get(s, s), r2, sw.get(t, t)) for s, r2, t in pat]
            key = ('g', fi, p, q, gi); lib[key] = pat; fil.add(key); prob[('f', key)] = 0.85 / 6
        prob[('empty',)] = 0.15; prob[('other',)] = 0.001
        H.append({'key': (fi, p, q), 'fil': fil, 'prob': prob, 'nopt': 8})
# Hinweis: ge-Kanten sind (s,t,r) -> Muster (s,r,t)
lib = {k: [(s, r, t) for (s, r, t) in v] for k, v in lib.items()}
for mode in ('iface', 'rel'):
    g = H2.total(tests['in'], D, [], {}, R, mode, 5); h = H2.total(tests['in'], D, H, lib, R, mode, 5)
    print(mode, 'oracle dict glue', round(g, 1), 'holes', round(h, 1))
