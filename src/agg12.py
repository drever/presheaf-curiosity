import json, glob, statistics as st
R={}
for f in glob.glob('e12_?_*_?.json'):
    d=json.load(open(f)); R.setdefault((d['depth'],d['n']),[]).append(d)
for (dp,n),L in sorted(R.items()):
    row=[]
    for m in ('none','hier30','hier100','grow30','grow100','gspan_mdl30','subdue_mdl'):
        v=[r['m'][m]['test'] for r in L if m in r['m'] and 'test' in r['m'][m]]
        if v: row.append(f'{m} {st.mean(v):6.1f}')
    d=[r['m']['grow100']['test']-r['m']['hier100']['test'] for r in L]
    print(f'Tiefe {dp} n={n:>3} ({len(L)} Seeds, Motivgroessen {L[0]["motif_sizes"]}): '+' | '.join(row)+f' || grow100-hier100 {st.mean(d):+.1f}')
