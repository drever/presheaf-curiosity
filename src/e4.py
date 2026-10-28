import sys, json, time, random, math, collections, logging
logging.Logger.__call__ = lambda self: self
import und
from und import *
from core import Comp, dict_bits, order_pattern, normalize
from kg_final import load, sample

def qd(comps, sig):
    out = []; extra = 0
    for c in comps:
        S = set()
        for _, a, r, b in c.E:
            if r in sig:
                s = sig[r]
                e = (a, r, b) if (r < s or (r == s and a <= b)) else (b, s, a)
                S.add(e)
            else: S.add((a, r, b))
        extra += 2 * sum(1 for e in S if e[1] in sig)
        out.append(Comp(c.n, sorted(S)))
    return out, extra

def reff(R, sig): return R - sum(1 for r, s in sig.items() if r < s)

def total_train(train, sig, R, maxn, K=10, topc=10):
    q, extra = qd(train, sig); Re = reff(R, sig)
    D = learn_u(q, Re, K, maxn, False, mode='hier', topc=topc, maxe=10)
    return total_u(q, D, Re, maxn, True) + extra + 2 * math.log2(R) * (len(sig) // 2 + sum(1 for r, s in sig.items() if r == s))

def ranking(train, R, sig):
    tot = collections.Counter(); hit = collections.Counter()
    for c in train:
        S = {(a, r, b) for _, a, r, b in c.E}
        for a, r, b in S:
            tot[r] += 1
            for s in range(R):
                if (b, s, a) in S: hit[(r, s)] += 1
    sc = []
    for (r, s), h in hit.items():
        if r <= s and r not in sig and s not in sig:
            f = (hit[(r, s)] + (hit[(s, r)] if r != s else 0)) / (tot[r] + (tot[s] if r != s else 0))
            if f >= .2: sc.append((f, r, s))
    return sorted(sc, reverse=True)

def est_mdl(train, R, maxn, ncand=12, maxpairs=14):
    sig = {}; best = total_train(train, sig, R, maxn)
    for _ in range(maxpairs):
        pick = None
        for f, r, s in ranking(train, R, sig)[:ncand]:
            t = dict(sig); t[r] = s; t[s] = r; L = total_train(train, t, R, maxn)
            if L < best: best, pick = L, (r, s)
        if pick is None: break
        sig[pick[0]] = pick[1]; sig[pick[1]] = pick[0]
    return sig

def main(seed, tout, with_opp):
    und.SYMS = set(); k = 5; maxn = k + 1
    tr, R = load('kinships'); rng = random.Random(seed); comps = sample(tr, 300, k, rng)
    cut = int(.7 * len(comps)); train_all, test = comps[:cut], comps[cut:]
    out = {'seed': seed, 'res': {}}
    for n in (20, 60, 210):
        train = train_all[:n]; res = {}
        D = learn_u(train, R, 20, maxn, False, mode='hier', topc=100, maxe=10)
        res['plain100'] = {'k': len(D), 'test': total_u(test, D, R, maxn, False) / len(test)}
        t0 = time.time(); sig = est_mdl(train, R, maxn); tm = time.time() - t0
        q, ex = qd(train, sig); Re = reff(R, sig)
        D = learn_u(q, Re, 20, maxn, False, mode='hier', topc=100, maxe=10)
        qt, ext = qd(test, sig)
        res['closure100'] = {'k': len(D), 'test': (total_u(qt, D, Re, maxn, False) + ext) / len(test), 'pairs': sorted((r, s) for r, s in sig.items() if r <= s), 'time': tm}
        if with_opp and n < 210:
            from mol_big import gspan_mol
            from mol_sel import greedy_select
            from mol_subdue import run_subdue
            from gm_kg import to_nx, pat_edges
            from skmine.graph.graphmdl.graph_mdl import GraphMDL
            def uniq(ps):
                Dd = []; s = set()
                for p in ps:
                    kk = canon_u(p, True)
                    if kk not in s: s.add(kk); Dd.append(p)
                return Dd
            def ev(nm, Dd, tm): res[nm] = {'k': len(Dd), 'test': total_u(test, Dd, R, maxn, False) / len(test), 'time': tm}
            t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.10 * n)), 8, f'{__import__("tempfile").gettempdir()}/e4_{seed}_{n}.gsp'); ev('gspan_mdl30', greedy_select(train, C, R, maxn, 20, 30), time.time() - t0)
            t0 = time.time(); pats, _ = run_subdue(train, 20, 500, 10, 4); tm = time.time() - t0; Dd = uniq(pats)[:20]
            trn = [total_u(train, Dd[:m], R, maxn) for m in range(len(Dd) + 1)]; ns = min(range(len(trn)), key=lambda m: trn[m]); ev('subdue20_mdl', Dd[:ns], tm)
            t0 = time.time(); g = GraphMDL().fit(to_nx(train)[0], timeout=tout); tm = time.time() - t0
            ev('graphmdl', uniq([tuple(order_pattern(normalize(pat_edges(Pt)))) for Pt in g.patterns() if Pt.number_of_edges() >= 2]), tm)
        out['res'][n] = res
        print(seed, n, {kk: (round(v['test'], 1), v['k']) for kk, v in res.items()}, 'pairs', len(res['closure100']['pairs']), round(res['closure100']['time']), 's', flush=True)
        json.dump(out, open(f'e4_{seed}.json', 'w'))

if __name__ == '__main__': main(int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]))
