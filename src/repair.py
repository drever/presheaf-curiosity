"""gRePair-artiger Baseline (Maneth et al.): Digramm-Ersetzung durch Nichtterminal-Hyperkanten (SL-HR-Grammatik),
Interface = Knoten, die ausserhalb des Digramms noch Kanten haben (nur die werden angehaengt, innere Knoten verschwinden).
Greedy nach MDL-Gewinn ueber alle Trainingsfenster; Anwendung auf Testfenster durch Wiederholung der Regeln in Reihenfolge.
Kosten wie im Rest des Projekts: Terminalkante 2*log n + log R; Nichtterminalkante log(|D|+1) + rang*log n."""
import itertools, collections
from core import LOG

def edges_of(comp): return [(('t', r), (u, v)) for _, u, r, v in comp.E]

def digram_key(e1, e2, deg, syms):
    best = None
    for a, b in ((e1, e2), (e2, e1)):
        oa = [a[1]] + ([a[1][::-1]] if a[0][0] == 't' and a[0][1] in syms else [])
        ob = [b[1]] + ([b[1][::-1]] if b[0][0] == 't' and b[0][1] in syms else [])
        for na in oa:
            for nb in ob:
                order = []; ix = {}
                for x in na + nb:
                    if x not in ix: ix[x] = len(order); order.append(x)
                enc = (a[0], tuple(ix[x] for x in na), b[0], tuple(ix[x] for x in nb))
                ext = tuple(deg[x] > (a[1].count(x) > 0) + (b[1].count(x) > 0) for x in order)
                k = (enc, ext)
                if best is None or k < best[0]: best = (k, order)
    return best

def degrees(g):
    deg = collections.Counter()
    for _, ns in g:
        for x in set(ns): deg[x] += 1
    return deg

def occurrences(g, syms, only=None):
    deg = degrees(g); inc = collections.defaultdict(list)
    for i, (_, ns) in enumerate(g):
        for x in set(ns): inc[x].append(i)
    pairs = set()
    for x, l in inc.items():
        for i, j in itertools.combinations(l, 2): pairs.add((i, j))
    out = collections.defaultdict(list)
    for i, j in pairs:
        k, order = digram_key(g[i], g[j], deg, syms)
        if only is None or k == only: out[k].append((i, j, order))
    return out

def select(occs):
    used = set(); sel = []
    for i, j, order in sorted(occs):
        if i in used or j in used: continue
        used |= {i, j}; sel.append((i, j, order))
    return sel

def apply(g, sel, key, sym_id):
    enc, ext = key
    ei = [i for i, f in enumerate(ext) if f]
    rem = set(); new = []
    for i, j, order in sel:
        rem |= {i, j}; new.append((('n', sym_id), tuple(order[t] for t in ei)))
    return [e for t, e in enumerate(g) if t not in rem] + new

def ecost(e, nlog, R, ND):
    return 2 * nlog + LOG(R) if e[0][0] == 't' else LOG(ND + 1) + len(e[1]) * nlog

def rule_bits(key, R, ND):
    enc, ext = key
    return 2 * LOG(R + ND + 1) + 8 + 2

def graph_bits(g, nlog, R, ND): return sum(ecost(e, nlog, R, ND) for e in g)

def learn(train, R, syms, K=int(__import__("os").environ.get("KR", 80)), topk=10):
    gs = [edges_of(c) for c in train]; nlogs = [LOG(c.n) for c in train]
    rules = []
    for it in range(K):
        allocc = collections.defaultdict(list)
        for gi, g in enumerate(gs):
            for k, l in occurrences(g, syms).items(): allocc[k] += [(gi, i, j, o) for i, j, o in l]
        cand = sorted(allocc, key=lambda k: -len(allocc[k]))[:topk]
        best = None; ND = len(rules)
        for k in cand:
            tot = 0; cnt = 0; per = collections.defaultdict(list)
            for gi, i, j, o in allocc[k]: per[gi].append((i, j, o))
            ext = k[1]; rank = sum(ext)
            for gi, l in per.items():
                sel = select(l); nl = nlogs[gi]
                before = ecost(gs[gi][0], nl, R, ND) * 0  # placeholder
                for i, j, o in sel:
                    b = ecost(gs[gi][i], nl, R, ND) + ecost(gs[gi][j], nl, R, ND)
                    a = LOG(ND + 2) + rank * nl
                    tot += b - a; cnt += 1
            gain = tot - rule_bits(k, R, ND)
            if cnt >= 2 and (best is None or gain > best[0]): best = (gain, k, per)
        if best is None or best[0] <= 0: break
        gain, k, per = best
        sid = len(rules)
        for gi, l in per.items(): gs[gi] = apply(gs[gi], select(l), k, sid)
        rules.append(k)
    return rules

def compress(comp, rules, R, syms):
    g = edges_of(comp)
    for sid, k in enumerate(rules):
        occ = occurrences(g, syms, only=k).get(k, [])
        if occ: g = apply(g, select(occ), k, sid)
    return g

def cost(comps, rules, R, syms):
    ND = len(rules); s = 0
    for c in comps: s += graph_bits(compress(c, rules, R, syms), LOG(c.n), R, ND)
    return s / len(comps)

def dict_cost(rules, R): return sum(rule_bits(k, R, i) for i, k in enumerate(rules))

# ---- Pruning (gRePair-artig): Blattregeln mit negativem Nettogewinn entfernen ----
def _remap(rules, drop):
    new = {}; c = 0
    for j in range(len(rules)):
        if j not in drop: new[j] = c; c += 1
    def lab(l): return ('n', new[l[1]]) if l[0] == 'n' else l
    return [((lab(k[0][0]), k[0][1], lab(k[0][2]), k[0][3]), k[1]) for j, k in enumerate(rules) if j not in drop]

def prune(train, rules, R, syms, nlog):
    rules = list(rules)
    while True:
        ND = len(rules)
        refs = collections.Counter()
        for k in rules:
            for l in (k[0][0], k[0][2]):
                if l[0] == 'n': refs[l[1]] += 1
        use = collections.Counter()
        for c in train:
            for lab, ns in compress(c, rules, R, syms):
                if lab[0] == 'n': use[lab[1]] += 1
        drop = set()
        for j, k in enumerate(rules):
            if refs[j]: continue
            rank = sum(k[1])
            b = sum((2 * nlog + LOG(R)) if l[0] == 't' else (LOG(ND + 1) + 2 * nlog) for l in (k[0][0], k[0][2]))
            a = LOG(ND + 1) + rank * nlog
            if use[j] * (b - a) - rule_bits(k, R, ND) <= 0: drop.add(j)
        if not drop: return rules
        rules = _remap(rules, drop)
