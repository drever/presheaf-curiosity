"""Rand des Quotienten: Glue/RePair auf Fenstern nur des Rands trainiert (Obergrenze fuer 'Kern per Regel + Rand per Kleben')."""
import pickle, random, json, time
from collections import defaultdict
from e32 import *
from netlist import windows_from, to_comp, Labeler
core = set(uv); L = Labeler()
EL2 = [(a, L(('x', l)), b) for a, l, b in EL]
restE = [(a, l, b) for a, l, b in EL2 if not (a in core and b in core)]; restraw = [(a, b, ('x', 0)) for a, l, b in restE]
RR = 120
out = {}
for seed in (0, 1, 2):
    rng = random.Random(seed)
    # Fenster nur aus Randkanten (Labels erhalten)
    Er = [(a, b, l) for a, l, b in restE]
    # windows_from erwartet (u, v, labelkey); Labeler ist identisch auf int-Labels -> direkt ('x', l)
    wins = windows_from([(a, b, ('y', l)) for a, b, l in Er], rng, 40, nmax=16, emin=6, labeler=Labeler())
    tr = [to_comp(w, random.Random(seed + 10), 31) for w in wins]
    t0 = time.time(); Dw = learn_h(tr, RR, 40, 32, False, mode='hier', topc=30, maxe=16, objective='hier')
    # Randgraph als Comp mit denselben Label-IDs wie die Fenster (neuer Labeler im Fensterlauf -> IDs in Reihenfolge des Auftretens; Rueckabbildung ueber Labeler2)
    L2 = Labeler(); _ = windows_from([(a, b, ('y', l)) for a, b, l in Er], random.Random(seed), 40, nmax=16, emin=6, labeler=L2)
    rc = Comp(nsup, [(a, L2(('y', l)), b) for a, l, b in restE]) if True else None
    gl = total_u([rc], Dw, RR, 32, False)
    rules = RP.learn(tr, RR, set(), K=60); rp = RP.cost([rc], rules, RR, set())
    out[seed] = {'glue_rest_trained_on_rest': gl, 'glue_dict': dict_bits_h(Dw, RR, 32), 'repair_rest': rp, 'repair_dict': RP.dict_cost(rules, RR), 'k': len(Dw), 'raw_rest': len(restE) * (2 * LOG(nsup) + LOG(RR)), 'rest_edges': len(restE)}
    print(seed, out[seed], flush=True)
json.dump(out, open('../results/e33b.json', 'w'))
