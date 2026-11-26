"""Chapter two, step 0: which automorphisms does nauty find in whole synthesised circuits, and in their rewiring?
Descriptive only, no compression. Usage: python symmetry.py NAME [NAME ...]   (names as in data/quip_synth/)
Three views of each netlist:
  plain : as the learner sees it (edge label = (driver type, sink type); input pins of a cell interchangeable)
  pins  : edge label also carries the sink pin for non-commutative cells (ANDNOT, ORNOT, MUX, DFF ...)
  cut   : pins, and every DFF -> DFF edge removed (the input shift chains cut into separate registers)
Each view also on its label- and degree-preserving rewiring (rewire.py, Random(8900)).
Encoding for nauty: undirected, each directed edge a -> b becomes a - t - h - b, with t coloured by the edge label and h a
head marker (the same trick as und.CANON_UNDIRECTED). Writes ../results/symmetry_NAME.json"""
import sys, os, json, math, random, collections, pynauty
from rewire import rewire
from quip import QUIP
COMMUTATIVE = {'AND', 'NAND', 'OR', 'NOR', 'XOR', 'XNOR'}

def netlist(name, pins):
    d = json.load(open(os.path.join(QUIP, name + '.json'))); mods = d['modules']
    top = [m for m, v in mods.items() if v.get('attributes', {}).get('top')]; mod = mods[top[0] if top else list(mods)[0]]
    driver, typ, outs = {}, {}, set()
    for pn, p in mod['ports'].items():
        for k, bit in enumerate(p['bits']):
            if not isinstance(bit, int): continue
            if p['direction'] == 'input': driver[bit] = f'in:{pn}[{k}]'; typ[f'in:{pn}[{k}]'] = 'IN'
            else: outs.add(bit)
    out_cells = set()
    for cn, c in mod['cells'].items():
        typ[cn] = c['type'].strip('$_').rstrip('_')
        for pn, dirn in c['port_directions'].items():
            if dirn == 'output':
                for bit in c['connections'][pn]:
                    if isinstance(bit, int): driver[bit] = cn; out_cells |= {cn} if bit in outs else set()
    E = []
    for cn in sorted(mod['cells']):
        c = mod['cells'][cn]
        for pn in sorted(c['port_directions']):
            if c['port_directions'][pn] != 'input': continue
            for bit in c['connections'][pn]:
                if isinstance(bit, int) and bit in driver:
                    pin = '' if (not pins or typ[cn] in COMMUTATIVE) else pn
                    E.append((driver[bit], cn, (typ[driver[bit]], typ[cn], pin)))
    return E, typ, out_cells

def aut(E, typ):
    vs = sorted(typ); ix = {v: i for i, v in enumerate(vs)}; n = len(vs)
    color = [('v', typ[v]) for v in vs]; adj = collections.defaultdict(list)
    for a, b, l in E:
        t, h = len(color), len(color) + 1; color += [('t',) + tuple(l), ('h',)]
        adj[ix[a]].append(t); adj[t].append(h); adj[h].append(ix[b])
    cl = collections.defaultdict(set)
    for i, c in enumerate(color): cl[c].add(i)
    g = pynauty.Graph(len(color), directed=False, adjacency_dict=dict(adj), vertex_coloring=[cl[c] for c in sorted(cl)])
    gens, m, e, orbits, norb = pynauty.autgrp(g)
    orb = collections.defaultdict(list)
    for i in range(n): orb[orbits[i]].append(vs[i])
    return {'log10_group_size': math.log10(m) + e, 'generators': len(gens), 'orbits': list(orb.values())}

def summary(E, typ, out_cells, used):
    r = aut(E, typ); cells = [v for v in typ if typ[v] != 'IN' and v in used]
    oc = [o for o in r['orbits'] if typ[o[0]] != 'IN' and o[0] in used]
    sizes = collections.Counter(len(o) for o in oc)
    out_orbits = [len(o) for o in oc if set(o) & out_cells]
    return {'log10_group_size': round(r['log10_group_size'], 2), 'generators': r['generators'], 'cells': len(cells),
            'cell_orbits': len(oc), 'cells_in_nontrivial_orbits': sum(len(o) for o in oc if len(o) > 1),
            'orbit_sizes': dict(sorted(sizes.items())), 'output_register_orbits': sorted(out_orbits, reverse=True)}

if __name__ == '__main__':
    for name in sys.argv[1:]:
        res = {'name': name}
        for view in ('plain', 'pins', 'cut'):
            E, typ, out_cells = netlist(name, pins=(view != 'plain'))
            if view == 'cut': E = [e for e in E if not (typ[e[0]].startswith('DFF') and typ[e[1]].startswith('DFF'))]
            used = {x for a, b, _ in E for x in (a, b)}; typ = {v: t for v, t in typ.items() if v in used}   # drops isolated vertices (Yosys scopeinfo cells)
            Er = rewire(E, random.Random(8900))[0]
            res[view] = {'circuit': summary(E, typ, out_cells, used), 'control': summary(Er, typ, out_cells, used), 'edges': len(E)}
            c, k = res[view]['circuit'], res[view]['control']
            print(f"{name:20s} {view:5s} edges {len(E):5d} | circuit: |Aut| 10^{c['log10_group_size']:<7} cells {c['cells']:5d} "
                  f"orbits {c['cell_orbits']:5d} in nontriv {c['cells_in_nontrivial_orbits']:5d} out-reg orbits {c['output_register_orbits'][:4]} "
                  f"| control: 10^{k['log10_group_size']:<6} orbits {k['cell_orbits']:5d} in nontriv {k['cells_in_nontrivial_orbits']:5d}", flush=True)
        json.dump(res, open(f'../results/symmetry_{name}.json', 'w'), indent=1)
