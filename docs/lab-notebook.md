# Lab notebook: does the presheaf view give an algorithmic advantage?

> **How to read this document.** This is the working log of the project, translated from the German original (`strategy.md` in the git history). It is a lab notebook, not a paper: sections are in chronological order, early sections are sometimes superseded by later ones, and every result is a *development* result (no held-out data set was kept until the very end; see section 6 and "Held-out test"). Baselines such as RePair are **our own re-implementations** following the published descriptions, without the original optimisations; nothing here should be read as a claim to beat RePair, gRePair, SUBDUE, gSpan or GraphMDL. Statements marked "belegt" in the original are literature-verified, "ungeprüft" are not.
> A short status table of all claims is in the top-level `README.md`.
> **Added 16 November 2026:** every comparison with our RePair re-implementation in sections 4d-4p is affected by the edge-order finding of section 9 and should be read as unverified.

Status of the original document: 11 October 2026 (interim conclusion in section 4a), extended until 28 October 2026.

## 1. Starting idea

From a conversation with Gemini: "artificial curiosity" (Schmidhuber) could be based on presheaves. Leinster: every presheaf is a colimit of representables (density), analogous to prime factorisation. An agent that views its data as a presheaf could learn its own base category: find reusable sub-colimits ("macros") that lower the description length (MDL), and use the learning progress as a curiosity reward.

Guiding question: **does the categorical view give a measurable advantage over what one would do anyway** (Re-Pair on graphs, SUBDUE, gSpan, GraphMDL)? A negative result is a valid result.

## 2. Approach so far

1. **Demo** (graphs, subgraph macros, triangles, an agent discovering its base): interactive page published as a Claude artifact.
2. **Learner** (`src/und.py`): MDL macro learner on many small components. One pattern per round. Candidates arise by gluing two touching pieces of the current cover (pushout). Exact selection by total description length.
3. **Honest tests** against gSpan (+ greedy MDL), SUBDUE (holderlb, patched), GraphMDL (scikit-mine), on molecules (RDKit solubility), Kinships, UMLS and planned synthetic worlds.
4. **Ablations** instead of competition: gluing versus growing by one edge (`grow`), equivalence on/off, flat versus hierarchical dictionary costs, with/without subgraph pool.

Methodological rules we imposed on ourselves:
* One shared, neutral evaluator for all methods (`total_u`); home advantage (we optimise what we measure) is always stated.
* Write down the hypothesis and the expected direction beforehand; controls with planned structure and without (`sym`/`nosym`).
* Several seeds, report the spread; a tie is not reported as a win.
* Report time limits and library failures (GraphMDL crashes) openly, do not silently drop them.

## 3. Findings so far (short version)

* **Selection by MDL** explains most of the lead over gSpan/SUBDUE.
* **Composition (gluing)** gives an additional advantage that grows with pattern size and hierarchy depth (planted hierarchies: 17/48/63 bits versus `grow` at depth 1/2/3; real data: 2.5-3.4 bits on Kinships, 7 bits on 16-atom molecules, 0 on UMLS). Partly a search advantage (`grow` gets stuck in local optima), partly encoding.
* **Hierarchical dictionary costs** (patterns as references to parts) shrink dictionaries 2-4x and help on molecules (2.8-3.5 bits).
* **Equivalence of macros** (inverse relations, estimated by MDL) helps a lot when the data have a clean symmetry (synthetic: about 17 bits at 40 components), nothing to slightly negative on Kinships.
* **GraphMDL** is a serious opponent on small sets, but the Python version does not finish at 700 components. The Java version was not reachable from here.
* So far **no evidence** that the presheaf view yields more on real graphs than Re-Pair with MDL selection.

## 4. Higher-order structure (current thread)

Observation: our approach lives in the colimit (pushout) fragment. A presheaf topos, however, is cartesian closed: products A x B, exponentials B^A with (B^A)(c) = Hom(y(c) x A, B), subobject classifier. We have not used that so far.

Plan of attack, in this order:

1. **Products (now).** Data from grids, ladders, cylinders = products of small chains. Dictionary entries may be expressions: `A x B` of two earlier entries. Two measurements:
   * Cost: a product costs two references plus an operator bit instead of its edge list.
   * **Compositional generalisation:** training contains only some of the factor pairs; unseen pairs occur at test time. A dictionary with product closure (all products of the chosen factors are implicitly contained) should be able to cover them, a pure colimit dictionary should not.
   Expectation: advantage of the closure on unseen pairs; none on seen pairs. Refuted if the gap on unseen pairs is not larger than on seen pairs.
2. **Parametrised macros** (holes): pushout along an interface H -> P, similar to the abstractions in DreamCoder/Stitch. Test on the planted hierarchies.
3. **Relation composition** as redundancy in the data (aunt = sister o mother), analogous to rule mining (AMIE) on Kinships/UMLS.
4. **Exponentials in the narrow sense:** states S, actions A, transition S x A -> S, curried to A -> S^S. This is the bridge back to the agent (curiosity about the predictability of behaviour spaces). Furthest away, closest to the original idea.

### Result step 1 (products), `src/e17.py`, `src/und4.py`, `results/e17_*`

World: 5 horizontal + 5 vertical chains (relation classes 0-5 / 6-11), 25 possible pairs, 15 of them in training, 10 never seen; each component contains 2 grids (Cartesian product of a pair) plus 4 noise edges. Test bits per component, mean over 5 seeds ("seen"/"unseen" pairs).

| Method | n=20 seen | n=20 unseen | n=50 seen | n=50 unseen | n=150 seen | n=150 unseen |
|---|---|---|---|---|---|---|
| Gluing (glue_hier) | 306.7 | 384.7 | 301.9 | 368.0 | 304.3 | 368.8 |
| Growing (grow_hier) | 326.1 | 370.0 | 331.9 | 353.2 | 328.1 | 347.2 |
| Closure, factors from the gluing dictionary (cross products only) | 289.2 | 365.1 | 278.3 | 344.1 | 272.8 | 352.9 |
| Closure, path factors, classes given | 263.7* | 341.0* | 260.2 | 329.8 | 247.4 | 317.2 |
| **Closure, fully data-driven (`prod_auto`)** | 236.1 | 329.2 | 214.1 | 257.3 | 204.5 | 230.3 |
| Oracle (true chains as factors) | 210.6 | 229.6 | 212.0 | 225.6 | 211.1 | 224.6 |

(*The row "classes given" is the one with learned classes, `prod_data_learnedcls`; with given classes it is similar.)

"Fully data-driven" (`prod_auto`) means: (1) learn relation classes from **squares** (4-cycles with equal opposite edges); the opposite-relation of labels is weighted 2-coloured; (2) factor candidates are the **fibres**, i.e. the connected components of the graph restricted to one class, present in at least 2 components; (3) selection by MDL, single steps before pair steps (a single factor alone generates nothing with cross products).

Reading, honestly:
* **Hypothesis confirmed:** with product closure the gap between seen and unseen factor pairs almost vanishes. At n=150 the automatic method scores 230 on unseen pairs versus 225 (oracle) and 369 (gluing): about 140 bits less, without prior knowledge of the classes.
* **This is compositional generalisation that a pure colimit dictionary does not provide.** Gluing stays at 304 vs 369 (seen/unseen).
* **Dependence on n:** at n=20 the fibres are missing (threshold of 2 components and rare chains); the gain on unseen pairs there is 55 bits, at n=50 111, at n=150 138. This is the expected direction (more data, more compositionality).
* **Errors on the way, corrected:** (a) square detection compared edges incorrectly; (b) BFS colouring let one noise square colour a label wrongly and thereby removed all chains with that label (n=50, seed 3: 348 instead of 244); (c) a 10% frequency threshold discarded rare chains.
* **Limitations:** the world was built by us and is exactly the structure the algorithm looks for (product of two relation classes, chains as factors, opposite edges labelled equally). Learner and evaluation share the cost function. The method selects 12-14 factors, 8-10 of them genuine; the others are harmless extra factors (the maximum maxf=14 is reached at n=150). Noise: only 4 edges per component.
* **Not measured:** gSpan/SUBDUE on this world, real data with product structure (grids, molecules with rings), more noise, factors with more than two classes, non-Cartesian gluings of products.

### Result step 1b: robustness to noise and gSpan as opponent (`src/e18.py`, `results/e18_*`)

Same world, noise edges per component 4 / 12 / 24 (grids occupy 20-40 edges); test bits, unseen pairs (seen in parentheses), mean over 3 seeds (noise 4: only 1 seed, n=50).

| Noise | n | Gluing | prod_auto | Oracle | gSpan+MDL |
|---|---|---|---|---|---|
| 4 | 50 | 324 (272) | 210 (195) | 187 (192) | 410 (369) |
| 12 | 50 | 473 (409) | 375 (324) | 337 (310) | 633 (525), 2 of 3 seeds |
| 12 | 150 | 478 (400) | 330 (304) | 332 (309) | 597 (510) |
| 24 | 50 | 612 (538) | 560 (499) | 466 (449) | timeout (400 s) |
| 24 | 150 | 606 (534) | 491 (465) | 471 (446) | 649 (626), 1 of 3 seeds |

Reading: at medium noise (12) the advantage of the closure holds (unseen pairs 100-150 bits below gluing), and at n=150 it sits on the oracle. At strong noise (24) it shrinks to 45-115 bits and stays a good distance from the oracle; at n=50 factor finding is then the bottleneck (noise edges change the fibres, squares become rarer). gSpan with MDL selection finds almost nothing useful here (large grids exceed the node limit and the run time; timeouts at noise 24); on unseen pairs it is at or above the empty dictionary. This is a comparison with an opponent that fits this world badly (no product closure, limits on nodes and run time), not a proof that no miner can do it. SUBDUE and GraphMDL were not measured here.

### Result step 1c: real street data (negative), `src/streets.py`, `e19*.py`, `results/e19*`

Data: the GitHub repo `amoraschi/spain-cities-geojson` (OSM streets of the Spanish provincial capitals, `highway` tag per way). Direct OSM access (Overpass, Geofabrik, Nominatim) and SNAP are not reachable from the container, only GitHub and PyPI. The Valencia file in the repo is empty.
Preparation: junction graph (nodes = endpoints and shared points), driving roads only (no footpaths/cycle paths, which would otherwise make up 70% of the edges), edge label = road class (major / medium / residential / service). Components = spatial windows (0.004 degrees, about 26 edges on average, at most 40 nodes). Training: 60-100 windows from Barcelona; test: 100 windows from Barcelona (held out) as well as Madrid, Zaragoza, Sevilla.

* **Streets are compressible:** test bits 372 (empty) -> 258 (gluing), patterns up to 7-10 edges. Gluing and growing are equally good (258.3 vs 257.3 in Barcelona).
* **Grid structure exists:** 45-60% of the windows contain 4-cycles, about 25% several.
* **Product closure brings nothing:** with road classes as labels (factors: single-colour paths, 3 seeds, n=60) 260.1 vs 259.8 / 251.1 vs 251.1 / 256.9 vs 256.6 (Barcelona); in pure geometry (all edges the same label, 3 seeds, n=100) 223.2 vs 222.7 / 221.3 vs 221.4 / 217.5 vs 217.5. The same on the other cities (difference at most 1.6 bits).
* **Interpretation (not tested, only plausible):** (1) the grids in the windows are small and irregular (non-induced embedding, missing edges, mixed classes), exact products of long paths are rare; (2) small grid building blocks (square, ladder) are already covered cheaply by gluing. (3) In real grids the road class belongs to the row (the street), not to the position along the street; that is not a product with factor labels as our synthetic world builds it. A more suitable model would be grid shape x labelling function. We had not built that yet.
* **Consequence:** the advantage of product closure is so far demonstrated only on the world we constructed. It did not show up on real streets.

### Result step 1d: model "grid shape x labelling function" on streets, `src/e20.py`, `e20b.py`, `results/e20*`

Model: two layers. (1) Shape: graph without labels (R=1), dictionary as before. (2) Labelling: the label of each edge, conditioned on the labels of already-coded neighbouring edges (BFS order; context = label pair of the first coded edge at each endpoint; table from the training set, Laplace 0.5). Compared with the previous marked gluing. Street windows as in 1c (n=100, 3 seeds, test on the held-out Barcelona windows and three other cities).

* **Decomposition:** shape (R=1) costs about 223 bits (empty 299), labelling about 48 bits (iid) or 31 bits (neighbour context). Product closure on the shape brings nothing (1c). Everything to be gained lies in the labelling layer, at most about 17-20 bits out of about 255.
* **Neighbour context helps:** label cost 48 -> 31 bits per window (Barcelona, similar in the other cities). Streets rarely change class in the middle of their course.
* **Total (test bits per window), marked gluing vs shape+labelling (neighbour context), mean over 3 seeds:** Barcelona 256.2 vs 251.5 | Madrid 237.4 vs 229.7 | Zaragoza 208.3 vs 201.8 | Sevilla 250.9 vs 243.6. A gain of 3.6-8.4 bits per window (1.5-3.5%) in each of the 12 cases (4 cities x 3 seeds). Shape+labelling with iid labels (no context) is **worse** than marked gluing (about 268 vs 256 in Barcelona): the marked patterns already capture label correlations partly.
* **Costs:** dictionary plus parameter bits are higher (context table about 400-430 bits against about 30 bits for iid, for 100 training windows in total, i.e. about 4 bits per window for the full approach; net, a gain of about 0.5-3 bits per window remains on the training data, 3.6-8.4 on test data where the dictionary does not count).
* **Product idea checked and discarded:** context "label of the opposite edge in the square" (labelling belongs to the row): 47.6 vs 48.3 (iid) and 31.2 vs 30.9 (with neighbour context). The labelling depends on the continuity of the street (neighbourhood), not on product structure.
* **Classification:** this is a generic context-model gain (any method could use neighbour labels as context), not an advantage of the presheaf view. It only shows that our marked patterns do not exploit label continuity optimally.
* **Open:** gSpan/SUBDUE/GraphMDL on streets not measured; an opponent with the same labelling model would also receive the gain.

## 4a. Interim conclusion (11 October 2026)

**Question:** does the presheaf view (graph as a colimit of representable pieces, macros as pushouts, now also products) have a measurable algorithmic advantage over what one would do anyway (Re-Pair/gSpan/SUBDUE/GraphMDL with MDL selection)?

**Short answer, as of that date:** on our synthetic worlds yes; on real data so far no, or only small and not specific.

### What is established, by strength of evidence

| Statement | Evidence | Limitation |
|---|---|---|
| MDL selection explains most of the lead over gSpan/SUBDUE | several data sets, seeds | not presheaf-specific (any miner can do MDL selection) |
| Gluing (pushout) beats growing by one edge; the lead grows with hierarchy depth | synthetic hierarchies: 17/48/63 bits at depth 1/2/3 | partly a search advantage against a locally stuck `grow` |
| Gluing on real data | Kinships 2.5-3.4 bits, molecules up to 7 bits, UMLS 0 | small (about 1-3%), data-set dependent |
| Hierarchical dictionary costs | molecules 2.8-3.5 bits | only there |
| Equivalence (inverse relation) | synthetic up to about 17 bits with clean symmetry | Kinships: nothing to slightly negative |
| **Product closure enables compositional generalisation** | synthetic grid world, 5 seeds: unseen factor pairs 230 vs 369 bits (n=150), oracle 225; holds at medium noise | the world is built to be exactly the structure sought; factors found only with class learning from squares and fibres |
| Labelling conditioned on neighbour labels (streets) | 3.6-8.4 bits per window, 12 of 12 cases | **generic**, no presheaf advantage |

