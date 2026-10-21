"""Array-Multiplizierer k x k als .bench (AND/NAND/NOT), eigener Generator (NICHT c6288)."""
import os
def gen(k, path):
    L = []; cnt = [0]
    def g(t, *ins): cnt[0] += 1; n = f'g{cnt[0]}'; L.append(f'{n} = {t}({", ".join(ins)})'); return n
    for i in range(k): L.append(f'INPUT(a{i})'); L.append(f'INPUT(b{i})')
    def fa(a, b, c):
        n1 = g('NAND', a, b); n2 = g('NAND', a, n1); n3 = g('NAND', b, n1); x = g('NAND', n2, n3)
        if c is None: return x, g('NOT', n1)
        n5 = g('NAND', x, c); n6 = g('NAND', x, n5); n7 = g('NAND', c, n5); return g('NAND', n6, n7), g('NAND', n1, n5)
    pp = [[g('AND', f'a{i}', f'b{j}') for i in range(k)] for j in range(k)]
    s = pp[0][:]; c = [None] * k; outs = [s[0]]; ctop = None
    for j in range(1, k):
        ns = []; nc = []
        for i in range(k):
            x2 = s[i + 1] if i + 1 < k else ctop; x3 = c[i]
            ins = [pp[j][i]] + [x for x in (x2, x3) if x is not None]
            if len(ins) == 3: sm, cy = fa(*ins)
            elif len(ins) == 2: sm, cy = fa(ins[0], ins[1], None)
            else: sm, cy = ins[0], None
            ns.append(sm); nc.append(cy)
        s, c = ns, nc; ctop = None; outs.append(s[0])
    # abschliessende Ripple-Addition von s[1:], c
    carry = None
    for i in range(k):
        x = s[i + 1] if i + 1 < k else None; y = c[i]
        ins = [t for t in (x, y, carry) if t is not None]
        if len(ins) == 3: sm, carry = fa(*ins)
        elif len(ins) == 2: sm, carry = fa(ins[0], ins[1], None)
        else: sm, carry = ins[0], None
        outs.append(sm)
    for o in outs: L.append(f'OUTPUT({o})')
    open(path, 'w').write('\n'.join(L) + '\n')
if __name__ == '__main__':
    import sys
    for k in (4, 6, 8, 12, 16, 24): gen(k, f'/tmp/claude-0/genbench/mul{k}.bench')
