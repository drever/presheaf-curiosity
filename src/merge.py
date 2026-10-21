"""Schnelle Zellbildung: Verkleben benachbarter Instanzen ohne erneutes Einbetten (statt cells3.merge_round).
Instanz-Stuecke = (Mustertreffer als Kantenmenge). Kandidat = kanonische Form der Vereinigung zweier Stuecke, die einen Knoten teilen; Gewinn arithmetisch
(2 Instanzen -> 1, Knotenzahl der Vereinigung, Woerterbuch +1 Muster). Wiedergabe auf anderer Schaltung = dieselben Runden anwenden (Paare mit gleicher kanonischer Form verkleben)."""
import itertools, collections
import und
from und import canon_u, embed_u, cover_u
from core import Comp, LOG, normalize, order_pattern, dict_bits

def pieces_of(comp, D):
    inst, raw = cover_u(comp, D); P = []
    for pi, ids, mm in inst:
        mp = dict(mm); es = frozenset((mp[u], r, mp[v]) for u, r, v in D[pi]); P.append({'pi': pi, 'es': es, 'nodes': frozenset(mp.values())})
    return P, len(raw)

HUB = 8
def adjacent_pairs(P, maxe):
    by = collections.defaultdict(list)
    for i, p in enumerate(P):
        for x in p['nodes']: by[x].append(i)
    by = {x: ids for x, ids in by.items() if len(ids) <= HUB}     # Hubs (Eingangsbus) verklebt man nicht: riesige Automorphismengruppe, pynauty haengt
    seen = set()
    for x, ids in by.items():
        for i, j in itertools.combinations(sorted(ids), 2):
            if (i, j) in seen: continue
            seen.add((i, j))
            if len(P[i]['es']) + len(P[j]['es']) <= maxe and not (P[i]['es'] & P[j]['es']): yield i, j

def wl_key(pat, rounds=4):
    out = collections.defaultdict(list); inn = collections.defaultdict(list); nodes = set()
    for u, r, v in pat: out[u].append((r, v)); inn[v].append((r, u)); nodes |= {u, v}
    col = {x: 0 for x in nodes}
    for _ in range(rounds):
        col = {x: hash((col[x], tuple(sorted((r, col[w]) for r, w in out[x])), tuple(sorted((r, col[w]) for r, w in inn[x])))) for x in nodes}
    return (len(nodes), len(pat), tuple(sorted(col.values())))

def union_key(p, q):
    es = p['es'] | q['es']; pat = normalize(es); return wl_key(pat), pat

def select(P, pairs_by_key):
    used = set(); sel = []
    for i, j in sorted(pairs_by_key, key=lambda ij: (-len(P[ij[0]]['nodes'] & P[ij[1]]['nodes']), ij)):   # zuerst Paare mit den meisten gemeinsamen Knoten (die eigentliche Zelle)
        if i in used or j in used: continue
        used |= {i, j}; sel.append((i, j))
    return sel

def merged(P, sel, newpi):
    gone = {x for ij in sel for x in ij}
    out = [p for k, p in enumerate(P) if k not in gone]
    for i, j in sel: out.append({'pi': newpi, 'es': P[i]['es'] | P[j]['es'], 'nodes': P[i]['nodes'] | P[j]['nodes']})
    return out

def learn_merges(comp, D, maxe=24, rounds=8, R=64, minc=3, topn=12, recover=True):
    D = list(D); P, nraw = pieces_of(comp, D); n = LOG(comp.n); recs = []; maxn = comp.n + 1
    for rd in range(rounds):
        cnt = collections.defaultdict(list); pat_of = {}
        for i, j in adjacent_pairs(P, maxe):
            k, pat = union_key(P[i], P[j]); cnt[k].append((i, j)); pat_of[k] = pat
        cands = sorted(cnt, key=lambda k: -len(cnt[k]) * len(pat_of[k]))[:topn] + sorted([k for k in cnt if len(cnt[k]) >= minc], key=lambda k: (-len(pat_of[k]), -len(cnt[k])))[:topn]
        best = None; ND = len(D)
        for k in dict.fromkeys(cands):
            sel = select(P, cnt[k])
            if not sel: continue
            nv_u = len({x for u, _, v in pat_of[k] for x in (u, v)})
            gain = sum(LOG(ND + 1) * 2 - LOG(ND + 2) + (len(P[i]['nodes']) + len(P[j]['nodes']) - nv_u) * n for i, j in sel) - (2 + len(pat_of[k]) * (2 * LOG(maxn) + LOG(R)))
            if gain > 0 and (best is None or gain > best[0]): best = (gain, k, sel)
        if best is None: break
        gain, k, sel = best; op = tuple(order_pattern(pat_of[k]))
        D.append(op); recs.append(k)
        if recover: P, nraw = pieces_of(comp, D)
        else: P = merged(P, sel, len(D) - 1)
        pass; print('  merge round', rd, 'edges', len(op), 'instances', len(sel), 'gain', round(gain), flush=True)
    return D, recs, P

def replay(comp, D0, Dfull, recs, maxe=24):
    """Wendet die gelernten Verklebungsrunden auf eine andere Schaltung an (Basismuster D0 = Anfang von Dfull)."""
    P, nraw = pieces_of(comp, D0)
    for rd, k in enumerate(recs):
        pairs = []
        for i, j in adjacent_pairs(P, maxe):
            kk, _ = union_key(P[i], P[j])
            if kk == k: pairs.append((i, j))
        sel = select(P, pairs); P = merged(P, sel, len(D0) + rd)
    return P, nraw

def to_inst(comp, D, P):
    """Stuecke -> (pi, ids, mm) mit Portzuordnung (Muster einbetten in lokales Teilgraphen-Comp)."""
    eid = {(u, r, v): e for e, u, r, v in comp.E}; inst = []; used = set()
    for p in P:
        pat = D[p['pi']]; es = sorted(p['es']); nodes = sorted(p['nodes']); ix = {x: k for k, x in enumerate(nodes)}
        loc = Comp(len(nodes), [(ix[u], r, ix[v]) for u, r, v in es]); res = embed_u(pat, loc, set())
        if res is None: raise RuntimeError('Muster passt nicht in Stueck')
        _, m = res; inst.append((p['pi'], tuple(), tuple(sorted((u, nodes[x]) for u, x in m.items()))))
        used |= {eid[e] for e in p['es']}
    return inst, [e[0] for e in comp.E if e[0] not in used]
