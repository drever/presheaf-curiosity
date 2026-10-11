import re, random
from collections import defaultdict, deque, Counter
from core import Comp
HB = '/tmp/dl/hdl-benchmarks/iscas85/bench/'
EB = '/tmp/dl/benchmarks/arithmetic/'

def load_bench(name):
    typ = {}; ins = defaultdict(list)
    for ln in open(HB + name + '.bench'):
        ln = ln.strip()
        if not ln or ln.startswith('#'): continue
        m = re.match(r'INPUT\((\S+)\)', ln)
        if m: typ[m.group(1)] = 'IN'; continue
        if ln.startswith('OUTPUT'): continue
        m = re.match(r'(\S+)\s*=\s*(\w+)\((.*)\)', ln)
        if m: typ[m.group(1)] = m.group(2).upper(); ins[m.group(1)] = [x.strip() for x in m.group(3).split(',')]
    E = []
    for v, srcs in ins.items():
        for s in srcs:
            if s in typ: E.append((s, v, (typ[s], typ[v])))
    return E

def load_blif(name):
    txt = open(EB + name + '.blif').read().replace('\\\n', ' ').split('\n')
    pis = set(); E = []; i = 0
    while i < len(txt):
        ln = txt[i].split()
        if ln and ln[0] == '.inputs': pis |= set(ln[1:])
        if ln and ln[0] == '.names':
            sig = ln[1:]; out = sig[-1]; ins = sig[:-1]; rows = []
            j = i + 1
            while j < len(txt) and txt[j] and not txt[j].startswith('.'): rows.append(txt[j].split()); j += 1
            pat = rows[0][0] if rows else ''
            for k, s in enumerate(ins):
                inv = (pat[k] == '0') if len(pat) == len(ins) else False
                E.append((s, out, ('PI' if s in pis else 'G', inv)))
            i = j; continue
        i += 1
    return E

class Labeler:
    def __init__(self): self.ids = {}
    def __call__(self, key): return self.ids.setdefault(key, len(self.ids))

def windows_from(E, rng, k, nmax=30, emin=8, labeler=None):
    """BFS-Baelle um zufaellige Startknoten (ungerichtet), induzierte Kanten; Label via labeler."""
    adj = defaultdict(set)
    for u, v, _ in E: adj[u].add(v); adj[v].add(u)
    lab = {}; outs = defaultdict(set)      # gerichtet: Treiber -> Senke
    for u, v, l in E: lab[(u, v)] = labeler(l); outs[u].add(v)
    nodes = sorted(adj); out = []; tries = 0
    while len(out) < k and tries < 20 * k:
        tries += 1; s = rng.choice(nodes); seen = {s}; q = deque([s])
        while q and len(seen) < nmax:
            u = q.popleft()
            for v in sorted(adj[u]):
                if v not in seen and len(seen) < nmax: seen.add(v); q.append(v)
        es = [(u, v, lab[(u, v)]) for u in seen for v in outs[u] if v in seen]
        if len(es) >= emin: out.append(es)
    return out

def to_comp(es, rng, NN=31):
    nodes = list({x for u, v, _ in es for x in (u, v)}); rng.shuffle(nodes); ix = {x: i for i, x in enumerate(nodes)}
    return Comp(NN, [(ix[u], l, ix[v]) for u, v, l in es])

def sq_stats(comps):
    tot = sq = 0; opp_eq = 0
    for c in comps:
        adj = defaultdict(dict)
        for _, a, r, b in c.E: adj[a][b] = r; adj[b][a] = r
        tot += len(c.E); seen = set()
        for u in adj:
            for v in adj[u]:
                for x in adj[u]:
                    if x <= v: continue
                    for w in set(adj[v]) & set(adj[x]):
                        if w == u: continue
                        key = frozenset((u, v, w, x))
                        # eindeutiges Quadrat: Zyklus u-v-w-x
                        k2 = (frozenset([(u, v), (v, u)]), frozenset([(v, w), (w, v)]), frozenset([(w, x), (x, w)]), frozenset([(x, u), (u, x)]))
                        kk = frozenset([frozenset((u, v)), frozenset((v, w)), frozenset((w, x)), frozenset((x, u))])
                        if kk in seen: continue
                        seen.add(kk); sq += 1
                        opp_eq += (adj[u][v] == adj[x][w]) + (adj[v][w] == adj[u][x])
    return tot / len(comps), sq / len(comps), (opp_eq / (2 * sq) if sq else 0)

if __name__ == '__main__':
    rng = random.Random(1)
    L = Labeler()
    for nm in ['c17', 'c432', 'c499', 'c880', 'c1355', 'c1908', 'c2670', 'c3540', 'c5315', 'c6288', 'c7552']:
        E = load_bench(nm); w = windows_from(E, rng, 100, labeler=L)
        cs = [to_comp(x, rng) for x in w]
        print('bench', nm, 'edges', len(E), 'windows', len(cs), 'mean edges/squares/oppEq', [round(x, 2) for x in sq_stats(cs)] if cs else None, flush=True)
    L2 = Labeler()
    for nm in ['adder', 'bar', 'max', 'multiplier', 'sin', 'square', 'sqrt', 'div', 'log2']:
        E = load_blif(nm); w = windows_from(E, rng, 100, labeler=L2)
        cs = [to_comp(x, rng) for x in w]
        print('blif', nm, 'edges', len(E), 'windows', len(cs), 'mean edges/squares/oppEq', [round(x, 2) for x in sq_stats(cs)] if cs else None, flush=True)
    print(len(L.ids), len(L2.ids))
