import sys, json, time
import mdlembed as ME
import qembed as QE
which = sys.argv[1]; out = {}
if which == 'c6288':
    import netlist; import paths; netlist.HB = paths.ISCAS
    import json as js, und; from und import *
    from cells import whole_comp
    from quotient import build_quotient
    und.SYMS = set(); comp, nodes, L = whole_comp(); D = [tuple(tuple(e) for e in p) for p in js.load(open('cells_D2.json'))['D']]
    pis = {n for n in range(comp.n) if not comp.inn[n]}; E_, nsup, inst, raw = build_quotient(comp, D, pis)
    ptype = {i: (inst[i][0] if i < len(inst) else -1) for i in range(nsup)}; Q = list(E_); N = nsup; jobs = [('c6288', Q, ptype, N)]
else:
    jobs = []
    for k in (16, 24, 32):
        Q, ptype, N, raw = QE.quotient(k); jobs.append((f'mul{k}', Q, ptype, N))
for name, Q, ptype, N in jobs:
    t0 = time.time(); E = QE.embed(Q, ptype, N); coord, disp2, sc, info = QE.refine(E, N, verbose=False) if 'verbose' in QE.refine.__code__.co_varnames else QE.refine(E, N); E['disp'] = disp2
    cur, br, disp, start = ME.optimize(E, ptype, N)
    out[name] = {'start_mdl': start, 'mdl': cur, 'breakdown': br, 'time': round(time.time() - t0), 'bundles_used': len(disp), 'edges': len(Q)}
    print(name, out[name], flush=True)
json.dump(out, open(f'../results/e43_{which}.json', 'w'), default=str)
