"""Our gluing coder on an RDF graph (N-Triples), to set beside ITR on a graph that is NOT our favourable case.
Nodes = distinct subjects/objects (IRIs and literals alike), edge label = predicate. Dictionary learned on NWIN random
BFS windows of the same graph, stored in the file. Usage: python rdf_run.py FILE.nt SEED [NWIN=40]"""
import sys, re, random, json, time, os
from collections import defaultdict, deque
import und
from und import *
from und3 import learn_h
from core import Comp
from iface import total_iface, total_old
import coder
fn = sys.argv[1]; seed = int(sys.argv[2]); nwin = int(sys.argv[3]) if len(sys.argv) > 3 else 40
T = []
for ln in open(fn, encoding='utf-8'):
    if ln.startswith('#') or not ln.strip(): continue
    m = re.match(r'\s*(<[^>]*>|_:\S+)\s+(<[^>]*>)\s+(.*?)\s*\.\s*$', ln)
    assert m, ln
    T.append(m.groups())
T = sorted(set(T)); labs = sorted({p for _, p, _ in T}); lid = {p: i for i, p in enumerate(labs)}; R = len(labs)
nodes = sorted({x for s, _, o in T for x in (s, o)}); random.Random(seed).shuffle(nodes); ix = {x: i for i, x in enumerate(nodes)}
E = [(ix[s], lid[p], ix[o]) for s, p, o in T]; random.Random(seed + 1).shuffle(E)
whole = Comp(len(nodes), E); adj = defaultdict(set)
for u, _, v in E: adj[u].add(v); adj[v].add(u)
print('triples', len(E), 'nodes', len(nodes), 'labels', R, 'max degree', max(len(a) for a in adj.values()), flush=True)
rng = random.Random(100 + seed); und.SYMS = set(); und.TWIN_MAX = 6; train = []; tries = 0
while len(train) < nwin and tries < 50 * nwin:
    tries += 1; s = rng.choice(range(len(nodes))); seen = {s}; q = deque([s])
    while q and len(seen) < 20:
        u = q.popleft()
        for v in sorted(adj[u]):
            if v not in seen and len(seen) < 20: seen.add(v); q.append(v)
    es = [(u, r, v) for u, r, v in E if u in seen and v in seen] if False else [(e[1], e[2], e[3]) for u in seen for e in whole.out[u] if e[3] in seen]
    if len(es) < 8: continue
    loc = sorted(seen); rng.shuffle(loc); li = {x: i for i, x in enumerate(loc)}
    train.append(Comp(31, sorted((li[u], r, li[v]) for u, r, v in es)))
t0 = time.time(); D = learn_h(train, R, 40, 32, False, mode='hier', topc=30, maxe=12, objective='hier')
print('patterns', len(D), 'sizes', sorted(len(p) for p in D), 'learn s', round(time.time() - t0), flush=True)
out = {'file': os.path.basename(fn), 'seed': seed, 'triples': len(E), 'nodes': len(nodes), 'labels': R, 'patterns': len(D), 'raw_model_bits': total_iface([whole], [], R, 32, False), 'runs': []}
for mode in ('all', 'boundary'):
    t0 = time.time(); b, info = coder.encode(whole, D, R, mode); v = coder.verify(whole, b, info, mode); info.pop('fresh_order')
    r = {'mode': mode, 'file_bits': 8 * len(b), **{k: round(x) if isinstance(x, float) else x for k, x in info.items()}, 'verify': v, 'time': round(time.time() - t0)}
    out['runs'].append(r); print(json.dumps(r), flush=True)
json.dump(out, open(f'../results/rdf_{os.path.basename(fn).split(".")[0]}_{seed}.json', 'w'), indent=1)