### What is refuted or not shown

* **Product closure on real streets: no gain** (difference at most 1.6 bits, marked and unmarked, 3 seeds). Reasons presumably: small irregular grids, squares and ladders are already covered cheaply by gluing, street class belongs to the street and not to the position.
* **"Labelling belongs to the row" (product idea for labels):** context "opposite edge in the square" brings nothing.
* No advantage over GraphMDL/SUBDUE/gSpan **with the same extra models** was measured; on the grid world and the streets gSpan+MDL was only partly comparable (node limit, time limit), GraphMDL and SUBDUE did not run there at all.
* Higher order beyond products (parametrised macros, exponentials, simplices) was **untested** at this point.

### Honest classification

1. The core "colimit of pieces, MDL selection" is a solid but known procedure; the presheaf frame supplies the language for it, so far with no demonstrable additional gain.
2. The only finding that can be explained **only** with a categorical idea (closure under products, hence generalisation to unseen combinations) holds so far only where the data have exactly that structure. That is a proof of feasibility, not evidence of usefulness in practice.
3. All tests share the cost function of learner and evaluation (home advantage), the worlds are built by us, seeds are few (3-10).
4. The core question now hangs on **data with exact, large product or parametrisation structure**; street windows are evidently too small and too irregular for that.

### Possible next steps (listed for decision at that time)

* **A. Look for real data with exact product structure** (circuit diagrams/chip layouts, grid simulations, cellular-automaton space-time, network topologies such as torus/hypercube); only GitHub and PyPI are reachable from here.
* **B. Parametrised macros** (step 2, holes/interfaces): a different mechanism, could carry on molecules and knowledge graphs where products do not occur.
* **C. Relation composition** on Kinships/UMLS (step 3), comparison with AMIE-like rule miners: an opponent that hits the question directly.
* **D. Equalise the opponents:** attach the labelling and equivalence models to SUBDUE/GraphMDL/gSpan too, so that the comparison does not hang on extra models.
* **E. Fix a stopping criterion:** if A-C also yield no lead on real data, document the project as "frame yes, advantage no".

### Result step 1e: chip netlists (data search and first measurement), `src/netlist.py`, `src/e21.py`, `results/e21_*`

**Data found** (only GitHub and PyPI are reachable): `ispras/hdl-benchmarks` (ISCAS85 `.bench` including c6288 = 16x16 array multiplier, LGSynth91, IWLS05, Quip designs such as barrel shifter, crossbar, multiplexer) and the `lsils`/`nbulsi` EPFL benchmarks (`arithmetic/*.blif`: adder, bar, multiplier, max, sin, square, sqrt, div, log2).
Preparation: node = signal/gate, edge = wiring (undirected), label = type pair (driver, sink) or, for AIGs, (source is an input?, input inverted?). Components = BFS windows around random gates (20 nodes, at least 8 edges, multiple overlap possible).

**Product structure at gate level:** raw 4-cycles are rare and mostly lie **inside** cells (e.g. XOR from 4 NANDs in c1355, opposite edges almost always labelled equally), not between cells. c6288: on average 2.6 squares per 40-edge window. The grid of the array multiplier (full adders in a skewed raster, in skewed coordinates a product of two paths) exists only at **cell level**, not at gate level.

**Measurement on c6288** (n=40 training windows, 3 seeds, test = 100 held-out windows of the same circuit; test bits per window).
*Correction:* the first version oriented edges by node name instead of driver -> sink; since the framework works with directed edges, equal cells with different name order did not match. The numbers below were re-measured with correct orientation (earlier numbers: gluing 169.5/152.9/170.7, growing 222.6/209.1/221.1).

| Seed | empty | Gluing (our learner) | Growing by 1 edge | SUBDUE (MDL section) | gSpan (maxv 11, patterns up to 6 edges) |
|---|---|---|---|---|---|
| 0 | 422.5 | 153.6 | 199.8 | 219.8 | 257.5 |
| 1 | 427.8 | 158.2 | 205.9 | 200.7 | 233.2 |
| 2 | 433.7 | 159.4 | 212.2 | 209.0 | 258.5 |

* **Gluing lies 46-53 bits (23-25%) below growing and 41-66 below SUBDUE** and 75-105 below gSpan; the composition advantage persists on real data and is the largest so far.
* **SUBDUE is in the range of growing** (run-to-run spread about 10 bits: for seed 0 two runs gave 205.5, 219.8 and 225.2). It finds patterns up to 26 edges, but its selection and instance counting are worse.
* **gSpan is practically not applicable to these windows:** with node limits 26 and 17 (bond-as-node: about 12 and 8 edges) and support 20% the run aborted after 500-900 s (time limit) in every seed; only with node limit 11 (patterns up to 6 edges) are there numbers. This is a comparison with gSpan under restricted conditions; with patterns limited to 6 edges it cannot in principle represent cells of up to 12 edges.
* **Product closure at gate level: no factor chosen**, hence no effect (expected, see above).
* **No transfer to other circuits** (c1355, c499, c880, c1908: gluing 0-30 bits better than empty, similar growing): c6288 cells do not occur there.
* **Limitations:** a single, extremely regular, hand-designed circuit; BFS windows overlap (training and test windows of the same circuit share cells); the 12-edge cap of our learner presumably cuts the cell; the opponents were run with the existing wrappers (greedy MDL selection of the gSpan candidates, SUBDUE with 20 iterations), without parameter tuning; we optimise the same cost function that we measure with (home advantage). The AIG multiplier (only 4 labels) was too slow for the learner (over 20 minutes, aborted).
* **Street results (1c, 1d):** the orientation problem has since been fixed and the runs repeated with symmetric labels, see the correction section after 1d; the conclusions stand.
* **Next step (proposal):** cell level. (1) Learn a cell macro (larger `maxe`), (2) cover the netlist with the macro, (3) quotient graph (node = cell instance, edge = wiring with port pair as label), (4) on it, classes from squares, fibres and product closure as in e17. That would be the actual "product of cells" test.

### Result step 1f: cell level of c6288 (quotient graph), `src/cells*.py`, `quotient.py`, `e23.py`, `results/e23_*`, `results/cells_D*.json`

**Set-up (everything learned, no manual work on the cell structure):**
1. Learn patterns (up to 12 edges) from 30 BFS windows (17 entries) and cover the **whole** c6288 netlist (2448 gates, 4800 edges) with them: only 81 edges remain raw. Three patterns occur about 225-240 times each (12, 5 and 3 edges) and together form the cell (about 240 full adders).
2. Two MDL-driven gluing rounds on the whole graph (gain 5089 and 2425 bits) yield the **cell with 20 edges, 195 complete instances**, plus border cells.
3. **Quotient graph:** node = cell instance (361 nodes); edges = gates and free wires shared by two instances; label = port pair (86 labels). The 32 primary inputs (bus, 16 cells each) are taken out of the quotient (otherwise cliques); which input goes into which cell would be the labelling.
4. On the quotient there are genuine **commuting squares** (259 squares, 155 per port pair): in one direction a bundle of 3 parallel wires between neighbouring cells, in the other one wire. That is the grid factor "bundle x edge". (The window loader initially lost parallel edges; fixed.)

**Measurement** (n=40 training windows of 16 cell nodes, 100 test windows, 3 seeds; test bits per window, mean):
empty 627.6 | gluing 243.1 | growing 257.4 (difference 3.5 / 25.3 / 14.3 per seed) | **product closure 242.9** (factors chosen: 0 / 2 / 0; gain over gluing 0.0 / 0.6 / 0.0 bits).

* **Product closure brings nothing at cell level either.** Classes are learned correctly (bundle labels versus the single edge), factors (bundle, bundle chains, single edges) are candidates, but the selection does not take them: the extended dictionary costs more pointer bits (about +12.7 bits over 40 windows in the pair-step test) than it saves.
* **Why, presumably:** the glued dictionary already contains the small grid pieces of up to 16 edges (bundle x edge has 8, bundle pair x path 15). The test windows (16 cell nodes, about 38 edges) are only 2-4 cells wide; larger products would help, but the embedding search (backtracking) can no longer cover exactly those affordably. With a cap of 32 for products nothing changed.
* **Composition advantage at cell level smaller than at gate level:** 3.5-25 bits against growing (gate level: 46-53 bits), because cells already carry the large structure.
* **Limitations:** one circuit, overlapping windows (training/test windows share cells), window size limited by the matcher, cell learned in windows only up to 12 edges and glued only on the whole graph, primary inputs left out, 3 seeds; the port-pair labels are an encoding decision of ours.
* **Conclusion on chips:** the only composition effect on real data of clear size (c6288, gate level) comes from **gluing**, not from products. A product advantage on real data is still not established (streets: zero; chips: zero). The finding remains: products act only where the data contain many large, exactly equal grids in many shapes.

### Correction to steps 1c/1d: streets with symmetric edges (`SYM=1`, result files `*_sym.json`)

The first street runs (1c, 1d) oriented edges by coordinate order and did not treat them as symmetric; streets are undirected. Repeated with `und.SYMS` = all labels and undirected canonicalisation (`und4.UND`). Same windows and seeds as before. Test bits per window (mean over 3 seeds unless noted):

| Measurement | Barcelona | Madrid | Zaragoza | Sevilla |
|---|---|---|---|---|
| empty | 369.3 | 337.6 | 301.9 | 361.6 |
| Gluing, directed (old) | 258.3 | 240.8 | 218.5 | 247.7 (seed 0) |
| **Gluing, symmetric** | 239.2 | 219.4 | 193.0 | 233.5 |
| **Growing, symmetric** | 238.6 | 217.6 | 191.6 | 231.4 |
| Shape+labelling (neighbour context), symmetric | 233.1 | 210.3 | 186.1 | 225.1 |
| Shape+labelling (iid labels only), symmetric | 250.3 | 230.8 | 205.4 | 246.6 |

* **Absolute compression better** (about 15-18 bits relative to the directed run, mean over 3 seeds); the orientation was thus a real handicap.
* **Gluing ≈ growing remains** (gluing minus growing: -0.6 to +5.0 bits, +1.5 on average in favour of growing). The statement "no composition advantage on streets" also holds symmetrically.
* **Shape+labelling with neighbour context still beats marked gluing**, in all 12 cases (4 cities x 3 seeds) by 4.7-9.8 bits per window (before: 3.6-8.4). That is a generic context-model gain.
* **Product closure, unmarked (geometry, all edges the same label):** seed 0: factor found, gain 1.5-2.5 bits (Barcelona 203.4 -> 201.3; Madrid 186.3 -> 184.8; Zaragoza 174.3 -> 172.6; Sevilla 193.0 -> 190.5); seed 1: no factor, gain 0.2-0.4 bits. Seed 2 was aborted after more than 75 minutes (the symmetric factor search is much slower). **Two seeds, a small gain of up to 1% (seed 0), not reliable.**
* **Product closure, marked (street classes):** difference (product minus gluing) Barcelona +3.1 / -2.2 / +0.1, Madrid +2.2 / -1.4 / +1.4, Zaragoza +1.3 / -2.5 / +0.6, Sevilla +3.3 / -2.3 / +2.2: mixed signs, slightly negative on average. **No effect.**
* **Conclusion unchanged, but now clean:** on real streets there is no reliable product advantage; the labelling gain remains, but is not presheaf-specific.

## 4b. Literature review on macros with holes

See `review-macros.md` (macros/interfaces in graph compression, cospans, exponential object; test proposals A-C).

## 4c. Test A: macros with interface (instance cost only for boundary nodes), 11 October 2026

Code: `src/iface.py`, `src/e24.py` (c6288), `src/e24s.py` (streets, symmetric). Cost model: an instance pays pattern index + count k + subset of the k *boundary nodes* (nodes with edges outside the instance; `log C(|V_p|,k)`) + k pointers; inner nodes are allocated fresh by the decoder. For safety, `min` with the old scheme + 1 flag bit per instance. Dictionary costs are not included (as before in the per-window figures); same dictionaries, only encoded differently, plus learners that optimise the interface objective directly.

**c6288 (gate level), 40 training windows, in-sample bits/window, mean over 3 seeds (re-encoding of the old dictionaries):**

| | old | with interface | gain |
|---|---|---|---|
| glue | 156.9 | 116.2 | 40.7 (26%) |
| grow | 196.7 | 176.8 | 19.9 (10%) |

The glue-grow gap grows from 39.8 to 60.6 bits: large patterns have more inner nodes and profit more. Mean pattern/instance size: glue |V| ≈ 5.4, k ≈ 2.3 boundary nodes; grow |V| ≈ 3.3, k ≈ 2.1. Learner with interface objective (seeds 1, 2 only; seed 0 was not finished when writing): glue 113.0 (vs 119.9 re-encoded), grow 198.3 (vs 175.4; here the learner learns *worse*, outlier from seed 2; a sign of noise at n=2, not a result). On other circuits (c1355, c499, c880, c1908) almost nothing changes (≤ 4 bits out of ~310-430): the dictionary hardly transfers.

**Streets (Barcelona -> Madrid/Zaragoza/Sevilla, symmetric, 50 windows, 3 seeds):** glue saves 21-25 bits, grow 21-26 bits; the glue-grow gap stays ≈ 0-2 bits. The gain here is a *general* encoding gain (inner nodes free), not an advantage for gluing.

**Reading.** (1) The interface cost model is a real but modest lever: ~10-26% on c6288. (2) It reinforces the already known advantage of gluing on c6288 (glue now beats grow by ~61 instead of ~40 bits), but not on streets. (3) Caveat: the old scheme (`#nodes · log n` per instance) is particularly generous compared with a fair baseline encoder that also leaves inner nodes implicit; the gain therefore holds relative to *our* old model, not relative to gRePair/SUBDUE (which have interfaces anyway). A fair comparison with an interface-capable baseline miner is missing. (4) Test A only examines interface costs; *real holes* (patterns in whose hole different sub-patterns fit) remain tests B/C of the review.
Raw data: `results/e24*.json|log`.

## 4d. Comparison with an interface-capable baseline miner (gRePair-like), 12 October 2026

Code: `src/repair.py` (baseline), `src/e25.py` (held-out test), `src/e25b.py` (incl. dictionary), `src/chk_repair.py` (losslessness). Baseline: RePair on graphs after Maneth et al.; digram = two hyperedges with a shared node, replaced by one nonterminal hyperedge to which only nodes with edges outside the digram are attached (inner nodes disappear); greedy by MDL gain over all training windows, rules are replayed on test windows in order. Same cost model (terminal edge `2 log n + log R`, nonterminal `log(|D|+1) + rank·log n`, rule ≈ 24 bits). **Our own re-implementation from the description, not the original code**, without rule pruning (at this point) and without gRePair's node-order optimisation. Losslessness checked: expansion of the compressed windows is isomorphic to the original (20/20, c6288). Same windows as in Test A (same seeds); label numbers may vary slightly between runs because of hash order (±3 bits).

**New windows, bits/window without dictionary (mean over 3 seeds):**

| | glue (interface) | grow (interface) | RePair re-impl. |
|---|---|---|---|
| c6288, new windows | 116.2* | 176.8* | 169.3 |
| Barcelona | 207.9 | 209.4 | 235.1 |
| Madrid | 208.8 | 208.3 | 236.6 |
| Zaragoza | 167.2 | 168.5 | 189.6 |
| Sevilla | 206.8 | 205.4 | 230.1 |

