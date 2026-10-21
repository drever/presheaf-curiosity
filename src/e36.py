"""E3 Groessentest: Zelle (18 Kanten) auf eigenem Multiplizierer k=16 gelernt (schnelle Zellbildung), Quotient, Gitterregel aus 4x4-Block, Anwendung auf k=16, 24, 32."""
import sys, os, json, time, random, pickle
from collections import Counter, defaultdict, deque
import netlist; netlist.HB = '/tmp/claude-0/genbench/'
import und
from und import *
from und3 import learn_h, dict_bits_h
from netlist import *
from core import Comp, LOG
import repair as RP
from e34 import comp_of
from latt import learn_rule, lattice_fit, rule_bits, raw_bits, gen_disps
und.SYMS = set(); K0 = 16; TESTS = [24, 32]
Dfull, recs, D0 = pickle.load(open(f'../results/e35_cells_{K0}.pkl', 'rb'))
_, Lids = pickle.load(open(f'../results/e35_D0_{K0}.pkl', 'rb'))
L = Labeler(); comps = {k: comp_of(f'mul{k}', L) for k in [K0] + TESTS}
def qfrom(comp, inst, raw, skip):
    memb = defaultdict(list)
    for k, (pi, ids, mm) in enumerate(inst):
        for u, n in mm: memb[n].append((k, pi, u))
    E = {}
    for n, M in memb.items():
        if n in skip: continue
        for i in range(len(M)):
            for j in range(i + 1, len(M)):
                a, b = M[i], M[j]
                if a[0] == b[0]: continue
                x, y = (a, b) if (a[1], a[2]) <= (b[1], b[2]) else (b, a); E[(x[0], y[0], (x[1], x[2], y[1], y[2]))] = 1
    return [(a, b, k) for (a, b, k) in E]
res = {}; core_es = {}; labid = {}
t0 = time.time()
for k, c in comps.items():
    inst, raw = cover_u(c, Dfull); pis = {n for n in range(c.n) if not c.inn[n]}
    cell = max(range(len(Dfull)), key=lambda i: sum(1 for pi, _, _ in inst if pi == i) * (len(Dfull[i]) >= 15))
    Q = qfrom(c, inst, raw, pis); core = {i for i, (pi, _, _) in enumerate(inst) if pi == cell}
    es = [(a, labid.setdefault(kk, len(labid)), b) for a, b, kk in Q if a in core and b in core]
    ix = {x: j for j, x in enumerate(sorted(core))}; es = [(ix[a], l, ix[b]) for a, l, b in es]
    core_es[k] = (es, len(core)); res[k] = {'cell_edges': len(Dfull[cell]), 'cells': len(core), 'quotient_edges': len(Q), 'core_edges': len(es), 'rest_edges': len(Q) - len(es), 'raw_gate_edges': len(raw), 'cover_s': round(time.time() - t0)}
    print(k, res[k], flush=True)
R = len(labid) + 1
# Regel aus einem 4x4-Block des k=16-Kerns
es16, n16 = core_es[K0]; gens_full = learn_rule(es16); print('generators on full k=16 core', [(ls, len(f)) for ls, f in gens_full[:4]])
g2 = gens_full[:2]; gl = [set(ls) for ls, _ in g2]; step = [defaultdict(list), defaultdict(list)]
for a, l, b in es16:
    for g in range(2):
        if l in gl[g]: step[g][a].append(b)
co = {}
srcs = sorted(range(n16), key=lambda x: (sum(1 for g in range(2) for ys in step[g].values() if x in ys), x)); co[srcs[0]] = (0, 0); q = deque([srcs[0]]); D2 = [(1, 0), (0, 1)]
back = [defaultdict(list), defaultdict(list)]
for g in range(2):
    for a, ys in step[g].items():
        for b in ys: back[g][b].append(a)
while q:
    x = q.popleft(); c = co[x]
    for g in range(2):
        for y in step[g][x]:
            if y not in co: co[y] = (c[0] + D2[g][0], c[1] + D2[g][1]); q.append(y)
        for y in back[g][x]:
            if y not in co: co[y] = (c[0] - D2[g][0], c[1] - D2[g][1]); q.append(y)
us = [p[0] for p in co.values()]; vs = [p[1] for p in co.values()]; print('coords', len(co), 'bbox', min(us), max(us), min(vs), max(vs))
t = 4; out = {'cells': res}
cu, cv = (min(us) + max(us)) // 2, (min(vs) + max(vs)) // 2
blk = [x for x, (u, v) in co.items() if cu <= u < cu + t and cv <= v < cv + t]; S = set(blk); bi = {x: j for j, x in enumerate(sorted(S))}
bes = [(bi[a], l, bi[b]) for a, l, b in es16 if a in S and b in S]
gens = learn_rule(bes); print('block', len(blk), 'edges', len(bes), 'generators', [(ls, len(f)) for ls, f in gens]); rb = rule_bits(gens, R) + 6 * (len(gens) - 2)
Dsp = gen_disps(gens, bes, len(blk)); print('displacements from block', Dsp); same = sorted(map(sorted, [ls for ls, _ in gens])) == sorted(map(sorted, [ls for ls, _ in gens_full])); print('rule equals full-core generators:', same, 'rule bits', round(rb, 1))
blockcomp = Comp(len(blk), bes)
D = learn_h([blockcomp], R, 40, 40, False, mode='hier', topc=30, maxe=16, objective='hier'); rules = RP.learn([blockcomp], R, set(), K=40)
rows = []
for k in [K0] + TESTS:
    es, n = core_es[k]; fit = lattice_fit(gens, es, n, Dsp); nex = fit['extra'] + fit['miss'] + fit['conflicts'] + fit['orphans'] + fit['dup']
    rec = rb + 2 * LOG(2 * k) + nex * (2 * LOG(n) + LOG(R)) + (1 if nex else 0)
    c = Comp(n, es); t1 = time.time(); gl_ = total_u([c], D, R, 40, False); rp = RP.cost([c], rules, R, set())
    row = {'k': k, 'cells': n, 'edges': len(es), 'raw': raw_bits(es, n, R), 'glue': gl_, 'repair': rp, 'recursive': rec, 'exceptions': nex, 'fit': fit}; rows.append(row); print(row, flush=True)
out['rows'] = rows; out['rule_bits'] = rb; out['dict_glue'] = dict_bits_h(D, R, 40); out['dict_repair'] = RP.dict_cost(rules, R); out['rule_stable'] = same
json.dump(out, open('../results/e36.json', 'w'), default=str)
