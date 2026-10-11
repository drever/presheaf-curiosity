import itertools
import und
from und import cover_u, canon_u, total_u
from core import LOG, normalize, order_pattern, dict_bits
from und3 import learn_h, dict_bits_h, pat_cost_h

def prod_pattern(A, B):
    va = sorted({x for a, r, b in A for x in (a, b)}); vb = sorted({x for a, r, b in B for x in (a, b)}); ix = {}
    def vid(x, y): return ix.setdefault((x, y), len(ix))
    E = []
    for a, r, b in A:
        for y in vb: E.append((vid(a, y), r, vid(b, y)))
    for a, r, b in B:
        for x in va: E.append((vid(x, a), r, vid(x, b)))
    return normalize(E)

def implicit_products(F, maxe, cross=None):
    out = []; seen = set()
    for i in range(len(F)):
        for j in range(i, len(F)):
            if cross and not cross(F[i], F[j]): continue
            p = prod_pattern(F[i], F[j])
            if len(p) > maxe: continue
            k = canon_u(p, False)
            if k in seen: continue
            seen.add(k); out.append(tuple(order_pattern(p)))
    return out

def effective_dict(D0, F, maxe, cross=None):
    imp = implicit_products(F, maxe, cross); keys = {canon_u(p, False) for p in imp}
    Dp = [p for p in D0 if canon_u(p, False) not in keys]
    have = {canon_u(p, False) for p in Dp}
    return Dp, Dp + [p for p in imp if canon_u(p, False) not in have]

def dict_bits_hp(D, R, maxn):
    """Hierarchische Kosten, zusaetzlich: Produkt zweier frueherer Eintraege kostet 2 Verweise + 1 Operator-Bit."""
    tot = 0; keys = [canon_u(p, False) for p in D]; prods = {}
    for k, p in enumerate(D):
        c = pat_cost_h(p, D[:k], R, maxn)
        pk = canon_u(p, False)
        for i in range(k):
            for j in range(i, k):
                q = prod_pattern(D[i], D[j])
                if len(q) == len(p) and canon_u(q, False) == pk:
                    c = min(c, 2 + 2 * LOG(k + 1) + 1); break
            else: continue
            break
        tot += c
    return tot

def learn_prod(train, R, K, maxn, maxe, maxf=6, max_factor_edges=4, cross=None):
    D0 = learn_h(train, R, K, maxn, False, mode='hier', topc=30, maxe=maxe, objective='hier')
    cand = find_factors(D0, maxs=max_factor_edges + 1)
    def L(F):
        Dp, Deff = effective_dict(D0, F, maxe, cross)
        return total_u(train, Deff, R, maxn, False) + dict_bits_h(Dp, R, maxn) + sum(LOG(len(Dp) + 1) + 1 for _ in F)
    F0 = []; base = L(F0)
    F = list(cand); cur = L(F)                      # Start mit allen gefundenen Faktoren, dann Rueckwaertselimination
    improved = True
    while improved and F:
        improved = False
        for f in list(F):
            t = [x for x in F if x is not f]; Ln = L(t)
            if Ln < cur: F, cur, improved = t, Ln, True; break
    if cur >= base: F = []
    Dp, Deff = effective_dict(D0, F, maxe, cross)
    return D0, F, Dp, Deff

def connected_subpatterns(p, maxs):
    nodes = [{a, b} for a, r, b in p]; cur = {frozenset([i]) for i in range(len(p))}; out = {}
    for size in range(1, maxs + 1):
        nxt = set()
        for s in cur:
            es = [p[i] for i in s]; pat = normalize(es); k = canon_u(pat, False)
            if k not in out: out[k] = pat
            if size < maxs:
                vs = set().union(*[nodes[i] for i in s])
                for j in range(len(p)):
                    if j not in s and nodes[j] & vs: nxt.add(s | {j})
        cur = nxt
    return list(out.values())

