"""Held-out test of the cell + lattice pipeline on c6288: cells and the lattice rule are learned on region A only
(gate-level windows -> glue dictionary -> fast merges -> cell; 4x4 block of A's quotient -> lattice rule) and applied to the disjoint region B."""
import sys, os, json, time, random
from collections import Counter, defaultdict, deque
import und
from und import *
from und3 import learn_h, dict_bits_h
from netlist import *
from core import Comp, LOG
import repair as RP
import merge as M
from latt import learn_rule, lattice_fit, rule_bits, raw_bits, gen_disps, _coords
und.SYMS = set(); R0 = 64; NN = 31; maxn = NN + 1
seed = int(sys.argv[1]); rng = random.Random(900 + seed); L = Labeler()
E = load_bench('c6288'); adj = defaultdict(set)
for u, v, _ in E: adj[u].add(v); adj[v].add(u)
nodes = sorted(adj); start = rng.choice(nodes); S = {start}; q = deque([start])
while q and len(S) < len(nodes) // 2:
    x = q.popleft()
    for y in sorted(adj[x]):
        if y not in S and len(S) < len(nodes) // 2: S.add(y); q.append(y)
EA = [e for e in E if e[0] in S and e[1] in S]; EB = [e for e in E if e[0] not in S and e[1] not in S]
def comp_of_edges(Es):
    ns = sorted({x for u, v, _ in Es for x in (u, v)}); ix = {x: i for i, x in enumerate(ns)}
    return Comp(len(ns), [(ix[u], L(l), ix[v]) for u, v, l in Es])
cA, cB = comp_of_edges(EA), comp_of_edges(EB)
wins = [to_comp(x, rng, NN) for x in windows_from(EA, rng, 40, nmax=20, labeler=L)]
t0 = time.time(); D0 = learn_h(wins, R0, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier'); print('D0', len(D0), round(time.time() - t0), 's', flush=True)
Dfull, recs, _ = M.learn_merges(cA, D0, maxe=24, rounds=6); print('merges', len(recs), flush=True)
res = {'seed': seed, 'edges_A': len(EA), 'edges_B': len(EB), 'merges': len(recs), 'pattern_edges': [len(p) for p in Dfull]}
def quotient_core(comp):
    inst, raw = cover_u(comp, Dfull); pis = {n for n in range(comp.n) if not comp.inn[n]}
    cnt = Counter(pi for pi, _, _ in inst); cell = max(cnt, key=lambda i: cnt[i] * (len(Dfull[i]) >= 15)) if any(len(Dfull[i]) >= 15 for i in cnt) else None
    memb = defaultdict(list)
    for k, (pi, ids, mm) in enumerate(inst):
        for u, n in mm: memb[n].append((k, pi, u))
    Eq = {}
    for n, Mb in memb.items():
        if n in pis: continue
        for i in range(len(Mb)):
            for j in range(i + 1, len(Mb)):
                a, b = Mb[i], Mb[j]
                if a[0] == b[0]: continue
                x, y = (a, b) if (a[1], a[2]) <= (b[1], b[2]) else (b, a); Eq[(x[0], y[0], (x[1], x[2], y[1], y[2]))] = 1
    core = sorted(k for k, (pi, _, _) in enumerate(inst) if pi == cell); ix = {x: j for j, x in enumerate(core)}
    return inst, raw, cell, [(ix[a], kk, ix[b]) for a, b, kk in Eq if a in ix and b in ix], len(core)
labid = {}
out = {}
for name, comp in (('A', cA), ('B', cB)):
    inst, raw, cell, es, n = quotient_core(comp)
    es = [(a, labid.setdefault(k, len(labid)), b) for a, k, b in es]
    out[name] = (es, n); res[name] = {'edges': len(comp.E), 'instances': len(inst), 'raw_edges': len(raw), 'cell_edges': len(Dfull[cell]) if cell is not None else None, 'cells': n, 'core_edges': len(es)}
    print(name, res[name], flush=True)
R = len(labid) + 1; esA, nA = out['A']
if nA >= 16 and esA:
    gens_full = learn_rule(esA); g2 = [set(ls) for ls, _ in gens_full[:2]]; print('A generators', [(ls, len(f)) for ls, f in gens_full[:4]])
    D2 = [(1, 0), (0, 1), (1, 1)][:len(gens_full)]; co, conf = _coords([set(ls) for ls, _ in gens_full], D2[:len(gens_full)], esA, nA)
    # 4x4 block in the middle of A's core, rule learned from block edges only
    us = [p[0] for p in co.values()]; vs = [p[1] for p in co.values()]; cu, cv = (min(us) + max(us)) // 2, (min(vs) + max(vs)) // 2
    blk = [x for x, (u, v) in co.items() if cu <= u < cu + 4 and cv <= v < cv + 4]; Sb = set(blk); bi = {x: j for j, x in enumerate(sorted(Sb))}
    bes = [(bi[a], l, bi[b]) for a, l, b in esA if a in Sb and b in Sb]; gens = learn_rule(bes); res['block'] = {'cells': len(blk), 'edges': len(bes), 'generators': [(ls, len(f)) for ls, f in gens]}
    print(res['block'], flush=True)
    if len(gens) >= 2:
        Dsp = gen_disps(gens, bes, len(blk)); rb = rule_bits(gens, R) + 6 * (len(gens) - 2); blockcomp = Comp(len(blk), bes)
        Dg = learn_h([blockcomp], R, 40, 40, False, mode='hier', topc=30, maxe=16, objective='hier'); rules = RP.learn([blockcomp], R, set(), K=40)
        rows = {}
        for name in ('A', 'B'):
            es, n = out[name]; fit = lattice_fit(gens, es, n, Dsp); nex = fit['extra'] + fit['miss'] + fit['conflicts'] + fit['orphans'] + fit['dup']
            c = Comp(n, es); rows[name] = {'cells': n, 'edges': len(es), 'raw': raw_bits(es, n, R), 'glue': total_u([c], Dg, R, 40, False), 'repair_reimpl': RP.cost([c], rules, R, set()), 'lattice_rule': rb + 2 * LOG(n + 1) + nex * (2 * LOG(n) + LOG(R)), 'exceptions': nex, 'fit': fit}
            print(name, rows[name], flush=True)
        res['rows'] = rows
json.dump(res, open(f'../results/heldout_lattice_{seed}.json', 'w'), default=str)
