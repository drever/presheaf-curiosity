import collections
from rdkit import Chem, RDLogger
RDLogger.DisableLog('rdApp.*')
from core import Comp

def load_mols(path):
    out = []
    for m in Chem.SDMolSupplier(path):
        if m is None: continue
        el = [a.GetSymbol() for a in m.GetAtoms()]
        out.append((m.GetNumAtoms(), [(b.GetBeginAtomIdx(), b.GetBondTypeAsDouble(), b.GetEndAtomIdx()) for b in m.GetBonds()], el))
    return out

def canon_bond(el, a, b, bt): return (a, b) if el[a] <= el[b] else (b, a)

def sample_comps(mols, N, k, rng, relid):
    big = [i for i, m in enumerate(mols) if m[0] >= k]; seen = set(); comps = []; tries = 0
    while len(comps) < N and tries < 100 * N:
        tries += 1; mi = rng.choice(big); n, bonds, el = mols[mi]
        nb = collections.defaultdict(set)
        for a, bt, b in bonds: nb[a].add(b); nb[b].add(a)
        S = [rng.randrange(n)]
        while len(S) < k:
            cand = [x for u in S for x in nb[u] if x not in S]
            if not cand: break
            S.append(rng.choice(cand))
        if len(S) < k: continue
        key = (mi, frozenset(S))
        if key in seen: continue
        seen.add(key); ix = {v: i for i, v in enumerate(S)}; ed = []
        for a, bt, b in bonds:
            if a in ix and b in ix:
                x, y = canon_bond(el, a, b, bt); ed.append((ix[x], relid[(bt, el[x], el[y])], ix[y]))
        comps.append(Comp(k, ed))
    return comps
