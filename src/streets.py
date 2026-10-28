import json, math, random
from collections import Counter, defaultdict
from core import Comp
import paths
BASE = paths.STREETS
CLS = {'motorway': 0, 'trunk': 0, 'primary': 0, 'motorway_link': 0, 'trunk_link': 0, 'primary_link': 0,
       'secondary': 1, 'secondary_link': 1, 'tertiary': 1, 'tertiary_link': 1,
       'residential': 2, 'unclassified': 2, 'living_street': 2,
       'service': 3,
       'pedestrian': 4, 'footway': 4, 'path': 4, 'steps': 4, 'cycleway': 4, 'track': 4, 'corridor': 4, 'bridleway': 4}
NLAB = 6
VEH = True   # nur Fahrstrassen (Klassen 0-3); Gehwege/Fusswege ausgelassen   # 5 Klassen + sonstige

def city_graph(name):
    d = json.load(open(BASE + name + '.geojson')); ways = []
    use = Counter()
    for f in d['features']:
        hw = f['properties'].get('highway')
        if hw is None: continue
        co = [(round(x, 6), round(y, 6)) for x, y in f['geometry']['coordinates']]
        if CLS.get(hw, 5) >= 4 and VEH: continue
        ways.append((CLS.get(hw, 5), co))
        for p in set(co): use[p] += 1
    E = {}
    for lab, co in ways:
        last = co[0]
        for p in co[1:]:
            if use[p] >= 2 or p == co[-1]:
                if p != last:
                    k = (last, p) if last < p else (p, last)
                    if k not in E: E[k] = lab
                last = p
    return E

def windows(E, cell=0.004, nmax=40, emin=8, emax=60):
    """Raeumliche Fenster (Zellen in Grad ~ 300-400 m); Komponente = Kanten mit beiden Endpunkten in der Zelle."""
    cells = defaultdict(list)
    for (u, v), lab in E.items():
        cx = (int(math.floor(u[0] / cell)), int(math.floor(u[1] / cell)))
        if cx == (int(math.floor(v[0] / cell)), int(math.floor(v[1] / cell))): cells[cx].append((u, v, lab))
    out = []
    for cx, es in cells.items():
        nodes = {x for u, v, _ in es for x in (u, v)}
        if len(nodes) <= nmax and emin <= len(es) <= emax: out.append(es)
    return out

def to_comp(es, rng, NN):
    nodes = list({x for u, v, _ in es for x in (u, v)}); rng.shuffle(nodes); ix = {x: i for i, x in enumerate(nodes)}
    return Comp(NN, [(ix[u], lab, ix[v]) for u, v, lab in es])

if __name__ == '__main__':
    import sys
    for c in sys.argv[1:]:
        E = city_graph(c); w = windows(E)
        print(c, 'edges', len(E), 'labels', Counter(E.values()), 'windows', len(w), 'mean edges', sum(len(x) for x in w) / max(1, len(w)))
