import json, sys
from collections import defaultdict, Counter
import und
from und import *
from cells import whole_comp

def build_quotient(comp, D, skip=frozenset()):
    """Knoten = Musterinstanzen (+ unueberdeckte Gatter); Kanten = geteilte Gatter und unueberdeckte Draehte; Label = Port-Paar."""
    inst, raw = cover_u(comp, D)
    memb = defaultdict(list)                       # Netzlistenknoten -> [(Super-ID, Muster, Port)]
    for k, (pi, ids, mm) in enumerate(inst):
        for u, n in mm: memb[n].append((k, pi, u))
    nsup = len(inst); sup_of_free = {}
    def members(n):
        nonlocal nsup
        if memb[n]: return memb[n]
        if n not in sup_of_free: sup_of_free[n] = nsup; nsup += 1
        return [(sup_of_free[n], -1, 0)]
    E = {}
    def add(a, b, key):
        if a[0] == b[0]: return
        (x, y) = (a, b) if (a[1], a[2]) <= (b[1], b[2]) else (b, a)
        E[(x[0], y[0], key + (x[1], x[2], y[1], y[2]))] = 1
    for n, M in list(memb.items()):
        if n in skip: continue
        for i in range(len(M)):
            for j in range(i + 1, len(M)): add(M[i], M[j], ('shared',))
    for e in raw:
        _, u, r, v = comp.E[e]
        if u in skip or v in skip: continue
        for a in members(u)[:1]:
            for b in members(v)[:1]: E[(a[0], b[0], ('raw', r, a[1], a[2], b[1], b[2]))] = 1 if a[0] != b[0] else None
    E = [(a, b, key) for (a, b, key), v in E.items() if v]
    return E, nsup, inst, raw

if __name__ == '__main__':
    und.SYMS = set(); comp, nodes, L = whole_comp()
    D = [tuple(tuple(e) for e in p) for p in json.load(open('cells_D2.json'))['D']]
    pis = {n for n in range(comp.n) if not comp.inn[n]}; print('primary inputs', len(pis))
    E, nsup, inst, raw = build_quotient(comp, D, pis)
    labs = Counter(k for _, _, k in E)
    print('super nodes', nsup, 'edges', len(E), 'distinct labels', len(labs)); print(labs.most_common(12))
    deg = Counter(); [deg.update([a, b]) for a, b, _ in E]; print('degree hist', sorted(Counter(deg.values()).items()))
    import pickle; pickle.dump((E, nsup), open('quotient.pkl', 'wb'))
