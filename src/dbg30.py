import sys
sys.argv = ['e30.py', 'syn', '0']
src = open('e30.py').read().split("res['time']")[0]
exec(src)
import collections
print('pattern sizes', sorted(len(p) for p in D))
cnt, nA = candidates(ctr, train)
print('n cand holes', len(cnt), 'nA', dict(nA))
for k, f in sorted(cnt.items(), key=lambda kv: -sum(kv[1].values()))[:8]: print(k, len(D[k[0]]), dict(f))
print('frames true edges 7; gadgets 3-4 edges. units/window', sum(len(u) for u, r in ctr)/len(ctr), 'raw/window', sum(len(r) for u, r in ctr)/len(ctr))
