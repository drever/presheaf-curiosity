import json, glob, statistics as st
def load(pat): return [json.load(open(f)) for f in sorted(glob.glob(pat))]
for name, pat in (('syn, 6 Fuellmuster', '../results/e30_syn_*_0.15_g6.json'), ('syn Kontrolle, 1 Fuellmuster, 15% leer', '../results/e30_syn_*_0.15_g1.json'), ('syn Null-Kontrolle: alles fest', '../results/e30_syn_*_0.0_g1.json'), ('c6288', '../results/e30_c6288_*.json'), ('streets', '../results/e30_streets_*.json')):
    rs = load(pat)
    if not rs: continue
    print(name, len(rs))
    for mode in ('iface', 'rel'):
        g = [r[mode]['mean_glue'] for r in rs]; h = [r[mode]['mean_holes'] for r in rs]
        dg = [r['dict_bits'] for r in rs]; dh = [r[mode]['dict_bits_alive'] + r[mode]['hole_dict_bits'] for r in rs]
        d = [a - b for a, b in zip(g, h)]; am = [(a + x / 100) - (b + y / 100) for a, b, x, y in zip(g, h, dg, dh)]
        print(f"  {mode:5s} glue {st.mean(g):6.1f} holes {st.mean(h):6.1f} gain {st.mean(d):5.1f} (min {min(d):5.1f}) | dict glue {st.mean(dg):6.0f} holes {st.mean(dh):6.0f} | gain incl. dict/100 {st.mean(am):5.1f} (min {min(am):5.1f}) | n_holes {[r[mode]['n_holes'] for r in rs]}")
