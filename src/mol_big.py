import sys, json, time, random, io, contextlib, collections
import und
from und import *
from core import GS, order_pattern, normalize
from molcommon import load_mols, sample_comps, canon_bond

def gspan_mol(train, K, minsup, maxv, fname):
    with open(fname, 'w') as f:
        for gi, c in enumerate(train):
            f.write(f't # {gi}\n')
            for v in range(c.n): f.write(f'v {v} 0\n')
            for j, (_, a, r, b) in enumerate(c.E):
                w = c.n + j; f.write(f'v {w} {r + 1}\n'); f.write(f'e {a} {w} 0\ne {w} {b} {0 if r in und.SYMS else 1}\n')
        f.write('t # -1\n')
    gs = GS(fname, min_support=minsup, min_num_vertices=3, max_num_vertices=maxv, is_undirected=True, verbose=False, visualize=False, where=False)
    gs.found = []
    with contextlib.redirect_stdout(io.StringIO()): gs.run()
    pats = []
    for code, sup in gs.found:
        vl = {}; ed = []
        for e in code:
            a, lb, b = int(e.vevlb[0]), int(e.vevlb[1]), int(e.vevlb[2])
            if a != -1: vl[e.frm] = a
            if b != -1: vl[e.to] = b
            ed.append((e.frm, e.to, lb))
        ok = True; pe = []
        for w in [v for v, l in vl.items() if l > 0]:
            r = vl[w] - 1
            inc = [((q if p == w else p), lb) for p, q, lb in ed if p == w or q == w]
            if len(inc) != 2: ok = False; break
            if r in und.SYMS:
                if inc[0][1] != 0 or inc[1][1] != 0: ok = False; break
                pe.append((inc[0][0], r, inc[1][0]))
            else:
                t = [x for x, lb in inc if lb == 0]; h = [x for x, lb in inc if lb == 1]
                if len(t) != 1 or len(h) != 1: ok = False; break
                pe.append((t[0], r, h[0]))
        if ok and pe:
            try: pats.append((sup * len(pe), tuple(order_pattern(normalize(pe)))))
            except ValueError: pass
    seen = set(); out = []
    for sc, p in sorted(pats, key=lambda x: -x[0]):
        k = canon_u(p, True)
        if k in seen: continue
        seen.add(k); out.append(p)
        if K is not None and len(out) == K: break
    return out, len(gs.found)

def main(k, seed, maxv, N=300):
    tr = load_mols('mol/solubility.train.sdf'); te = load_mols('mol/solubility.test.sdf')
    keys = sorted({(bt, el[x], el[y]) for ms in (tr, te) for n, bonds, el in ms for a, bt, b in bonds for x, y in [canon_bond(el, a, b, bt)]})
    relid = {t: i for i, t in enumerate(keys)}; R = len(keys); und.SYMS = {i for t, i in relid.items() if t[1] == t[2]}
    rng = random.Random(seed); train = sample_comps(tr, int(.7 * N), k, rng, relid); te_c = sample_comps(te, N - int(.7 * N), k, rng, relid)
    test = te_c; maxn = k + 1
    out = {'k': k, 'seed': seed, 'maxv': maxv, 'R': R, 'ntr': len(train), 'nte': len(test),
           'edges': sum(len(c.E) for c in train + test) / (len(train) + len(test)), 'm': {},
           'raw_test': total_u(test, [], R, maxn, False) / len(test)}
    def ev(nm, D, tm, extra=None):
        out['m'][nm] = {'k': len(D), 'max_edges': max([len(p) for p in D] or [0]), 'test': total_u(test, D, R, maxn, False) / len(test),
                        'dict': total_u([], D, R, maxn), 'time': tm}
        if extra: out['m'][nm].update(extra)
    Ds = {}
    for mode in ('hier', 'grow'):
        t0 = time.time(); Ds[mode] = learn_u(train, R, 20, maxn, True, mode=mode, maxe=max(10, k)); ev(mode, Ds[mode], time.time() - t0)
        print('  ', mode, round(time.time() - t0, 1), 's', flush=True)
    kk = max(len(Ds['hier']), 1)
    t0 = time.time(); G, nf = gspan_mol(train, kk, max(2, int(float(__import__("os").environ.get("MINSUP","0.10")) * len(train))), maxv, f'/tmp/mb_{k}_{seed}.gsp'); ev('gspan', G, time.time() - t0, {'n_found': nf})
    print('   gspan', round(time.time() - t0, 1), 's,', nf, 'Muster', flush=True)
    cnts = collections.Counter(e[2] for c in train for e in c.E)
    ev('relationen', [((0, r, 1),) for r, _ in cnts.most_common(kk)], 0.0)
    json.dump(out, open(f'mb_{k}_{seed}.json', 'w')); print('fertig', k, seed, flush=True)

if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
