"""E3 Teil 2a: Raender als Teil eines typisierten Z^2-Gitters? Greedy-Einbettung aller Zellen des Quotienten mit je Label festem Verschiebungsvektor."""
import pickle, itertools
from collections import Counter, defaultdict, deque
E, nsup = pickle.load(open('quotient.pkl', 'rb')); pos, A, B = pickle.load(open('lattice_pos.pkl', 'rb'))
uv = {x: (i + j, j + 13) for x, (i, j) in pos.items()}
nt = {}
for a, b, k in E:
    if k[0] == 'shared': nt[a] = k[1]; nt[b] = k[3]
# Labels, die immer auf denselben Knotenpaaren liegen, zu Buendeln vereinen
pairs_of = defaultdict(set)
for a, b, k in E: pairs_of[k].add((a, b))
bid = {}; groups = {}
for k, ps in pairs_of.items(): bid[k] = groups.setdefault(frozenset(ps), len(groups))
E = list({(a, b, bid[k]) for a, b, k in E})
print('bundles', len(groups))
adj = defaultdict(list)
for a, b, k in E: adj[a].append((b, k, 1)); adj[b].append((a, k, -1))
coord = dict(uv); occ = {p: x for x, p in coord.items()}; disp = {}
for a, b, k in E:
    if a in uv and b in uv: disp.setdefault(k, (uv[b][0] - uv[a][0], uv[b][1] - uv[a][1]))
print('core labels', {k: d for k, d in disp.items()})
cands = sorted([(du, dv) for du in range(-4, 5) for dv in range(-4, 5) if (du, dv) != (0, 0)], key=lambda d: (abs(d[0]) + abs(d[1]), d))
q = deque(sorted(coord)); fails = 0
while q:
    x = q.popleft(); cx = coord[x]
    for y, k, s in adj[x]:
        if y in coord: continue
        if k in disp:
            d = disp[k]; p = (cx[0] + s * d[0], cx[1] + s * d[1])
            if p in occ: fails += 1; continue
        else:
            p = None
            for d in cands:
                pp = (cx[0] + s * d[0], cx[1] + s * d[1])
                if pp not in occ: p = pp; disp[k] = d; break
        coord[y] = p; occ[p] = y; q.append(y)
print('embedded', len(coord), 'of', nsup, 'collisions', fails, 'labels with disp', len(disp), 'of', len({k for _, _, k in E}))
bad = [(a, b, k) for a, b, k in E if a in coord and b in coord and (coord[b][0] - coord[a][0], coord[b][1] - coord[a][1]) != disp[k]]
tot = sum(1 for a, b, k in E if a in coord and b in coord)
print('inconsistent edges', len(bad), 'of', tot)
cnt = Counter(disp[k] for _, _, k in E if k in disp); print('displacement vectors used', len(cnt), cnt.most_common(8))
us = [p[0] for p in coord.values()]; vs = [p[1] for p in coord.values()]; print('bbox', min(us), max(us), min(vs), max(vs))
for v in range(min(vs), max(vs) + 1):
    print(f'{v:3d} ' + ''.join((chr(ord('A') + nt.get(occ[(u, v)], 0) % 26) if (u, v) in occ else '.') for u in range(min(us), max(us) + 1)))
pickle.dump((coord, disp), open('embed33.pkl', 'wb'))
