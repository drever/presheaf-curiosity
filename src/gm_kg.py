import sys, json, time, random
import networkx as nx
import und
from und import *
from kg_final import load, sample
from skmine.graph.graphmdl.graph_mdl import GraphMDL
from core import order_pattern, normalize

def to_nx(train):
    G = nx.DiGraph(); off = 0; seen = {}
    for c in train:
        for j in range(c.n):
            G.add_node(off + j); G.nodes[off + j]['label'] = 'x'
        for (i, a, r, b) in c.E:
            if G.has_edge(off + a, off + b):  # DiGraph: eine Kante je Paar
                seen['multi'] = seen.get('multi', 0) + 1; continue
            G.add_edge(off + a, off + b, label=str(r))
        off += c.n
    return G, seen

def pat_edges(P):
    nodes = {v: i for i, v in enumerate(P.nodes)}
    return [(nodes[a], int(d['label'] if not isinstance(d['label'], (tuple, list, set, frozenset)) else list(d['label'])[0]), nodes[b]) for a, b, d in P.edges(data=True)]

def main(name, seed, timeout, k=5, N=300):
    und.SYMS = set()
    tr, R = load(name); rng = random.Random(seed); comps = sample(tr, N, k, rng)
    cut = int(.7 * len(comps)); train, test = comps[:cut], comps[cut:]; ntr = len(train); maxn = k + 1
    G, info = to_nx(train)
    t0 = time.time(); g = GraphMDL().fit(G, timeout=timeout); tm = time.time() - t0
    pats = list(g.patterns()); print('patterns', len(pats), 'time', round(tm), 'DL', g.initial_description_length(), g.description_length(), info, flush=True)
    D = []; seen = set(); raw = []
    for P in pats:
        try: E = pat_edges(P)
        except Exception as e: print('skip', e); continue
        raw.append((P.number_of_nodes(), len(E)))
        if len(E) < 2: continue
        pe = tuple(order_pattern(normalize(E)))
        kk = canon_u(pe, True)
        if kk not in seen: seen.add(kk); D.append(pe)
    out = {'name': name, 'seed': seed, 'time': tm, 'npat': len(pats), 'nD': len(D), 'dl0': g.initial_description_length(), 'dl': g.description_length(), 'raw': raw, 'm': {}}
    def ev(nm, Dn):
        out['m'][nm] = {'k': len(Dn), 'dict': total_u([], Dn, R, maxn), 'train': total_u(train, Dn, R, maxn, False) / ntr, 'test': total_u(test, Dn, R, maxn, False) / len(test)}
        print(nm, len(Dn), round(out['m'][nm]['test'], 1), flush=True)
    ev('gmdl_all', D); ev('gmdl20', D[:20])
    trn = [total_u(train, D[:m], R, maxn) for m in range(len(D) + 1)]
    ns = min(range(len(trn)), key=lambda m: trn[m]); ev('gmdl_mdl', D[:ns])
    ev('none', [])
    json.dump(out, open(f'gm_{name}_{seed}.json', 'w'))

if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]))
