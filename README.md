# presheaf-curiosity

Experiments on whether an MDL "macro learner" motivated by presheaves
(every presheaf is a colimit of representables; macros = reusable sub-colimits, glued along shared parts)
gives an algorithmic advantage over graph-pattern miners. This is an empirical test, not a proof;
the interactive demo (graphs, subgraph macros, triangles) is published separately as a Claude artifact.

## Status in one paragraph

(Interim conclusion of 2026-10-11: strategy.md, section 4a. Literature review on macros with holes / category theory: review-makros.md.)


On gSpan+MDL and SUBDUE the learner wins clearly. GraphMDL (scikit-mine, pure Python) is the strongest
opponent measured so far; with 100 candidates our learner is on par with it on Kinships at a fraction of the runtime.
The only clear *conceptual* advantage found so far appears when the data contain a hidden symmetry
(relation/inverse-relation pairs) and the learner estimates it by MDL (equivalence of macros). On Kinships that
equivalence does not help (it costs 1-2.5 bits). No advantage of the presheaf view on real graphs has been shown.

## Method (src/und.py, src/und2.py)

* Data: many small components (edge lists `(a, relation, b)`), train/test split.
* Cost (shared by all methods, `total_u`): raw edge `2*log2(n)+log2(R)` bits, pattern instance
  `log2(|D|+1)+#vertices*log2(n)`, dictionary `2+|p|*(2*log2(maxn)+log2(R))` per pattern. Greedy cover, larger patterns first.
* `learn_u(mode='hier')`: one pattern per round; candidates = unions of two overlapping pieces of the current cover
  ("Verkleben"); prefilter by count*size, top `topc` evaluated exactly by total description length.
  `mode='grow'`: one piece must be a single edge (SUBDUE/gSpan-like growth).
* `learn_x` / `learn_best` (`und2.py`): additionally a pool of all connected sub-edge-sets up to `maxs` edges;
  the dictionary with the smaller *training* description length is kept.
* Equivalence (`e2.py`, `e4.py`): estimated involution on relations (`est_mdl`), quotient of the data,
  orientation bits charged (1 bit per edge on synthetic data, 2 bits per canonical edge on Kinships).
* Opponents: gSpan (`gspan-mining`) + greedy MDL selection, SUBDUE (holderlb/Subdue, patched `Graph.Compress`, see `src/mol_subdue.py`;
  set `SUBDUE_SRC` to its `src` dir), GraphMDL (scikit-mine 1.0.0; needs `logging.Logger.__call__` workaround, see `src/e3.py`).

## Key results (test bits per component, lower is better; see `results/*.json`)

Kinships (5 seeds, 5-node components): plain `hier100` 99.7 at 210 training components; SUBDUE 113.9; gSpan+MDL 109.3.
With 20/60 training components: plain 106.4/101.3, GraphMDL 107.9/104.5, gSpan+MDL 118.0/109.0, SUBDUE 128.5/116.6.

Synthetic world with hidden inverse relations (10 seeds): with 40 training components plain 76.6,
learner + estimated equivalence 59.6, oracle 57.3; GraphMDL 73.8 (5 seeds).
Without symmetry the estimated equivalence costs 1-2 bits.

Molecules (RDKit solubility, 16-atom components, 10 seeds): hier30 126.3, SUBDUE 130.5, gSpan+MDL 141.7 (older runs, scripts `mol_*.py`).

## Composition vs. hierarchy depth (src/e12.py, e13.py; results/e12_*, e13_*)

Synthetic world: library of 6 motifs per level, base = 2-edge path, each higher level glues two lower-level motifs at one node
(depth d -> motifs with 2^(d+1) edges: 2, 4, 8, 16), 3 motifs + 4 noise edges per component of 24 nodes, 12 relations, 5 seeds.
Test bits per component (n=100 training components; n=300 gives the same picture for depths 0-2):

| depth | none | hier100 | grow100 | gSpan+MDL | SUBDUE |
|---|---|---|---|---|---|
| 0 | 125.7 | 99.0 | 99.0 | 99.0 | 102.1 |
| 1 | 200.0 | 129.2 | 146.5 | 128.5 | 136.0 |
| 2 | 343.8 | 190.9 | 238.7 | 213.5 (vertex limit 20) | 234.6 |
| 3 | 620.7 | 327.5 | 390.5 | timeout (>400 s) | 436.3 |

