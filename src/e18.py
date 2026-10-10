import sys, json, time, random, signal
import und
from und import *
from e17 import *
from mol_big import gspan_mol
from mol_sel import greedy_select

def main(n, seed, nnoise, tmax=400, maxv=24):
    und.SYMS = set(); rng = random.Random(7000 + seed); H, V, seen, unseen = make_world(rng)
    gc = lambda ps: gen_comp(rng, H, V, ps, nnoise=nnoise)
    train = [gc(seen) for _ in range(n)]; te_s = [gc(seen) for _ in range(100)]; te_u = [gc(unseen) for _ in range(100)]
    out = {'n': n, 'seed': seed, 'nnoise': nnoise, 'm': {}}
    def ev(nm, D, tm, extra=None):
        out['m'][nm] = {'k': len(D), 'seen': total_u(te_s, D, R, maxn, False) / 100, 'unseen': total_u(te_u, D, R, maxn, False) / 100, 'time': tm}
        if extra: out['m'][nm].update(extra)
        print(n, seed, nnoise, nm, {a: round(b, 1) for a, b in out['m'][nm].items()}, flush=True)
    ev('none', [], 0)
    t0 = time.time(); D0, F, Dp, Deff, col = learn_prod_auto(train, R, 40, maxn, MAXE); ev('prod_auto', Deff, time.time() - t0, {'nfactors': len(F)}); ev('glue_hier', D0, 0)
    cross = lambda A, B: (min(r for _, r, _ in A) < 6) != (min(r for _, r, _ in B) < 6)
    Fo = [tuple(order_pattern(normalize(c))) for c in H + V]; _, Deffo = effective_dict(D0, Fo, MAXE, cross); ev('oracle', Deffo, 0)
    def handler(sig, frm): raise TimeoutError()
    signal.signal(signal.SIGALRM, handler)
    try:
        signal.alarm(tmax); t0 = time.time(); C, nf = gspan_mol(train, None, max(2, int(.2 * n)), maxv, f'/tmp/e18_{n}_{seed}_{nnoise}.gsp')
        D = greedy_select(train, C, R, maxn, 40, 30); signal.alarm(0); ev('gspan', D, time.time() - t0, {'ncand': len(C)})
    except TimeoutError: out['m']['gspan'] = {'timeout': True}; print('gspan timeout', flush=True)
    json.dump(out, open(f'e18_{n}_{seed}_{nnoise}.json', 'w'))
if __name__ == '__main__': main(*[int(x) for x in sys.argv[1:]])
