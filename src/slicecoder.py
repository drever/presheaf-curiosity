"""Chapter two: a top-down decomposition coder for whole netlists (docs/prereg-slices.md).

The graph is cut into pieces (here: the exclusive part of each output slice, see slice_shapes.py) and the rest R0.
Pieces are sorted into isomorphism classes (nauty, undirected encoding). For each class chosen for factoring the file
holds one representative and, per copy, an attachment table: which node outside the pieces each of its slots is.
Everything else is coded as a plain edge list. The same coder with no class factored is the plain baseline.

File layout (exact big-integer rANS from coder2, every bit counted):
  header      vocabulary: node types and, per type, the pins of its inputs
  numbering   counts of non-factored nodes per type (they are numbered by type)
  classes     per factored class: representative (node types, slot flags, edges), number of copies
  copies      per copy, per slot: attachment, adaptive model per (class, slot type) over nodes already used by
              earlier copies, without replacement within the copy; escape -> uniform over unused nodes of that type
  edges       every edge not inside a factored piece: per sink, in-degree (gamma), then source (uniform) and pin
Decoding rebuilds the graph and verify() checks it equals the input up to the renumbering the encoder chose."""
import collections, pynauty
from coder2 import Enc, Dec, put_gamma, get_gamma

def put_str(w, s):
    b = s.encode(); put_gamma(w, len(b))
    for c in b: w.uni(c, 256)
def get_str(d): return bytes(d.uni(256) for _ in range(get_gamma(d))).decode()

def canon(nodes, edges, typ, internal):
    """nodes: list; edges: (a, b, label) among them. Returns (key, nodes in canonical order)."""
    ix = {v: i for i, v in enumerate(nodes)}
    color = [('i' if v in internal else 's', typ[v]) for v in nodes]; adj = collections.defaultdict(list)
    for a, b, l in edges:
        t = len(color); color += [('t',) + tuple(l), ('h',)]; adj[ix[a]].append(t); adj[t].append(t + 1); adj[t + 1].append(ix[b])
    cl = collections.defaultdict(set)
    for i, c in enumerate(color): cl[c].add(i)
    keys = sorted(cl)
    g = pynauty.Graph(len(color), directed=False, adjacency_dict=dict(adj), vertex_coloring=[cl[c] for c in keys])
    lab = pynauty.canon_label(g)
    return pynauty.certificate(g) + repr(keys).encode(), [nodes[i] for i in lab if i < len(nodes)]

def analyse(E, typ, pieces):
    """pieces: list of disjoint node sets. Returns the piece structure used by encode()."""
    owner = {v: k for k, P in enumerate(pieces) for v in P}
    pe = collections.defaultdict(list); cross = []
    for e in E:
        a, b = owner.get(e[0]), owner.get(e[1])
        if a is not None and b is not None and a != b: cross.append(e)
        elif a is not None or b is not None: pe[a if a is not None else b].append(e)
    info = []
    for k, P in enumerate(pieces):
        es = pe[k]; slots = sorted({x for a, b, _ in es for x in (a, b) if x not in P})
        nodes = sorted(P) + slots; key, order = canon(nodes, es, typ, P)
        info.append({'key': key, 'order': order, 'internal': P, 'edges': es})
    classes = collections.defaultdict(list)
    for k, I in enumerate(info): classes[I['key']].append(k)
    return info, dict(classes)

