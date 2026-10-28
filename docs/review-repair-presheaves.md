# Stocktaking, RePair claims, and arguments for the presheaf perspective

Status: 15 October 2026 (translated from the German original). Tags as in `review-macros.md`: **[established]** (in a source I read), **[standard]** (textbook knowledge, not re-checked), **[proof sketch]** (own derivation, not checked by others), **[interpretation]**, **[unverified]**.

Throughout, "RePair" in our own measurements means **our re-implementation** of a gRePair-like digram grammar, not the original code.

---

## 1. Which effects are we investigating?

| Effect | Operation | What we test | State of evidence |
|---|---|---|---|
| **E1 Gluing** | colimit/pushout (interface = cospan) | patterns from patterns; instances pay only boundary nodes | c6288: glue ≫ grow (23-25%; with interface 31% ahead of our gRePair-like baseline); streets: glue ≈ grow, both ≈ 12-14% ahead of our baseline (lab notebook 1e, 4c-4e) |
| **E2a Product** | limit (box product, closed monoidal) | product closure of the dictionary | synthetic only (e17), ≈ 0 on real data (1c, 1e, 1f); theoretical argument: treewidth separation (3.2) |
| **E2b Exponential object B^A** (= higher-order: macro with hole, currying, insertion = evaluation) | internal hom | label hole (anti-unification), hole with subgraph filler (depth 1), **hole in hole (depth 2)** | label hole: synthetic 22-92 bits, real nothing (4f/4g). Subgraph filler depth 1: synthetic 28-35 bits/window, real hardly any holes (4h). **Depth 2: lab notebook 4j** |
| **E3 Recursion = fixpoint** | initial algebra / W-type (X ≅ F(X)) | 4k (lattice rule on the c6288 cell quotient) | **first test in 4k, see below.** More than E2b: the exponential object gives higher-order but terminating macros (like SL grammars with parameters); self-reference needs a fixpoint |

The project had two goals: (a) gluing as a strengthening of the presheaf perspective (E1), (b) a higher-order effect. Clarification of 15 Oct.: "recursive" here means the **exponential object** (E2b: macros as elements of B^A, macros in macros through currying). Real recursion through a fixpoint (E3) is more than the exponential object and a separate effect, untested at that date. RePair (SL-HR grammars) knows recursion only as *nesting* (nonterminals that use nonterminals, no real self-reference).

---

## 2. Where does the RePair community claim its advantage?

Read: gRePair (Maneth/Peternek, arXiv 1704.05254), ITR (arXiv 2306.01028v3), gRDF (PMC 9003471), Claude/Navarro (abstract, TWEB 2010), TreeRePair (arXiv 1007.5406).

| Data family | Source | Statement **[established]** | Limitation |
|---|---|---|---|
| **RDF graphs with few predicates** (DBpedia extracts, Identica, Jamendo) | gRePair | against k²-trees "consistently better, partly by a factor of several hundred". Mean at maxRank 4: RDF 4.85 bit/edge (network graphs 11.44, version graphs 5.57) | comparison against adjacency-matrix structures (k²), not against pattern miners |
| **RDF with star/tree patterns** (LUBM, ArchivesHub, ScholarlyData) | gRDF | works best when subject-predicate and object-predicate pairs recur often and there are few predicates; star/tree patterns halve the edge count. Weak on real data (many predicates); dictionaries make up ≈ 75% of the compressed size | gRDF lead over the best competitor on real data only 1.9-3.3% |
| **Version graphs** (tic-tac-toe 5 634 nodes / 10 016 edges, chess-legal 76 272 / 113 039, DBLP snapshots) | gRePair, ITR | highly regular (ttt: 3 labels); ITR+ reaches 14.23% of the raw size on ttt-win and beats "all others" | on network/version graphs other methods are partly better (ITR authors) |
| **Web graphs** | Claude/Navarro | Re-Pair does not reach the compression rate of WebGraph, but navigates faster at equal space | the advantage is navigation, not size |
| **XML trees** | TreeRePair | SLCF grammars share *repeated tree patterns with parameters* (= macros with holes!), DAGs only identical subtrees; SLCF can be exponentially smaller than DAGs (cited, [LM06]) | corpus names not given in the excerpt read |
| **Social/network/collaboration graphs** (CA-AstroPh, Enron, Wiki-Vote …) | gRePair | highest bit/edge; gRePair+DSR mostly best, but small lead | no structural claim |

**Reading.** The advantage is claimed where (i) very few distinct labels/predicates, (ii) highly regular local repetition (stars, paths, tree pieces, versions) and (iii) hierarchical repetition exist. In these sources there is **no** claim for grid- or product-like structures. The rank parameter is critical: best maxRank = 4; the authors show theoretically (Lemma 8/9) that too small a rank can prevent compression [established].

