"""An actual encoder and decoder for the dictionary-plus-cover description of a graph.

Until now every number for our method was a computed code length. This module writes the bytes and reads them back.

Coding: every symbol is an integer from a known range; the whole message is one mixed-radix integer, so a symbol with
range r costs exactly log2(r) bits and the file is ceil(total bits / 8) bytes. No probabilities, no arithmetic coder.

File layout
  header   n (number of nodes), R (label alphabet), number of patterns, number of instances, number of raw edges
  patterns for each: number of edges, number of nodes, then (a, label, b) per edge            (flat, not hierarchical)
  instances for each: pattern index, then
      mode 'all'      : one node pointer per pattern node                      -> node numbers are preserved exactly
      mode 'boundary' : k, which k of the V pattern nodes are boundary nodes, k node pointers; the other nodes have no
                        edge outside the instance and are numbered afresh by the decoder -> graph preserved up to
                        renaming of those nodes
  raw edges (u, label, v)

decode() needs nothing but the bytes. Verification is in verify(): exact equality in mode 'all'; in mode 'boundary'
equality after renaming, with the renaming checked to be a bijection that fixes every boundary node, plus an independent
isomorphism check by colour refinement."""
import math, collections
from und import cover_u


class Writer:
    def __init__(s): s.syms = []; s.bits = 0.0
    def put(s, v, r):
        assert 0 <= v < r, (v, r)
        s.syms.append((v, r)); s.bits += math.log2(r)
    def tobytes(s):
        x = 0
        for v, r in reversed(s.syms): x = x * r + v
        return x.to_bytes(max(1, (x.bit_length() + 7) // 8), 'big')


class Reader:
    def __init__(s, b): s.x = int.from_bytes(b, 'big')
    def get(s, r):
        s.x, v = divmod(s.x, r); return v


def _subset_rank(sub, V):
    """Rank of a sorted k-subset of range(V) among all k-subsets (combinatorial number system)."""
    return sum(math.comb(c, i + 1) for i, c in enumerate(sub))

def _subset_unrank(rank, V, k):
    out = []
    for i in range(k, 0, -1):
        c = i - 1
        while math.comb(c + 1, i) <= rank: c += 1
        out.append(c); rank -= math.comb(c, i)
    return sorted(out)


HDR = 1 << 32

def encode(comp, D, R, mode='boundary'):
    """comp: core.Comp; D: list of patterns (tuples of (a, label, b)). Returns (bytes, info)."""
    inst, raw = cover_u(comp, D); n = comp.n; w = Writer()
    for v in (n, R, len(D), len(inst), len(raw)): w.put(v, HDR)
    hdr_bits = w.bits
    for p in D:
        V = 1 + max(max(a, b) for a, _, b in p)
        w.put(len(p), HDR >> 16); w.put(V, HDR >> 16)
        for a, r, b in p: w.put(a, V); w.put(r, R); w.put(b, V)
    dict_bits = w.bits - hdr_bits; fresh = []
    for pi, ids, mm in inst:
        mp = dict(mm); V = len(mp); idset = set(ids); w.put(pi, len(D))
        if mode == 'all':
            for pv in range(V): w.put(mp[pv], n)
        else:
            bnd = [pv for pv in range(V) if any(e[0] not in idset for e in comp.out[mp[pv]]) or any(e[0] not in idset for e in comp.inn[mp[pv]])]
            w.put(len(bnd), V + 1); w.put(_subset_rank(bnd, V), math.comb(V, len(bnd)))
            for pv in bnd: w.put(mp[pv], n)
            fresh += [mp[pv] for pv in range(V) if pv not in set(bnd)]
    inst_bits = w.bits - hdr_bits - dict_bits
    for e in raw:
        _, a, r, b = comp.E[e]; w.put(a, n); w.put(r, R); w.put(b, n)
    b = w.tobytes()
    return b, {'bytes': len(b), 'bits_exact': w.bits, 'header_bits': hdr_bits, 'dict_bits': dict_bits, 'instance_bits': inst_bits,
               'raw_bits': w.bits - hdr_bits - dict_bits - inst_bits, 'instances': len(inst), 'raw_edges': len(raw), 'fresh_order': fresh}


def decode(b, mode='boundary'):
    """Returns (n, sorted edge list [(u, label, v)], list of freshly numbered nodes in order of creation)."""
    rd = Reader(b); n, R, nD, nI, nR = (rd.get(HDR) for _ in range(5)); D = []
    for _ in range(nD):
        ne = rd.get(HDR >> 16); V = rd.get(HDR >> 16); D.append((V, [(rd.get(V), rd.get(R), rd.get(V)) for _ in range(ne)]))
    edges = []; nxt = n; fresh = []
    for _ in range(nI):
        V, p = D[rd.get(nD)]
        if mode == 'all': mp = [rd.get(n) for _ in range(V)]
        else:
            k = rd.get(V + 1); bnd = _subset_unrank(rd.get(math.comb(V, k)), V, k); mp = [None] * V
            for pv in bnd: mp[pv] = rd.get(n)
            for pv in range(V):
                if mp[pv] is None: mp[pv] = nxt; fresh.append(nxt); nxt += 1      # numbered afresh, above the original range
        edges += [(mp[a], r, mp[bb]) for a, r, bb in p]
    for _ in range(nR): edges.append((rd.get(n), rd.get(R), rd.get(n)))
    return n, sorted(edges), fresh


def _wl(edges, rounds=6):
    col = collections.defaultdict(int)
    for _ in range(rounds):
        sig = collections.defaultdict(list)
        for u, r, v in edges: sig[u].append(('o', r, col[v])); sig[v].append(('i', r, col[u]))
        col = collections.defaultdict(int, {x: hash((col[x], tuple(sorted(s)))) for x, s in sig.items()})
    return sorted(collections.Counter(col.values()).items())

def verify(comp, b, info, mode):
    orig = sorted((a, r, bb) for _, a, r, bb in comp.E); n, dec, fresh = decode(b, mode)
    if mode == 'all': return {'exact_equal': dec == orig}
    ren = dict(zip(fresh, info['fresh_order']))                              # decoder's fresh node -> original node
    back = sorted((ren.get(u, u), r, ren.get(v, v)) for u, r, v in dec)
    touched = {x for u, _, v in dec for x in (u, v)}
    return {'equal_after_renaming': back == orig, 'renaming_is_bijection': len(set(ren.values())) == len(ren) and not (set(ren.values()) & (touched - set(ren))),
            'nodes_renamed': len(ren), 'colour_refinement_equal': _wl(dec) == _wl(orig)}
