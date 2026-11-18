"""Size family of the pre-registered Quip measurement (docs/prereg-quip.md, P5): does the gluing dictionary learned on
barrel16 code barrel32 and barrel64 about as well as their own dictionaries? Usage: python quip_size.py SEED"""
import sys, json, random
import und
from und3 import learn_h
from netlist import Labeler, windows_from, to_comp
import split as SP, coder2
from quip import load_quip
seed = int(sys.argv[1]); NN = 31; MAXN = 32
und.SYMS = set(); und.TWIN_MAX = 6; und.EMBED_BUDGET = 2000; L = Labeler()
Es = {n: load_quip(n) for n in ('barrel16', 'barrel32', 'barrel64')}; R = max(64, len({l for E in Es.values() for *_, l in E}))
LD = lambda T: learn_h(T, R, 40, MAXN, False, mode='hier', topc=30, maxe=12, objective='hier')
data = {}
for n, E in Es.items():
    sp = SP.hub_walk_split(E, random.Random(900 + seed)); rng = random.Random(10900 + seed)
    tr = [to_comp(w, rng, NN) for w in windows_from(sp['A'], rng, 40, nmax=20, labeler=L)]
    te = [to_comp(w, rng, NN) for w in windows_from(sp['B'], rng, 100, nmax=20, labeler=L)]
    data[n] = (tr, te)
D = {n: LD(tr) for n, (tr, te) in data.items()}
def bits(te, Dd):
    b, info = coder2.encode(te, coder2.model_plain(Dd), R, 'boundary'); assert all(coder2.verify(te, b, info).values())
    return sum(info['per_comp_bits']) / len(te)
out = {'seed': seed, 'R': R, 'patterns': {n: len(d) for n, d in D.items()}}
for n in ('barrel32', 'barrel64'):
    te = data[n][1]; out[n] = {'empty': bits(te, []), 'own': bits(te, D[n]), 'from_barrel16': bits(te, D['barrel16'])}
    out[n]['ratio'] = out[n]['from_barrel16'] / out[n]['own']
print(json.dumps(out), flush=True)
json.dump(out, open(f'../results/quip_size_{seed}.json', 'w'), indent=1)