Caveats: `grow` stalls early (max pattern 2-6 edges at depth 3) rather than being unable in principle to reach large patterns;
at depth 1 gSpan equals hier because its support threshold finds the 4-edge motifs directly; the dictionary cost is flat (a composite
pattern is not charged as a reference to its parts), so the benefit measured here is a *search* benefit, not a shorter hierarchical dictionary.

## Hierarchical dictionary cost (src/und3.py, src/e14.py; results/e14_*)

`dict_bits_h`: a dictionary pattern is paid as references to earlier patterns/edges plus gluing bits (new-or-identified flag per vertex,
and which earlier vertex it is identified with), capped by the flat edge-list cost. `learn_h(objective='hier')` selects patterns with this cost.
Same depth-world as above, 5 seeds. Train cover + dictionary/n under the hierarchical cost, and test bits (cover only):

| depth, n | hier (flat obj.) | hier (hier obj.) | grow (hier obj.) | gSpan+MDL | SUBDUE |
|---|---|---|---|---|---|
| 2, 30 | 211.4 / 204.3 | 203.2 / 192.7 | 242.7 / 237.3 | 224.4 / 221.0 | 254.1 / 250.4 |
| 2, 100 | 194.6 / 191.5 | 194.6 / 191.8 | 240.3 / 238.4 | 214.1 / 213.5 | 236.5 / 234.0 |
| 3, 30 | 350.4 / 344.5 | 339.7 / 327.9 | 394.8 / 389.8 | – | – |
| 3, 100 | 332.4 / 329.6 | 326.8 / 321.8 | 388.9 / 386.7 | – | – |

(entries: Train+Dict-hier / Test). The dictionary of the compositional learner shrinks 2-4x under the hierarchical cost
(depth 3, n=100: 1825 -> 504 bits), grow's dictionary only about 2x. Selecting with the hierarchical cost adds 5-11 bits on top of the search advantage,
mostly with little data and large motifs. The glue-cost model is my own choice and the objective is also the evaluation measure.

## Real data with the hierarchical dictionary cost (src/e15.py, e16.py; results/e15_*, e16_*)

Kinships/UMLS: 1000 sampled 5-node components (700 train / 300 test), K=40, 5 seeds. Molecules (RDKit solubility): 300 components of 12 or 16 atoms
(210 train / 90 test), K=40, 5 seeds. Test bits per component; in brackets Train+Dictionary/n under the hierarchical dictionary cost.
`hier_*`/`grow_*` = gluing any two pieces / growing by one edge; `_flat`/`_hier` = flat or hierarchical dictionary cost used for selection.

| data | hier_flat | hier_hier | grow_flat | grow_hier | gSpan+MDL | SUBDUE |
|---|---|---|---|---|---|---|
| Kinships | 96.2 (96.6) | 96.3 (96.7) | 99.6 (99.9) | 98.9 (99.2) | 108.7 (108.2) | 112.7 (1 seed) |
| UMLS | 86.9 (85.9) | 86.9 (85.7) | 86.5 (85.5) | 86.3 (85.4) | 106.7 (104.1) | not run |
| Molecules, 16 atoms | 123.0 (123.9) | 120.2 (121.6) | 130.0 (130.1) | 127.2 (128.5) | 142.1 (143.8) | 127.7 (130.4) |
| Molecules, 12 atoms | 88.4 (86.8) | 84.9 (84.7) | 90.9 (90.2) | 88.1 (89.0) | 94.6 (94.3) | 90.5 (90.4) |

Gluing beats one-edge growth by 2.6-3.4 bits on Kinships (5/5 seeds), 7 bits on 16-atom molecules (5/5), 2.5-3.2 on 12-atom molecules (5/5), and not at all on UMLS (-0.5).
The hierarchical selection cost helps only on molecules (2.8-3.5 bits). GraphMDL was not run at this scale (infeasible in the pure-Python port).

## Products and compositional generalization (src/und4.py, e17.py; results/e17_*)

Synthetic grids = Cartesian products of two chain families; 10 of 25 factor pairs never appear in training. A dictionary with product closure
(all products of chosen factors are implicit entries) and fully data-driven factor discovery (relation classes from squares, factors = fibers,
MDL selection) lowers test bits on unseen pairs from 369 (gluing only) to 257 (n=50) and 230 (n=150); oracle factors give 225. At n=20 the gain is small (329 vs 385).
Synthetic world matching the algorithm's assumptions; no comparison with gSpan/SUBDUE yet. Details and caveats: strategy.md, section 4.

