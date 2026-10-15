"""E3-Test: rekursives Makro (Gitterregel = Fixpunkt X = Zelle (+) X-um-eins) auf dem Zellquotienten von c6288.
Regel wird aus einem kleinen t x t Block gelernt (nur Kanten + Labels, keine Koordinaten), dann auf groessere Bloecke und die ganze Schaltung angewendet."""
import sys, os, json, pickle, math, random, time
from collections import Counter, defaultdict, deque
import und
from und import *
from und3 import learn_h, dict_bits_h
from core import Comp, LOG
import repair as RP
und.SYMS = set()
E, nsup = pickle.load(open('quotient.pkl', 'rb')); pos0, A0, B0 = pickle.load(open('lattice_pos.pkl', 'rb'))
labid = {}
for _, _, k in sorted(E, key=lambda x: str(x[2])): labid.setdefault(k, len(labid))
NL = len(labid); R = NL + 1
EL = [(a, labid[k], b) for a, b, k in E]            # alle Kanten des Quotienten (a -label-> b)
# Gitterkoordinaten (u,v)=(i+j, j+13) fuer die 195 Kernzellen (nur fuer Blockauswahl + Auswertung, nicht fuer das Lernen)
uv = {x: (i + j, j + 13) for x, (i, j) in pos0.items()}
inv = {p: x for x, p in uv.items()}
def block_nodes(u0, u1, v0, v1): return [x for x, (u, v) in uv.items() if u0 <= u < u1 and v0 <= v < v1]
def induced(nodes):
    S = set(nodes); ix = {x: k for k, x in enumerate(sorted(S))}
    return [(ix[a], l, ix[b]) for a, l, b in EL if a in S and b in S], len(S)
def comp_of(nodes):
    es, n = induced(nodes); return Comp(n, es)

def raw_bits(es, n): return len(es) * (2 * LOG(n) + LOG(R))

# ---------- Gitterregel lernen (aus Kantenliste eines Blocks, ohne Koordinaten) ----------
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

def rule_bits(gens): return sum(LOG(R) * len(ls) + 8 for ls, _ in gens) + 16     # Labels + Buendelgroesse + Kopf

def check_commute(gens):
    ok = tot = 0
    (l1, f1), (l2, f2) = gens[0], gens[1]
    for x in f1:
        if x in f2 and f1[x] in f2 and f2[x] in f1: tot += 1; ok += f2[f1[x]] == f1[f2[x]]
    return ok, tot

def apply_rule(gens, labels_of_rule, es, n):
    """Wendet Regel (Erzeuger = Label-Mengen) auf Block (es,n) an: Koordinaten per BFS aus der Regel; liefert Ausnahmen."""
    gl = [set(ls) for ls, _ in gens]
    succ = [defaultdict(dict) for _ in gl]       # succ[g][x][frozen label set] -> y
    cnt = [defaultdict(lambda: defaultdict(set)) for _ in gl]
    for a, l, b in es:
        for g, s in enumerate(gl):
            if l in s: cnt[g][(a, b)][0] = cnt[g][(a, b)][0] | {l}
    covered = set(); pair_ok = 0
    for g, s in enumerate(gl):
        for (a, b), d in cnt[g].items():
            if d[0] == s: covered |= {(a, l, b) for l in s}      # vollstaendiges Buendel: von Regel erzeugt
    miss = 0   # Regel sagt Kante voraus (Nachbar existiert), Buendel unvollstaendig
    for g, s in enumerate(gl):
        for (a, b), d in cnt[g].items():
            if d[0] != s: miss += len(s - d[0])
    extra = [e for e in es if e not in covered]
    return covered, extra, miss


