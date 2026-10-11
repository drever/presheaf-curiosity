"""Test A: Makros mit Interface. Instanzkosten zahlen nur die Randknoten (Knoten, die auch Kanten ausserhalb der Instanz haben);
innere Knoten werden vom Dekoder frisch vergeben. Kosten je Instanz: Musterindex + |V_p|-Zaehler k + Teilmenge der Randknoten
(log C(|V_p|,k)) + k Zeiger. Zur Sicherheit min() mit dem alten Schema + 1 Flagbit."""
import math
import und
from und import cover_u
from und3 import dict_bits_h
from core import LOG

def lcomb(n, k): return math.log2(math.comb(n, k)) if 0 <= k <= n else 0.0

def inst_bits(c, D, pi, ids, mm, n):
    mp = dict(mm); idset = set(ids); V = len(mp)
    k = 0
    for pv, cv in mp.items():
        if any(e[0] not in idset for e in c.out[cv]) or any(e[0] not in idset for e in c.inn[cv]): k += 1
    old = LOG(len(D) + 1) + V * n
    new = LOG(len(D) + 1) + LOG(V + 1) + lcomb(V, k) + k * n
    return old, new, k, V

def total_iface(comps, D, R, maxn, with_dict=True, stats=None):
    s = 0
    for c in comps:
        inst, raw = cover_u(c, D); n = LOG(c.n)
        s += len(raw) * (2 * n + LOG(R))
        for pi, ids, mm in inst:
            o, w, k, V = inst_bits(c, D, pi, ids, mm, n)
            s += min(o, w) + 1
            if stats is not None: stats.append((V, k, o, w))
    return s + (dict_bits_h(D, R, maxn) if with_dict else 0)

def total_old(comps, D, R, maxn, with_dict=True):
    return und.total_u(comps, D, R, maxn, False) + (dict_bits_h(D, R, maxn) if with_dict else 0)
