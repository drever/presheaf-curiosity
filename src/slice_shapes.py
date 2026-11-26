"""Are the output slices of a synthesised circuit isomorphic to each other? Usage: python slice_shapes.py NAME [NAME ...]
For every output register, two views, both as pin-labelled digraphs (pins as in symmetry.py, view 'pins'):
  cone      : its whole combinational input cone (backwards to registers and inputs, which are kept as leaves),
              including logic shared with other outputs (the select decoder)
  exclusive : only the gates no other output uses, plus the edges into them; shared gates, registers and inputs are leaves
Canonical form via the undirected encoding of symmetry.py. Writes ../results/slice_shapes.json (updated per name)."""
import sys, os, json, collections, pynauty
import symmetry as SYM

def shape(edges, typ):
    vs = sorted({x for a, b, _ in edges for x in (a, b)}); ix = {v: i for i, v in enumerate(vs)}
    color = [('v', typ[v]) for v in vs]; adj = collections.defaultdict(list)
    for a, b, l in edges:
        t = len(color); color += [('t',) + tuple(l), ('h',)]; adj[ix[a]].append(t); adj[t].append(t + 1); adj[t + 1].append(ix[b])
    cl = collections.defaultdict(set)
    for i, c in enumerate(color): cl[c].add(i)
    g = pynauty.Graph(len(color), directed=False, adjacency_dict=dict(adj), vertex_coloring=[cl[c] for c in sorted(cl)])
    return pynauty.certificate(g) + repr(sorted(cl)).encode()

def analyse(name):
    E, typ, outc = SYM.netlist(name, pins=True); pred = collections.defaultdict(list)
    for e in E: pred[e[1]].append(e)
    comb = lambda v: not typ[v].startswith('DFF') and typ[v] != 'IN'
    into = lambda o: [e for e in pred[o] if e[2][2] == 'D']          # data input of the output register only
    def cone(o):
        seen, st, es = set(), [], list(into(o))
        st = [e[0] for e in es if comb(e[0])]; seen.update(st)
        while st:
            x = st.pop()
            for e in pred[x]:
                es.append(e)
                if comb(e[0]) and e[0] not in seen: seen.add(e[0]); st.append(e[0])
        return seen, es
    cones = {o: cone(o) for o in sorted(outc)}; cnt = collections.Counter(x for g, _ in cones.values() for x in g)
    res = {}
    for view in ('cone', 'exclusive'):
        sh = collections.Counter(); size = {}
        for o, (gates, es) in cones.items():
            if view == 'exclusive':
                ex = {x for x in gates if cnt[x] == 1}; es = into(o) + [e for x in ex for e in pred[x]]; gates = ex
            k = shape(es, typ); sh[k] += 1; size[k] = [len(es), len(gates)]
        res[view] = {'distinct_shapes': len(sh), 'class_counts': sorted(sh.values(), reverse=True),
                     'edges_gates': sorted({tuple(v) for v in size.values()})}
    res['outputs'] = len(outc)
    return res

if __name__ == '__main__':
    path = '../results/slice_shapes.json'; out = json.load(open(path)) if os.path.exists(path) else {}
    for name in sys.argv[1:]:
        r = analyse(name); out[name] = r
        print(f"{name:20s} outputs {r['outputs']:3d} | cone: {r['cone']['distinct_shapes']:3d} shapes {r['cone']['class_counts'][:5]} (edges, gates) {r['cone']['edges_gates'][:3]}"
              f" | exclusive: {r['exclusive']['distinct_shapes']:3d} shapes {r['exclusive']['class_counts'][:5]} (edges, gates) {r['exclusive']['edges_gates'][:3]}", flush=True)
    json.dump(out, open(path, 'w'), indent=1)
