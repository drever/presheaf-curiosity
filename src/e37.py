"""Analyse: was liegt ausserhalb der 18-Kanten-Zelle im eigenen Multiplizierer (k=16)?"""
import sys, pickle
from collections import Counter, defaultdict
import netlist; netlist.HB = '/tmp/claude-0/genbench/'
import und; from und import *
from netlist import *
from e34 import comp_of
und.SYMS = set()
Dfull, recs, D0 = pickle.load(open('../results/e35_cells_16.pkl', 'rb'))
k = int(sys.argv[1]) if len(sys.argv) > 1 else 16
L = Labeler(); comps = {kk: comp_of(f'mul{kk}', L) for kk in (16, 24, 32)}; c = comps[k]
inst, raw = cover_u(c, Dfull)
cell = max(range(len(Dfull)), key=lambda i: sum(1 for pi, _, _ in inst if pi == i) * (len(Dfull[i]) >= 15))
cnt = Counter(pi for pi, _, _ in inst); print('cell pattern', cell, 'edges', len(Dfull[cell]), 'instances', cnt[cell])
for pi, n in cnt.most_common(14): print(' pattern', pi, 'edges', len(Dfull[pi]), 'count', n, Dfull[pi] if len(Dfull[pi]) <= 8 else '')