Noise sweep (src/e18.py): with 12 noise edges per component the advantage holds (unseen 330 vs 478 gluing at n=150, oracle 332); with 24 it shrinks (491 vs 606, oracle 471). gSpan+MDL is far behind on this world (597-649), partly due to size/time limits.

Real street data (src/streets.py, e19*.py): OSM roads of Spanish cities (from a GitHub repo, since OSM servers are not reachable from the sandbox). Product closure gives no gain (differences <= 1.6 bits, 3 seeds, labelled and unlabelled); gluing compresses windows by ~30%. See strategy.md, 1c.

(Street results were re-run with symmetric edges, `SYM=1`: see strategy.md, correction after 1d; conclusions unchanged.)

Shape x labeling model on streets (src/e20*.py): unlabelled shape dictionary + neighbour-context label coder beats labelled gluing by 3.6-8.4 bits per window (1.5-3.5%, 12/12 cases), but this is a generic context-model gain, not a presheaf advantage; "opposite edge in a square" gives nothing. See strategy.md, 1d.

Chip netlists (src/netlist.py, e21.py): ISCAS85 c6288 (16x16 array multiplier) windows (correct driver->sink orientation): gluing beats grow-by-one-edge by 46-53 bits (23-25%, 3 seeds), SUBDUE sits near grow-by-one, gSpan only runs with patterns <= 6 edges (larger limits time out) and is much worse; the largest composition effect on real data so far; no product factors at gate level (the cell lattice only exists after contracting cells). Data: github.com/ispras/hdl-benchmarks, EPFL arithmetic benchmarks. See strategy.md, 1e.

Cell level of c6288 (src/cells*.py, quotient.py, e23.py): learned 20-edge adder cell (195 instances), quotient graph with commuting squares (bundle x edge); gluing beats growing by 3.5-25 bits, product closure picks 0-2 factors and gains <= 0.6 bits. See strategy.md, 1f.

## Caveats

* Our learner optimizes the same function that is used for evaluation (home advantage).
* SUBDUE pattern extraction from compressed graphs is imperfect (instance agreement 67-89%).
* GraphMDL ran under time limits (90-600 s) and crashed in two pruning steps (library bug); its numbers at larger n are not reliable.
* Few seeds (3-10), one molecule set, synthetic worlds written by us.
* Early scripts (control tests, approximate matching, symmetry on UMLS) were lost in an environment reset; their results are not in this repo.

## Reproducing

Street experiments additionally need `git clone https://github.com/amoraschi/spain-cities-geojson /tmp/dl/spain-cities-geojson` (path set in src/streets.py).
Netlist experiments need `git clone https://github.com/ispras/hdl-benchmarks /tmp/dl/hdl-benchmarks` (and an EPFL benchmarks clone at /tmp/dl/benchmarks; see src/netlist.py).


```
pip install -r requirements.txt   # use a venv; pynauty needs a recent setuptools
cd src
# data (not in the repo): kgdata/{kinships,umls}/train.txt (tab-separated triples, e.g. from the PyKEEN datasets),
# mol/solubility.{train,test}.sdf (RDKit solubility set)
python e2.py sym 0            # synthetic world with symmetry, seed 0
python e3.py sym 0 90         # opponents (gSpan, SUBDUE, GraphMDL) on that world
python e4.py 0 300 1          # Kinships: plain vs equivalence vs opponents
python e8.py nosym 0 && python e10.py sym 0
```

Test A (macros with interface, src/iface.py, e24*.py): charging instances only for boundary vertices saves ~41 bits (26%) for glue and ~20 bits (10%) for grow on c6288 windows (3 seeds, re-costed dictionaries); on streets ~21-26 bits for both, i.e. a generic coding gain. See strategy.md, 4c.

Baseline with interfaces (src/repair.py, e25*.py; gRePair-like digram replacement, own re-implementation): on c6288 glue with interface coding stays ~53 bits (31%) better than the baseline, which lands just under grow-by-one; on streets glue ~ grow and both ~27 bits better than the (overfitting) baseline. See strategy.md, 4d.
