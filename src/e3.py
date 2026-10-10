import sys, json, time, random, logging
logging.Logger.__call__ = lambda self: self
import und
from und import *
import e2
from e2 import R, maxn, NS, NTEST, P, make_world, gen_comp
from gm_kg import to_nx, pat_edges
from skmine.graph.graphmdl.graph_mdl import GraphMDL
from core import order_pattern, normalize
from mol_big import gspan_mol
from mol_sel import greedy_select
from mol_subdue import run_subdue

def uniq(ps):
    D = []; s = set()
    for p in ps:
        kk = canon_u(p, True)
        if kk not in s: s.add(kk); D.append(p)
    return D

def main(world, seed, tout):
    und.SYMS = set(); sym = world == 'sym'
    rng = random.Random(1000 + seed); perm, motifs, nrel = make_world(rng, sym)
    allc = [gen_comp(rng, perm, motifs, nrel, sym) for _ in range(max(NS) + NTEST)]
    test = allc[max(NS):]; out = {'world': world, 'seed': seed, 'res': {}}
    for n in NS:
        train = allc[:n]; res = {}
        def ev(nm, D, tm): res[nm] = {'k': len(D), 'test': total_u(test, D, R, maxn, False) / len(test), 'time': tm}
        t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.10 * n)), 8, f'/tmp/e3_{world}_{seed}_{n}.gsp'); ev('gspan_mdl30', greedy_select(train, C, R, maxn, 20, 30), time.time() - t0)
        t0 = time.time(); pats, _ = run_subdue(train, 20, 500, 10, 4); tm = time.time() - t0; D = uniq(pats)[:20]
        trn = [total_u(train, D[:m], R, maxn) for m in range(len(D) + 1)]; ns = min(range(len(trn)), key=lambda m: trn[m]); ev('subdue20_mdl', D[:ns], tm)
        if n >= 10:
            t0 = time.time(); g = GraphMDL(); crashed = False
            try: g.fit(to_nx(train)[0], timeout=tout)
            except Exception as ex: crashed = True
            tm = time.time() - t0
            ev('graphmdl', uniq([tuple(order_pattern(normalize(pat_edges(Pt)))) for Pt in g.patterns() if Pt.number_of_edges() >= 2]), tm); res['graphmdl']['crashed'] = crashed
        out['res'][n] = res
        print(world, seed, n, {k: (round(v['test'], 1), v['k'], round(v['time'])) for k, v in res.items()}, flush=True)
    json.dump(out, open(f'e3_{world}_{seed}.json', 'w'))

if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]))
