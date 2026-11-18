"""Actual encoder and decoder for dictionaries with PRODUCTS and with HOLES (lab notebook, section 16).

Extends coder.py (plain gluing dictionaries) in three ways:
  * Entropy coding. Symbols are written with exact big-integer rANS: a symbol with frequency f out of total T costs
    log2(T/f) bits (a uniform symbol from range r is the case f = 1, T = r, i.e. the mixed-radix code of coder.py).
  * Product closure. The file carries the explicit patterns Dp, the factor patterns F (as references into Dp, or as edge
    lists when a factor is not in Dp), the label classes and the cap maxe. The decoder rebuilds the implicit products
    itself with und4.implicit_products and so obtains exactly the effective dictionary the encoder used.
  * Holes. A hole is (frame pattern, two frame nodes p, q, list of filler patterns). Every occurrence of the frame
    stores which filler sits in each of its holes, or "none"; the choice is coded with option frequencies counted on
    the data itself (two passes; the counts are in the file). An inserted filler costs no pattern index and no pointers
    of its attachment nodes; its inner nodes are pointed to only if they have edges outside the unit (mode 'boundary').
    The model of holes2.py distinguishes "empty" and "other"; the coder merges both into "none" (no filler edges
    inserted; whatever is there stays for later instances or raw edges).

Everything that the decoder needs is in the bytes. verify() decodes and compares, as in coder.py.
Files are written for a list of components (windows); the dictionary is written once."""
import math, collections
import und
from und import cover_u, canon_u, embed_u
from core import order_pattern
import und4
import holes2 as H2
from coder import _subset_rank, _subset_unrank, _wl

HDR = 1 << 32; SMALL = 1 << 16


