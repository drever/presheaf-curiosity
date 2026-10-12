import json, glob, statistics as st, collections
rows = collections.defaultdict(list)
for f in glob.glob('../results/e27_*_40_*.json'):
    p = f.split('/')[-1][:-5].split('_'); seed, n, pf, pd, fh = p[1], p[2], p[3], p[4], p[5]
    rows[(fh, pf, pd)].append(json.load(open(f)))
M = ['none', 'exact', 'shape_raw', 'AU', 'AU_oracle', 'repair']
print('fh   pf   pd   nseeds | held-out bits/window (amortised +dict/100)')
for key in sorted(rows):
    rs = rows[key]; line = f"{key[0]:>4} {key[1]:>5} {key[2]:>5} {len(rs)} |"
    for m in M:
        line += f" {m}:{st.mean(r[m]['held'] for r in rs):6.1f}({st.mean(r[m]['amort'] for r in rs):6.1f})"
    d = [r['exact']['held'] - r['AU']['held'] for r in rs]; line += f" | exact-AU {st.mean(d):5.1f} min {min(d):5.1f}"
    print(line)