*c6288: re-encoding of the dictionaries from Test A (3 seeds); "in" = newly drawn windows of the same circuit. Other circuits: all methods ≈ uncompressed (RePair c1355 417, c499 314, c880 328, c1908 386).

**With dictionary (training windows + dictionary per window; c6288 only 2 seeds, seed 2 ran too long and was aborted; streets 3 seeds):** c6288 glue 122.4, grow 197.7, RePair 183.4; streets glue 210.6, grow 212.2, RePair 240.9. RePair learns 60-80 rules (dictionary 1.4-1.6 kbit versus 0.2-0.7 kbit for glue/grow). On streets the number of rules hits the cap of 80; with a cap of 300 (seed 0) it is 93 rules and the cost on new windows is the same (239.9 vs 239.8), so not a truncation artefact.

**Reading.**
1. c6288: under a fair interface cost model, glue stays about 53 bits (31%) better than the gRePair-like baseline; the baseline lies just below grow-by-one (169 vs 177). The advantage of gluing on circuits is therefore not merely an artefact of the old, generous cost model. Caveat: my baseline is probably weaker than the original (no pruning) and builds large patterns only through many recursion levels.
2. Streets: glue ≈ grow, both about 27 bits better than the baseline. That does not speak for gluing but shows overfitting of the baseline (80 rules); with rule pruning it would improve, the size of the remaining gap is uncertain.
3. Open: the original gRePair and SUBDUE-with-interface were not cross-checked.
Raw data: `results/e25*.json|log`.

## 4e. Street numbers made more reliable (baseline strengthened, 5 seeds), 12 October 2026

Code: `src/e26.py` (run), `src/agg26.py` (evaluation), pruning in `src/repair.py`. Set-up: Barcelona training windows (50), validation windows (30), new windows in 4 cities (100 each); 5 seeds with new window draws; symmetric edges; all methods on the same windows. The baseline was strengthened in three directions: (a) rule cap 300 instead of 80, (b) **pruning** (leaf rules with negative net gain are removed, repeatedly), (c) **number of rules chosen on validation windows** (prefix of the rule list, criterion: validation cost + dictionary/100). (c) uses windows from the same city for tuning and is thus generous to the baseline.

| Method (mean over 5 seeds) | Rules | Dictionary (bits) | new windows, bits/window (sd) | + dictionary/100 |
|---|---|---|---|---|
| uncompressed | – | – | 343.6 | – |
| glue (interface) | 20 | 419 | 201.5 (5.6) | 205.7 |
| grow (interface) | 24 | 461 | 198.8 (5.7) | 203.4 |
| RePair re-impl., full | 86 | 1791 | 227.1 (5.4) | 245.0 |
| RePair re-impl. + pruning | 67 | 1345 | 229.9 (4.5) | 243.3 |
| RePair re-impl., rule count validated | 56 | 1111 | 228.7 (6.4) | 239.8 |
| RePair re-impl., pruning + validated | 45 | 883 | 232.3 (5.3) | 241.2 |

Paired difference to glue (bits/window, baseline minus glue): full 25.6 (range 21.4-30.6), pruning 28.4, validated 27.2 (24.1-33.4), both 30.8; including dictionary/100: 34-39. **In all 5 seeds and all 4 cities (min 19.6 bits) every baseline variant lies behind glue.** glue against grow: grow − glue = −2.7 bits (in 4 of 5 seeds grow slightly better; spread 3-5 bits), i.e. on par.

**Reading.** (1) The statement from 4d is stable: on streets our patterns (arbitrarily large, chosen by MDL) are about 12-14% more compact than digram-based grammars with an interface, and this cannot be removed by pruning or by choosing the number of rules. (2) This is **not** a gluing advantage: grow (one edge after the other, no gluing) is just as good. The difference lies in the pattern family and the selection (patterns of up to 24 edges, evaluated globally by MDL) versus digrams with rank costs, not in the presheaf structure. (3) The baseline remains our own re-implementation and not the original gRePair; order/node-ordering optimisations and extra encodings of the original are missing. (4) Consequence for the overall picture: with the interface cost model, c6288 (glue ≫ grow ≈ baseline) and streets (glue ≈ grow ≫ baseline) are consistent; the presheaf gain (gluing) is still measurable only on circuits.
Raw data: `results/e26_*.json|log`.

## 4f. Test B: anti-unification (macros with label holes, noise sweep), 12 October 2026

Code: `src/e27.py` (synthetic world + methods), `src/agg27.py` (evaluation, output `results/e27_agg.txt`), `src/run27.sh`, `src/e28.py` (real data). **Idea.** Anti-unification = most specific generalisation of the occurrences. Pipeline "AU": (1) learn shapes from label-deleted windows (glue, MDL), (2) per pattern edge estimate the label distribution of the occurrences: the edge stays "fixed" (peaked distribution) or becomes a "hole" (broad distribution); cost = interface encoding of the instance + Σ −log2 p(label | pattern edge), with an escape for unknown labels; the dictionary contains the label tables. Comparison: exact glue on true labels ("exact"), shapes + log R per label ("shape_raw"), RePair re-implementation with interface, and "AU_oracle" (true macro shapes, only distributions learned).

**Synthetic world** (4 macros of 6 nodes/7 edges, each edge fixed or hole with 4 labels out of 64; 2 instances + 4 clutter edges per window; 40 training windows, 100 test windows, 5 seeds). Noise: pf = label swap per edge, pd = edge missing. Bits/window on test windows without dictionary (uncompressed ≈ 282):

| Holes | pf | pd | exact | shape_raw | AU | AU_oracle | RePair re-impl. |
|---|---|---|---|---|---|---|---|
| 0% | 0 | 0 | 110.8 | 192.4 | 122.8 | 119.2 | 153.2 |
| 0% | 0 | .05 | 128.6 | 194.6 | 140.0 | 156.7 | 164.7 |
| 0% | .05 | 0 | 139.5 | 190.8 | 126.8 | 125.8 | 175.6 |
| 0% | .10 | 0 | 161.4 | 191.0 | 133.0 | 131.9 | 185.0 |
| 30% | 0 | 0 | 161.4 | 192.0 | 130.9 | 127.8 | 187.8 |
| 30% | 0 | .05 | 173.0 | 196.1 | 151.2 | 160.7 | 197.6 |
| 30% | .05 | 0 | 189.3 | 191.8 | 137.0 | 134.7 | 207.0 |
| 30% | .10 | 0 | 206.3 | 192.5 | 143.8 | 142.4 | 215.2 |
| 60% | 0 | 0 | 214.3 | 191.3 | 137.9 | 137.7 | 223.0 |
| 60% | 0 | .05 | 215.2 | 193.9 | 155.1 | 166.4 | 225.6 |
| 60% | .05 | 0 | 225.1 | 194.7 | 150.6 | 143.9 | 231.5 |
| 60% | .10 | 0 | 238.7 | 190.1 | 147.1 | 145.4 | 241.7 |

Findings: (1) as soon as there are holes or label noise, AU beats exact glue on average by 12.6-91.6 bits (positive in every seed and every one of these configurations, smallest seed gap 2.2 bits; smallest at 0% holes and 5% label noise, largest at 60% holes); with 60% holes exact collapses almost to "uncompressed", AU does not. (2) AU is close to AU_oracle (±1-7 bits): shape discovery on label-deleted graphs works; with missing edges (pd) AU is even *better* than the oracle because learned sub-patterns still fit across gaps. (3) Control without holes and without noise: exact is 12 bits better (AU pays for label tables and smoothing); with 5% missing edges and no holes also 11.5 bits. (4) The gains over shape_raw (shape without a label model) of about 45-70 bits show that the positional label model, not the shape, carries the main part. **Caveat:** the world is built according to the hypothesis (fixed macros with holes); the test shows that the approach works under this assumption and wins robustly against exact gluing, not that real data look like this.

**Real data** (same AU pipeline, bits/window on new windows without dictionary): c6288 (2 seeds, third run aborted): exact 124.2, AU 135.6, shape_raw 263.0, RePair re-impl. 169.7; streets (3 seeds): exact 198.5, AU 206.2, shape_raw 219.6, RePair re-impl. 224.9. **AU does not beat exact glue on real data** (+11 bits on c6288 with high spread: +24.8 / −1.9 per seed; +4 to +13 bits on streets, 3/3 seeds), but is clearly ahead of the RePair re-implementation and shape_raw. Reading: in the real data the labels (gate-type pairs, street types) carry structural information that is lost when labels are deleted before shape discovery (c6288: 12 instead of 24 shapes, shape_raw collapses to 263); there are no free "holes" with independent fillers that a positional label model could exploit. A hybrid (exact patterns + wildcard edges only where MDL pays) was not tested at this point.
Raw data: `results/e27_*`, `e28_*`.

## 4g. Hybrid: exact patterns + anti-unification shape patterns in one dictionary, 13 October 2026

Code: `src/hybrid.py`, `src/e29.py`, `src/run29.sh`, `src/agg29.py` (output `results/e29_agg.txt`). **Idea.** A dictionary of (a) exactly labelled patterns (labels fixed, cost 0 bits) and (b) shape patterns from label-deleted windows with a label distribution per edge (4f). The cover is cost-aware: at each step the instance with the largest bit gain is chosen (raw edge cost minus instance cost including label bits). Distributions are re-estimated in two rounds from the hybrid cover; unused patterns are removed. The hybrid may thus decide per window where exact labels and where holes are cheaper.

**Synthetic world (as in 4f, 5 seeds, 12 configurations), bits/window on new windows without dictionary:**

| Holes | pf | pd | exact | AU | Hybrid | Hybrid vs best of exact/AU (mean; smallest seed) |
|---|---|---|---|---|---|---|
| 0% | 0 | 0 | 110.8 | 122.8 | 109.7 | 1.1 (−0.6) |
| 0% | 0 | .05 | 128.6 | 140.0 | 127.1 | 1.5 (−1.2) |
| 0% | .05 | 0 | 139.5 | 126.8 | 116.6 | 10.2 (5.3) |
| 0% | .10 | 0 | 161.4 | 133.0 | 123.8 | 9.2 (3.1) |
| 30% | 0 | 0 | 161.4 | 130.9 | 122.4 | 8.6 (6.8) |
| 30% | 0 | .05 | 173.0 | 151.2 | 142.7 | 8.5 (4.9) |
| 30% | .05 | 0 | 189.3 | 137.0 | 130.2 | 6.7 (2.0) |
| 30% | .10 | 0 | 206.3 | 143.8 | 136.3 | 7.5 (2.4) |
| 60% | 0 | 0 | 214.3 | 137.9 | 132.0 | 5.9 (2.1) |
| 60% | 0 | .05 | 215.2 | 155.1 | 150.8 | 4.3 (1.9) |
| 60% | .05 | 0 | 225.1 | 150.6 | 142.2 | 8.4 (5.9) |
| 60% | .10 | 0 | 238.7 | 147.1 | 140.8 | 6.3 (3.0) |

The hybrid is as good as exact in the control without holes and without noise (109.7 versus 110.8; the 12-bit loss of AU is gone) and, in all configurations with holes or label noise, better than either single method (4-10 bits on average; only in 2 of 60 seed configurations marginally worse, −0.6 and −1.2 bits).

**Real data (new windows, bits/window without dictionary):** c6288 (2 seeds, third run aborted): exact 117.3, AU 134.9, **hybrid 109.7** (−7.6 relative to exact, better in both seeds: 112.9->109.4, 121.8->110.0; 13-16 exact + 8-10 shape patterns). Streets (3 seeds): exact 198.5, AU 206.2, **hybrid 194.2** (−4.3 relative to exact; seeds: 200.4->194.0, 194.0->194.9 (+0.9), 201.1->193.6; 19-22 exact + 7-10 shape patterns).

**Cost of the dictionary.** The label tables make hybrid storage large (c6288: amortised per 100 windows equal to exact, 122.9 versus 122.9; streets: 211.5 versus 203.0, i.e. worse at 100 windows, break-even at about 400 windows). The table costs (number of labels × (log R + log N)) are a rough upper bound; a better encoding (e.g. shared label frequencies across patterns) would improve this. The result "better held-out, more expensive dictionary" holds regardless.

**Reading.** (1) The hybrid removes AU's deficiency on real data and keeps the gain with holes/noise: on all four data sources it is at least as good as the best single method and better than exact gluing on c6288 and (2 of 3 seeds) streets. (2) The real-data gain is small (3-6%) and costs dictionary storage; whether it carries beyond 100 windows depends on data volume. (3) Whether it is "presheaf-specific": the positional label model is generic (shapes × label distribution, cf. 1d); new is only the coupling with exact gluing in one MDL dictionary. No comparison with the original gRePair or with miners with wildcards.
Raw data: `results/e29_*`.

## 4h. Test C: macros with a hole whose filler is a subgraph (macros in macros), 14 October 2026

Code: `src/holes.py` (first version, bottom-up over the glue cover; discarded), `src/holes2.py` (learner and cost model), `src/e30.py` (worlds, runs), `src/run30.sh`, `src/agg30.py` (output `results/e30_agg.txt`), `src/oracle30.py` (upper bound). **Model.** A macro with a hole = frame pattern A (from the glue dictionary) with a hole (p,q): two attachment nodes, interface I = two points. A filler is a subgraph attached to the frame only at a, b (≤ 5 edges, component analysis over outer nodes, canonical with marked attachments). Options per hole: filler pattern from a learned library, **"empty" (trivial filler = initial object under I, cf. review-macros.md 1a)** or "other". Cost of an option: −log2 p (distribution from training frequencies). The inserted filler costs *no* pattern index and *no* pointers (its attachment nodes are internal); the frame pays only its boundary nodes. Learning: candidates top-down (every pattern ≥ 4 edges, every node pair, filler frequencies ≥ 2), selection by MDL group-wise per frame (all holes of a frame together), with a choice of whether the combination patterns contained in the frame are removed from the dictionary; then 2 rounds of "subtract filler edges -> relearn dictionary -> relearn holes". Baseline "glue" = the same dictionary learning without holes, instances with interface encoding (`iface`) or additionally relative addressing against already placed nodes (`rel`); the latter changes nothing (≤ 1 bit), so the saving does not come merely from missing pointers.

**Two lessons from development.** (1) Bottom-up (reading holes off the glue cover) finds hardly anything: the glue learner does not cleanly separate frame and filler but learns combination patterns (frame + frequent filler) that already pocket the saving. Only the joint removal of these combination patterns together with the introduction of the hole makes the hole profitable (not submodular: a hole alone looks like a loss). (2) When measuring fillers, "ambiguous" (component touches more than a, b) must be distinguished from "empty", otherwise collisions falsify the distribution.

**Synthetic world** (3 frames of 6 nodes/7 edges, 2 holes each with an attachment pair; 6 filler patterns of 3-4 edges, 15% of the holes empty; 2 instances with disjoint nodes + 4 clutter edges per window; 120 training, 100 test windows, dictionary limit 80, 5 seeds). Bits/window on new windows without dictionary:

| | glue | hole model | gain (min. seed) | gain incl. dictionary/100 | holes found |
|---|---|---|---|---|---|
| 6 filler patterns | 151.3 | 116.7 | 34.6 (24.3) | 28.0 (20.4) | 6/6 in 5/5 seeds |
| Upper bound (oracle: true frames/fillers, 1 seed) | 188.5* | 110.3 | – | – | – |