def lattice_fit(gens, es, n):
    """Koordinaten per BFS nur aus der Regel (Erzeuger 1 = (1,0), Erzeuger 2 = (0,1)); Ausnahmen = Kanten, die die Regel nicht erklaert + von der Regel vorhergesagte, aber fehlende Kanten + Knoten ohne Koordinate."""
    if len(gens) < 2: return None
    gl = [set(ls) for ls, _ in gens[:2]]; D = [(1, 0), (0, 1)]
    step = [defaultdict(set), defaultdict(set)]; back = [defaultdict(set), defaultdict(set)]
    for a, l, b in es:
        for g in range(2):
            if l in gl[g]: step[g][a].add(b); back[g][b].add(a)
    co = {}; conflicts = 0; best = None
    start = min(range(n), key=lambda x: (sum(len(back[g][x]) for g in range(2)), x))
    co[start] = (0, 0); q = deque([start])
    while q:
        x = q.popleft(); c = co[x]
        for g in range(2):
            for y in step[g][x]:
                cy = (c[0] + D[g][0], c[1] + D[g][1])
                if y in co: conflicts += co[y] != cy
                else: co[y] = cy; q.append(y)
            for y in back[g][x]:
                cy = (c[0] - D[g][0], c[1] - D[g][1])
                if y in co: conflicts += co[y] != cy
                else: co[y] = cy; q.append(y)
    inv_ = defaultdict(list)
    for x, c in co.items(): inv_[c].append(x)
    dup = sum(len(v) - 1 for v in inv_.values())
    expl = 0; miss = 0; E = set(es)
    for a, l, b in es:
        for g in range(2):
            if l in gl[g] and a in co and b in co and co[b] == (co[a][0] + D[g][0], co[a][1] + D[g][1]): expl += 1; break
    for x, c in co.items():
        for g in range(2):
            for y in inv_.get((c[0] + D[g][0], c[1] + D[g][1]), []):
                for l in gl[g]:
                    if (x, l, y) not in E: miss += 1
    extra = len(es) - expl
    return {'extra': extra, 'miss': miss, 'conflicts': conflicts, 'orphans': n - len(co), 'dup': dup}

# ---------- Lauf ----------
if __name__ == '__main__':
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    train_nodes = block_nodes(2, 2 + t, 2, 2 + t); tes, tn = induced(train_nodes)
    gens = learn_rule(tes); print('train block', t, 'nodes', tn, 'edges', len(tes), 'generators', [(ls, len(f)) for ls, f in gens]); print('commute', check_commute(gens))
    rb = rule_bits(gens); print('rule bits', round(rb, 1))
    res = {'t': t, 'rule_bits': rb, 'gens': [ls for ls, _ in gens]}
    rows = []
    D = learn_h([comp_of(train_nodes)], R, 40, 40, False, mode='hier', topc=30, maxe=16, objective='hier')
    print('glue dict', len(D), 'edges', [len(p) for p in D])
    rules = RP.learn([comp_of(train_nodes)], R, set(), K=40)
    print('repair rules', len(rules))
    for m in (4, 6, 8, 10, 12, 13):
        nodes = block_nodes(1, 1 + m, 1, 1 + m); es, n = induced(nodes); c = Comp(n, es)
        fit = lattice_fit(gens, es, n); nex = fit['extra'] + fit['miss'] + fit['conflicts'] + fit['orphans'] + fit['dup']
        exc = nex * (2 * LOG(n) + LOG(R)) + (1 if nex else 0)
        rec = rb + 2 * LOG(m + 1) + exc
        t0 = time.time(); gl = total_u([c], D, R, 40, False); t1 = time.time() - t0
        rp = RP.cost([c], rules, R, set())
        row = {'m': m, 'nodes': n, 'edges': len(es), 'raw': raw_bits(es, n), 'glue': gl, 'repair': rp, 'recursive': rec, 'exceptions': nex, 'fit': fit, 'glue_time': round(t1)}
        rows.append(row); print(row, flush=True)
    res['rows'] = rows; res['dict_glue'] = dict_bits_h(D, R, 40); res['dict_repair'] = RP.dict_cost(rules, R)
    json.dump(res, open(f'../results/e32_t{t}.json', 'w'), default=str)
