"""Region splits for the held-out test. Standard library only, so the split can be tested without pynauty.

An edge is (source, sink, label) as produced by netlist.load_bench, where label = (source type, sink type) and a primary
input has the type 'IN'."""
from collections import defaultdict, deque, Counter


def is_input_edge(e):
    return e[2][0] == 'IN'


def walk(edges, rng, frac=0.5):
    """Breadth-first walk over the undirected graph of `edges` from one random start node, until `frac` of the nodes are
    reached. Neighbours are visited in sorted order, so the result depends only on `edges` (as a set) and on `rng`.
    Returns the set of reached nodes."""
    adj = defaultdict(set)
    for u, v, _ in edges: adj[u].add(v); adj[v].add(u)
    nodes = sorted(adj); target = int(len(nodes) * frac)
    start = rng.choice(nodes); S = {start}; q = deque([start])
    while q and len(S) < target:
        x = q.popleft()
        for y in sorted(adj[x]):
            if y not in S and len(S) < target: S.add(y); q.append(y)
    return S


def gate_walk_split(E, rng, frac=0.5):
    """Split a netlist into two node-disjoint regions A and B without walking through primary inputs.

    The old split (heldout.py) walked the full undirected graph. In c6288 each of the 32 inputs feeds 16 gates, so the
    walk reached every input and every AND gate within a few steps and left B as fragmented NOR-to-NOR remainder. Here
    the fan-out edges of the inputs are left out of the walk AND of both regions: an input feeds gates on both sides,
    so its edges cannot be given to one region without making the regions share a node.

    Returns a dict: A, B (edge lists), SA (node set of A), cut (gate edges with one end on each side), input_edges
    (number of input fan-out edges left out)."""
    gate = [e for e in E if not is_input_edge(e)]
    SA = walk(gate, rng, frac)
    A = [e for e in gate if e[0] in SA and e[1] in SA]
    B = [e for e in gate if e[0] not in SA and e[1] not in SA]
    return {'A': A, 'B': B, 'SA': SA, 'cut': len(gate) - len(A) - len(B), 'input_edges': len(E) - len(gate)}


def inner_split(A, rng, frac):
    """Split one region again by the same walk: the reached part is for training, the rest for testing. The two parts
    share no node, so no test window can overlap a training window. Edges between the parts are dropped."""
    S = walk(A, rng, frac)
    train = [e for e in A if e[0] in S and e[1] in S]
    test = [e for e in A if e[0] not in S and e[1] not in S]
    return {'train': train, 'test': test, 'cut': len(A) - len(train) - len(test)}


def nodes_of(edges):
    return {x for u, v, _ in edges for x in (u, v)}


def components(edges):
    """Sizes (in nodes) of the connected components of the undirected graph of `edges`, largest first."""
    adj = defaultdict(set)
    for u, v, _ in edges: adj[u].add(v); adj[v].add(u)
    seen = set(); sizes = []
    for s in sorted(adj):
        if s in seen: continue
        seen.add(s); q = deque([s]); n = 1
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in seen: seen.add(y); q.append(y); n += 1
        sizes.append(n)
    return sorted(sizes, reverse=True)


def describe(edges):
    """What a reader needs in order to judge whether two regions are the same kind of graph."""
    lab = Counter('%s>%s' % tuple(l) for _, _, l in edges); comps = components(edges)
    return {'edges': len(edges), 'nodes': len(nodes_of(edges)), 'components': len(comps), 'largest_component': comps[0] if comps else 0,
            'labels': dict(sorted(lab.items(), key=lambda kv: (-kv[1], kv[0])))}
