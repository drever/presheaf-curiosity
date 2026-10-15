"""Test E2b Tiefe 2: Loch in Loch (Hom(A, B^C)). Fuellung eines Lochs ist selbst ein Rahmen ('Mittelstueck') mit eigenem Loch.
Pipeline: (1) Tiefe-1-Modell (flache Fuellungen, maxF gross) -> (2) die gefundenen flachen Fuellungen als Trainingsfenster (mit Markern an a,b)
-> H2.refine darauf (Woerterbuch D', Loecher H', Blatt-Bibliothek) -> (3) Mittelstueck x Blatt wird zu zusammengesetzten Fuellungen expandiert
(auch ungesehene Kombinationen), Optionswahrscheinlichkeit = p_mitte * p_blatt. Kosten der Bibliothek: Mitten + Blaetter + Unterloecher statt Produktmenge."""
import collections, os
from core import Comp, LOG
import holes2 as H2
from und import embed_u

def collect_fillers(c, D, H, lib):
    used = set(); out = []; bykey = collections.defaultdict(list)
    for h in H: bykey[h['key'][0]].append(h)
    for pi in sorted(bykey, key=lambda i: -len(D[i])):
        while True:
            res = embed_u(D[pi], c, used)
            if not res: break
            ids, m = res; A_ids = set(ids); A_V = set(m.values()); fill = set()
            for hi, h in enumerate(bykey[pi]):
                _, p, q = h['key']; a, b = m[p], m[q]
                for f in h['fil']:
                    r = H2.match_filler(c, lib[f], a, b, A_V - {a, b}, used | A_ids | fill)
                    if r: fill |= set(r[0]); out.append((h['key'], f)); break
            used |= A_ids | fill
    return out

def marked_comp(pat, R):
    n = 2 + max([max(u, v) for u, _, v in pat] + [1])
    return Comp(n + 2, list(pat) + [(n, R + 1, 0), (n + 1, R + 2, 1)])

def parse_mid(P, R):
    """Rahmenmuster mit Markern -> (lokale Kanten, Knotenabbildung alt->lokal) oder None."""
    ma = [v for u, r, v in P if r == R + 1]; mb = [v for u, r, v in P if r == R + 2]
    if len(ma) != 1 or len(mb) != 1 or ma[0] == mb[0]: return None
    dummy = {u for u, r, v in P if r in (R + 1, R + 2)}
    loc = {ma[0]: 0, mb[0]: 1}
    edges = [(u, r, v) for u, r, v in P if r not in (R + 1, R + 2)]
    for u, r, v in edges:
        for x in (u, v):
            if x not in loc and x not in dummy: loc[x] = len(loc)
    return [(loc[u], r, loc[v]) for u, r, v in edges], loc

def compose(mid, c, d, leaf):
    N = 1 + max([max(u, v) for u, _, v in mid] + [1]); mp = {0: c, 1: d}; out = list(mid)
    for u, r, v in leaf:
        for x in (u, v):
            if x not in mp: mp[x] = N + len(mp) - 2
        out.append((mp[u], r, mp[v]))
    return out

def build_depth2(train, D2, H, lib, alive, R, mode, LD, maxF, maxn, rounds=2):
    """Gibt (H3, lib3, extra_dict_bits) zurueck oder None, wenn nichts zerlegt wurde."""
    from und3 import dict_bits_h
    inst = []
    for c in train: inst += collect_fillers(c, D2, H, lib)
    if not inst: return None
    Rp = R + 3
    fcomps = [marked_comp(lib[f], R) for _, f in inst]
    LD2 = lambda comps: LD2f(comps)
    import und3
    def LD2f(comps): return LD(comps, Rp)
    Dp0 = LD2f(fcomps)
    cst, Dp, Hp, libp, alivep, hbp, rd = H2.refine(fcomps, Dp0, Rp, mode, LD2f, 4, rounds, maxn=maxn)
    mids = {}   # pi' -> (mid edges, sub-holes)
    for h in Hp:
        pi, p, q = h["key"]
        if os.environ.get("DBG"): print("DBGMID", Dp[pi])
        pm = parse_mid(Dp[pi], R)
        if pm is None or pi not in alivep: continue
        edges, loc = pm
        if p not in loc or q not in loc: continue
        mids.setdefault(pi, (edges, []))[1].append((loc[p], loc[q], h))
    if not mids: return None
    # expandierte Kandidaten: (pi', Unterloch-Index, Blattoption) -> flaches Muster
    comp_pat = {}
    for pi, (edges, subs) in mids.items():
        for si, (c, d, hs) in enumerate(subs):
            opts = [('empty', edges)] + [(('f', f), compose(edges, c, d, libp[f])) for f in hs['fil']]
            for o, pat in opts: comp_pat[(pi, si, o)] = pat
    # welche flachen Fuellungen werden erklaert?
    keyof = {}
    for k, pat in comp_pat.items(): keyof.setdefault(H2.filler_key(pat, R), []).append(k)
    explained = {f for f in lib if H2.filler_key(lib[f], R) in keyof}
    lib3 = dict(lib); H3 = []; mid_used = set(); leaf_used = set(); sub_used = set()
    for h in H:
        fil_flat = [f for f in h['fil'] if f not in explained]
        prob = {o: pr for o, pr in h['prob'].items() if not (o[0] == 'f' and o[1] in explained)}
        ptop = collections.defaultdict(float)
        for f in h['fil']:
            if f in explained:
                for k in keyof[H2.filler_key(lib[f], R)]: ptop[k[0]] += h['prob'][('f', f)]; break
        # Mitte pi' mit mindestens einer Erklaerung: alle Blattoptionen (auch ungesehene)
        newf = []
        for pi, pt in ptop.items():
            edges, subs = mids[pi]; c, d, hs = subs[0]
            for o in [('empty',)] + [('f', f) for f in hs['fil']]:
                k = (pi, 0, o[0] if o[0] == 'empty' else o)
                pat = comp_pat.get(k)
                if pat is None: continue
                key = ('n', pi, o)
                lib3[key] = pat; newf.append(key); prob[('f', key)] = pt * hs['prob'][o if o[0] != 'empty' else ('empty',)]
            mid_used.add(pi); sub_used.add(pi)
        fil = sorted(fil_flat + newf, key=lambda f: -len(lib3[f]))
        H3.append({'key': h['key'], 'fil': fil, 'prob': prob, 'nopt': len(prob), 'score': h['score'], 'flat': fil_flat, 'mids': sorted(ptop)})
    # Bibliotheksbits
    def ent(pat): return 2 + 3 * len(pat) * LOG(8)
    Vs = {i: len({x for a, _, b in D2[i] for x in (a, b)}) for i in range(len(D2))}
    bits = 0.0
    for h in H3:
        nm = len(h['mids']) + len(h['flat']) + 2
        bits += H2.hole_bits({'nopt': nm}, len(D2), Vs[h['key'][0]]) + sum(ent(lib[f]) for f in h['flat'])
    leafset = set()
    for pi in mid_used:
        edges, subs = mids[pi]; bits += ent(edges)
        for c, d, hs in subs[:1]:
            bits += 2 * LOG(max(2, 6)) + hs['nopt'] * (LOG(len(Dp) + 1) + 2 * LOG(6) + 6)
            leafset |= set(hs['fil'])
    bits += sum(ent(libp[f]) for f in leafset)
    return H3, lib3, bits, {'n_mids': len(mid_used), 'n_leaves': len(leafset), 'n_explained': len(explained), 'n_flat_lib': len(lib)}
