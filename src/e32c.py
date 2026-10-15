"""Kontrolle: gleiches Kantenlabel-Multiset, aber Ziele zufaellig vertauscht (kein Gitter). Findet der Regel-Lerner trotzdem Erzeuger und wie teuer waeren die Ausnahmen?"""
import random
from e32 import *
rng = random.Random(5)
m = 13; nodes = block_nodes(1, 1 + m, 1, 1 + m); es, n = induced(nodes)
tgt = [b for _, _, b in es]; rng.shuffle(tgt); es2 = [(a, l, b) for (a, l, _), b in zip(es, tgt) if a != b]
trn = block_nodes(2, 6, 2, 6)
# Trainingsblock: Kanten innerhalb der ersten 16 Knoten des Zufallsgraphen
ix = {x: k for k, x in enumerate(sorted(nodes))}; sub = {ix[x] for x in trn}
tes = [e for e in es2 if e[0] in sub and e[2] in sub]
g = learn_rule(tes); print('shuffled: train edges', len(tes), 'generators', [(ls, len(f)) for ls, f in g])
if len(g) >= 2:
    print(lattice_fit(g, es2, n), 'edges', len(es2))
else: print('no lattice rule found -> model not applicable')
