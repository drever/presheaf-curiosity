# presheaf-curiosity

Experiments on whether an MDL "macro learner" motivated by presheaves
(every presheaf is a colimit of representables; macros = reusable sub-colimits, glued along shared parts)
gives an algorithmic advantage over graph-pattern miners. This is an empirical test, not a proof;
the interactive demo (graphs, subgraph macros, triangles) is published separately as a Claude artifact.

## Status in one paragraph

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

## Caveats

* Our learner optimizes the same function that is used for evaluation (home advantage).
* SUBDUE pattern extraction from compressed graphs is imperfect (instance agreement 67-89%).
* GraphMDL ran under time limits (90-600 s) and crashed in two pruning steps (library bug); its numbers at larger n are not reliable.
* Few seeds (3-10), one molecule set, synthetic worlds written by us.
* Early scripts (control tests, approximate matching, symmetry on UMLS) were lost in an environment reset; their results are not in this repo.

## Reproducing

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
