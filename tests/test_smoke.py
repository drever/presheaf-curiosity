"""Smoke tests: pattern covering, the lattice rule learner, and the RePair-style baseline (lossless round trip)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import und
from und import cover_u, canon_u
from core import Comp
from latt import learn_rule, lattice_fit

def test_cover_finds_repeated_pattern():
    und.SYMS = set()
    # three disjoint copies of a labelled 2-path a -0-> b -1-> c
    es = []
    for k in range(3): es += [(3 * k, 0, 3 * k + 1), (3 * k + 1, 1, 3 * k + 2)]
    comp = Comp(9, es); pat = ((0, 0, 1), (1, 1, 2))
    inst, raw = cover_u(comp, [pat])
    assert len(inst) == 3 and not raw

def test_canon_is_isomorphism_invariant():
    und.SYMS = set()
    a = [(0, 0, 1), (1, 1, 2)]; b = [(5, 0, 7), (7, 1, 3)]
    assert canon_u(a, False) == canon_u(b, False)

def test_lattice_rule_is_learned_and_extrapolates():
    # an m x m grid with two edge labels: label 0 along u, label 1 along v
    def grid(m):
        ix = lambda u, v: u * m + v; es = []
        for u in range(m):
            for v in range(m):
                if u + 1 < m: es.append((ix(u, v), 0, ix(u + 1, v)))
                if v + 1 < m: es.append((ix(u, v), 1, ix(u, v + 1)))
        return es, m * m
    es, n = grid(4); gens = learn_rule(es)
    assert len(gens) == 2
    big, nb = grid(12); fit = lattice_fit(gens, big, nb)
    assert fit['extra'] == 0 and fit['miss'] == 0 and fit['orphans'] == 0

# --- held-out split (src/split.py) and deterministic windows (src/netlist.py) ---
import random, subprocess, json
import split as SP

def _toy_netlist(m=8):
    """m x m grid of NOR gates (g<row>_<col>), plus 4 primary inputs that each feed one gate in every row."""
    E = []
    for r in range(m):
        for c in range(m):
            if r + 1 < m: E.append((f'g{r}_{c}', f'g{r + 1}_{c}', ('NOR', 'NOR')))
            if c + 1 < m: E.append((f'g{r}_{c}', f'g{r}_{c + 1}', ('NOR', 'NOR')))
    for i in range(4):
        for r in range(m): E.append((f'in{i}', f'g{r}_{2 * i}', ('IN', 'NOR')))
    return E

def test_gate_walk_split_leaves_inputs_out_and_regions_share_no_node():
    E = _toy_netlist(); sp = SP.gate_walk_split(E, random.Random(1))
    na, nb = SP.nodes_of(sp['A']), SP.nodes_of(sp['B'])
    assert sp['input_edges'] == 32 and not any(x.startswith('in') for x in na | nb)
    assert na and nb and not (na & nb)
    assert len(sp['A']) + len(sp['B']) + sp['cut'] == len(E) - 32
    assert abs(len(na) - len(nb)) <= 8          # two halves, not a sliver and a rest
    # the old walk goes through the inputs and takes them into its half: that is the flaw this split removes
    old = SP.walk(E, random.Random(1)); assert any(x.startswith('in') for x in old)

def test_split_does_not_depend_on_edge_order():
    E = _toy_netlist(); F = list(E); random.Random(7).shuffle(F)
    a = SP.gate_walk_split(E, random.Random(3)); b = SP.gate_walk_split(F, random.Random(3))
    assert a['SA'] == b['SA'] and sorted(a['A']) == sorted(b['A']) and a['cut'] == b['cut']

def test_inner_split_parts_share_no_node():
    E = _toy_netlist(); A = SP.gate_walk_split(E, random.Random(1))['A']; inn = SP.inner_split(A, random.Random(2), 0.5)
    assert inn['train'] and inn['test'] and not (SP.nodes_of(inn['train']) & SP.nodes_of(inn['test']))
    assert len(inn['train']) + len(inn['test']) + inn['cut'] == len(A)

def test_components_counts_pieces():
    assert SP.components([('a', 'b', ('NOR', 'NOR')), ('c', 'd', ('NOR', 'NOR')), ('d', 'e', ('NOR', 'NOR'))]) == [3, 2]

_WINDOW_PROBE = r'''
import sys, json, random
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
from netlist import windows_from, to_comp, Labeler
from test_smoke import _toy_netlist
rng = random.Random(5); ws = windows_from(_toy_netlist(), rng, 6, nmax=12, emin=4, labeler=Labeler())
print(json.dumps([ws, [to_comp(w, rng, 31).E for w in ws]]))
'''

def test_windows_do_not_depend_on_the_hash_seed():
    here = os.path.dirname(os.path.abspath(__file__)); src = os.path.join(here, '..', 'src'); outs = []
    for hs in ('1', '2', '3'):
        p = subprocess.run([sys.executable, '-c', _WINDOW_PROBE, src, here], capture_output=True, text=True, env={**os.environ, 'PYTHONHASHSEED': hs})
        assert p.returncode == 0, p.stderr
        outs.append(p.stdout)
    assert json.loads(outs[0])[0] and outs[0] == outs[1] == outs[2]

# --- coder: bytes written and read back ---
def test_coder_roundtrip_both_modes():
    import coder
    from core import Comp
    pat = ((0, 0, 1), (1, 1, 2), (2, 0, 0))                       # a labelled triangle
    edges = []
    for k in range(5):                                            # five triangles in a chain, joined at one node each
        a, b, c = 2 * k, 2 * k + 1, 2 * k + 2
        edges += [(a, 0, b), (b, 1, c), (c, 0, a)]
    edges.append((0, 1, 10))
    comp = Comp(11, edges)
    for mode in ('all', 'boundary'):
        b, info = coder.encode(comp, [pat], 2, mode); v = coder.verify(comp, b, info, mode)
        assert info['instances'] == 5 and all(v.values()), (mode, v)
    assert coder._subset_unrank(coder._subset_rank([1, 3, 4], 6), 6, 3) == [1, 3, 4]

# --- coder2: products and holes, bytes written and read back ---
def test_coder2_rans_and_models():
    import random, coder2
    from core import Comp
    # rANS with skewed frequencies round-trips
    w = coder2.Enc(); rng = random.Random(1); syms = [rng.choice([0, 0, 0, 1, 2]) for _ in range(300)]; tab = [50, 3, 1]
    for s in syms: w.freq(s, tab)
    w.uni(7, 11); d = coder2.Dec(w.tobytes())
    assert [d.freq(tab) for _ in syms] == syms and d.uni(11) == 7 and d.done()
    # product closure: a 3x2 grid is rebuilt by the decoder from two path factors
    import und4
    h = ((0, 0, 1), (1, 0, 2)); v = ((0, 1, 1),)
    g = und4.prod_pattern(h, v)
    comp = Comp(12, [(a, r, b) for a, r, b in g] + [(a + 6, r, b + 6) for a, r, b in g])
    m = coder2.model_product([], [h, v], {0: 0, 1: 1}, 12)
    for mode in ('all', 'boundary'):
        b, info = coder2.encode([comp], m, 2, mode); assert all(coder2.verify([comp], b, info).values()) and info['raw_edges'] == 0
    # hole: frame triangle with a hole between nodes 0 and 1, two different fillers, one empty
    frame = ((0, 0, 1), (1, 0, 2), (2, 0, 0)); f1 = ((0, 1, 2), (2, 1, 1)); f2 = ((0, 2, 2), (2, 2, 3), (3, 2, 1))
    es = []
    def add(base, fil):
        es.extend((base + a, r, base + b) for a, r, b in frame)
        if fil:
            loc = {0: base, 1: base + 1}
            for k in range(2, 2 + max(max(a, b) for a, _, b in fil) - 1): loc[k] = base + 1 + k
            es.extend((loc[a], r, loc[b]) for a, r, b in fil)
    add(0, f1); add(6, f2); add(12, None); add(18, f1)
    comp = Comp(24, es)
    m = coder2.model_holes([frame], [{'key': (0, 0, 1), 'fil': ['a', 'b']}], {'a': f1, 'b': f2}, {0})
    for mode in ('all', 'boundary'):
        b, info = coder2.encode([comp], m, 3, mode); v = coder2.verify([comp], b, info)
        assert all(v.values()) and info['units'] == 4 and info['raw_edges'] == 0, (mode, v, info)