*Oracle glue = only frame and filler patterns as separate instances, not the learned dictionary. The hole model reaches 116.9 in seed 0 versus 110.3 for the oracle, i.e. the learner recovers most of the possible saving. Dictionary (patterns + hole tables): 2297 versus 1634 bits.
Controls: (a) 1 filler pattern, 15% empty: gain 27.3 (seeds 0, 1; seed 2: no hole, gain 0); (b) null control, everything fixed (1 filler pattern, never empty): 11.5 bits on average, but only through one seed (one hole; the other two: no hole, 0 gain). Both controls are **not a pure null case**: the whole macro (frame + 2 fillers, 14-15 edges) exceeds the pattern cap `maxe = 12` of the glue learner, while the hole model can express it as frame + fillers. Part of the gain is therefore a "composition advantage against the pattern size cap", not variation. The 6-filler world is thus only partly a variation gain; this was not separated.

**Real data.** c6288 (3 seeds): one hole in 1 of 3 seeds (gain there ≈ 9.5 bits), 3.2 bits on average (incl. dictionary/100: 2.7); streets (3 seeds): no holes, gain 0.0. Complete: `results/e30_*.json`.

**Reading.** (1) Macros whose hole is filled with a sub-pattern are a real, measurable gain **if** the data contain such structures (frames with exchangeable two-terminal building blocks): 28-35 bits/window (≈ 20-23%) at negligible extra dictionary cost. The gain does not come from pointer savings alone (rel ≈ iface) but from the structure "frame × filler" instead of "frame×filler as individual combination patterns". (2) On the real data the learner hardly finds holes of this kind: c6288 has almost no recurring two-terminal fillers, street windows have no clean two-attachment appendages. Hole kinds with more than two attachments, overlapping holes and nested holes (filler with its own hole) were not tested. (3) The synthetic world is built after the model; it shows that the learner recovers the structure, not that real data have it. (4) The stripping/relearning procedure is heuristic (2 rounds, best round chosen by training cost).
Raw data: `results/e30_*`.

## 4i. Stocktaking, RePair research, arguments for the sheaf perspective, 15 October 2026

See `review-repair-presheaves.md`. In brief: (1) the RePair community claims its advantage on RDF graphs with few predicates, version graphs and XML trees (patterns with parameters), not on grid-/product-like structures; the gRePair advantage is mostly against k²-trees. (2) Strongest theoretical argument: a straight-line HR grammar whose right-hand sides have at most s nodes generates only graphs of treewidth ≤ s − 1 (proof sketch); the n×n grid (treewidth n) therefore needs grammar size ≥ n + 1, while a dictionary with box product gets by with O(log n) entries. (3) Our product closure is the box product (closed monoidal), not the categorical product of the graph topos. (4) Clarification of 15 Oct.: effects E1 gluing, E2a product, E2b exponential object (macros with holes, higher-order), E3 fixpoint/recursion (more than E2b, untested at that point). The depth-2 test (hole in hole) is in 4j.

## 4j. Depth-2 test (E2b): hole in hole, Hom(A, B^C), 15 October 2026

**Question.** Is the exponential object really *closed*: can the filler of a hole itself be a macro with a hole, and does that pay off against flat composite fillers?

**Set-up** (`src/holes3.py`, `src/e31.py`, `src/agg31.py`, `results/e31_*`). Synthetic world: 3 frames × 2 holes; filler of a frame hole = one of M=4 middle pieces (3 edges, with an inner node pair = sub-hole); filler of the sub-hole = one of L=8 leaves (2-4 edges). Probability of empty 0.15 / 0.2. A middle piece with a leaf has up to 7 edges (maxF=8). The flat learner thus has to learn up to 32 combinations individually as fillers, the nested model only 4+8.
Pipeline: (1) depth-1 model (H2.refine, maxF=8, flat fillers); (2) the fillers found serve as training windows with markers at a, b; dictionary + holes are learned once more on them (H2.refine) = middle-piece frame with sub-hole + leaf library; (3) middle piece × leaf is expanded (also *unseen* combinations), option cost −log2(p_mid·p_leaf); library bits = middles + leaves + sub-holes instead of all combinations. Test cost = bits per window, 100 test windows. Selection rule: depth 2 only if the training cost (incl. dictionary) falls.

**Result** (4 seeds per size; each seed has its own random frames/gadgets):

| Training windows | Test glue | flat (depth 1) | depth 2 | depth 2 chosen |
|---|---|---|---|---|
| n=60 | 274.6 | 268.7 | 264.9 (only 2 of 4 seeds decomposable) | 1 of 4 |
| n=150 | 272.5 | 251.4 | 232.3 | 4 of 4 |

- n=150: depth 2 beats flat by 19.1 bits/window (smallest value 6.4) and glue by 40.2. The dictionary is smaller at depth 2 than flat (3474-3979 vs 3607-4506 bits).
- Net (test cost + dictionary/100): n=150 glue 283.2 / flat 291.7 / depth 2 **269.9**; n=60 glue 279.4 / flat 282.6 / depth 2 280.8. The flat holes *lose* net against glue (large dictionary with 170-240 fillers); only the nested representation wins (13 bits vs glue). This hinges on the arbitrary weighting /100.
- Control (depth-1 world, sub-hole always empty, n=60, 3 seeds): no hole found, flat = glue, depth 2 not applied. That is "no harm", but not a test of the selection rule with holes; only seed 3 at n=60 provides that (depth 2 not chosen, difference 0.1).

**Reading and limits.**
- What the test shows: nested holes are found and pay off **if** the structure really is middle piece × leaf and enough data are available (data saving = combinatorics 4·8 instead of 4+8, plus generalisation to unseen combinations). This is the concrete form of "Hom(A, B^C)" in the compression problem and the argument for closedness.
- What it does not show: the world is synthetic and tailored exactly to this structure. On real data (c6288, streets) we hardly found depth 1 (4h), so depth 2 is to be expected even less there. No RePair comparison: SL grammars with parameters presumably reach similar effects; open.
- Weaknesses: the sub-hole is considered for only one pair per middle piece; at n=60 the decomposition is found in only 2 of 4 seeds (middle pieces too rare); 4 seeds are few; the library bits are roughly estimated.
- E3 (fixpoint/size extrapolation) is more than E2b; first test in 4k.

## 4k. E3 test: recursive macro (lattice rule) on the c6288 cell quotient, 15 October 2026

**Question.** Does a *recursive* macro (fixpoint X ≅ X ⊕ cell along a generator), learned from a small block, help to describe larger blocks up to the whole circuit (size extrapolation)?

**Set-up** (`src/e32.py`, `e32b.py`, `e32c.py`, `results/e32*`). Object: the cell quotient graph of c6288 from 1f (361 cells, 1179 edges; 195 core cells form a parallelogram with 4 edge labels: bundle of 3 parallel edges in one direction, one edge in the other). Learning uses only the edges and labels of a t×t block (t = 3, 4, 5), without coordinates: functional labels lying on the same node pairs form a generator (bundle); commutation of the generators is checked. The rule "free lattice Z², generated by these two bundles" is the recursive macro. Encoder: rule (57.8 bits) + sizes (2·log m) + exceptions (every unexplained or missing edge at the full raw price 2·log n + log R, plus nodes without coordinates). Coordinates are determined by BFS from the rule and the actual edges only (`lattice_fit`). Baselines: gluing (glue, MDL dictionary) and RePair (our re-implementation), both learned from the same t×t block.

**Results.**
1. **The rule is stable:** t = 3, 4, 5 yield the same two generators ({65,68,69} and {70}, commuting; 6/6, 2/2, 12/12 squares).
2. **Extrapolation without exceptions:** blocks m×m, m = 4…13 (up to 169 cells, 612 edges) are generated exactly by the rule learned from ≤ 25 cells (0 exceptions, `conflicts`/`orphans` = 0). Costs (bits, m=13): recursive 65 (62 at m=4), gluing 2383-3687, RePair re-impl. 3387-6237, raw 13002. Gluing and RePair grow with the number of cells (m=4: about 124-156 / 148-281; m=8: 827-1078 / 934-1850), the recursive macro by 0.4 bits per step (log m).
3. **Perturbations** (13×13, p randomly deleted edges, exceptions cost 21 bits each): recursive 66 / 109 / 173 / 279 / 491 / 1129 / 2191 / 4315 for p = 0, 2, 5, 10, 20, 50, 100, 200; gluing (t = 4) 3089 / 3171 / 3354 / 3381 / 3757 / 4252 / 4651 / 5203. Break-even at about p ≈ 220 of 612 edges (≈ 36%).
4. **Control (random graph, same label distribution, targets shuffled):** the learner finds three spurious generators from 5 training edges, but `lattice_fit` explains 0 of 609 edges (168 nodes without coordinates); the rule would not be chosen.
5. **Whole quotient** (361 cells, 1179 edges; glue/RePair learned on 40 windows of the whole graph, i.e. the stronger baseline): raw 27629; gluing 9188 (+ dictionary 950); RePair re-impl. 9215 (+ 1423); lattice rule for the core + raw for the border 11041; **lattice rule for the core + gluing for the border ≈ 5070 (+ 950)**, i.e. about 45% less than pure gluing. The core (711 edges) costs only the rule, the rest (468 edges, borders) keeps the gluing cost (≈ 10.7 bits per edge).

**Reading.** (1) The effect is real and of a different kind from everything before: the description length does not grow with size, the rule extrapolates. That is the kind of advantage a fixpoint/initial algebra provides and that gluing, products and holes (all: cost ∝ number of instances) do not have in principle. (2) In this form it is almost trivial: the core of c6288 is a perfect lattice; I specified the rule class ("free Z² lattice from bundles"), only *which* bundles is learned. A general fixpoint learner (recursive macros with holes, borders as their own 1D recursion) has not been built. (3) Extrapolation here means: small block -> larger block of the *same* circuit. A real size test would need multipliers of other widths (only c6288 is available; EPFL `multiplier` is an optimised AIG and was not examined). (4) The cell level itself comes from gluing (1f); without the cells there is no lattice at gate level (1e). Cell dictionary costs are missing equally for all methods. (5) RePair is my re-implementation without pruning and lies just above gluing here; an original SL-HR grammar would need, because of the treewidth bound (3.2), size at least ≈ m for the lattice, but not O(log m) in our form; this is a calculation, not a measurement. (6) The gain on the whole graph hinges on the border treatment (5070 vs 11041); the borders are themselves 1D chains and would be the natural next recursive macro.

## 4l. E3 continued: borders, EPFL multiplier, size family, 21 October 2026

Three questions from 4k ("borders as their own recursion", "real size test"). **Mostly negative or incomplete results.**

**(1) Borders as part of the same lattice? No.** `src/e33.py`: greedy embedding of all 361 quotient cells into Z² with a fixed displacement vector per edge bundle (63 bundles). The bundle lattice of the core (2 generators) is unique; for the border there is no consistent embedding: 84 collisions, 36 cells not embeddable, 18 bundles without displacement. The border consists of about 26 chains of mixed cell types (length 5-16), partly interlocked across different types; it is not a bundle lattice. A 1D chain rule (start, length, alignment to other chains) was not built, only the failure of the simple embedding was measured.
**Measurement as a substitute** (`src/e33b.py`, 3 seeds): border (468 edges, raw 11185 bits) with gluing trained on border windows 4137 / 4746 / 5058 (+ dictionary ≈ 1020), with RePair re-impl. 3172 / 3318 / 3742 (+ dictionary ≈ 1467). RePair is better than gluing on the border, unlike on the core. **Total (whole quotient, incl. dictionary):** lattice rule for the core + RePair for the border ≈ 74 + 3411 + 1467 ≈ **4950 bits**, versus pure gluing ≈ 9188 + 950 = 10138 and pure RePair ≈ 9215 + 1423 = 10638, i.e. about 51% less. The gain comes almost entirely from the core (711 edges). Caveat: cell dictionary and cell cover left out for all methods.

**(2) EPFL `multiplier` (64 bit, 27190 nodes): unsuitable for the size test.** WL classes (3 rounds): c6288 97 classes, the 20 most frequent cover 82% of the nodes; EPFL multiplier 4442 classes, 28%. The graph is optimised and irregular, there is no cell lattice.

**(3) Size family of own array multipliers** (`src/genmul.py`, `src/e34.py`; k = 8, 16, 24; own generator with NAND full adders, **not c6288**; single run). The pattern dictionary learned from 40 windows of k=8 (maxe 12) transfers to larger instances: edges 1064 / 4688 / 10872, instances 141 / 601 / 1381, uncovered edges 34 / 76 / 118 (3.2% / 1.6% / 1.1%; grows only with the border). Cell formation (gluing rounds `cells3.merge_round`) and hence quotient and lattice rule did **not** run through: at k=8 one round took over 4 minutes with subsequent dictionaries, so I aborted (two runs with different dictionaries, hash order). A size test of the *rule* across multiplier sizes was therefore still outstanding. The log of the one complete cover run was overwritten (numbers in `results/e34_cover.json`).

**Reading.** The core gain from 4k remains, the border is piecemeal and too irregular for a second recursion; size extrapolation across real size differences was not shown. The next step would go through cell formation: speed up the merge step (limit candidates) or take the generator's cell directly as given and test only the rule over k.

## 4m. E3 size test with accelerated cell formation (own multipliers, k = 16 -> 24, 32), 21 October 2026

**Speed-up** (`src/merge.py`). The cause of the hangs in 4l was not embedding but `canon_u` (pynauty) on unions of pieces that share input-bus nodes (fan-out 16-32): huge automorphism groups. Changes: (1) hubs (nodes shared by more than 8 pieces) are not glued; (2) candidates are counted by a fast WL key (4 rounds, edge labels) instead of pynauty; (3) the gain of a gluing is computed arithmetically (2 instances -> 1, node saving, dictionary entry) instead of by a full cover per candidate; (4) after each chosen round, re-cover freshly with `cover_u` so that inconsistent tilings of the pieces are not frozen (replaying a pair at piece level found only 71 instead of 182 cells). Result: one gluing round takes about 2-3 seconds (before > 4 minutes), four rounds in total ≈ 8 s at k=16.

**Pipeline (`src/e35.py`, `e36.py`, `latt.py`, `genmul.py`; own generator with NAND full adders, not c6288).** Base patterns (maxe 12, from 40 windows of an 8×8 multiplier; the dictionary from windows of k=16 was not awaited, it ran over 12 minutes) -> four gluing rounds on k=16 -> **an 18-edge cell**, 182 instances at k=16, 462 at k=24, 870 at k=32 (interior lattice cells (k−2)² = 196 / 484 / 900, i.e. 93-97%). Quotient (primary-input nodes excluded), core = instances of the cell. Lattice rule from a 4×4 block of the k=16 core (16 cells, 45 edges, only edges and labels): three generators ({0,1} bundle, {3}, {2}), displacements (1,0), (0,1), (1,1) (triangular lattice), identical to the generators from the whole k=16 core; 55 bits.

**Result (bits, core without border, gluing/RePair re-impl. learned on the same 4×4 block):**

| k | Cells | Edges | raw | Gluing | RePair re-impl. | Lattice rule | Exceptions |
|---|---|---|---|---|---|---|---|
| 16 | 182 | 635 | 11009 | 3855 | 3637 | **65** | 0 |
| 24 | 462 | 1699 | 34023 | 12042 | 10748 | **66** | 0 |
| 32 | 870 | 3275 | 71564 | 25468 | 22207 | **67** | 0 |