class Enc:
    """Collects (cum, freq, total) triples; rANS is last-in-first-out, so they are encoded in reverse at the end."""
    def __init__(s): s.sy = []; s.bits = 0.0
    def uni(s, v, r):
        assert 0 <= v < r, (v, r); s.sy.append((v, 1, r)); s.bits += math.log2(r)
    def freq(s, sym, table):
        """table: list of positive integer frequencies; sym: index into it"""
        T = sum(table); c = sum(table[:sym]); f = table[sym]; assert f > 0
        s.sy.append((c, f, T)); s.bits += math.log2(T / f)
    def tobytes(s):
        x = 1
        for c, f, T in reversed(s.sy): x = (x // f) * T + c + (x % f)
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')


class Dec:
    def __init__(s, b): s.x = int.from_bytes(b, 'big')
    def uni(s, r):
        s.x, v = divmod(s.x, r); return v
    def freq(s, table):
        T = sum(table); s.x, m = divmod(s.x, T); c = 0
        for k, f in enumerate(table):
            if m < c + f: s.x = f * s.x + m - c; return k
            c += f
    def done(s): return s.x == 1


def put_gamma(w, v):
    """Elias gamma code of v >= 0 (2*floor(log2(v+1)) + 1 bits)."""
    x = v + 1; k = x.bit_length()
    for _ in range(k - 1): w.uni(0, 2)
    w.uni(1, 2)
    for i in range(k - 2, -1, -1): w.uni((x >> i) & 1, 2)

def get_gamma(d):
    k = 1
    while d.uni(2) == 0: k += 1
    x = 1
    for _ in range(k - 1): x = 2 * x + d.uni(2)
    return x - 1

def _put_pattern(w, p, R):
    """Flat edge list; vertex numbers 0..V-1 are kept."""
    V = 1 + max(max(a, b) for a, _, b in p)
    put_gamma(w, len(p)); put_gamma(w, V)
    for a, r, b in p: w.uni(a, V); w.uni(r, R); w.uni(b, V)

def _get_pattern(d, R):
    ne = get_gamma(d); V = get_gamma(d)
    return tuple((d.uni(V), d.uni(R), d.uni(V)) for _ in range(ne))

def _hier_parts(p, earlier):
    """Parts of p: instances of earlier patterns (largest first, as und.cover_u) and leftover edges; vertices of p."""
    from core import Comp
    vs = sorted({x for a, r, b in p for x in (a, b)}); ix = {v: i for i, v in enumerate(vs)}
    comp = Comp(len(vs), [(ix[a], r, ix[b]) for a, r, b in p]); inst, raw = cover_u(comp, earlier)
    parts = [('ref', pi, [dict(mm)[v] for v in range(_nverts(earlier[pi]))]) for pi, ids, mm in inst]
    parts += [('edge', comp.E[e][2], [comp.E[e][1], comp.E[e][3]]) for e in raw]
    return parts, vs

def _put_hier(w, parts, earlier, R):
    """Writes the parts; returns the decoded pattern and the map (vertex of the cover component -> decoded vertex)."""
    put_gamma(w, len(parts)); seen = []; num = {}; edges = []
    for kind, x, verts in parts:
        if earlier: w.uni(kind == 'ref', 2)
        if kind == 'ref': w.uni(x, len(earlier))
        else: w.uni(x, R)
        for v in verts:
            if seen: w.uni(v in num, 2)
            if v in num: w.uni(seen.index(v), len(seen))
            else: num[v] = len(seen); seen.append(v)
        loc = [num[v] for v in verts]
        if kind == 'ref': edges += [(loc[a], r, loc[b]) for a, r, b in earlier[x]]
        else: edges.append((loc[0], x, loc[1]))
    return tuple(order_pattern(edges)), num

def _get_hier(d, earlier, R):
    n = get_gamma(d); seen = 0; edges = []
    for _ in range(n):
        ref = d.uni(2) if earlier else 0
        x = d.uni(len(earlier)) if ref else d.uni(R)
        k = _nverts(earlier[x]) if ref else 2; loc = []
        for _ in range(k):
            old = d.uni(2) if seen else 0
            if old: loc.append(d.uni(seen))
            else: loc.append(seen); seen += 1
        if ref: edges += [(loc[a], r, loc[b]) for a, r, b in earlier[x]]
        else: edges.append((loc[0], x, loc[1]))
    return tuple(order_pattern(edges))

def put_dict(w, D, R):
    """Each pattern flat or as a gluing of earlier (already decoded) patterns, whichever is shorter. Returns the decoded
    dictionary and, per pattern, the map from the given pattern's vertices to the decoded pattern's vertices."""
    put_gamma(w, len(D)); out = []; maps = []
    for p in D:
        parts, vs = _hier_parts(p, out); t = Enc(); dec, num = _put_hier(t, parts, out, R); f = Enc(); _put_pattern(f, p, R)
        if t.bits < f.bits:
            w.uni(1, 2); _put_hier(w, parts, out, R); out.append(dec); maps.append({vs[c]: num[c] for c in num})
        else:
            w.uni(0, 2); _put_pattern(w, p, R); out.append(tuple(p)); maps.append({v: v for v in range(_nverts(p))})
    return out, maps

def get_dict(d, R):
    out = []
    for _ in range(get_gamma(d)): out.append(_get_hier(d, out, R) if d.uni(2) else _get_pattern(d, R))
    return out

def _nverts(p): return 1 + max(max(a, b) for a, _, b in p)


# ---------------------------------------------------------------- model description

def model_plain(D):
    return {'kind': 'plain', 'Dp': [tuple(p) for p in D]}

def model_product(Dp, F, col, maxe):
    """col: label -> class 0/1 (labels without class absent); None means no class restriction (products of all pairs)."""
    return {'kind': 'product', 'Dp': [tuple(p) for p in Dp], 'F': [tuple(f) for f in F], 'col': col, 'maxe': maxe}

def model_holes(D, holes, lib, alive):
    return {'kind': 'holes', 'D': [tuple(p) for p in D], 'holes': holes, 'lib': lib, 'alive': set(alive)}


def effective(model):
    """The dictionary the cover uses, computed exactly as the decoder will compute it."""
    if model['kind'] == 'plain': return list(model['Dp'])
    if model['kind'] == 'product':
        cross = None
        if model['col'] is not None: cross = und4.class_preds(model['col'])[1]
        imp = und4.implicit_products(model['F'], model['maxe'], cross)
        have = {canon_u(p, und4.UND) for p in model['Dp']}
        return list(model['Dp']) + [p for p in imp if canon_u(p, und4.UND) not in have]
    raise ValueError


# ---------------------------------------------------------------- parse (encoder only)

def parse_holes(c, D, holes, lib, alive):
    """Same procedure as holes2.window_cost: frames with holes first (largest first), fillers in library order, then the
    remaining alive patterns, then raw edges. Returns (units, instances, raw)."""
    used = set(); units = []; bykey = collections.defaultdict(list)
    for hi, h in enumerate(holes): bykey[h['key'][0]].append((hi, h))
    for pi in sorted(bykey, key=lambda i: -len(D[i])):
        while True:
            res = embed_u(D[pi], c, used)
            if not res: break
            ids, m = res; A_ids = set(ids); A_V = set(m.values()); fill_ids = set(); choice = []
            for hi, h in bykey[pi]:
                _, p, q = h['key']; a, b = m[p], m[q]; got = None
                for oi, f in enumerate(h['fil']):
                    r = H2.match_filler(c, lib[f], a, b, A_V - {a, b}, used | A_ids | fill_ids)
                    if r: got = (oi, r); break
                if got: fill_ids |= set(got[1][0]); choice.append((hi, got[0], got[1][1]))
                else: choice.append((hi, None, None))
            used |= A_ids | fill_ids; units.append((pi, dict(m), choice, A_ids | fill_ids))
    inst, raw, used = H2.cover_used(c, D, used, alive)
    return units, [(pi, dict(m), ids) for pi, ids, m in inst], raw


def _unit_nodes(D, holes, lib, pi, m, choice):
    """Node order of a unit: frame vertices 0..V-1, then for each hole with a filler the filler's inner vertices 2..Vf-1."""
    nodes = [m[v] for v in range(_nverts(D[pi]))]
    for hi, oi, fm in choice:
        if oi is None: continue
        f = lib[holes[hi]['fil'][oi]]
        nodes += [fm[v] for v in range(2, _nverts(f))]
    return nodes


# ---------------------------------------------------------------- encode / decode

def _write_pointers(w, comp, nodes, idset, n, mode, fresh):
    if mode == 'all':
        for x in nodes: w.uni(x, n)
        return
    V = len(nodes)
    bnd = [i for i, x in enumerate(nodes) if any(e[0] not in idset for e in comp.out[x]) or any(e[0] not in idset for e in comp.inn[x])]
    w.uni(len(bnd), V + 1); w.uni(_subset_rank(bnd, V), math.comb(V, len(bnd)))
    for i in bnd: w.uni(nodes[i], n)
    fresh += [nodes[i] for i in range(V) if i not in set(bnd)]

def _read_pointers(d, V, n, mode, nxt, fresh):
    if mode == 'all': return [d.uni(n) for _ in range(V)], nxt
    k = d.uni(V + 1); bnd = _subset_unrank(d.uni(math.comb(V, k)), V, k); out = [None] * V
    for i in bnd: out[i] = d.uni(n)
    for i in range(V):
        if out[i] is None: out[i] = nxt; fresh.append(nxt); nxt += 1
    return out, nxt


def encode(comps, model, R, mode='boundary'):
    """Returns (bytes, info). info['per_comp_bits'] = data bits of each component (excluding dictionary and header).
    The encoder covers with the dictionary exactly as the decoder will rebuild it (hierarchically coded patterns come back
    renumbered, so the encoder switches to the decoded versions before covering)."""
    w = Enc(); kind = {'plain': 0, 'product': 1, 'holes': 2}[model['kind']]; w.uni(kind, 3); put_gamma(w, R); put_gamma(w, len(comps))
    w.uni({'all': 0, 'boundary': 1}[mode], 2)
    ns = {c.n for c in comps}; w.uni(len(ns) == 1, 2)
    if len(ns) == 1: put_gamma(w, comps[0].n)
    b0 = w.bits
    if model['kind'] in ('plain', 'product'):
        Dp, _ = put_dict(w, model['Dp'], R); m2 = dict(model, Dp=Dp)
        if model['kind'] == 'product':
            put_gamma(w, model['maxe']); put_gamma(w, len(model['F'])); keys = [canon_u(p, und4.UND) for p in Dp]; F = []
            for f in model['F']:
                k = canon_u(f, und4.UND)
                if k in keys: w.uni(1, 2); w.uni(keys.index(k), len(Dp)); F.append(Dp[keys.index(k)])
                else: w.uni(0, 2); _put_pattern(w, f, R); F.append(tuple(f))
            w.uni(model['col'] is not None, 2)
            if model['col'] is not None:
                for r in range(R): w.uni({None: 0, 0: 1, 1: 2}[model['col'].get(r)], 3)
            m2['F'] = F
        D = effective(m2); holes = []; lib = {}; alive = None
    else:
        D0 = model['D']; frames = sorted({h['key'][0] for h in model['holes']}); keep = sorted(set(model['alive']) | set(frames))
        remap = {j: i for i, j in enumerate(keep)}; D, maps = put_dict(w, [D0[j] for j in keep], R); alive = {remap[j] for j in model['alive']}
        libkeys = sorted({f for h in model['holes'] for f in h['fil']}, key=str); lib = {f: model['lib'][f] for f in libkeys}
        holes = []
        for h in model['holes']:
            pi = remap[h['key'][0]]; holes.append({'key': (pi, maps[pi][h['key'][1]], maps[pi][h['key'][2]]), 'fil': list(h['fil'])})
        for i in range(len(D)): w.uni(i in alive, 2)
        put_gamma(w, len(libkeys)); lidx = {f: i for i, f in enumerate(libkeys)}
        for f in libkeys: _put_pattern(w, lib[f], R)
        put_gamma(w, len(holes))
        for h in holes:
            pi, p, q = h['key']; V = _nverts(D[pi]); w.uni(pi, len(D)); w.uni(p, V); w.uni(q, V); put_gamma(w, len(h['fil']))
            for f in h['fil']: w.uni(lidx[f], len(libkeys))
    # first pass: parse every component, count hole options
    parses = []; counts = [[0] * (len(h['fil']) + 1) for h in holes]
    for c in comps:
        if model['kind'] == 'holes':
            units, inst, raw = parse_holes(c, D, holes, lib, alive)
            for _, _, choice, _ in units:
                for hi, oi, _ in choice: counts[hi][len(holes[hi]['fil']) if oi is None else oi] += 1
        else:
            ii, raw = cover_u(c, D); units = []; inst = [(pi, dict(mm), set(ids)) for pi, ids, mm in ii]
        parses.append((units, inst, raw))
    tables = [[k + 1 for k in cnt] for cnt in counts]          # +1: every option stays decodable
    for cnt in counts:
        for k in cnt: put_gamma(w, k)
    dict_bits = w.bits - b0; per = []; fresh = []
    hframes = sorted({h['key'][0] for h in holes}); hidx = {pi: i for i, pi in enumerate(hframes)}
    plain_ix = sorted(alive) if alive is not None else list(range(len(D))); pidx = {pi: i for i, pi in enumerate(plain_ix)}
    for c, (units, inst, raw) in zip(comps, parses):
        fresh.append([]); b = w.bits; n = c.n
        if len(ns) > 1: put_gamma(w, n)
        put_gamma(w, len(units)) if hframes else None; put_gamma(w, len(inst)); put_gamma(w, len(raw))
        for pi, m, choice, ids in units:
            w.uni(hidx[pi], len(hframes))
            for hi, oi, _ in choice: w.freq(len(holes[hi]['fil']) if oi is None else oi, tables[hi])
            _write_pointers(w, c, _unit_nodes(D, holes, lib, pi, m, choice), ids, n, mode, fresh[-1])
        for pi, m, ids in inst:
            w.uni(pidx[pi], len(plain_ix)); _write_pointers(w, c, [m[v] for v in range(_nverts(D[pi]))], set(ids), n, mode, fresh[-1])
        for e in raw:
            _, a, r, bb = c.E[e]; w.uni(a, n); w.uni(r, R); w.uni(bb, n)
        per.append(w.bits - b)
    out = w.tobytes()
    return out, {'bytes': len(out), 'bits_exact': w.bits, 'dict_bits': dict_bits, 'per_comp_bits': per, 'effective_dict_size': len(D),
                 'units': sum(len(p[0]) for p in parses), 'instances': sum(len(p[1]) for p in parses), 'raw_edges': sum(len(p[2]) for p in parses),
                 'option_counts': counts, 'fresh_order': fresh}


def decode(b):
    """Returns list of (n, sorted edge list) per component, the freshly numbered nodes per component in order, and the mode."""
    d = Dec(b); kind = d.uni(3); R = get_gamma(d); ncomp = get_gamma(d); mode = ['all', 'boundary'][d.uni(2)]
    same_n = d.uni(2); n0 = get_gamma(d) if same_n else None
    holes = []; lib = []
    if kind in (0, 1):
        Dp = get_dict(d, R)
        if kind == 1:
            maxe = get_gamma(d); F = []
            for _ in range(get_gamma(d)): F.append(Dp[d.uni(len(Dp))] if d.uni(2) else _get_pattern(d, R))
            col = None
            if d.uni(2):
                col = {}
                for r in range(R):
                    v = d.uni(3)
                    if v: col[r] = v - 1
            D = effective({'kind': 'product', 'Dp': Dp, 'F': F, 'col': col, 'maxe': maxe})
        else: D = Dp
        alive = list(range(len(D)))
    else:
        D = get_dict(d, R); alive = [i for i in range(len(D)) if d.uni(2)]
        lib = [_get_pattern(d, R) for _ in range(get_gamma(d))]
        for _ in range(get_gamma(d)):
            pi = d.uni(len(D)); V = _nverts(D[pi]); p = d.uni(V); q = d.uni(V); nf = get_gamma(d)
            holes.append({'key': (pi, p, q), 'fil': [d.uni(len(lib)) for _ in range(nf)]})
    tables = [[get_gamma(d) + 1 for _ in range(len(h['fil']) + 1)] for h in holes]
    hframes = sorted({h['key'][0] for h in holes}); byframe = collections.defaultdict(list)
    for hi, h in enumerate(holes): byframe[h['key'][0]].append(hi)
    out = []; fresh = []
    for _ in range(ncomp):
        n = n0 if same_n else get_gamma(d)
        nu = get_gamma(d) if hframes else 0; ni = get_gamma(d); nr = get_gamma(d); edges = []; nxt = n; fresh.append([])
        for _ in range(nu):
            pi = hframes[d.uni(len(hframes))]; choice = []
            for hi in byframe[pi]:
                o = d.freq(tables[hi]); choice.append((hi, None if o == len(holes[hi]['fil']) else o))
            V = _nverts(D[pi]); extra = [(hi, oi, _nverts(lib[holes[hi]['fil'][oi]]) - 2) for hi, oi in choice if oi is not None]
            nodes, nxt = _read_pointers(d, V + sum(x[2] for x in extra), n, mode, nxt, fresh[-1])
            edges += [(nodes[a], r, nodes[bb]) for a, r, bb in D[pi]]; pos = V
            for hi, oi, k in extra:
                _, p, q = holes[hi]['key']; f = lib[holes[hi]['fil'][oi]]; loc = {0: nodes[p], 1: nodes[q]}
                for v in range(2, 2 + k): loc[v] = nodes[pos + v - 2]
                edges += [(loc[a], r, loc[bb]) for a, r, bb in f]; pos += k
        for _ in range(ni):
            pi = alive[d.uni(len(alive))]; nodes, nxt = _read_pointers(d, _nverts(D[pi]), n, mode, nxt, fresh[-1])
            edges += [(nodes[a], r, nodes[bb]) for a, r, bb in D[pi]]
        for _ in range(nr): edges.append((d.uni(n), d.uni(R), d.uni(n)))
        out.append((n, sorted(edges)))
    assert d.done(), 'trailing data'
    return out, fresh, mode


def verify(comps, b, info):
    dec, fresh, mode = decode(b); orig = [sorted((a, r, bb) for _, a, r, bb in c.E) for c in comps]
    if mode == 'all': return {'exact_equal': [e for _, e in dec] == orig}
    back = []; inj = True
    for (_, e), fd, fe in zip(dec, fresh, info['fresh_order']):
        ren = dict(zip(fd, fe)); inj &= len(set(ren.values())) == len(ren) == len(fd)
        back.append(sorted((ren.get(u, u), r, ren.get(v, v)) for u, r, v in e))
    return {'equal_after_renaming': back == orig, 'renaming_is_injective': inj,
            'colour_refinement_equal': all(_wl(e) == _wl(o) for (_, e), o in zip(dec, orig))}
