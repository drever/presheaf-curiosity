"""Whole c6288 through ITR / libcgraph and xz, in two presentations of the same graph.
'sorted': node numbers and triple order follow the gate names of the netlist file; 'shuf': anonymous random node numbers and
random triple order. Reports the grammar part of the ITR output and the xz size of the N-Triples text.
Usage: python itr_whole.py /path/to/cgraph-cli [workdir]"""
import sys, os, random, re, json, subprocess, tempfile, lzma
from netlist import load_bench
import split as SP
CLI = sys.argv[1]; work = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp()
E = load_bench('c6288'); out = []
for name, es in (('full', E), ('gates', [e for e in E if not SP.is_input_edge(e)])):
    for order in ('sorted', 'shuf0', 'shuf1'):
        nodes = sorted({x for u, v, _ in es for x in (u, v)}, key=lambda x: (len(x), x)); es2 = sorted(es, key=lambda e: (len(e[0]), e[0], len(e[1]), e[1]))
        if order != 'sorted':
            r = random.Random(int(order[-1])); r.shuffle(nodes); r.shuffle(es2)
        ix = {x: i for i, x in enumerate(nodes)}; nt = os.path.join(work, f'{name}_{order}.nt'); cg = nt[:-3] + '.cg'
        txt = ''.join(f'<n:{ix[u]}> <l:{l[0]}{l[1]}> <n:{ix[v]}> .\n' for u, v, l in es2); open(nt, 'w').write(txt)
        p = subprocess.run([CLI, '-v', '--overwrite', '-f', 'ntriples', nt, cg], capture_output=True, text=True)
        g = int(re.search(r'Grammar Size is (\d+) byte', p.stdout + p.stderr).group(1))
        out.append({'graph': name, 'order': order, 'edges': len(es2), 'nodes': len(nodes), 'itr_grammar_bits': 8 * g, 'itr_file_bits': 8 * os.path.getsize(cg),
                    'xz_bits': 8 * len(lzma.compress(txt.encode(), preset=9 | lzma.PRESET_EXTREME))})
        print(out[-1], flush=True)
json.dump(out, open('../results/itr_whole.json', 'w'), indent=1)
