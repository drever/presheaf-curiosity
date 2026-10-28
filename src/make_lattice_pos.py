"""Lattice coordinates of the 195 cell instances of the c6288 quotient graph (reads quotient.pkl, writes lattice_pos.pkl).
Generators: the bundle of three parallel wires (labels A1..A3) and the single wire B between neighbouring cells."""
import pickle
from collections import Counter, defaultdict, deque
E, nsup = pickle.load(open('quotient.pkl', 'rb'))
A1 = ('shared', 18, 1, 18, 6); A2 = ('shared', 18, 2, 18, 10); A3 = ('shared', 18, 3, 18, 12); B = ('shared', 18, 5, 18, 13)
def succ(lab):
    d = defaultdict(list)
    for a, b, k in E:
        if k == lab: d[a].append(b)
    return d
sA = [succ(l) for l in (A1, A2, A3)]; sB = succ(B)
A = {x: v[0] for x, v in sA[0].items()}; Bm = {x: v[0] for x, v in sB.items()}
nodes = set(A) | set(A.values()) | set(Bm) | set(Bm.values())
start = [x for x in nodes if x not in set(A.values()) and x not in set(Bm.values())]
pos = {start[0]: (0, 0)}; q = deque([start[0]])
while q:
    x = q.popleft(); i, j = pos[x]
    for f, (di, dj) in ((A, (1, 0)), (Bm, (0, 1))):
        if x in f and f[x] not in pos: pos[f[x]] = (i + di, j + dj); q.append(f[x])
    for f, (di, dj) in ((A, (-1, 0)), (Bm, (0, -1))):
        for y, z in f.items():
            if z == x and y not in pos: pos[y] = (i + di, j + dj); q.append(y)
assert len(pos) == 195 and max(Counter(pos.values()).values()) == 1
pickle.dump((pos, A, Bm), open('lattice_pos.pkl', 'wb')); print('cells', len(pos))
