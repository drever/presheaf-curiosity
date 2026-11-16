"""Reference run of a published grammar-based graph compressor on the held-out windows of heldout2.py.

Compressor: ITR / libcgraph (Adler et al., "ITR: Grammar-based Graph Compression Supporting Fast Triple Queries",
https://github.com/adlerenno/IncidenceTypeRePair), the successor of gRePair; the original gRePair code is not public.
The test windows of one region (the same windows as in results/heldout2_SEED.json) are written as ONE graph of disjoint
components and compressed. Reported: size of the grammar part of the output ("Grammar Size", without the node-name
dictionary) in bits per window. Losslessness is checked by querying all edges back.

Not like for like with our numbers: ITR learns its grammar on the test windows themselves (its rules are inside the
reported size), writes a queryable succinct structure rather than a minimal code, and addresses nodes of the whole file
(not of one window).

Usage: python itr_windows.py SEED /path/to/cgraph-cli [workdir]"""
import sys, os, random, json, subprocess, re, tempfile
import und
from netlist import *
import split as SP
NN = 31; seed = int(sys.argv[1]); CLI = sys.argv[2]; work = sys.argv[3] if len(sys.argv) > 3 else tempfile.mkdtemp()
und.SYMS = set(); L = Labeler()
E = load_bench('c6288')
sp = SP.gate_walk_split(E, random.Random(900 + seed)); inner = SP.inner_split(sp['A'], random.Random(1900 + seed), 0.5)
rng = random.Random(2900 + seed)
regions = {'A_train': inner['train'], 'A_new': inner['test'], 'B_heldout': sp['B']}
raw = {'A_train': windows_from(regions['A_train'], rng, 40, nmax=20, labeler=L)}
for t in ('A_new', 'B_heldout'): raw[t] = windows_from(regions[t], rng, 100, nmax=20, labeler=L)
ref = json.load(open(f'../results/heldout2_{seed}.json'))
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)
out = {'seed': seed, 'compressor': 'ITR/libcgraph', 'sets': {}}
for t in ('A_new', 'B_heldout'):
    ws = raw[t]
    assert [sorted(SP.nodes_of(w)) for w in ws] == [w['nodes'] for w in ref['windows'][t]], 'windows differ from heldout2'
    for order in ('name_sorted', 'random'):
        r = random.Random(5 + seed); triples = []
        for wi, w in enumerate(ws):
            nodes = sorted(SP.nodes_of(w))
            if order == 'random': r.shuffle(nodes)
            ix = {x: i for i, x in enumerate(nodes)}
            triples += [(f'n:{wi:03d}_{ix[u]:02d}', f'l:{l}', f'n:{wi:03d}_{ix[v]:02d}') for u, v, l in w]
        if order == 'random': r.shuffle(triples)
        nt = os.path.join(work, f'{t}_{seed}_{order}.nt'); cg = nt[:-3] + '.cg'
        with open(nt, 'w') as f:
            for s, p, o in triples: f.write(f'<{s}> <{p}> <{o}> .\n')
        p = run([CLI, '-v', '--overwrite', '-f', 'ntriples', nt, cg]); m = re.search(r'Grammar Size is (\d+) byte', p.stdout + p.stderr)
        assert m, p.stdout + p.stderr
        # losslessness: query every edge back, label by label
        nl = int(run([CLI, cg, '--edge-labels']).stdout.split()[-1]); nn = int(run([CLI, cg, '--node-count']).stdout.split()[-1])
        names = []
        for a0 in range(0, nn, 20): names += run([CLI, cg] + sum([['--extract-node', str(i)] for i in range(a0, min(nn, a0 + 20))], [])).stdout.split()
        assert len(names) == nn
        back = []
        for li in range(nl):
            lab = run([CLI, cg, '--extract-edge', str(li)]).stdout.split()[-1]
            for a, b in re.findall(r'\(\d+,\s*(\d+),\s*(\d+)\)', run([CLI, cg, '--hyperedges', f'2,{li},?,?']).stdout): back.append((names[int(a)], lab, names[int(b)]))
        g = int(m.group(1))
        out['sets'].setdefault(t, {})[order] = {'windows': len(ws), 'edges': len(triples), 'grammar_bytes': g, 'file_bytes': os.path.getsize(cg),
                                                'grammar_bits_per_window': 8 * g / len(ws), 'lossless': sorted(back) == sorted(triples)}
    out['sets'][t]['ours'] = {k: ref['methods'][k][t] for k in ('none', 'glue', 'grow', 'repair_reimpl')}
print(json.dumps(out, indent=1))
json.dump(out, open(f'../results/itr_windows_{seed}.json', 'w'), indent=1)
