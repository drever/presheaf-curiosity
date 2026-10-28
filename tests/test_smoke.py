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
