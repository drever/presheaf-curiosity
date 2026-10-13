import json, glob, statistics as st, collections, sys
rows = collections.defaultdict(list)
for f in glob.glob('../results/e29_syn_*.json'):
    p = f.split('/')[-1][:-5].split('_'); rows[(p[5], p[3], p[4])].append(json.load(open(f)))
print('Loecher pf pd n | held-out bits/window (amortised)  | hybrid-best(exact,AU) min over seeds')
for key in sorted(rows):
    rs = rows[key]; line = f"{key[0]:>4} {key[1]:>5} {key[2]:>5} {len(rs)} |"
    for m in ('exact', 'AU', 'hybrid'): line += f" {m}:{st.mean(r[m]['mean'] for r in rs):6.1f}({st.mean(r[m]['amort'] for r in rs):6.1f})"
    d = [min(r['exact']['mean'], r['AU']['mean']) - r['hybrid']['mean'] for r in rs]
    line += f" | vs best-of {st.mean(d):5.1f} min {min(d):5.1f}  k_ex {st.mean(r['hybrid']['k_exact'] for r in rs):4.1f} k_sh {st.mean(r['hybrid']['k_shape'] for r in rs):4.1f}"
    print(line)
for w in ('c6288', 'streets'):
    rs = [json.load(open(f)) for f in sorted(glob.glob(f'../results/e29_{w}_*.json'))]
    if not rs: continue
    print(w, len(rs))
    for m in ('exact', 'AU', 'hybrid'): print(f"  {m:7s} held {st.mean(r[m]['mean'] for r in rs):6.1f} amort {st.mean(r[m]['amort'] for r in rs):6.1f} per-seed {[round(r[m]['mean'],1) for r in rs]}")
    print('  k_exact/k_shape', [(r['hybrid']['k_exact'], r['hybrid']['k_shape']) for r in rs])
