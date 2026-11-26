"""Top-down slice decomposition on whole netlists (docs/prereg-slices.md). Usage: python slices_run.py NAME SEED
Three graphs, one cut: the cut is computed once on the intact circuit (exclusive part of each output slice, as in
slice_shapes.py) and the same node sets are used on all three graphs.
  intact   : the synthesised netlist (pins labelled)
  shuffled : edges from shared gates into the exclusive slice interiors get their sources permuted among edges with the
             same label (driver type, sink type, pin); slice interiors and fan-outs of shared gates stay fixed (Kardashev)
  rewired  : label- and degree-preserving rewiring of the whole graph (rewire.py, 20 swaps per edge)
For each graph: plain file (no class factored) and decomposition file (MDL choice of classes), both decoded and verified.
Writes ../results/slices_NAME_SEED.json"""
import sys, json, random, collections, time
import symmetry as SYM, slicecoder as SC
from rewire import rewire

def cut(E, typ, outc):
    pred = collections.defaultdict(list)
    for e in E: pred[e[1]].append(e)
    comb = lambda v: not typ[v].startswith('DFF') and typ[v] != 'IN'
    cones = {}
    for o in sorted(outc):
        if comb(o): st = [o]                                # output driven by a gate: its cone starts at that gate
        else: st = [e[0] for e in pred[o] if e[2][2] == 'D' and comb(e[0])]   # output register: start at its data input
        seen = set(st)
        while st:
            x = st.pop()
            for e in pred[x]:
                if comb(e[0]) and e[0] not in seen: seen.add(e[0]); st.append(e[0])
        cones[o] = seen
    cnt = collections.Counter(x for s in cones.values() for x in s)
    pieces = [{x for x in s if cnt[x] == 1} for o, s in sorted(cones.items())]
    shared = {x for x in cnt if cnt[x] > 1}
    return [P for P in pieces if P], shared

def shuffle(E, pieces, shared, rng):
    interior = set().union(*pieces); groups = collections.defaultdict(list)
    for i, (a, b, l) in enumerate(E):
        if a in shared and b in interior: groups[l].append(i)
    E2 = list(E); moved = 0
    for l, ix in sorted(groups.items()):
        src = [E[i][0] for i in ix]; rng.shuffle(src)
        for i, a in zip(ix, src): moved += a != E[i][0]; E2[i] = (a, E[i][1], E[i][2])
    return E2, {'attachment_edges': sum(len(v) for v in groups.values()), 'groups': len(groups), 'sources_changed': moved}

def run(E, typ, pieces):
    t0 = time.time(); info, classes = SC.analyse(E, typ, pieces); out = {}
    for mode in ('plain', 'decomposed'):
        F = set() if mode == 'plain' else SC.best(E, typ, info, classes)
        b, inf = SC.encode(E, typ, info, classes, F)
        out[mode] = {'bits': inf['bits'], 'bytes': len(b), 'parts': inf['parts'], 'factored_classes': inf['factored_classes'],
                     'copies': inf['copies'], 'verified': SC.verify(b, inf)}
    out['classes'] = sorted((len(v) for v in classes.values()), reverse=True)
    out['saving_bits'] = out['plain']['bits'] - out['decomposed']['bits']
    out['saving_share'] = out['saving_bits'] / out['plain']['bits']; out['seconds'] = round(time.time() - t0)
    return out

if __name__ == '__main__':
    name, seed = sys.argv[1], int(sys.argv[2])
    E, typ, outc = SYM.netlist(name, pins=True)
    used = {x for a, b, _ in E for x in (a, b)}; typ = {v: t for v, t in typ.items() if v in used}
    pieces, shared = cut(E, typ, outc)
    res = {'name': name, 'seed': seed, 'edges': len(E), 'nodes': len(typ), 'pieces': len(pieces),
           'piece_edges': sum(1 for a, b, _ in E if a in set().union(*pieces) or b in set().union(*pieces))}
    Es, res['shuffle'] = shuffle(E, pieces, shared, random.Random(7700 + seed))
    Er = rewire(E, random.Random(8900 + seed))[0]
    for tag, G in (('intact', E), ('shuffled', Es), ('rewired', Er)):
        res[tag] = run(G, typ, pieces); r = res[tag]
        print(f"{name:20s} s{seed} {tag:8s} plain {r['plain']['bits']:9.0f} decomposed {r['decomposed']['bits']:9.0f} saving {r['saving_share']*100:5.1f}% "
              f"classes factored {r['decomposed']['factored_classes']} copies {r['decomposed']['copies']} largest classes {r['classes'][:4]} "
              f"verified {r['plain']['verified'] and r['decomposed']['verified']} {r['seconds']}s", flush=True)
    json.dump(res, open(f'../results/slices_{name}_{seed}.json', 'w'), indent=1)
