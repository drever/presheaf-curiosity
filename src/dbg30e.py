import sys, collections, os
os.environ['NTR'] = '120'; os.environ['KD'] = '80'
sys.argv = ['e30.py', 'syn', '0']
src = open('e30.py').read().split("res['k_dict']")[0]
exec(src)
H, lib, alive, hb = H2.learn(train, D, R, 'iface', 5, maxn=maxn)
print('holes', [(h['key'], len(D[h['key'][0]]), len(h['fil']), round(h['prob'][('empty',)],2), round(h['prob'][('other',)],2)) for h in H])
st = [H2.strip_window(c, D, H, lib, 5) for c in train]
print('edges before/after strip', sum(len(c.E) for c in train)/len(train), sum(len(c.E) for c in st)/len(st))
D2 = LD(st) if 'LD' in dir() else learn_h(st, R, 80, maxn, False, mode='hier', topc=30, maxe=12, objective='hier')
print('D2 sizes', sorted(len(p) for p in D2))
print('D sizes', sorted(len(p) for p in D))
