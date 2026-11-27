"""Structural check for docs/prereg-slices.md, amendment 1: do the pieces keep their isomorphism class under the two
shuffling controls? Prints class sizes only (no file lengths). Usage: python slices_classcheck.py NAME [NAME ...]"""
import sys, random, collections

import symmetry as SYM, slicecoder as SC, slices_run as SR
for name in sys.argv[1:]:
    E, typ, outc = SYM.netlist(name, pins=True)
    used = {x for a, b, _ in E for x in (a, b)}; typ = {v: t for v, t in typ.items() if v in used}
    pieces, shared = SR.cut(E, typ, outc)
    def cls(G):
        info, classes = SC.analyse(G, typ, pieces); return [I['key'] for I in info], sorted((len(v) for v in classes.values()), reverse=True)
    k0, c0 = cls(E); line = f"{name:20s} intact classes {c0[:5]}"
    for seed in (0, 1):
        Es, _ = SR.shuffle(E, pieces, shared, random.Random(7700 + seed)); k1, c1 = cls(Es)
        Ep, st = SR.permute_within(E, typ, pieces, shared, random.Random(7700 + seed)); k2, c2 = cls(Ep)
        same = lambda ka, kb: all((ka[i] == ka[j]) == (kb[i] == kb[j]) for i in range(len(ka)) for j in range(len(ka)))
        line += f" | s{seed} global: {c1[:5]} pieces changed {sum(a != b for a, b in zip(k0, k1))}, partition same {same(k0, k1)}; within: {c2[:5]} pieces changed {sum(a != b for a, b in zip(k0, k2))}, edges moved {st['edges_changed']}"
    print(line, flush=True)