def encode(E, typ, info, classes, factored, want_bytes=True):
    types = sorted(set(typ.values())); tix = {t: i for i, t in enumerate(types)}
    pins = collections.defaultdict(set)
    for a, b, l in E: pins[typ[b]].add(l[2])
    pins = {t: sorted(pins[t]) for t in types}
    w = Enc(); parts = {}
    def mark(name, b0): parts[name] = parts.get(name, 0) + w.bits - b0
    b0 = w.bits; put_gamma(w, len(types))
    for t in types:
        put_str(w, t); put_gamma(w, len(pins[t]))
        for p in pins[t]: put_str(w, p)
    mark('header', b0)
    fac = [c for c in sorted(classes) if c in factored]
    in_fac = {v for c in fac for k in classes[c] for v in info[k]['internal']}
    rest = sorted((v for v in typ if v not in in_fac), key=lambda v: (tix[typ[v]], v))
    new = {v: i for i, v in enumerate(rest)}; g = len(rest)
    b0 = w.bits; cnt = collections.Counter(typ[v] for v in rest)
    for t in types: put_gamma(w, cnt[t])
    start = {}; s = 0
    for t in types: start[t] = s; s += cnt[t]
    mark('numbering', b0)
    # classes: representative in canonical order of the first copy
    b0 = w.bits; put_gamma(w, len(fac)); reps = []
    for c in fac:
        I0 = info[classes[c][0]]; order = I0['order']; pos = {v: i for i, v in enumerate(order)}; m = len(order)
        put_gamma(w, m)
        for v in order: w.uni(tix[typ[v]], len(types)); w.uni(int(v in I0['internal']), 2)
        ins = collections.defaultdict(list)
        for a, b, l in I0['edges']: ins[pos[b]].append((l[2], pos[a]))
        for j in range(m):
            put_gamma(w, len(ins[j]))
            for p, a in sorted(ins[j]):
                w.uni(a, m)
                if len(pins[typ[order[j]]]) > 1: w.uni(pins[typ[order[j]]].index(p), len(pins[typ[order[j]]]))
        put_gamma(w, len(classes[c]) - 1); reps.append((c, order, I0['internal']))
    mark('classes', b0)
    # copies: internal nodes get new numbers g, g+1, ... in canonical order; slots are attached
    b0 = w.bits; nid = g; fac_edges = set()
    for c, order0, int0 in reps:
        seen = collections.defaultdict(list)              # slot type -> list of node ids seen (with multiplicity as counts)
        counts = collections.defaultdict(collections.Counter)
        for k in classes[c]:
            I = info[k]; used = set()
            for j, v in enumerate(I['order']):
                if order0[j] in int0: new[v] = nid; nid += 1; continue
                t = typ[v]; x = new[v]; cand = [y for y in seen[t] if y not in used]
                table = [counts[t][y] for y in cand] + [1]
                if x in cand: w.freq(cand.index(x), table)
                else:
                    w.freq(len(cand), table)
                    free = [y for y in range(start[t], start[t] + cnt[t]) if y not in used and y not in counts[t]]
                    w.uni(free.index(x), len(free)); seen[t].append(x)
                counts[t][x] += 1; used.add(x)
            fac_edges.update(id(e) for e in I['edges'])
    mark('copies', b0)
    # all other edges
    b0 = w.bits; n = nid; ins = collections.defaultdict(list)
    for e in E:
        if id(e) not in fac_edges: ins[new[e[1]]].append((e[2][2], new[e[0]]))
    inv = {i: v for v, i in new.items()}
    for j in range(n):
        put_gamma(w, len(ins[j])); P = pins[typ[inv[j]]]
        for p, a in sorted(ins[j]):
            w.uni(a, n)
            if len(P) > 1: w.uni(P.index(p), len(P))
    mark('edges', b0)
    graph = sorted((new[a], new[b], l[2]) for a, b, l in E)
    ntypes = [typ[inv[j]] for j in range(n)]
    return (w.tobytes() if want_bytes else None), {'bits': w.bits, 'parts': parts, 'factored_classes': len(fac),
            'copies': sum(len(classes[c]) for c in fac), 'graph': graph, 'types': ntypes}

def decode(b):
    d = Dec(b); types = [None] * get_gamma(d); pins = {}
    for i in range(len(types)):
        types[i] = get_str(d); pins[types[i]] = [get_str(d) for _ in range(get_gamma(d))]
    cnt = [get_gamma(d) for _ in types]; ntype = [t for t, c in zip(types, cnt) for _ in range(c)]; g = len(ntype)
    start = {}; s = 0
    for t, c in zip(types, cnt): start[t] = s; s += c
    reps = []
    for _ in range(get_gamma(d)):
        m = get_gamma(d); rt = []; isint = []
        for _ in range(m): rt.append(types[d.uni(len(types))]); isint.append(d.uni(2))
        re = []
        for j in range(m):
            for _ in range(get_gamma(d)):
                a = d.uni(m); P = pins[rt[j]]; p = P[d.uni(len(P))] if len(P) > 1 else P[0]
                re.append((a, j, p))
        reps.append((rt, isint, re, get_gamma(d) + 1))
    edges = []; nid = g
    for rt, isint, re, ncopy in reps:
        seen = collections.defaultdict(list); counts = collections.defaultdict(collections.Counter)
        for _ in range(ncopy):
            used = set(); mp = {}
            for j, t in enumerate(rt):
                if isint[j]: mp[j] = nid; ntype.append(t); nid += 1; continue
                cand = [y for y in seen[t] if y not in used]; table = [counts[t][y] for y in cand] + [1]
                k = d.freq(table)
                if k < len(cand): x = cand[k]
                else:
                    free = [y for y in range(start[t], start[t] + cnt[types.index(t)]) if y not in used and y not in counts[t]]
                    x = free[d.uni(len(free))]; seen[t].append(x)
                counts[t][x] += 1; used.add(x); mp[j] = x
            edges += [(mp[a], mp[b], p) for a, b, p in re]
    n = nid
    for j in range(n):
        P = pins[ntype[j]]
        for _ in range(get_gamma(d)):
            a = d.uni(n); p = P[d.uni(len(P))] if len(P) > 1 else P[0]
            edges.append((a, j, p))
    assert d.done()
    return sorted(edges), ntype

def verify(b, info):
    edges, ntype = decode(b)
    return edges == info['graph'] and ntype == info['types']

def best(E, typ, info, classes):
    """MDL choice of the classes to factor: start with every class that has >= 2 copies, drop classes while that helps."""
    F = {c for c, ks in classes.items() if len(ks) >= 2}
    cost = lambda F: encode(E, typ, info, classes, F, want_bytes=False)[1]['bits']
    cur = cost(F); improved = True
    while improved and F:
        improved = False
        for c in sorted(F, key=lambda c: len(classes[c])):
            x = cost(F - {c})
            if x < cur: F = F - {c}; cur = x; improved = True
    return F
