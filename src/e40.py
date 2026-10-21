import json, random, time
from collections import Counter
from qembed import *
from und3 import learn_h, dict_bits_h
from core import Comp, LOG
import repair as RP
from netlist import windows_from, to_comp
out = {}; qs = {}
labid = {}
for k in (16, 24, 32):
    t0 = time.time(); Q, ptype, N, raw = quotient(k); E = embed(Q, ptype, N); nrect, shear = rectangles(E['coord'], ptype)
    qs[k] = (Q, N)
    out[k] = {'nodes': N, 'quotient_edges': len(Q), 'bundles': E['bundles'], 'exceptions': E['exceptions'], 'collisions': E['collisions'], 'unplaced': E['unplaced'], 'rectangles': nrect, 'shear': shear, 'types': len(set(ptype.values())), 'time': round(time.time() - t0)}
    print(k, out[k], flush=True)
# Kosten: Beschreibung der Einbettung vs. rohe Kanten / Kleben / RePair (auf Fenstern des k=16-Quotienten gelernt)
R = 0
for k in qs:
    for a, b, kk in qs[k][0]: labid.setdefault(kk, len(labid))
R = len(labid) + 1
def comp_q(k): Q, N = qs[k]; return Comp(N, [(a, labid[kk], b) for a, b, kk in Q])
rng = random.Random(3); L = Labeler(); Q16, N16 = qs[16]
wins = windows_from([(a, b, ('x', labid[kk])) for a, b, kk in Q16], rng, 40, nmax=16, emin=6, labeler=L)
tr = [to_comp(w, random.Random(4), 31) for w in wins]; D = learn_h(tr, R, 40, 32, False, mode='hier', topc=30, maxe=16, objective='hier'); rules = RP.learn(tr, R, set(), K=60)
Lw = Labeler(); Lw.ids = dict(L.ids)
for k in qs:
    Q, N = qs[k]; cq = Comp(N, [(a, Lw(('x', labid[kk])), b) for a, b, kk in Q]); n = LOG(N)
    o = out[k]; o['raw'] = len(Q) * (2 * n + LOG(R)); o['glue'] = total_u([cq], D, R, 32, False); o['repair'] = RP.cost([cq], rules, R, set())
    o['embedding_model'] = o['bundles'] * (2 * LOG(o['types']) + 2 * LOG(8) + 6) + o['rectangles'] * (LOG(o['types']) + 4 * LOG(2 * k + 4)) + o['exceptions'] * (2 * n + LOG(R)) + 55
    print(k, {a: (round(b) if isinstance(b, float) else b) for a, b in o.items() if a in ('raw', 'glue', 'repair', 'embedding_model', 'rectangles', 'exceptions')}, flush=True)
out['dict_glue'] = dict_bits_h(D, R, 32); out['dict_repair'] = RP.dict_cost(rules, R)
json.dump(out, open('../results/e40.json', 'w'), default=str)