The rule learned from 16 cells generates the cores of two **larger, different circuits** (k=24, 32) without exception; gluing and RePair grow with the number of cells (factor ≈ 6.6 and 6.1 from k=16 to 32), the rule by 0.4 bits per size step.

**Reading and limits.** (1) This is the desired size test: small block -> larger circuits, with a learned cell (only the rule class "Z² lattice from bundles" is given). (2) Only the core is explained. The border is large: quotient edges outside the core 1058 / 2250 / 3730 at k=16 / 24 / 32 (at least as many as in the core). It contains border cells and the roughly 4-7% of inner cells not covered as the 18-edge cell (a 7-edge pattern occurs 44 / 132 / 236 times; correction in 4n: that is the input bus, not a cell variant). A total gain over the whole circuit is therefore not established and for this family presumably clearly smaller than for c6288 (4k/4l). (3) Own generator, a single run (PYTHONHASHSEED=1), dictionary from 8×8 windows; the generator is more regular than real netlists. (4) Cell dictionary and cell cover are left out for all methods. (5) RePair remains my re-implementation.

## 4n. E3: border and "second cell variant" - quotient as a typed Z² lattice, 22 October 2026

**Correction to 4m.** The 7-edge pattern (44 / 132 / 236 instances) was not a second cell variant but the **input bus**: the fan-out of an input node (star). If the edges leaving the inputs are removed (`src/e38.py`), the fast cell formation learns the same 18-edge cell (full adder) in three rounds, and the interior is **exactly (k−2)² cells** (196 / 484 / 900), without raw edges (raw 0). The remaining pieces grow linearly in k (lengths e.g. 2k−2, k+1, k−1, k−2, k−3, k−4): they are border strips, not cell variants.

**Quotient as a lattice** (`src/qembed.py`, `e39.py`, `e40.py`; own multiplier, cell learned on k=16, PI edges removed). Embedding of all quotient nodes into Z²: core via the three generators (displacements (1,0), (0,1), (1,1)), then each edge bundle with a fixed displacement vector; unknown vectors are chosen by trial (score: consistent edges, free target places). Result for k = 16, 24, 32: **all** nodes embedded (300 / 644 / 1116), 0 collisions, **47 bundles at all three sizes**, **2 exception edges** (each a bundle with one outlier), and the type map decomposes into **18 type-constant rectangles** (shear 1) at all three sizes: core parallelogram, two strips left, two right, two at the bottom, some corners.
Costs (bits; gluing/RePair re-impl. learned from 40 windows of the k=16 quotient, dictionaries 949 / 1360 bits not included, dictionary of the 10 patterns likewise for no method):

| k | Quotient edges | raw | Gluing | RePair re-impl. | Embedding model |
|---|---|---|---|---|---|
| 16 | 794 | 17594 | 6854 | 5868 | **1408** |
| 24 | 1770 | 43121 | 16337 | 14436 | **1450** |
| 32 | 3130 | 81219 | 30551 | 27627 | **1481** |

The embedding model consists of a bundle table (47 × ≈ 23 bits, roughly estimated, which is the major part), 18 rectangles, 2 exceptions and the core rule (55 bits); it grows only through the coordinate lengths (≈ log k).

**Bus** (`src/e41.py`). Of the inputs (32 / 48 / 64), 28 / 44 / 60 attach to whole lattice lines of core cells, in exactly **two parallel line families** (directions (1,0) and (1,−1), k−2 lines each, spacing 1: the offsets form an arithmetic sequence). Thus 392 / 968 / 1800 of 510 / 1150 / 2046 bus edges are explained by a rule of a few dozen bits. 118 / 182 / 246 edges (≈ 4k) remain: the target ANDs of the border cells. For these the line test was not run (only core targets tested); they would very probably also be lines along the strips.

**Reading.** (1) For this family the entire quotient structure (core, borders) is a typed Z² lattice with a constant number of rules; the description length grows only logarithmically, while gluing and RePair grow linearly to quadratically in the number of cells. (2) The border is thus not a second recursion of a different kind: it is 1D strips in the same lattice (unlike c6288 in 4l, where the greedy embedding failed; there the borders are more mixed, and the c6288 cells contain the bus attachment differently). (3) Limits: own, very regular generator; one run; bundle table costs are a rough estimate and the rectangle decomposition is greedy; cell interior and dictionary left out; bus only partly explained; RePair is my re-implementation without pruning, and against stars (bus) RePair/SL-HR grammars presumably have an advantage that was not measured here. (4) Whether the same works on c6288 with the improved embedding (bundles instead of single labels, scoring by consistent edges) was not tested; there the test would be whether the 63 bundles of the quotient, the border and the bus decompose into a few rectangles and line families.

## 4o. E3 on c6288: quotient as a typed Z² lattice (real data), 22 October 2026

**Question.** Does the finding from 4n (whole quotient = typed Z² lattice with a constant number of rules) also hold on c6288, whose borders failed with the simple embedding in 4l? (`src/e42.py`, `qembed.py` with `refine`; quotient from 1f: 361 nodes, 1179 edges, cell = 20-edge pattern 18, 195 instances, PI edges excluded.)

**Changes relative to 4l.** (1) Labels that always lie on the same node pairs are merged into **bundles** (63 bundles instead of 86 labels); (2) the displacement of each unknown bundle is chosen by consistency and free target places; (3) then local search over the 59 non-core bundles (displacements with |du|,|dv| ≤ 3), score = inconsistent edges + collisions + omissions.

**Result.**
- Greedy alone: 41 nodes not placed, 88 collisions, 115 inconsistent edges. **After the search: all 361 nodes placed, 0 collisions**, relative to the chosen displacement table 66 inconsistent edges, relative to the **majority displacement per bundle only 14** (10 bundles have more than one value, each 1-2 outliers among 13-15 edges).
- Type map: core 195 cells (parallelogram) + 166 non-core cells. Decomposed into runs (constant type along a direction with steps |Δ| ≤ 2, greedy longest first): **31 runs**; 13 of them of length ≥ 6 (eight runs of length 14, one each 12, 8, 7, 6), 18 short (length 1-2). Axis-parallel rectangles in the skewed system need 52, because the right border is a diagonal strip with period 2 (every second row occupied).
- Bus: 28 of 32 inputs attach to whole lines of core cells, in **two families of 14 lines each, spacing 1** (directions (1,0) and (1,−1)); 390 of 512 bus edges (remaining 4 inputs and border targets not explained). Identical to the finding for the own multipliers.

**Costs** (bits, whole quotient without bus, without cell/pattern dictionary):
raw 27866 | gluing 9188 (+ dictionary 950) | RePair re-impl. 9215 (+ 1423) | lattice core + RePair border ≈ 4950 (4l) | **embedding model ≈ 2150** (63 bundles × ≈ 24, 32 parts (core + 31 runs) × ≈ 26, 14 exceptions × 25, core rule 55).

**Reading and limits.**
1. On real data it succeeds **partly**: the entire quotient is, up to 14 edges, a Z² lattice with bundle displacements. The finding from 4l ("border not embeddable") was due to the weak embedding, not to the structure. 31 runs are many; whether there would remain a constant number for a larger instance of the same family cannot be checked on c6288 (only size 16).
2. The comparison is **in-sample**: displacement table, runs and exceptions are fitted to exactly these graphs; gluing/RePair re-impl. were learned on windows of the same graph and evaluated on the whole graph. The costs of the bundle table (≈ 1500 bits, major part) and of the runs are **rough estimates**; underestimating by a factor of 1.5 would keep the gap to gluing/RePair (factor ≈ 4), but an exact encoder was not built.
3. The embedding was searched for consistency, not for description length; an MDL-driven search could save or cost further exceptions.
4. Cell interior, dictionary (cell 20 edges + 13 border patterns) and bus remainders are not included. RePair remains my re-implementation.
5. The structure (two bus line families, parallelogram, diagonal strip) suggests that the multiplier is an *inductively defined* object whose quotient depends on two parameters; evidence for extrapolation would need further real sizes (for example c6288 next to smaller array multipliers), which are missing here. The own multipliers from 4n provide this for a more regular family.

## 4p. Embedding directly by description length (exact two-sided model), 22 October 2026

**Model** (`src/mdlembed.py`, `e43.py`, `results/e43_*`). Description length = (1) **bundle table**: per used bundle 2·log T + 2·log 20 bits per label (T = number of cell types) + 2 bits + displacement 2·log 7; (2) **node places**: core region as a parallelogram (shear −1…1; gaps count as exceptions) + greedy runs for all remaining cells (per run type, start, direction out of 12, length); (3) **exceptions**: *two-sided exact*, i.e. missing predicted edges (a bundle with displacement d predicts an edge for every pair of matching types at places p, p+d) **plus** unpredicted actual edges, each 2·log N + label bits, plus unplaced nodes. A bundle may also be "discarded" (all its edges are then exceptions). Optimisation: start from the consistency embedding (4o) *and* from the iterated majority displacement per bundle (better start), then coordinate descent over the displacement of each non-core bundle (|d| ≤ 3, or discarded), objective = this total length.

**Result (bits, whole quotient without bus and without cell/pattern dictionary):**

| Object | raw | Gluing | RePair re-impl. | Embedding before (estimate 4n/4o) | **MDL embedding** | of which bundles / places / exceptions |
|---|---|---|---|---|---|---|
| c6288 | 27866 | 9188 | 9215 | 2148 | **2642** | 1353 / 620 / 669 (20 edges, 25 runs, 48 of 63 bundles used) |
| mul16 | 17594 | 6854 | 5868 | 1408 | **1460** | 1023 / 342 / 95 (3 edges, 14 runs, 44 bundles) |
| mul24 | 43121 | 16337 | 14436 | 1450 | **1494** | 1023 / 370 / 102 |
| mul32 | 81219 | 30551 | 27627 | 1481 | **1519** | 1023 / 389 / 107 |

(Gluing and RePair re-impl. learned on windows of the respective quotient; dictionaries 950 and 1423 for c6288, 949 and 1360 for the multipliers, not included.)

**Reading.** (1) With the exact model the finding stays, but the c6288 number rises by 23% relative to the estimate (2642 instead of 2148): the majority displacements alone were not a consistent decoder (66 exception edges relative to a fixed table, not 14). For the multipliers the estimate is right to within 3-4% (same structure, only 3 exception edges). (2) c6288: about 3.5 times shorter than gluing and RePair re-impl., 1.9 times shorter than "lattice core + RePair border" (≈ 4950). Multipliers: the embedding grows from k=16 to 32 by 59 bits (3.9%), gluing by a factor of 4.5, RePair re-impl. by 4.7. (3) Coordinate descent from the consistency start alone gave 4511 bits, from the majority start 2963, then 2642: the objective is very bumpy because of the dependent placement; a global optimiser (MDL-driven placement, restarts) could save more bits, so the result is an upper bound. (4) Limits: bundle label costs (≈ 16 bits per label) and run costs are modelled but not verified against a real coder; bus, cell interior and dictionary not included; everything in-sample (validation: see open points, section 6); RePair is my re-implementation without pruning; gluing/RePair do not have the same encoding advantage from bundling for their edge labels (a bundle shares displacement and port pairs), so the comparison may be skewed in favour of the lattice model.

## 5. Open thread: simplices (for later)

Why: in graphs one can glue pieces only at nodes (nodes are the only genuine sub-objects of an edge). In simplicial sets (presheaves on Delta) there are faces: triangles can be glued along a shared **edge**, tetrahedra along **faces**. Here the density/pushout view actually offers more than Re-Pair on graphs. In addition, a filled triangle differs from a hollow 3-cycle although both have the same edges; graph methods do not see the difference.

Planned test:
* Data: complexes of filled and hollow triangles, tetrahedra, pairs sharing an edge; noise; several sizes/depths.
* Rebuild the learner: pattern = set of simplices; embeddings must respect boundaries; redefine cost per simplex (a 2-simplex is one element, not three edges plus a flag).
* Comparison: simplest graph encoding (edges only) against simplicial encoding, and gluing along edges against only at nodes.
* Expectation: advantage grows with the size of the shared boundaries. Refuted if the simplicial encoding is not better than the graph encoding with an extra edge for "filled".
* The largest rebuilding effort of all threads; hence after the products. **Not started.**

## 6. Further open points

* More flexible equivalence model for Kinships (a relation as a composition of others, not just exactly one partner).
* Better estimator for equivalences with small data (the largest gap to the oracle there); stricter acceptance criterion against false pairs.
* n-ary relations (hypergraph schema): shows schema independence, but is not simplicial.
* The curiosity part itself: active selection of the next data by expected learning progress versus random order (bandit on the compression signal). **Untested.**
* GraphMDL Java version (Inria GitLab was not reachable) or GraphMDL on larger sets with a longer time limit.
* Molecules and knowledge graphs with products/parametrisation, once the synthetic tests carry.
* **Validation on unseen data (important, missing so far).** Almost all results (in particular 4k-4o: lattice rules, embedding, comparison with gluing/RePair) are evaluated in-sample on a single circuit, or on windows of the same circuit, or on self-generated families; parameters, runs and displacement tables are fitted to exactly these graphs. Proposals: (a) **split** the data: training and test on separate sub-graphs (e.g. rows/columns of the lattice, disjoint circuit parts, different cities), not on overlapping windows; (b) create a **frozen validation set** that is not looked at during development (e.g. further ISCAS circuits such as c1355/c499 only as a negative test, further array multipliers and adders of other widths from independent sources, EPFL arithmetic, further cities); (c) look for **entirely fresh data sets** and keep them untouched (netlists from open-source chips, independently generated multipliers/adders, tic-tac-toe state graph, lattices from the review); (d) for size extrapolation, real families of different sizes (not only c6288 and own generators). Until then all numbers count as development results, not validation results.

## 7. Held-out test (28 October 2026)