def find_factors(D, maxs=5):
    """Primfaktor-artige Zerlegung: alle (A,B) mit A x B == p fuer Eintraege p von D. Gibt die Faktoren zurueck."""
    facs = {}
    for p in D:
        if len(p) < 4: continue
        vp = len({x for a, r, b in p for x in (a, b)}); pk = canon_u(p, False)
        subs = connected_subpatterns(p, maxs)
        info = [(s, len({x for a, r, b in s for x in (a, b)})) for s in subs]
        for i, (A, va) in enumerate(info):
            for B, vb in info[i:]:
                if va * vb != vp or len(A) * vb + len(B) * va != len(p): continue
                if canon_u(prod_pattern(A, B), False) == pk:
                    for f in (A, B): facs[canon_u(f, False)] = tuple(order_pattern(f))
    return list(facs.values())

def is_path(p):
    from collections import Counter
    deg = Counter(); 
    for a, r, b in p: deg[a] += 1; deg[b] += 1
    vs = len(deg)
    return len(p) == vs - 1 and max(deg.values()) <= 2

def data_factors(train, maxs=3, topk=24, minfrac=0.15, pure=None):
    """Kandidaten-Faktoren direkt aus den Daten: haeufige Pfad-Teilmuster (1..maxs Kanten), nach Dokumenthaeufigkeit."""
    from und2 import subgraph_pool
    pool = subgraph_pool(train, False, maxs); cand = [(c, p) for k, (c, p) in pool.items() if is_path(p) and c >= minfrac * len(train) and (pure is None or pure(p))]
    singles = {}
    for c in train:
        for _, a, r, b in c.E: singles.setdefault(r, set()).add(id(c))
    for r, s in singles.items():
        if len(s) >= minfrac * len(train): cand.append((len(s), normalize([(0, r, 1)])))
    cand = [(c, p) for c, p in cand if pure is None or pure(p)]
    cand.sort(key=lambda x: (-x[0], -len(x[1])))
    return [tuple(order_pattern(p)) for c, p in cand[:topk]]

def learn_prod_data(train, R, K, maxn, maxe, cross=None, topk=16, maxf=14, pure=None):
    D0 = learn_h(train, R, K, maxn, False, mode='hier', topc=30, maxe=maxe, objective='hier')
    cand = data_factors(train, topk=topk, pure=pure)
    def L(F):
        Dp, Deff = effective_dict(D0, F, maxe, cross)
        return total_u(train, Deff, R, maxn, False) + dict_bits_h(Dp, R, maxn) + sum(LOG(len(Dp) + 1) + 1 for _ in F)
    F = []; cur = L(F); print('cand', len(cand), 'L0', round(cur), flush=True)
    while len(F) < maxf:
        best = None
        for c in cand:
            if c in F: continue
            Ln = L(F + [c])
            if Ln < cur and (best is None or Ln < best[0]): best = (Ln, c)
        if best is None:   # Paar-Schritt: zwei Faktoren zugleich (ein einzelner erzeugt mit Kreuz-Produkten nichts)
            for i, c1 in enumerate(cand):
                for c2 in cand[i + 1:]:
                    if c1 in F or c2 in F or (cross and not cross(c1, c2)): continue
                    Ln = L(F + [c1, c2])
                    if Ln < cur and (best is None or Ln < best[0]): best = (Ln, c1, c2)
            if best is None: break
            cur, F = best[0], F + [best[1], best[2]]; continue
        cur, F = best[0], F + [best[1]]
    Dp, Deff = effective_dict(D0, F, maxe, cross)
    return D0, F, Dp, Deff

