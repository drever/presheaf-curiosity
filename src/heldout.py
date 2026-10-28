"""Held-out test on c6288: split the netlist into two disjoint regions A and B (BFS half / rest, cut edges dropped).
Dictionaries (gluing, grow-by-one, RePair-style baseline) are learned on windows from A and evaluated on NEW windows from A and on windows from B."""
import sys, json, time, random
from collections import defaultdict, deque
import und
from und import *
from und3 import learn_h
from netlist import *
from iface import total_iface
import repair as RP
NN = 31; maxn = NN + 1; R = 64
seed = int(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
und.SYMS = set(); rng = random.Random(900 + seed); L = Labeler()
E = load_bench('c6288'); adj = defaultdict(set)
for u, v, _ in E: adj[u].add(v); adj[v].add(u)
nodes = sorted(adj); start = rng.choice(nodes); seen = [start]; S = {start}; q = deque([start])
while q and len(S) < len(nodes) // 2:
    x = q.popleft()
    for y in sorted(adj[x]):
        if y not in S and len(S) < len(nodes) // 2: S.add(y); seen.append(y); q.append(y)
EA = [e for e in E if e[0] in S and e[1] in S]; EB = [e for e in E if e[0] not in S and e[1] not in S]
print('A edges', len(EA), 'B edges', len(EB), 'cut', len(E) - len(EA) - len(EB), flush=True)
def win(Es, k): return [to_comp(x, rng, NN) for x in windows_from(Es, rng, k, nmax=20, labeler=L)]
train = win(EA, n); tests = {'A_new': win(EA, 100), 'B_heldout': win(EB, 100)}
res = {'edges_A': len(EA), 'edges_B': len(EB)}
def ev(name, D=None, rules=None, tm=0):
    r = {'k': len(D if D is not None else rules), 'time': round(tm)}
    for t, c in tests.items():
        r[t] = (total_iface(c, D, R, maxn, False) if D is not None else RP.cost(c, rules, R, set())) / len(c)
    res[name] = r; print(seed, name, {a: round(b, 1) for a, b in r.items()}, flush=True)
ev('none', D=[])
t0 = time.time(); ev('glue', D=learn_h(train, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier'), tm=time.time() - t0)
t0 = time.time(); ev('grow', D=learn_h(train, R, 40, maxn, False, mode='grow', topc=30, maxe=12, objective='hier'), tm=time.time() - t0)
t0 = time.time(); ev('repair_reimpl', rules=RP.learn(train, R, set(), K=80), tm=time.time() - t0)
json.dump(res, open(f'../results/heldout_{seed}.json', 'w'))