**Possible data sets.** From the sources: LUBM (generator), ArchivesHub, ScholarlyData, Jamendo, DBpedia extracts, Wikidata (RDF); tic-tac-toe/chess/DBLP (version graphs); CA-AstroPh, NotreDame, Wiki-Talk (SNAP). **[unverified]** whether reachable from the sandbox (only GitHub and package registries are certain); the origin of "ttt-win"/"chess-legal" is not stated in the excerpts read. The tic-tac-toe game graph can be generated locally (not identical to ttt-win). For *our* question (high treewidth plus product/hierarchy structure), better fits are: circuit arithmetic (EPFL, c6288 - available), FEM meshes, grids/tori/hypercubes (generable), state-space graphs of puzzles.

---

## 3. Theory: arguments for the presheaf perspective

### 3.1 Box product vs categorical product (clarification)
Our product closure (`prod_pattern`) is the **box product** (Cartesian product of graph theory), not the categorical product of the graph topos. **[established]** (TAC 41-23, arXiv 2310.00493): the category of (reflexive) graphs has exactly two closed symmetric monoidal products, the box product and the categorical product. Both thus have an internal hom (currying). The grid = path □ path is a product in the first, not in the second. **[interpretation]** That means: the "right" categorical home of the product closure is the box-monoidal structure, and the currying reading of macros with holes (review 1a, 5) holds for both structures.

### 3.2 Argument A (strongest): generating high treewidth - a separation from SL-HR grammars
**Claim [proof sketch].** Let Γ be a straight-line HR grammar whose rules have right-hand sides with at most s nodes (external nodes included), and G the generated graph. Then tw(G) ≤ s − 1.
*Sketch.* The derivation tree of Γ is a tree; assign to each rule-application node as a bag the node set of its right-hand side. Terminal edges lie in the bag of their rule; a node occurs in the rule that creates it and in all children to which it is passed as an external node, hence in a connected subtree. That is a tree decomposition of width ≤ s − 1. The statement "HR grammars generate graphs of bounded treewidth" appears as an introductory sentence in the literature **[established]** (Chimes/Iosif/Zuleger, arXiv 2402.17015); the per-grammar bound is my own formulation.
**Consequence.** Every SL-HR grammar for G has a rule with ≥ tw(G) + 1 nodes, hence size ≥ tw(G) + 1 (size measure: nodes of the right-hand sides). The n×n grid has tw = n [standard]; every grammar therefore has size ≥ n + 1.
**On the other side.** With a dictionary that has the box product as an operation: path P_n by doubling with O(log n) entries, grid = P_n □ P_n, in total O(log n) entries. That is an **exponential gap** in description size (log n against n). The same holds for tori, hypercubes (tw grows exponentially in the dimension) and all products of families with growing treewidth.
**Limits, honestly.**
- The comparison "model with an additional operation against model without" is expected in itself. The content is: the box product is **not** generable from gluing operations with interfaces of bounded size. That is exactly the difference between the colimit fragment (E1) and the rest of the topos (E2).
- With unbounded rank an SL-HR grammar can build the grid row by row; I suspect O(n log n) [unverified], hence no exponential but a polynomial gap to O(log n). In practice the rank is small (gRePair: best maxRank = 4), and then the gap cannot be bridged.
- For **our real data** the effect does not show: product closure brings ≈ 0 on c6288, cell level and streets (lab notebook 1c, 1e, 1f). The argument says *where* an effect is possible (families with high treewidth and product structure), not that the data examined are such families.
- The argument is strong against RePair grammars *in the grid case*, irrelevant against the practice of RePair (stars, few labels, small treewidth).

### 3.3 Argument B: one algebra instead of three heuristics (distributivity)
In topoi colimits commute with products (universality of colimits) **[standard]**; for closed monoidal structures (box product) this follows from the adjunction (a left adjoint preserves colimits in each argument) **[standard]**. Concretely: (A ∪_C B) □ D = (A □ D) ∪_{C □ D} (B □ D). Consequence for the dictionary: there are algebraic rewrites between "first glue, then multiply" and "first multiply, then glue"; canonical normal forms and equality tests for dictionary entries are possible. The grammar view has no counterpart (there is only syntax). **Strength:** nice, but so far without an established compression gain. **[interpretation]**

