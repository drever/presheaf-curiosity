import json, glob, statistics as st
for name, pat in (('Tiefe-2-Welt n=60', '../results/e31_d2_*_n60.json'), ('Tiefe-2-Welt n=150', '../results/e31_d2_*_n150.json'), ('Kontrolle Tiefe-1-Welt n=60', '../results/e31_d1_*_n60.json')):
    rs = [json.load(open(f)) for f in sorted(glob.glob(pat))]
    if not rs: continue
    print(name, len(rs))
    for r in rs:
        d2 = r['d2']
        print(f"  glue {r['glue']:6.1f} flat {r['flat']:6.1f} d2 {('%6.1f' % d2) if d2 else '  -   '} | dict glue {r['dict_glue']:5.0f} flat {r['dict_flat']:5.0f} d2 {('%5.0f' % r['dict_d2']) if d2 else '  -  '} | holes {r['n_holes']} chosen {r.get('d2_chosen')} {r.get('info','')}")
    ok = [r for r in rs if r['d2']]
    if ok:
        print('  mean test: glue %.1f flat %.1f d2 %.1f; d2-vs-flat %.1f (min %.1f); d2-vs-glue %.1f' % (st.mean(r['glue'] for r in ok), st.mean(r['flat'] for r in ok), st.mean(r['d2'] for r in ok), st.mean(r['flat'] - r['d2'] for r in ok), min(r['flat'] - r['d2'] for r in ok), st.mean(r['glue'] - r['d2'] for r in ok)))
