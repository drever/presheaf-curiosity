import sys, json, time, random, io, contextlib, collections, os
sys.path.insert(0, os.environ.get('SUBDUE_SRC', '/home/claude/holderlb/subdue/src'))
import Parameters, Graph, Subdue as SM
import und
from und import *
from core import order_pattern, normalize
from molcommon import load_mols, sample_comps, canon_bond

def _safe_compress(self, iteration, pattern):
    """Kopie von Graph.Compress; einzige Aenderung: Kanten, die durch fruehere Kompression zu Schleifen wurden,
    werden nicht zweimal aus derselben Liste entfernt (Original wirft ValueError)."""
    instanceNum = 0
    for instance in pattern.instances:
        instanceNum += 1
        newVertexLabel = 'PATTERN-' + str(iteration)
        newVertexId = 'PATTERN-' + str(iteration) + '-' + str(instanceNum)
        newVertex = Graph.Vertex(newVertexId)
        newVertex.timestamp = instance.max_timestamp()
        newVertex.add_attribute('label', newVertexLabel)
        self.vertices[newVertexId] = newVertex
        for instanceEdge in instance.edges:
            if instanceEdge in instanceEdge.source.edges: instanceEdge.source.edges.remove(instanceEdge)
            if instanceEdge in instanceEdge.target.edges: instanceEdge.target.edges.remove(instanceEdge)
            del self.edges[instanceEdge.id]
        for instanceVertex in instance.vertices:
            for edge in instanceVertex.edges:
                if edge.source == instanceVertex: edge.source = newVertex
                if edge.target == instanceVertex: edge.target = newVertex
                if edge not in newVertex.edges: newVertex.edges.append(edge)
            del self.vertices[instanceVertex.id]
Graph.Graph.Compress = _safe_compress

def build_graph(train):
    arr = []; orig = {}
    for ci, c in enumerate(train):
        for j in range(c.n):
            arr.append({'vertex': {'id': f'c{ci}v{j}', 'attributes': {}}})
        for (i, a, r, b) in c.E:
            eid = f'c{ci}e{i}'; orig[eid] = (a, r, b)
            arr.append({'edge': {'id': eid, 'source': f'c{ci}v{a}', 'target': f'c{ci}v{b}',
                                 'directed': 'false' if r in und.SYMS else 'true', 'attributes': {'label': str(r)}}})
    g = Graph.Graph(); g.load_from_json(arr)
    return g, orig

def run_subdue(train, iters, limit, maxsize, beam):
    g, orig = build_graph(train)
    p = Parameters.Parameters(); p.iterations = iters; p.limit = limit; p.maxSize = maxsize; p.beamWidth = beam
    p.numBest = 3; p.overlap = 'none'; p.set_defaults_for_graph(g)
    content = {}; pats = []; info = []
    for it in range(1, iters + 1):
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()): pl = SM.DiscoverPatterns(p, g)
        if not pl: break
        best = pl[0]; exp = []
        for inst in best.instances:
            es = {e.id for e in inst.edges}
            for v in inst.vertices:
                if v.id in content: es |= content[v.id]
            exp.append(es)
        keys = collections.Counter(); reps = {}
        for es in exp:
            pe = normalize([orig[e] for e in es])
            try: k = canon_u(pe, True)
            except Exception: continue
            keys[k] += 1; reps[k] = pe
        if not keys: break
        k = keys.most_common(1)[0][0]
        pats.append(tuple(order_pattern(reps[k])))
        info.append({'it': it, 'ninst': len(best.instances), 'edges': len(exp[0]), 'agree': keys[k] / len(exp), 'time': time.time() - t0})
        for n, es in enumerate(exp, 1): content[f'PATTERN-{it}-{n}'] = es
        g.Compress(it, best)
        if len(g.edges) == 0: break
    return pats, info

def main(k, seed, limit, iters=20, N=300):
    tr = load_mols('mol/solubility.train.sdf'); te = load_mols('mol/solubility.test.sdf')
    keys = sorted({(bt, el[x], el[y]) for ms in (tr, te) for n, bonds, el in ms for a, bt, b in bonds for x, y in [canon_bond(el, a, b, bt)]})
    relid = {t: i for i, t in enumerate(keys)}; R = len(keys); und.SYMS = {i for t, i in relid.items() if t[1] == t[2]}
    rng = random.Random(seed); train = sample_comps(tr, int(.7 * N), k, rng, relid); test = sample_comps(te, N - int(.7 * N), k, rng, relid)
    maxn = k + 1
    t0 = time.time(); pats, info = run_subdue(train, iters, limit, max(10, k), 4); tm = time.time() - t0
    D = []; seen = set()
    for p in pats:
        kk = canon_u(p, True)
        if kk not in seen: seen.add(kk); D.append(p)
    trn = [total_u(train, D[:n], R, maxn) for n in range(0, len(D) + 1)]
    nstar = min(range(len(trn)), key=lambda n: trn[n])
    def ev(Dn): return {'k': len(Dn), 'max_edges': max([len(p) for p in Dn] or [0]), 'test': total_u(test, Dn, R, maxn, False) / len(test), 'dict': total_u([], Dn, R, maxn)}
    out = {'k': k, 'seed': seed, 'limit': limit, 'time': tm, 'nraw': len(pats), 'ndistinct': len(D), 'nstar': nstar, 'info': info,
           'full': ev(D), 'mdl': ev(D[:nstar])}
    json.dump(out, open(f'mx_{k}_{seed}_{iters}.json', 'w')); print('fertig', k, seed, round(tm, 1), 's', 'Muster', len(pats), 'distinct', len(D), 'n*', nstar, flush=True)

if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
