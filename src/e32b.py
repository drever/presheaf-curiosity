"""E3 Teil 2: (a) Stoerungen im Gitter, (b) ganze Quotientengraph (Kern + Rand) gegen Glue/RePair, die auf Fenstern des ganzen Graphen trainiert sind."""
import sys, json, random, pickle, time
from e32 import *
from netlist import windows_from, to_comp, Labeler
t = 4; rng = random.Random(7)
train_nodes = block_nodes(2, 2 + t, 2, 2 + t); tes, tn = induced(train_nodes); gens = learn_rule(tes); rb = rule_bits(gens)
# Verschiebungen der Erzeuger in (u,v) (Einbettung der abstrakten Regel in den Block = Aufgabe des Kodierers)
disp = []
for ls, f in gens:
    ds = Counter((uv[inv_b][0] - uv[a][0], uv[inv_b][1] - uv[a][1]) for a_, b_ in [] for inv_b in [])    # Platzhalter
nodes_all = list(uv); orig = {k: x for k, x in enumerate(sorted(train_nodes))}
# Verschiebung ueber die Originalknoten: lerne Edge-Label -> Verschiebung aus dem Trainingsblock
labdisp = {}
S = set(train_nodes)
for a, l, b in EL:
    if a in S and b in S and a in uv and b in uv: labdisp.setdefault(l, Counter())[(uv[b][0] - uv[a][0], uv[b][1] - uv[a][1])] += 1
gdisp = [Counter(d for l in ls for d in labdisp[l].elements()).most_common(1)[0][0] for ls, _ in gens]
print('generator displacements (u,v):', gdisp)
glabels = [set(ls) for ls, _ in gens]
def predicted(nodeset):
    P = set()
    for g, d in enumerate(gdisp):
        for x in nodeset:
            u, v = uv[x]; y = inv.get((u + d[0], v + d[1]))
            if y is not None and y in nodeset:
                for l in glabels[g]: P.add((x, l, y))
    return P
def exceptions(nodeset, edges):
    P = predicted(nodeset); Ed = {(a, l, b) for a, l, b in edges if a in nodeset and b in nodeset}
    return len(Ed - P), len(P - Ed)
out = {}
# (a) Stoerung: m=13 Block, p Kanten loeschen / p Kanten falsch verdrahten (Label vertauscht -> ein Extra + eine fehlende)
m = 13; nodes = set(block_nodes(1, 1 + m, 1, 1 + m)); es_all = [e for e in EL if e[0] in nodes and e[2] in nodes]
rows = []
for p in (0, 2, 5, 10, 20, 50, 100, 200):
    for rep in range(3):
        es = list(es_all); rng.shuffle(es); es = es[p:]            # p Kanten geloescht
        ex, mi = exceptions(nodes, es); n = len(nodes)
        ix = {x: k for k, x in enumerate(sorted(nodes))}; c = Comp(n, [(ix[a], l, ix[b]) for a, l, b in es])
        D = learn_h([comp_of(train_nodes)], R, 40, 40, False, mode='hier', topc=30, maxe=16, objective='hier') if p == 0 and rep == 0 else D
        rec = rb + 2 * LOG(m + 1) + (ex + mi) * (2 * LOG(n) + LOG(R)) + 1
        gl = total_u([c], D, R, 40, False)
        rows.append({'deleted': p, 'extra': ex, 'missing': mi, 'recursive': rec, 'glue': gl, 'raw': raw_bits(es, n)})
    print(rows[-1], flush=True)
out['perturb'] = rows
# (b) ganzer Quotient
Q = Comp(nsup, EL); coreset = set(uv)
core_es = [e for e in EL if e[0] in coreset and e[2] in coreset]; rest = [e for e in EL if not (e[0] in coreset and e[2] in coreset)]
ex, mi = exceptions(coreset, EL)
rec = rb + 2 * LOG(15) + 2 * LOG(15) * (1 if len(coreset) < 196 else 0) + (ex + mi) * (2 * LOG(nsup) + LOG(R)) + len(rest) * (2 * LOG(nsup) + LOG(R))
print('core exceptions', ex, mi, 'rest edges', len(rest), 'total edges', len(EL))
L = Labeler(); ELw = [(a, b, ('x', l)) for a, l, b in EL]; EL2 = [(a, L(('x', l)), b) for a, l, b in EL]; wins = windows_from(ELw, random.Random(3), 40, nmax=16, emin=6, labeler=L)
# windows_from vergibt eigene Label-IDs; Rueckabbildung egal fuer Kosten (nur Gleichheit zaehlt)
trw = [to_comp(w, random.Random(4), 31) for w in wins]
t0 = time.time(); Dw = learn_h(trw, R, 40, 32, False, mode='hier', topc=30, maxe=16, objective='hier'); print('glue dict windows', len(Dw), time.time() - t0, flush=True)
Qc = Comp(nsup, EL2)
t0 = time.time(); glQ = total_u([Qc], Dw, R, 32, False); print('glue whole Q', glQ, time.time() - t0, flush=True)
restc = Comp(nsup, [e2 for e, e2 in zip(EL, EL2) if not (e[0] in coreset and e[2] in coreset)]); glrest = total_u([restc], Dw, R, 32, False)
rules = RP.learn(trw, R, set(), K=60); rpQ = RP.cost([Qc], rules, R, set())
out['whole'] = {'raw': raw_bits(EL, nsup), 'glue_windows': glQ, 'glue_dict': dict_bits_h(Dw, R, 32), 'repair_windows': rpQ, 'repair_dict': RP.dict_cost(rules, R), 'recursive_plus_raw_rest': rec, 'rest_edges': len(rest), 'glue_rest': glrest, 'hybrid_recursive_core_plus_glue_rest': rb + 2 * LOG(15) + 2 * LOG(15) + glrest, 'core_edges': len(core_es)}
print(out['whole'])
json.dump(out, open('../results/e32b.json', 'w'), default=str)
