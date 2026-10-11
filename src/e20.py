import sys, json, math, random
from collections import Counter, defaultdict
import und
from und import total_u
from e19 import *
from e19c import uni

def order_edges(c):
    """Kanten in BFS-Reihenfolge ueber die Knoten; liefert Liste (idx, a, r, b)."""
    adj = defaultdict(list)
    for e in c.E: adj[e[1]].append(e); adj[e[3]].append(e)
    seen_e = set(); out = []; seen_v = set()
    for s in sorted(adj):
        if s in seen_v: continue
        q = [s]; seen_v.add(s)
        while q:
            u = q.pop(0)
            for e in sorted(adj[u]):
                if e[0] not in seen_e: seen_e.add(e[0]); out.append(e)
                v = e[3] if e[1] == u else e[1]
                if v not in seen_v: seen_v.add(v); q.append(v)
    return out

def contexts(c, mode):
    """Fuer jede Kante (in Codierreihenfolge): (Kontext, Label). Kontext aus Labels bereits codierter Nachbarkanten."""
    done = defaultdict(list); res = []; nbr = defaultdict(dict)
    for _, a, r, b in order_edges(c):
        la, lb = done[a], done[b]
        opp = -1
        if mode in ('opp', 'opponly'):
            for x, lx in nbr[a].items():
                for y, ly in nbr[b].items():
                    if x != b and y != a and y in nbr[x]: opp = nbr[x][y]; break
                if opp != -1: break
        if mode == 'iid': ctx = ()
        elif mode == 'last': ctx = (la[-1] if la else -1, lb[-1] if lb else -1); ctx = tuple(sorted(ctx))
        elif mode == 'opp': ctx = (tuple(sorted((la[0] if la else -1, lb[0] if lb else -1))), opp)
        elif mode == 'opponly': ctx = (opp,)
        elif mode == 'first': ctx = tuple(sorted((la[0] if la else -1, lb[0] if lb else -1)))
        elif mode == 'maj':
            def m(l): return Counter(l).most_common(1)[0][0] if l else -1
            ctx = tuple(sorted((m(la), m(lb))))
        elif mode == 'deg':
            ctx = (min(len(la), 3), min(len(lb), 3))
            ctx = tuple(sorted(ctx))
        res.append((ctx, r)); done[a].append(r); done[b].append(r); nbr[a][b] = r; nbr[b][a] = r
    return res

class Model:
    def __init__(self, mode, alpha=0.5): self.mode = mode; self.t = defaultdict(Counter); self.alpha = alpha
    def fit(self, comps):
        for c in comps:
            for ctx, r in contexts(c, self.mode): self.t[ctx][r] += 1
        self.g = Counter(); [self.g.update(v) for v in self.t.values()]
    def cost(self, comps):
        tot = 0
        for c in comps:
            for ctx, r in contexts(c, self.mode):
                cnt = self.t.get(ctx, self.g); n = sum(cnt.values()); tot -= math.log2((cnt[r] + self.alpha) / (n + self.alpha * NLAB))
        return tot / len(comps)
    def nparams(self): return len(self.t) * (NLAB - 1)

def main(n=100, seed=0):
    und.SYMS = set(); rng = random.Random(11 + seed)
    tr_all = load('barcelona', rng, n + 100); train, te_in = tr_all[:n], tr_all[n:]
    tests = {'in:barcelona': te_in}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
    out = {}
    for mode in ('iid', 'first', 'opponly', 'opp'):
        m = Model(mode); m.fit(train)
        out[mode] = {t: round(m.cost(c), 1) for t, c in tests.items()}; out[mode]['train'] = round(m.cost(train), 1); out[mode]['nparams'] = m.nparams()
        print(seed, mode, out[mode], flush=True)
    # Anteil Kanten mit gleichem Label wie ein Nachbar
    same = tot = 0
    for c in train:
        L = {}
        for _, a, r, b in c.E: L.setdefault(a, []).append(r); L.setdefault(b, []).append(r)
        for _, a, r, b in c.E:
            nb = L[a] + L[b]; nb.remove(r); nb.remove(r) if r in nb and False else None
            tot += 1; same += r in nb
    print('Anteil Kanten, die ein Nachbar-Label teilen:', round(same / tot, 3))
    json.dump(out, open(f'e20_{seed}.json', 'w'))
if __name__ == '__main__': main(100, int(sys.argv[1]))