### 3.4 Argument C: substitution as evaluation - common semantics for macros with holes
HR replacement and SLCF tree grammars (TreeRePair patterns with parameters **[established]**) are special cases of "macro with hole = arrow A -> B, insertion = evaluation" (review 5). The cospan category (Fong-Spivak) provides the HR algebra; presheaf topoi add limits and internal homs. **[interpretation]**; the identification "SL-HR = programs over a cospan signature" follows Bauderon-Courcelle **[unverified]**.

### 3.5 Argument D: fixpoint (E3) and size extrapolation
Recursive macros μX. F(X) (e.g. ripple-carry chain: a cell that contains itself as the filler of a hole) are, in topoi with a natural-numbers object, initial algebras of polynomial functors (W-types) **[standard, not re-checked]**. SL grammars have no self-reference: a chain of length n needs either n rules or doubling (O(log n)), each for a fixed n. A recursive macro with a parameter has cost O(log n) for the *application*, but the macro itself is size-independent. **Testable hypothesis [interpretation]:** a recursive macro *extrapolates* to sizes that did not occur in training (e.g. training on 4-/8-bit adders, test on 16-bit); a grammar for a fixed graph cannot. That would be an effect of the fixpoint (E3), not of the exponential object alone, and it is not eaten up by "RePair can do that too (with more rules)". *(First tests: lab notebook 4k-4p, on cell quotients of multipliers; a lattice-shaped special case with the rule class given.)*

### 3.6 Argument E: sheaf condition as decodability (weak)
Matching families of local sections that agree on overlaps glue uniquely (sheaf condition). In our encoding that is exactly the consistency "instances identify the same boundary nodes". **[interpretation]** This explains decodability but gives no compression advantage; pure formalisation.

### 3.7 Argument F: Yoneda/density - patterns as features
Embeddings of a pattern P into G are elements of Hom(P, G) (Yoneda); homomorphism counts determine the graph up to isomorphism (Lovász) **[standard]**. Compression as the choice of a smaller diagram presentation with the same colimit (cofinal) **[interpretation]**. Technically clean, so far without an algorithm.

---

## 4. What the presheaf perspective has *not* delivered (counter-arguments)

- E1 (gluing) is already contained in HR/gRePair (cospan, nonterminal with rank). Our advantage over the gRePair-like baseline on c6288 lies in the pattern family (larger building blocks, global MDL selection), not in the presheaf structure; on streets `grow` without gluing is just as good. Note also that this baseline is our own re-implementation.
- E2: product/hole gains only in constructed worlds. The treewidth statement (3.2) names the data family on which this could carry; we had not measured there yet.
- E3 (recursion): first test in lab notebook 4k (lattice rule extrapolates exactly from 3x3-5x5 to 13x13, cost ~65 bits against 2400-3700 for gluing; core is a perfect lattice, rule class given).
- RePair is very strong on stars/few labels/version graphs; our patterns have not been shown to win there.

## 5. Proposals (theory side, ordered by effort)
1. **Work out claim 3.2 properly** (write the proof; fix the size measure; check the upper bound O(n log n) for unbounded rank; literature: Courcelle/Engelfriet, HR and treewidth). This is the clearest theoretical argument.
2. **Work through distributivity 3.3 on an example** (dictionary with normal form, proof that first-glue-then-multiply and the reverse give the same bit costs).
3. **Depth-2 test (E2b)**: hole whose filler itself has a hole (Hom(A, B^C)); result in lab notebook 4j. Only after that **size extrapolation (3.5, E3)**: training on small arithmetic circuits, test on larger ones, with a macro that contains itself.
4. Data side: grids/tori/hypercubes (generable) and arithmetic circuits of different widths (EPFL, available); version graphs (generate tic-tac-toe locally) only for orientation against RePair.

## Sources
- Maneth, Peternek: Grammar-Based Graph Compression, [arXiv 1704.05254](https://arxiv.org/pdf/1704.05254)
- ITR: Grammar-based Graph Compression Supporting Fast Triple Queries, [arXiv 2306.01028](https://arxiv.org/html/2306.01028v3)
- gRDF, [PMC 9003471](https://pmc.ncbi.nlm.nih.gov/articles/PMC9003471)
- Claude, Navarro: Fast and Compact Web Graph Representations, [Abstract](https://users.dcc.uchile.cl/~gnavarro/abstracts/tweb10.html)
- Lohrey, Maneth, Mennicke: Tree structure compression with RePair, [arXiv 1007.5406](https://arxiv.org/pdf/1007.5406)
- Closed symmetric monoidal structures on the category of graphs, [arXiv 2310.00493](https://arxiv.org/abs/2310.00493)
- Chimes, Iosif, Zuleger: Tree-Verifiable Graph Grammars, [arXiv 2402.17015](https://arxiv.org/html/2402.17015v2)