**Correction (15 November 2026): this split is flawed and the table below does not support a conclusion about generalisation.** Pointed out by Reticuli on thecolony.cc and confirmed by our own recomputation: the undirected BFS reaches all 32 inputs within a few steps (each feeds 16 gates), so for both seeds half A contains all 32 inputs and all 256 AND gates, while half B is 99.7% / 99.3% NOR-to-NOR edges and falls into 24 / 10 disconnected pieces (A: 47.8% / 49.9% NOR-to-NOR, one piece). A and B are different kinds of graph. In addition (reported by Reticuli, not recomputed by us) the "new" windows of A overlap the training windows heavily (on average 58% / 46% of a test window's edges), the "empty" reference pays 6 bits per label (R = 64) although the circuit has only 7 labels, and the 1-10 bit difference between growing and gluing on B is within what hash-order effects and two seeds can produce. The numbers are kept as a record; a repaired split (BFS that does not pass through input nodes, sorted iteration, saved patterns and per-window costs) is planned.

Protocol (`src/heldout.py`, results `results/heldout_{0,1}.json`): c6288 is split by seeded BFS into two disjoint halves (seed 0: A 2074 / B 1758 edges, 968 cut edges dropped; seed 1: 2113 / 1778 / 909). Dictionaries are learned on 40 windows of A only and evaluated on 100 fresh windows of A and 100 windows of B (bits/window, lower is better; no dictionary cost). Candidate patterns with a node carrying more than 6 identical twin edges (bus fan-out stars) are skipped because `pynauty` hangs on them (`und.TWIN_MAX = 6`).

| seed | method | A (new windows) | B (held out) |
|---|---|---|---|
| 0 | empty | 363.5 | 413.5 |
| 0 | gluing | 87.2 | 189.3 |
| 0 | growing | 107.9 | 179.6 |
| 0 | RePair re-impl. | 95.7 | 279.4 |
| 1 | empty | 369.9 | 414.1 |
| 1 | gluing | 95.7 | 168.9 |
| 1 | growing | 119.3 | 167.7 |
| 1 | RePair re-impl. | 97.9 | 239.1 |

Original reading (**withdrawn**, see the correction above): the dictionaries transfer to B less well than within A, and the gluing advantage over growing seen on A is absent on B. Because A and B differ in composition and B is fragmented, this says nothing reliable about generalisation in either direction.

## 8. Held-out test on a repaired split (16 November 2026)

The split of section 7 was flawed (see the correction there). Reticuli contributed a repaired split and script (pull request #1, merge commit a2700c1); we reviewed the diff, ran it here and obtained the contributor's numbers exactly.

Protocol (`src/heldout2.py`, split in `src/split.py`, contributed by Reticuli in pull request #1; results `results/heldout2_{0,1}.json`): the walk that cuts c6288 in two does not pass through primary inputs, and the 512 input fan-out edges are in neither region. Region A is cut once more by the same walk into a training part and a test part that share no node. Cuts: 82 / 94 edges between A and B, 51 / 36 inside A (seeds 0 / 1). Every region is 85-91% NOR-to-NOR; training part and test part of A are one piece each, B is 3 pieces (seed 0) or one (seed 1). Dictionaries are learned on 40 windows of the training part (about a quarter of the circuit) and evaluated on 100 windows of the other part of A and 100 windows of B. Bits per window, lower is better, no dictionary cost. The output is identical under different `PYTHONHASHSEED` values; our run reproduced the contributor's numbers exactly.

| seed | method | patterns / rules | A (unseen part) | B (held out) |
|---|---|---|---|---|
| 0 | empty | 0 | 455.0 | 458.6 |
| 0 | gluing | 24 | 99.7 | 101.4 |
| 0 | growing | 12 | 185.4 | 186.8 |
| 0 | RePair re-impl. | 72 | 82.4 | 73.8 |
| 1 | empty | 0 | 460.4 | 449.1 |
| 1 | gluing | 16 | 103.3 | 118.5 |
| 1 | growing | 10 | 186.8 | 189.1 |
| 1 | RePair re-impl. | 62 | 81.4 | 85.7 |

Reading:
* **Transfer.** On a split whose halves are the same kind of graph, the dictionaries do about as well on B as on the unseen part of A. The drop on B in the first attempt was an artefact of the split.
* **Gluing against growing.** Gluing is lower by 71-86 bits on average, on 100 / 100 windows of A and 100 / 94 of 100 windows of B. This is the first support for the gluing advantage on circuit parts not seen in training. Caveat: growing stops at 12 and 10 patterns, and we have not found out why.
* **Our RePair re-implementation against gluing.** It is lower than gluing in all four cells. Its dictionary is larger (1673 / 1432 bits against 479 / 330), but with the dictionary spread over 100 windows it stays lower (seed 0: 99 / 91 against 105 / 106; seed 1: 96 / 100 against 107 / 122). **This contradicts claim 4 for c6288**, where earlier in-sample runs had gluing about 53 bits ahead. We do not know which difference is responsible: the missing input edges, the skipped star patterns (`und.TWIN_MAX = 6`), 80 rules against 40 patterns, or the in-sample set-up of the earlier runs.
* **Limits.** Two seeds, one circuit; windows of one region overlap each other, so 100 windows are far fewer than 100 independent draws; no window contains an input label any more; R = 64 although 6 labels occur; learner and evaluation still share one cost function.

## 9. Why growing stops, and why the baseline ordering flipped (16 November 2026)

Two open questions from section 8. Scripts `src/diag_order.py`, `src/diag_grow.py`; raw output `results/diag_order.jsonl`, `results/diag_grow.jsonl`. Whole c6288, 40 training and 100 fresh windows (in-sample, as in 4c/4d), seeds 0 and 1.

**(1) The flip is caused by the order of edges inside a window, not by the split.** Pull request #1 sorted the edge list of each window by node name (to remove the dependence on Python's hash order). Our RePair re-implementation picks non-overlapping digram occurrences greedily in edge order, so it is very sensitive to that order; the gluing learner is not. Bits per window (seed 0 / seed 1):

| windows | edge order | gluing | RePair re-impl. (<= 80 rules) | RePair re-impl. (<= 40 rules) |
|---|---|---|---|---|
| with input edges | sorted by node name | 108.2 / 103.2 | 52.3 / 52.6 | 108.6 / 109.5 |
| with input edges | random | 114.8 / 102.8 | 169.3 / 169.5 | 177.5 / 172.2 |
| without input edges | sorted by node name | 107.0 / 102.5 | 41.8 / 51.7 | 68.6 / 71.1 |
| without input edges | random | 117.4 / 105.2 | 182.9 / 187.4 | 183.9 / 190.8 |
| without input edges | from the graph alone (label, then degrees; ties random) | 117.2 / 104.6 | 121.5 / 134.9 | 152.5 / 141.6 |

Reading. (a) With random edge order we recover the old numbers of 4d (about 169); with name-sorted order the same re-implementation needs a third of that and is far below gluing. The earlier statement "gluing is about 53 bits ahead of the gRePair-like baseline on c6288" (4d) was therefore **an artefact of feeding the baseline edges in hash order**. It is withdrawn. (b) Input edges, the skipped star patterns and the rule cap are not the cause: the effect is the same with and without input edges, and at 40 rules the sorted baseline is level with or below gluing. (c) Sorting by node name is side information: gate names in the c6288 file follow the layout of the array, and the node numbers inside a window are shuffled, so a compressor that sees only the anonymous graph does not have this order. With an order computed from the graph alone (a crude one) the baseline lands between the two (122-135), still behind gluing here. The published gRePair spends effort on exactly this (node order); our re-implementation never did. So the honest statement is: **our re-implementation spans 42-187 bits per window depending on edge order, and no comparison with it supports a claim in either direction** until it has a principled graph-only order. The street comparison (4d, 4e) used the same code with edges in file/hash order and must be regarded as unverified for the same reason. (d) Gluing moves by 0-10 bits with the order (through the greedy cover); small, but not zero.

**(2) Growing stops in a structural local optimum, not because of the candidate cap.** Traced on windows without input edges, seed 0. Growing stops after 9 patterns (largest: 4 edges). At that point only 25 distinct candidate patterns exist in total (fewer than the cap of 30), and the best of them makes the training description 0.7 bits *longer*. Cause: in our growing mode a candidate is an existing cover piece plus one adjacent piece that is a single edge. Once the windows are tiled by 2-4-edge patterns, hardly any single edges are left next to an instance, so there is almost nothing to extend with. Gluing may join two multi-edge pieces and continues to 15 patterns (largest 12 edges). With random edge order growing stops even earlier (4 patterns). This is the "search advantage" caveat of section 3 in sharp form: **the gluing-versus-growing gap (71-86 bits in section 8) is measured against a growing variant that is weak by construction.** A fair growing baseline (extend an instance by any adjacent edge, also one currently covered by another instance, as SUBDUE does) has not been built. Note also that both learners optimise the old cost (`total_h`, all node pointers) while the evaluation uses interface costs.

**Consequences.** Claim 4 is withdrawn for c6288 and marked unverified for streets. Claim 2's held-out number stands as a measurement but only against our weak growing variant. Next steps would be a graph-only edge order for the baseline (or the original gRePair), and a fair growing baseline.

## 10. A published grammar compressor as reference: ITR (16 November 2026)

**Which code.** The original gRePair implementation (Maneth and Peternek, Scala) is not public: the gRePair paper links no code, the ITR paper only cites it, and the gRDF authors write that they "received a prototypical implementation ... from the authors". Publicly available are (a) **ITR / libcgraph** (Adler et al., https://github.com/adlerenno/IncidenceTypeRePair, C, commit 396f377), the successor of gRePair by an overlapping group, and (b) RDFRePair in https://github.com/dice-group/GraphCompression (Java port for RDF; not tried). We built ITR here. Build notes: needs libdivsufsort with `-DBUILD_DIVSUFSORT64=ON` and serd; the command-line tool does not compile without the web service, fixed by a two-line `#ifdef` (`docs/itr-build-fix.patch`, no change to the compressor). `--decompress` returned an error for our files, so losslessness on the window files was checked by querying every edge back (all identical); the whole-graph files were not checked in this way.

**What is measured.** ITR writes a file; we report its grammar part ("Grammar Size", i.e. without the dictionary of node names) in bits. This is a real, queryable data structure, not a model code length, and it contains its own rules. Our numbers are model code lengths with a dictionary learned on 40 windows. The two are **not like for like**; the table is a reference, not a contest. Scripts: `src/itr_whole.py`, `src/whole_graph.py`, `src/itr_windows.py`; results `results/itr_whole.json`, `results/whole_graph_*.json`, `results/itr_windows_*.json`.

**Whole c6288 as one graph** (kbit; "name order" = node numbers and triple order follow the gate names of the netlist file, "anonymous" = random node numbers and random order, two shuffles):

| | with input edges (4800 edges) | without input edges (4288 edges) |
|---|---|---|
| ITR grammar, name order | 70.4 | 59.8 |
| ITR grammar, anonymous | 132.7 / 134.7 | 120.7 / 120.2 |
| xz -9e on the N-Triples text, name order | 65.2 | 60.9 |
| xz -9e, anonymous | 168.6 / 169.3 | 152.0 / 152.0 |
| our model: every edge raw | 136.9 | 122.1 |
| our model: gluing, incl. dictionary (seeds 0 / 1) | 34.9 / 39.0 | 35.2 / 34.8 |
| our model: RePair re-impl., name order, incl. dictionary | 64.7 / 64.9 | 32.7 / 34.3 |

**Held-out windows of section 8 as one file of 100 disjoint windows** (bits per window): ITR grammar 313-366 with name order and 599-613 with random order (seeds 0/1, sets A and B), against 100-119 for gluing and 449-460 for our "empty" reference. Here ITR is far outside its design range: about 2,900 edges, fixed structure overhead, and node addresses over the whole file (11 bits) instead of one window (5 bits).

**Reading.**
1. **A real grammar compressor also depends strongly on the presentation of the graph**: a factor of about two between name order and anonymous numbering, for ITR and for xz alike. With anonymous numbering ITR's grammar is about as large as our "every edge raw" model. So the order sensitivity found in section 9 is not a peculiarity of our re-implementation; it is where much of the compression in this family comes from, and the gate names of c6288 carry the layout.
2. Our model figure for gluing on the whole circuit (about 35 kbit including dictionary) is roughly half of ITR's grammar in name order. **This is not a result against ITR**: one side is a model code length that no coder has produced, the other a file that supports queries; ITR's design targets large RDF graphs, not a 4,800-edge netlist. What the comparison does give is a scale: our model lengths are not absurdly far from what real tools write, and an actual coder for our model (Leo's point 1) is the missing piece.
3. The window-level setting, in which all our earlier baseline comparisons were made, is not one in which a published compressor can be run meaningfully. Baseline comparisons should move to whole graphs.
4. Our own re-implementation remains in the repository as a labelled side line (`src/repair.py`); its numbers are not to be read as gRePair's.

## 11. An actual coder for the gluing description (16 November 2026)

Until here every number for our method was a computed code length. `src/coder.py` writes the bytes and reads them back; `src/coder_run.py` applies it to the whole c6288 (dictionary learned on 40 windows as before, stored inside the file); results `results/coder_{full,gates}_{0,1}.json`; a round-trip test is in `tests/`.

**Coder.** Every symbol is an integer from a known range; the message is one mixed-radix integer, so a symbol of range r costs exactly log2(r) bits. File = header (five 32-bit counts), patterns as flat edge lists, instances, raw edges. Two instance modes:
* **all**: one pointer per pattern node. Node numbers are preserved exactly; the decoder's output is compared for exact equality with the input. This is the same task ITR solves (its grammar part also excludes node names).
* **boundary**: pointers only for nodes that have an edge outside the instance, the rest are numbered afresh by the decoder. The graph is preserved up to renaming of those nodes (about half of all nodes here). Verified by equality after renaming, a check that the renaming is a bijection fixing all other nodes, and colour refinement.
All 32 files (2 graphs, 2 seeds, 2 numberings, 2 modes, R = 64 and R = number of labels) decode correctly.

**Sizes, whole c6288, kbit, R = 64** (seed 0 / seed 1; "name" = node numbers and edge order follow gate names, "anonymous" = random numbers and random edge order):

| | with input edges | without input edges |
|---|---|---|
| our file, mode all, name | 50.4 / 52.6 | 45.8 / 45.5 |
| our file, mode all, anonymous | 50.2 / 52.3 | 44.5 / 44.4 |
| our file, mode boundary, name | 36.3 / 40.5 | 35.9 / 35.6 |
| our file, mode boundary, anonymous | 36.0 / 40.0 | 33.3 / 33.4 |
| model length for the same cover (boundary) | 34.9 / 39.0 | 35.2 / 34.8 |
| ITR grammar, name | 70.4 | 59.8 |
| ITR grammar, anonymous | 132.7 / 134.7 | 120.7 / 120.2 |
| xz -9e on N-Triples, name / anonymous | 65.2 / 169 | 60.9 / 152 |

**Reading.**
1. **The model lengths were honest to within 2-4%.** The file is slightly longer than the computed length (flat instead of hierarchical dictionary, a 160-bit header) and never shorter. This closes the "no real coder" caveat for the gluing description of this graph; it does not cover holes, products, label tables, lattice rules or the embedding model, which are still computed lengths only.
2. **The gluing description does not depend on how the graph is presented**: name order or anonymous numbering changes the file by 0-7%, whereas ITR and xz double. A dictionary of subgraph patterns finds repeated cells by matching, not through the numbering.
3. On the like-for-like task (node numbers preserved, mode all) our file is 50-53 kbit against ITR's 70 kbit in name order and 133-135 kbit anonymous. **We do not read this as beating ITR.** ITR's output answers neighbourhood queries without decompression and is designed for RDF graphs with millions of triples; ours is a plain archive format. The graph is one small, extremely regular circuit, the case most favourable to a cell dictionary; pattern matching by `cover_u` would not scale to ITR's graph sizes. What can be said: on this circuit a subgraph-pattern dictionary yields an actual file that is smaller than a published digram-grammar compressor's grammar, and in the anonymous setting much smaller.
4. Still in-sample in the sense of section 6: one circuit, the dictionary learned on its own windows (but paid for inside the file).

## 12. A second kind of graph: two DBpedia extracts (16 November 2026)

To leave our most favourable case, we took the two RDF files found in a public repository of this research line: `persondata_en.ttl` and `geo_coordinates_en.ttl` from the test resources of https://github.com/dice-group/GraphCompression (commit 526d761), 49,999 triples each. DBpedia extracts are the data family on which the gRePair papers report their advantage; these are not the files used in those papers (their data sets are on a server we cannot reach). Script `src/rdf_run.py`; results `results/rdf_*_0.json`. Nodes = distinct subjects and objects (literals included), label = predicate; node numbers and edge order random; pipeline unchanged (dictionary from 40 BFS windows of 20 nodes, `maxe = 12`, stored in the file; coder of section 11). ITR on the original files, grammar part only.

| graph | nodes | predicates | largest degree | ITR grammar | our file, node numbers preserved | our file, up to renaming of inner nodes | every edge raw (our model) |
|---|---|---|---|---|---|---|---|
| geo_coordinates | 46,107 | 4 | 12,500 | 1,075 kbit | 1,324 kbit | 1,183 kbit | about 1,650 kbit |
| persondata | 31,594 | 10 | 6,304 | 1,173 kbit | 889 kbit | 644 kbit | about 1,660 kbit |

Seed 0; all four files decode correctly. Run time: ITR under one second per file; ours 90 s and 558 s for learning plus 23 s and 51 s for encoding.

**Reading.**
1. **Mixed.** On geo_coordinates ITR's grammar is smaller than our file; on persondata ours is smaller. On the like-for-like task (node numbers preserved) that is +23% and -24%.
2. **Why we lose on geo_coordinates.** The graph is 12,500 small stars that all meet in one node (the class). Windows of 20 nodes grown from a random start almost always sit on that node; the learner finds only seven patterns, and the greedy largest-first cover then leaves 28,124 of 49,999 edges uncovered. A single star pattern would presumably describe the graph far better (not tested); our window sampling and cover do not find that description. This is the star-shaped, few-predicate case in which the grammar compressors claim their advantage, and here the claim holds against us.
3. **Not robust and not scalable.** With seed 1 the learner chose other patterns and the cover of the whole graph did not finish within 40 minutes for either file (backtracking through nodes of degree 6,000-12,500). So the numbers above are one seed, and a different draw of training windows can make our pipeline unusable on graphs of this kind. ITR needs under a second.
4. Consequence for the status table: claim 15 now reads "smaller on c6288 and on one of two RDF extracts, larger on the other, sometimes not finishing". That is not an advantage over published grammar compressors; it is a description of where a subgraph-pattern dictionary helps (repeated cells with internal structure) and where it does not (stars around hubs, at least with this learner).

## 13. The curiosity half, first test: data selection by predicted gain (16 November 2026)

Protocol fixed in advance in `docs/prereg-curiosity.md` (three dated amendments, each committed before the step it concerns). Scripts `src/curio_common.py`, `curio_gate.py`, `curio.py`, `curio_agg.py`; results `results/curio_gate_*.json`, `results/curio_*.json`, `results/curio_agg.json`.

**Gate (passed).** For every learning round on a pool of 200 windows from region A, the 30 candidates the learner evaluates were ranked by their gain on the pool and by their gain on 100 windows of the unseen region B. Spearman correlation: pooled median 0.95 over 66 rounds (per seed 0.96, 0.87, 0.93; lowest round 0.52). On this circuit the in-sample gain of a pattern predicts its held-out gain well.

**Experiment.** Budget 60 windows in 12 batches of 5, dictionary relearned after every batch, held-out bits per window on B after each batch; five seeds, all arms on the same pool and test windows. Arms: random order; highest predicted gain first; highest current cost first ("surprise"). Two pools: clean, and with 60 of 200 windows replaced by windows with random endpoints. Primary outcome: mean held-out bits per window over the 12 rounds (lower is better).

| pool | random | gain | surprise |
|---|---|---|---|
| clean, per seed | 113.7 116.7 115.0 115.8 117.6 | 112.3 119.8 128.5 115.1 117.5 | 110.1 110.4 111.7 118.0 108.3 |
| clean, mean | 115.8 | 118.6 | 111.7 |
| with unlearnable windows, per seed | 145.8 152.3 117.2 122.2 131.5 | 151.2 154.0 175.0 137.3 146.3 | 157.9 177.4 173.1 173.9 188.0 |
| with unlearnable windows, mean | 133.8 | 152.8 | 174.0 |
| unlearnable windows among the 60 chosen (18 expected) | 24 20 13 15 16 | 36 34 36 31 33 | 52 45 46 49 47 |

**Pre-registered hypotheses.**
* **H1 (gain beats random, clean pool): refuted.** Random minus gain = -2.9 bits on average, positive in 3 of 5 seeds. Gain is clearly worse in rounds 1-4 (-16.5, 1 of 5 seeds) and slightly better in rounds 5-12 (+3.9, 5 of 5); the late advantage was not a pre-registered criterion and is descriptive only.
* **H2 (gain beats surprise, pool with unlearnable windows): holds by the stated criterion** (surprise minus gain = +21.3, positive in 4 of 5 seeds; gain picks 31-36 unlearnable windows, surprise 45-52). **But the criterion was too weak**: gain is worse than *random* in all five seeds (-19.0 on average) and picks about twice as many unlearnable windows as random does. Progress-ordering avoids noise better than surprise-ordering, and worse than not choosing at all.
* **H3:** in the clean pool surprise is the best arm (4.1 bits ahead of random, 4 of 5 seeds; 6.9 ahead of gain). Descriptive.

**Why the gain arm fails (looked at after the fact, so a hypothesis, not a result).** The predicted gain is a one-step estimate: the best single new pattern. In round 1 it prefers clean windows (median 157 against 126 bits). After a few rounds the dictionary covers clean windows and their predicted gain drops to about zero, while the "unlearnable" windows keep a small positive value (5-9 bits): their labels were drawn from the pool's label frequencies, 85% of which are NOR-to-NOR, so they still contain generic two-edge chains. The arm then drifts into the noise. Two design weaknesses of our own protocol are visible here: the noise windows are not truly unlearnable, and the estimator saturates. In the clean pool the gain arm starts badly because the five windows with the highest predicted gain are near-duplicates (four of the first five have identical scores), so the first batch is less diverse than a random one.

**Further observations.** With unlearnable windows in the training set, held-out cost gets *worse* as more data arrive in the surprise arm (the learner spends dictionary entries on noise). **Oracle arm (added later the same day; seeds 0-2, clean pool).** Mean over the budget 116.5, 120.1, 119.7 bits per window, against random 113.7, 116.7, 115.0 on the same seeds: the "oracle" is *worse* than random in all three. As defined (relearn with each of 30 candidate windows, take the five that are individually best), it is not an upper reference: the five individually best windows are similar to each other, so the batch adds little beyond its first member. The same lack of diversity hurts the gain arm in the early rounds. A batch-aware oracle was not run.

**What this means for the idea.** The premise of curiosity-as-compression-progress holds in its static form (the gate: in-sample gain predicts held-out gain). The first operational form of it, choosing data by a one-step predicted gain, does not help on this circuit and is harmful when part of the data is noise-like, although it is less harmful than choosing by surprise. One circuit, one estimator, five seeds. A fair next test needs a progress estimate that does not saturate (e.g. realised progress on a window class over time, as in Schmidhuber's formulation, rather than a one-step prediction per window), truly unlearnable distractors, and data in which windows differ in what they teach; on c6288 nearly every window contains the same cells, as anticipated in the pre-registration.

## 14. Is the dictionary a stable "basis"? Stability and spectrum (16 November 2026)

Motivation: the loose analogy with PCA. Components should be a property of the data rather than of the sample, and a few of them should carry most of the effect. Script `src/basis.py` (committed with its four expectations before the first run), results `results/basis_{0..4}.json`. Per seed: repaired split of c6288; dictionaries from 100 windows each: A1 and A2 (two independent draws from region A), B1 (region B), X (circuit c880); 100 fresh evaluation windows of A and of B.

**Stability** (five seeds):

| pair, evaluated on B | identical patterns | Jaccard | share of covered edges that the first dictionary covers with patterns also present in the second |
|---|---|---|---|
| A1 vs A2 (same region, other sample) | 15-21 of 16-24 | 0.63-0.96 | 96-100% |
| A1 vs B1 (other region) | 13-17 of 16-26 | 0.45-0.67 | 93-99% |
| B1 vs A1 (other direction) | same | same | 66-92% |

Bits per window on B: with the dictionary from B itself 105.8, 99.4, 100.0, 110.2, 99.6; with the dictionary from A 106.5, 115.6, 104.0, 109.8, 109.5 (differences +0.7%, +16.3%, +4.0%, -0.4%, +9.9%). For comparison, two samples of the *same* region differ by up to 9% as well (on A: A1 103.8 109.3 99.7 101.6 103.9, A2 106.4 102.6 98.9 101.6 98.2).

**Spectrum** (dictionary A1, evaluated on B, patterns in the order the learner added them): the first pattern alone gives 49-51% of the total saving, two patterns 57-60%, five 72-76%, ten 91-94%; 90% is reached with 9-10 of 16-22 patterns. The sizes of the first ten patterns are almost the same in every seed (2, 4, 1, 8, 2 or 3, ...). In the final cover 4-7 patterns of each dictionary are not used at all (they were stepping stones for larger ones).

**Against the expectations.**
* E1 (other region is about as similar as another sample of the same region): **holds** in the direction A1 -> B1 (93-99% against 96-100%).
* E2 (at least 70% shared use; coding B with the dictionary from A costs at most 10% more): the shared-use part **holds**; the cost part **fails in one of five seeds** (+16.3%) and is at the limit in another (+9.9%). In both, A1 had only 16 patterns, i.e. the learner stopped early on that sample; the spread between two samples of one region is of the same order.
* E3 (a dictionary from c880 shares little): **uninformative**. It shares nothing (0 patterns, no compression), but c880 uses other gate types, so its edge labels hardly occur in c6288 at all; this was a badly chosen reference and says nothing about structure.
* E4 (half of the saving with at most 3 patterns, 90% with at most 10): **holds** (1-2 and 9-10).

**Reading.** On this circuit the learned patterns behave like a basis in the two senses asked for: the patterns that do the work are the same whichever half or sample they are learned from (the core that carries 93-100% of the cover recurs), and the gain is concentrated in few of them. Three qualifications. (1) The dictionary as a *set* is much less stable (Jaccard 0.45-0.96): the tail varies, and the learner sometimes stops early, costing up to 16%. Unlike PCA there is no uniqueness. (2) The reverse direction is weaker: a dictionary learned on B uses patterns absent from A's dictionary for 8-34% of its cover. (3) One very regular circuit; the first "component" is a generic two-edge NOR chain, which says more about the label statistics than about cells. A reference with the same labels but different structure (another NOR-only circuit, or a degree-preserving rewiring of c6288) is the missing control.

**Addendum to sections 8 and 9 (18 November 2026), suggested by Reticuli.** Edge order is a parameter of every figure for the RePair re-implementation, so the held-out table of section 8 was rerun with three random edge orders per seed (`heldout2.py SEED 40 100 random0|1|2`; same windows, same node numbering; results `results/heldout2_{0,1}_random{0,1,2}.json`). Ranges over the three orders, bits per window, A (unseen part) / B (held out): seed 0 gluing 108.4-110.7 / 108.6-112.0, growing 186.4-206.3 / 183.4-212.8, RePair re-impl. 190.2-205.3 / 194.5-207.4; seed 1 gluing 114.1-123.3 / 129.3-137.7, growing 214.8 / 215.5, RePair re-impl. 189.0-193.2 / 196.6-204.9 (name order: section 8). With random order the re-implementation is far above gluing in all twelve cells, with name order below it in all four: the ordering of the two methods is decided by the edge order. Gluing itself moves by 7-19 bits per window on these windows, more than the at most 10 bits of the in-sample diagnostic; the README table now shows both orders side by side.

## 15. Control for section 14: the same measurement on a rewired c6288 (18 November 2026)

`python basis.py SEED rewired`, results `results/basis_rewired_{0..4}.json`; expectations C1-C3 committed in the script before the first run. The rewiring swaps the targets of two edges with the same label, 20 swaps per edge: every node keeps its gate type, its in- and out-degree and its label counts, the cells of the multiplier are destroyed. Everything else as in section 14 (same seeds, same split procedure, dictionaries from 100 windows). Note: windows of 20 nodes contain fewer edges in the rewired graph (empty code 303-305 bits per window against 456-459), so absolute bits are not comparable and shares of the empty code are reported as well.

| measure (5 seeds) | original c6288 | rewired control |
|---|---|---|
| bits per window on B, dictionary from A | 104.0-115.6 | 128.8-141.7 |
| share of the empty code that remains | 23-25% | 42-47% |
| largest pattern in the dictionary from A (edges) | 10-12 | 7-12 |
| Jaccard, two samples of one region | 0.62-0.95 | 0.35-0.43 |
| Jaccard, dictionary from A vs from B | 0.45-0.67 | 0.20-0.38 |
| shared use, dictionary from A vs from B, on B | 93-99% | 57-86% |
| shared use, other direction | 66-92% | 39-57% |
| coding B with A's dictionary instead of B's own | -0.4% to +16.3% | -3.3% to +6.6% |
| saving reached with 1 / 5 / 10 patterns | 49-51% / 72-76% / 91-94% | 62-65% / 86-93% / 94-98% |
| patterns needed for 90% of the saving | 9-10 | 5-7 |

**Against the expectations.**
* C1 (at least 30% more bits per window on B): **fails as stated** (+11% to +36%, one seed of five above 30%). The criterion was badly chosen, because rewired windows have fewer edges; measured as the share of the empty code that remains, the rewired graph keeps about twice as much (42-47% against 23-25%).
* C2 (flatter spectrum in the control): **refuted, the opposite holds.** The control's spectrum is steeper: one pattern (a two-edge NOR chain) gives 62-65% of the saving and 5-7 patterns give 90%.
* C3 (stability of the working core stays at least 80% in the control): **refuted** (57-86%, one seed of five at 80% or above). Stability drops clearly when the cell structure is destroyed.

**Reading. This corrects part of section 14 and of claim 16.**
1. **A steep spectrum is not a sign of a good basis.** It is steeper in the structureless control, because there only a few small, generic patterns help at all. That "one pattern gives half of the saving" in section 14 says more about the label statistics than about cells.
2. **Stability of the working core is a sign of structure.** In the original, the patterns that do the work recur across samples and halves (93-99% shared use); in the control much less so (57-86%), and the dictionaries as sets overlap about half as much. This was the point of the control: without it, stability could have been an artefact of labels and degrees, and it is not.
3. **What the structure buys is the level of compression and large patterns that recur**: about half the residual code length, and the stable core of 8-12-edge patterns. In the control, transfer between halves is as good as in the original or better (the halves are equally random), so good transfer alone is no evidence either.
4. In the PCA analogy: a good basis is shown not by how quickly the explained share rises, but by components that are reproducible and that explain much more than the same procedure explains on a structureless graph with the same marginals.

## 16. An actual coder for products and holes (18 November 2026)

`src/coder2.py` extends the coder of section 11 to the two higher-order constructions; `src/coder2_check.py` applies it to the synthetic worlds of sections 4 (product world, e17, n = 50 training windows) and 4h (hole world, e30, 120 training windows), seeds 0-2; results `results/coder2_{product,holes}_{0,1,2}.json`; round-trip tests in `tests/`.

**What changed against coder.py.** (1) Exact big-integer rANS instead of fixed-width fields, so a symbol with frequency f of T costs log2(T/f) bits. (2) Counts and sizes in Elias gamma code instead of 32- or 16-bit fields (a first version with fixed fields cost about 128 bits per window more than the model, purely in headers). (3) Dictionary patterns are written either flat or as a gluing of earlier patterns, whichever is shorter, as the hierarchical model assumes; the encoder switches to the decoder's renumbered copies before covering. (4) Products: the file carries the explicit patterns, the factors (as references or as edge lists), the label classes and the size cap; the decoder rebuilds the implicit products itself. (5) Holes: frame, attachment pair, filler library; each frame occurrence stores which filler sits in each hole (or none), with option frequencies counted on the data and stored in the file. "Empty" and "other" of the model are merged into "none". All 24 files (2 worlds x 3 seeds x 2 models x seen/unseen or test) decode correctly.

**Computed length against file, bits per test window (data part, dictionary excluded), and dictionary bits:**

| world, seed | model | data: computed | data: file | dictionary: computed | dictionary: file |
|---|---|---|---|---|---|
| product 0, unseen pairs | gluing | 324.2 | 337.0 | 1073 | 1081 |
| | product closure | 209.6 | 220.0 | 1005 | 1063 |
| product 1, unseen pairs | gluing | 363.6 | 375.6 | 1000 | 1009 |
| | product closure | 221.4 | 230.9 | 973 | 1022 |
| product 2, unseen pairs | gluing | 420.1 | 433.1 | 1062 | 1070 |
| | product closure | 310.5 | 322.5 | 1018 | 1085 |
| holes 0 | gluing | 157.8 | 164.3 | 1539 | 1501 |
| | holes | 116.9 | 119.5 | 2476 | 1177 |
| holes 1 | gluing | 153.5 | 160.0 | 1467 | 1401 |
| | holes | 112.4 | 114.4 | 2291 | 1395 |
| holes 2 | gluing | 145.5 | 152.2 | 1795 | 1823 |
| | holes | 121.2 | 123.4 | 2189 | 1415 |

(Seen factor pairs in the product world: the same picture, file 9-12 bits above the computed figure.)

**Reading.**
1. **The computed lengths of the higher-order models were honest.** The file is 2-13 bits per window above the computed figure, for every model alike (the counts per window that the model leaves out), so the differences between models survive unchanged: product closure against gluing on unseen pairs 117 / 145 / 111 bits per window in the file against 115 / 142 / 110 computed; holes against gluing 45 / 46 / 29 against 41 / 41 / 24.
2. **Two modelling slips came to light, both small.** The product model charged factors as pointers into the dictionary, but 11-12 of 12-13 factors are not dictionary entries; written out they cost 50-67 bits more in total. The hole model over-charged its dictionary (hole tables at 6 bits per option plus filler costs): the file needs 1,177-1,415 bits where the model said 2,189-2,476, so the hole model was *more* expensive than necessary.
3. Synthetic worlds built for these constructions; this shows that the bits are real, not that real data have the structure. That is the next step (Quip circuits).

## 17. Circuits designed by others: the pre-registered Quip measurement (18 November 2026)

Pre-registration `docs/prereg-quip.md` (two amendments, both dated, the second after the first two results: hub-aware split). Ten Quip circuits from `ispras/hdl-benchmarks`, synthesised with Yosys defaults; seeds 0 and 1; `src/quip_run.py`, `src/quip_size.py`, `src/quip_agg.py`; results `results/quip_*_{0,1}.json`, `results/quip_size_{0,1}.json`, `results/quip_agg.json`. Every number below is from an actual `coder2` file (mode `boundary`), decoded and verified (all 80 circuit files and 40 control files round-trip).

**Data bits per test window (100 windows of region B, dictionary excluded), share of the empty file that remains, and the same share on the label- and degree-preserving rewiring (gluing only).** Product and holes columns are omitted because they equal gluing everywhere except one entry (see below). TV = label-mix distance between regions A and B.

| circuit | seed | TV | empty | gluing | share | control share | shared use circuit / control |
|---|---|---|---|---|---|---|---|
| barrel16 | 0 | 0.08 | 332.0 | 122.9 | 0.370 | 0.482 | 0.32 / 0.74 |
| | 1 | 0.08 | 330.4 | 126.2 | 0.382 | 0.503 | 0.20 / 0.75 |
| barrel32 | 0 | 0.03 | 315.9 | 99.2 | 0.314 | 0.433 | 0.34 / 0.46 |
| | 1 | 0.03 | 315.6 | 96.7 | 0.306 | 0.449 | 0.67 / 0.48 |
| barrel64 | 0 | 0.01 | 313.7 | 89.5 | 0.285 | 0.393 | 0.77 / 0.40 |
| | 1 | 0.01 | 313.9 | 81.3 | 0.259 | 0.410 | 0.93 / 0.37 |
| mux8_64bit | 0 | 0.02 | 313.2 | 84.2 | 0.269 | 0.425 | 0.20 / 0.24 |
| | 1 | 0.02 | 313.1 | 78.7 | 0.251 | 0.442 | 0.99 / 0.34 |
| mux8_128bit | 0 | 0.01 | 312.3 | 64.8 | 0.208 | 0.430 | 0.22 / 0.85 |
| | 1 | 0.02 | 312.3 | 71.2 | 0.228 | 0.438 | 0.99 / 0.43 |
| mux32_16bit | 0 | 0.08 | 316.2 | 150.4 | 0.476 | 0.450 | 0.46 / 0.30 |
| | 1 | 0.08 | 309.2 | 121.1 | 0.392 | 0.393 | 0.19 / 0.36 |
| mux64_16bit | 0 | 0.06 | 313.9 | 138.7 | 0.442 | 0.443 | 0.49 / 0.29 |
| | 1 | 0.04 | 311.7 | 124.2 | 0.398 | 0.448 | 0.36 / 0.21 |
| oc_aes_core | 0 | 0.32 | 343.1 | 287.3 | 0.837 | 0.803 | 0.72 / 0.61 |
| | 1 | 0.34 | 338.3 | 274.8 | 0.812 | 0.793 | 0.71 / 0.52 |
| oc_des_area_opt | 0 | 0.37 | 316.5 | 141.8 | 0.448 | 0.604 | 0.54 / 0.76 |
| | 1 | 0.43 | 319.9 | 138.3 | 0.432 | 0.535 | 0.76 / 0.45 |
| oc_des_perf_opt | 0 | 0.25 | 349.0 | 299.7 | 0.859 | 0.830 | 0.41 / 0.56 |
| | 1 | 0.23 | 348.8 | 292.7 | 0.839 | 0.879 | 0.49 / 0.62 |

**Size family (P5), data bits per window:** barrel16 dictionary on barrel32 138.7 / 133.4 (seed 0 / 1) against own 99.2 / 96.7, ratio 1.40 / 1.38; on barrel64 129.6 / 130.8 against own 89.5 / 81.3, ratio 1.45 / 1.61.

**Verdicts against the pre-registered expectations.**
* **P1 fails.** Gluing beats the rewired control by at least 10 points in 12 of 20 runs: all barrel shifters, both narrow multiplexers (mux8_64bit, mux8_128bit, 16-22 points) and oc_des_area_opt. It does not in the wide multiplexers (mux32_16bit, mux64_16bit: -3 to +5 points), nor in AES and DES-perf, where the circuit is even slightly worse than its control. For AES and the two DES variants the regions differ in label mix (TV 0.23-0.43), so these are not same-kind held-out tests, as the amendment said in advance.
* **P2 holds.** Product closure selected no factor in any circuit or seed; its file equals the gluing file.
* **P3 holds formally, and the one hole is useless.** A hole was found once (oc_des_area_opt, seed 0, in the training windows); on the test windows it costs 1.0 bit per window *more* than gluing (142.8 against 141.8) and a larger dictionary (1,094 against 960 bits). Nowhere does a hole save anything.
* **P4 fails.** Shared use is higher on the circuit than on its control in 4 of 10 circuits (seed 0); with seed 1 it would be 7 of 10. The measure jumps between seeds on the same circuit (mux8_64bit 0.20 / 0.99, mux8_128bit 0.22 / 0.99), so on these circuits it does not separate structure from rewiring; the clean separation of section 15 (c6288: 93-99% against 57-86%) does not carry over.
* **P5 fails clearly.** The barrel16 dictionary costs 38-61% more on the larger barrel shifters than their own dictionaries, not at most 10%. The patterns learned on the small instance do not transfer to the larger members of the same family at the window level.

**Reading.**
1. On circuits we did not design, the presheaf constructions beyond gluing contribute nothing measurable: no product factors, no useful holes, as expected in advance (P2, P3) and as on streets and c6288.
2. The gluing dictionary does find circuit-specific structure in the barrel shifters and narrow multiplexers (clearly better than the rewiring, on held-out regions with matching label mix). In the wide multiplexers and in AES/DES it does not; there the compression it achieves is what the label and degree statistics alone already allow.
3. The two "basis" properties claimed for c6288 (section 14-15) were stability and transfer. Neither holds here as pre-registered: stability is noisy and not better than the control in most circuits, and transfer across sizes of the same design family is poor. Claim 16 stays restricted to c6288.
4. Residual home advantage: Yosys may itself produce regular structure; the four positive circuits are also the most regular designs in the set.

## 18. Why the wide multiplexers look like their rewiring: window size and hub edges (19 November 2026)

Pre-registration `docs/prereg-quip-window.md` (committed before any output was inspected; three timing runs had been started before it was written, as stated there). `src/quip_window.py`, `src/quipw_agg.py`; results `results/quipw_*.json`, `results/quipw_agg.json`. Gluing only, all 72 files round-trip. The runs with 20-node windows and no hub edges reproduce the shares of section 17 exactly.

Label counts and out-degrees suggest that Yosys builds the multiplexers as a one-hot select decoder whose lines fan out to every output bit, NAND gates for data and select, and an AND tree per output bit (mux8_64bit: 8 select lines with fan-out 64; mux32_16bit: 32 with fan-out 16; mux64_16bit: 64 with fan-out 16). In the presheaf view, a product (output bit x select line) glued along the select lines.

**Gap = control share of empty minus circuit share (positive = circuit compresses better than its rewiring), seed 0 / seed 1.**

| circuit | window 20 | window 40 | window 60 | window 20 + hub edges | 40 + hubs | 60 + hubs |
|---|---|---|---|---|---|---|
| mux32_16bit | -0.026 / +0.001 | -0.019 / -0.046 | +0.013 / -0.082 | -0.023 / -0.072 | -0.134 / -0.129 | -0.155 / -0.141 |
| mux64_16bit | +0.001 / +0.049 | -0.045 / +0.036 | -0.019 / +0.067 | -0.099 / +0.034 | -0.122 / -0.061 | -0.116 / -0.097 |
| mux8_64bit | +0.156 / +0.191 | +0.151 / +0.142 | +0.127 / +0.105 | -0.035 / +0.027 | -0.029 / +0.009 | +0.030 / +0.082 |

**Verdicts.**
* **W1 fails.** Going from 20 to 60 nodes changes the gap of the wide multiplexers by +0.04 / -0.08 (mux32_16bit) and -0.02 / +0.02 (mux64_16bit), not by +0.10 or more. Larger windows do not let the circuit pull away from its rewiring.
* **W2 holds.** mux8_64bit changes by -0.03 / -0.09; it keeps its lead at every window size, shrinking slightly.
* **H1 fails, in the opposite direction.** With the select-line edges added back, the gap at 20 nodes changes by +0.00 / -0.07 (mux32_16bit) and -0.10 / -0.02 (mux64_16bit). Hub edges make the circuit look *less* structured than its rewiring, and they also wipe out most of the lead of the narrow multiplexer (+0.16 / +0.19 down to -0.04 / +0.03). On mux8_64bit seed 0, adding hub edges moves the circuit from 84 to 116 bits per window and the control from 133 to 102. Why the control gains is not understood. One candidate, flagged in advance: windows that contain a select line contain stars of many identical edges, which the learner skips (`und.TWIN_MAX = 6`).

**Reading.**
1. Neither explanation holds as stated: the wide multiplexers do not become distinguishable from their rewiring with larger windows or with the select lines included.
2. The confound named in advance is binding: the largest learned pattern has exactly 12 edges, the cap, in 27 of 36 circuit runs (the other runs reach 8-11 edges). The learner cannot hold a whole 32- or 64-input slice, whatever the window. So this refutes "window size alone, with the current pattern cap", not "the structure is larger than what the learner can represent". A test of that would need a larger cap and its own pre-registration; it is also where learning time grows fastest.
3. The structure a human sees at once in these circuits (identical slices sharing select lines) does not show up as an MDL gain of the gluing dictionary at any setting tried. Where the select lines are included, they even hurt. For the presheaf view this is the most direct negative so far: the product is there by construction of the circuit, and the learner does not turn it into shorter files.

## 19. Centaur's probe: a multiplexer ladder with a raised pattern cap (25 November 2026)

Pre-registration `docs/prereg-mux-ladder.md` (amendment 1: an undirected encoding for the canonical form, `und.CANON_UNDIRECTED`, after pynauty stalled on 24-32-edge patterns in timing runs on seed 9). Prompted by a comment by Centaur on thecolony.cc. `scripts/gen_mux_ladder.py` writes N-to-1, 16-bit multiplexers in the Quip template; for N = 32 and 64 its netlists match the Quip originals in edge and label counts. `src/mux_ladder_run.py`, `src/ladder_agg.py`; results `results/ladder_*.json`, `results/ladder_agg.json`. Windows of 60 nodes, gluing only, hub edges left out, 2 seeds, all 96 files round-trip.

Measured before any learning run: one output slice has 16 / 32 / 64 edges for N = 4 / 8 / 16, so already at N = 4 no whole slice fits under the old cap of 12.

**Gap to the rewired control (points of the empty file size, mean of seeds 0 and 1).**

| N | slice edges | cap 12 | cap 32 | cap 64 | largest learned pattern at cap 64 (seed 0 / 1) |
|---|---|---|---|---|---|
| 2 (MUX cells, descriptive) | 4 | 7.4 | 11.4 | 12.0 | 38 / 37 |
| 4 | 16 | 13.6 | 16.9 | 16.3 | 49 / 64 |
| 8 | 32 | 16.3 | 19.1 | 18.9 | 29 / 41 |
| 16 | 64 | 7.4 | 6.4 | 6.0 | 23 / 39 |

**Verdicts.**
* **L1 (reach) fails.** At the smallest cap that holds a whole slice the gap grows by +3.4 (N = 4), +2.8 (N = 8) and -1.4 points (N = 16), not by 10 or more.
* **L2 (no gain) holds.** Between cap 12 and cap 64 the gap changes by +2.7, +2.6 and -1.4 points, under the 5-point threshold for every N.

**Descriptive.**
1. At fixed cap and window the lead over the rewiring rises from N = 4 to N = 8 and then halves at N = 16 (16.3 to 7.4 points at cap 12), the same fall-off as between the Quip circuits mux8_64bit and mux32_16bit (section 17). The cap does not explain it.
2. Given room, the learner does not build slice-sized patterns where slices are large: for N = 16 the largest pattern stays at 23 edges in seed 0 at both cap 32 and cap 64 (identical results), and at 39 edges in seed 1 against a 64-edge slice. Where slices are small (N = 4) it builds patterns larger than a slice (up to 64 edges), which then span parts of several slices.
3. For N = 2, whose slice is a single MUX cell, a larger cap adds about 4-5 points; there the extra room is used for patterns spanning many slices.
4. Region label mix differs in one run (N = 4, seed 1: TV 0.23); the others are 0.04-0.14.

**Reading.** Centaur's probe separates the two stories, and in this design it comes out for "no gain": the learner can now represent a whole slice, and it neither builds one nor gets more out of the circuit than at the old cap. The fall-off between N = 8 and N = 16 is real and reproducible on our own Quip-template ladder, but it is not a matter of how large a pattern may be. What remains as an explanation lies outside the pattern cap: the window (a 16-to-1 slice with its registers takes about as many nodes as a 60-node window holds), the share of the circuit taken by the shared decoder and the input shift registers, or the bottom-up search itself, which never proposes a whole slice as one candidate. With this result the chapter-one learner is fully scoped: within its search, a larger cap is not the missing piece.
