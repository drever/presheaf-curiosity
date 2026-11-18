"""Label- and degree-preserving rewiring of a directed labelled edge list (control graphs, lab notebook sections 15 and 17)."""
import collections

def rewire(E, rng, per_edge=20):
    """Swap targets of two edges with equal label; keeps labels, gate types and all in/out degrees."""
    E = list(E); pairs = {(u, v) for u, v, _ in E}; bylab = collections.defaultdict(list)
    for i, (u, v, l) in enumerate(E): bylab[l].append(i)
    done = 0; tries = 0
    while done < per_edge * len(E) and tries < 50 * per_edge * len(E):
        tries += 1; i = rng.randrange(len(E)); idx = bylab[E[i][2]]
        if len(idx) < 2: continue
        j = rng.choice(idx); (a, b, l), (c, d, _) = E[i], E[j]
        if i == j or a == d or c == b or (a, d) in pairs or (c, b) in pairs: continue
        pairs -= {(a, b), (c, d)}; pairs |= {(a, d), (c, b)}; E[i] = (a, d, l); E[j] = (c, b, l); done += 1
    return E, done
