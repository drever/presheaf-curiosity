"""Hybrid: exakte (voll beschriftete) Muster UND Formmuster mit Labelverteilung (Anti-Unifikation) in EINEM Woerterbuch.
Kostenbewusste greedy-Ueberdeckung: in jedem Schritt wird die Musterinstanz mit dem groessten Bitgewinn gewaehlt.
Exakte Instanz: Musterindex + Schnittstelle. Forminstanz: dasselbe + sum -log2 p(Label | Musterkante)."""
import math, collections
import und
from und import embed_u
from core import LOG
from iface import lcomb
from e27 import erase, label_bits, fit_labels, label_dict_bits
from und3 import dict_bits_h

def inst_cost(comp, ids, mp, n, ND):
    idset = set(ids); V = len(mp); k = 0
    for cv in mp.values():
        if any(e[0] not in idset for e in comp.out[cv]) or any(e[0] not in idset for e in comp.inn[cv]): k += 1
    old = LOG(ND + 1) + V * n; new = LOG(ND + 1) + LOG(V + 1) + lcomb(V, k) + k * n
    return min(old, new) + 1

def cover_hybrid(c, Dex, Ds, counts, N, R):
    ec = erase(c); n = LOG(c.n); ND = len(Dex) + len(Ds); used = set(); inst = []
    while True:
        best = None
        for typ, D, comp in (('ex', Dex, c), ('sh', Ds, ec)):
            for pi, p in enumerate(D):
                res = embed_u(p, comp, used)
                if not res: continue
                ids, m = res
                bits = inst_cost(comp, ids, m, n, ND)
                if typ == 'sh': bits += sum(label_bits(counts[pi][j], N[pi], c.E[e][2], False) for j, e in enumerate(ids))
                gain = len(ids) * (2 * n + LOG(R)) - bits
                if gain > 0 and (best is None or gain > best[0]): best = (gain, typ, pi, ids, bits)
        if best is None: break
        _, typ, pi, ids, bits = best; used |= set(ids); inst.append((typ, pi, tuple(ids), bits))
    raw = [e[0] for e in c.E if e[0] not in used]
    return inst, raw

def cost_hybrid(comps, Dex, Ds, counts, N, R):
    s = 0
    for c in comps:
        inst, raw = cover_hybrid(c, Dex, Ds, counts, N, R); n = LOG(c.n)
        s += len(raw) * (2 * n + LOG(R)) + sum(b for *_, b in inst)
    return s / len(comps)

def learn_hybrid(train, Dex, Ds, R, rounds=2):
    counts, N = fit_labels(train, Ds)                      # Start: Verteilungen aus reiner Form-Ueberdeckung
    for _ in range(rounds):
        cn = collections.defaultdict(lambda: collections.defaultdict(collections.Counter)); Nn = collections.Counter()
        useEx = collections.Counter(); useSh = collections.Counter()
        for c in train:
            inst, raw = cover_hybrid(c, Dex, Ds, counts, N, R)
            for typ, pi, ids, _ in inst:
                if typ == 'ex': useEx[pi] += 1
                else:
                    useSh[pi] += 1; Nn[pi] += 1
                    for j, e in enumerate(ids): cn[pi][j][c.E[e][2]] += 1
        counts, N = cn, Nn
    return counts, N, useEx, useSh

def prune_dicts(Dex, Ds, useEx, useSh, counts, N):
    """Unbenutzte Muster entfernen; Verteilungen und Indizes neu abbilden."""
    keepS = [i for i in range(len(Ds)) if useSh[i] > 0]; keepE = [i for i in range(len(Dex)) if useEx[i] > 0]
    Ds2 = [Ds[i] for i in keepS]; Dex2 = [Dex[i] for i in keepE]
    c2 = collections.defaultdict(lambda: collections.defaultdict(collections.Counter)); N2 = collections.Counter()
    for new, old in enumerate(keepS): c2[new] = counts[old]; N2[new] = N[old]
    return Dex2, Ds2, c2, N2