def learn_classes(train, minsq=3):
    """Relationsklassen aus Quadraten: 4-Zyklen u-v-w-x mit gleichen Gegenkanten (a,b,a,b). Labels a,b stehen sich gegenueber;
    der Gegenueber-Graph wird 2-gefaerbt. Gibt (colors, nsquares) zurueck; unbekannte Labels haben keine Farbe."""
    from collections import defaultdict, Counter, deque
    cnt = Counter()
    for c in train:
        adj = defaultdict(list)
        for _, a, r, b in c.E: adj[a].append((b, r)); adj[b].append((a, r))
        for u in adj:
            for v, a in adj[u]:
                for x, b in adj[u]:
                    if x == v or a == b and False: continue
                    for w, a2 in adj[v]:
                        if w == u or w == x or a2 != b: continue
                        if any(y == x and r == a for y, r in adj[w]):
                            cnt[tuple(sorted((a, b)))] += 1
    par = {}; pr = {}                       # Union-Find mit Paritaet; Kanten nach Gewicht absteigend, Widersprueche werden verworfen
    def find(x):
        if par.setdefault(x, x) == x: pr.setdefault(x, 0); return x, 0
        r, p = find(par[x]); par[x] = r; pr[x] = pr.get(x, 0) ^ p; return r, pr[x]
    for (a, b), k in sorted(cnt.items(), key=lambda t: -t[1]):
        if k < minsq or a == b: continue
        ra, pa = find(a); rb, pb = find(b)
        if ra != rb: par[ra] = rb; pr[ra] = pa ^ pb ^ 1
    col = {}
    roots = {}
    for x in list(par):
        r, p = find(x); col[x] = p
    # Komponenten verschiedener Wurzeln: Farben koennten kollidieren; wir nehmen nur die groesste Komponente (Hauptgraph)
    from collections import Counter as _C
    big = _C(find(x)[0] for x in par).most_common(1)[0][0] if par else None
    col = {x: find(x)[1] for x in par if find(x)[0] == big}
    return col, sum(cnt.values())

def class_preds(col):
    def pure(p):
        cs = {col.get(r) for _, r, _ in p}; return len(cs) == 1 and None not in cs
    def cross(A, B):
        ca = {col.get(r) for _, r, _ in A}; cb = {col.get(r) for _, r, _ in B}
        return len(ca) == 1 and len(cb) == 1 and None not in ca | cb and ca != cb
    return pure, cross

def fiber_factors(train, col, topk=24, minfrac=0.0, maxe=4, mincount=2):
    """Kandidaten = Zusammenhangskomponenten des auf eine Klasse eingeschraenkten Graphen (die 'Fasern' eines Gitters), nach Haeufigkeit."""
    from collections import Counter, defaultdict
    cnt = Counter(); rep = {}
    for c in train:
        seen_k = set()
        for k in (0, 1):
            E = [(a, r, b) for _, a, r, b in c.E if col.get(r) == k]
            par = {}
            def f(x):
                while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
                return x
            for a, r, b in E: par[f(a)] = f(b)
            comp = defaultdict(list)
            for e in E: comp[f(e[0])].append(e)
            for es in comp.values():
                if len(es) > maxe: continue
                p = normalize(es); key = canon_u(p, False)
                if key not in seen_k: seen_k.add(key); cnt[key] += 1; rep[key] = p
    out = [(n, rep[k]) for k, n in cnt.items() if n >= max(mincount, minfrac * len(train))]
    out.sort(key=lambda x: (-x[0], -len(x[1])))
    return [tuple(order_pattern(p)) for n, p in out[:topk]]

def learn_prod_auto(train, R, K, maxn, maxe, topk=30, maxf=14, D0=None, minsq=3, fib_maxe=4):
    """Voll datengetrieben: Klassen aus Quadraten, Faktoren aus Fasern, Auswahl per MDL (Einzel- und Paar-Schritte)."""
    col, nsq = learn_classes(train, minsq=minsq); pure, cross = class_preds(col)
    if D0 is None: D0 = learn_h(train, R, K, maxn, False, mode='hier', topc=30, maxe=maxe, objective='hier')
    cand = fiber_factors(train, col, topk=topk, maxe=fib_maxe)
    def L(F):
        Dp, Deff = effective_dict(D0, F, maxe, cross)
        return total_u(train, Deff, R, maxn, False) + dict_bits_h(Dp, R, maxn) + sum(LOG(len(Dp) + 1) + 1 for _ in F)
    F = []; cur = L(F)
    while len(F) < maxf:
        best = None
        for c in cand:
            if c in F: continue
            Ln = L(F + [c])
            if Ln < cur and (best is None or Ln < best[0]): best = (Ln, [c])
        if best is None:
            for i, c1 in enumerate(cand):
                if c1 in F: continue
                for c2 in cand[i + 1:]:
                    if c2 in F or not cross(c1, c2): continue
                    Ln = L(F + [c1, c2])
                    if Ln < cur and (best is None or Ln < best[0]): best = (Ln, [c1, c2])
        if best is None: break
        cur, F = best[0], F + best[1]
    Dp, Deff = effective_dict(D0, F, maxe, cross)
    return D0, F, Dp, Deff, col
