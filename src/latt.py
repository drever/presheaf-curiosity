"""Gitterregel-Lerner (aus e32.py ausgelagert, ohne c6288-Daten): learn_rule, lattice_fit, Kosten. R wird uebergeben."""
from collections import defaultdict, Counter, deque
from core import LOG
def learn_rule(es):
    """Findet Erzeuger: Buendel funktionaler Labels (gleiche Endpunktpaare), die auf einem Gitter kommutieren. Rueckgabe: Liste von Label-Mengen."""
    byl = defaultdict(list)
    for a, l, b in es: byl[l].append((a, b))
    func = {}
    for l, ps in byl.items():
        if len({a for a, _ in ps}) == len(ps) and len({b for _, b in ps}) == len(ps): func[l] = frozenset(ps)
    bund = defaultdict(list)
    for l, ps in func.items(): bund[ps].append(l)
    gens = sorted(bund.items(), key=lambda kv: -len(kv[0]))
    return [(sorted(ls), dict(ps)) for ps, ls in gens]

     # Labels + Buendelgroesse + Kopf

def _coords(gl, D, es, n):
    step = [defaultdict(set) for _ in gl]; back = [defaultdict(set) for _ in gl]
    for a, l, b in es:
        for g in range(len(gl)):
            if l in gl[g]: step[g][a].add(b); back[g][b].add(a)
    co = {}; conflicts = 0
    start = min(range(n), key=lambda x: (sum(len(back[g][x]) for g in range(len(gl))), x)); co[start] = (0, 0); q = deque([start])
    while q:
        x = q.popleft(); c = co[x]
        for g in range(len(gl)):
            for y in step[g][x]:
                cy = (c[0] + D[g][0], c[1] + D[g][1])
                if y in co: conflicts += co[y] != cy
                else: co[y] = cy; q.append(y)
            for y in back[g][x]:
                cy = (c[0] - D[g][0], c[1] - D[g][1])
                if y in co: conflicts += co[y] != cy
                else: co[y] = cy; q.append(y)
    return co, conflicts

def gen_disps(gens, es, n):
    """Verschiebungen der Erzeuger >= 3 relativ zu den Koordinaten aus den ersten beiden (aus dem Trainingsblock gelernt)."""
    gl = [set(ls) for ls, _ in gens]; co, _ = _coords(gl[:2], [(1, 0), (0, 1)], es, n); D = [(1, 0), (0, 1)]
    for g in range(2, len(gl)):
        c = Counter((co[b][0] - co[a][0], co[b][1] - co[a][1]) for a, l, b in es if l in gl[g] and a in co and b in co)
        D.append(c.most_common(1)[0][0] if c else (0, 0))
    return D

def lattice_fit(gens, es, n, D=None):
    """Koordinaten per BFS nur aus der Regel; Ausnahmen = nicht erklaerte Kanten + fehlende vorhergesagte Kanten + Konflikte + Knoten ohne Koordinate."""
    if len(gens) < 2: return None
    gl = [set(ls) for ls, _ in gens]; D = D or [(1, 0), (0, 1)] + [(0, 0)] * (len(gl) - 2)
    co, conflicts = _coords(gl, D, es, n)
    inv_ = defaultdict(list)
    for x, c in co.items(): inv_[c].append(x)
    dup = sum(len(v) - 1 for v in inv_.values()); expl = 0; miss = 0; E = set(es)
    for a, l, b in es:
        for g in range(len(gl)):
            if l in gl[g] and a in co and b in co and co[b] == (co[a][0] + D[g][0], co[a][1] + D[g][1]): expl += 1; break
    for x, c in co.items():
        for g in range(len(gl)):
            for y in inv_.get((c[0] + D[g][0], c[1] + D[g][1]), []):
                for l in gl[g]:
                    if (x, l, y) not in E: miss += 1
    return {'extra': len(es) - expl, 'miss': miss, 'conflicts': conflicts, 'orphans': n - len(co), 'dup': dup}

def rule_bits(gens, R): return sum(LOG(R) * len(ls) + 8 for ls, _ in gens) + 16
def raw_bits(es, n, R): return len(es) * (2 * LOG(n) + LOG(R))
