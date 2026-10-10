import math, collections
import pynauty
from gspan_mining import gSpan

LOG = math.log2

class Comp:
    def __init__(s, n, edges):
        s.n = n
        s.E = [(i, a, r, b) for i, (a, r, b) in enumerate(edges)]
        s.out = collections.defaultdict(list); s.inn = collections.defaultdict(list); s.byrel = collections.defaultdict(list)
        for e in s.E:
            s.out[e[1]].append(e); s.inn[e[3]].append(e); s.byrel[e[2]].append(e)

def order_pattern(edges):
    rest = list(edges); out = [rest.pop(0)]; seen = {out[0][0], out[0][2]}
    while rest:
        for i, e in enumerate(rest):
            if e[0] in seen or e[2] in seen:
                out.append(rest.pop(i)); seen |= {e[0], e[2]}; break
        else: raise ValueError('unzusammenhaengend')
    return out

def normalize(edges):
    vs = sorted({x for e in edges for x in (e[0], e[2])}); ix = {v: i for i, v in enumerate(vs)}
    return tuple(sorted((ix[a], r, ix[b]) for a, r, b in edges))

def dict_bits(D, R, maxn):
    return sum(2 + len(p) * (2 * LOG(maxn) + LOG(R)) for p in D)

class GS(gSpan):
    def _report(self, projected): self.found.append((list(self._DFScode), self._support))
    def _report_size1(self, g, support): pass
