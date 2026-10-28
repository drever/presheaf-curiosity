# Short review: macros (with holes) in graph compression, and their category-theoretic reading

Status: 11 October 2026 (translated from the German original). Purpose: clarify theory/literature before testing "macros with holes" numerically.

**Labels.** Every statement carries a tag:
- **[established]** - said in this way in a source I read (abstract/full text/search hit).
- **[interpretation]** - my own bridge; plausible, but not claimed by the authors.
- **[unverified]** - from memory, not verified.

Access problems: the HAL page of GraphMDL+ (access denied) could not be read; Aguiñaga et al. (arXiv 1608.03192) was found but not read.

---

## 1. What is a "macro with a hole"?

A macro without a hole is a fixed subgraph pattern that occurs several times; one stores it once and refers to it. That is what our `glue` learner does (pattern = gluing of smaller patterns, cost per instance = pointer + attachment nodes).

A macro **with holes** additionally has *parameters*: places where something different is inserted at every use. For graphs there are three usual shapes:
1. **External nodes** (interface): the pattern has k distinguished nodes through which it is glued to the rest.
2. **Nonterminal edges**: a placeholder (hyperedge of rank k) that is later replaced by a subgraph pattern.
3. **Under-specified labels/parts**: anti-unification - the pattern is the common generalisation of several occurrences, the differences are the holes.

### 1a. Clarification (14 October 2026): macro without hole = macro with trivial filler

**[interpretation, checked by calculation]** Two notions are not needed. A macro with a hole is a context C with an interface I -> C; a filler is an object X with I -> X, inserted by pushout C ∪_I X. The *empty* object ∅ is an admissible filler only if I = ∅ (otherwise there is no map I -> ∅). The right "initial object" lives in the category of fillers, i.e. the category under I (coslice I/𝒞): there the initial object is the identity I -> I, and inserting it returns C unchanged, i.e. the macro without a hole. Two equivalent readings: (a) macro without hole = macro with empty interface (I = ∅, where ∅ is the only filler); (b) macro without hole = macro with a hole into which the trivial filler id_I is plugged. In exponential language: a hole of sort A is an arrow A -> B; a macro without hole is the constant arrow 1 -> B; a hole of sort 0 gives B^0 = 1, i.e. exactly one point.

**Why we still separate them in the implementation.** Purely cost-wise the separation is a shortcut: the trivial filler has a cost in a code only if it is rare; if almost all instances have no filler it costs ≈ 0 bits, and the uniform representation is as cheap as the separate one. In learning, holes arise where occurrences differ (anti-unification), fixed parts where they stay equal.

**Terminology error in my earlier tests (corrected here).** "Interface" and "hole" are different things. In Test A (lab notebook 4c) interface denotes the boundary nodes of a pattern towards the *rest of the window*; nothing of it is filled later. In Test B/hybrid (4f/4g) the "holes" are edges with a variable *label*, the filler is a label from a distribution. A hole whose filler is a *subgraph* (the case of the cospan/exponential reading) was first tested in Test C (lab notebook 4h).

## 2. Grammar-based graph compression (hyperedge replacement)

- **[established]** Compression via *straight-line hyperedge replacement (SL-HR) grammars* (gRePair, Maneth et al.): digrams (pairs of adjacent edges) are iteratively replaced by a nonterminal hyperedge whose rule generates the digram. A nonterminal edge has a *rank* = number of attached (external) nodes. This is exactly a macro with k holes in the sense of (1)+(2): the external nodes are the interface to the rest.
- **[interpretation]** Our `glue` learner corresponds to a gRePair with larger building blocks and MDL selection instead of a frequency heuristic; the difference from a "macro with hole" is that we do *not* treat the interface as a first-class object - per instance we store the full node references (`#vertices·log2 n`). A macro with interface would only charge the external nodes per instance, internal nodes would be "free".
- **[established]** Kukluk-Holder-Cook: inference of recursive node/edge replacement grammars with overlapping instances (on a SUBDUE basis). Recursion = macro that contains itself as a hole.
- **[established]** SUBDUE itself compresses iteratively by replacing the best substructure by a node (MDL); the replacing node has the connections of the instance -> implicitly a macro with interface, but without typing of the holes.

## 3. MDL miners with vocabulary and ports

- **[established]** VoG (Koutra et al.): MDL selection from a *fixed* structure vocabulary (cliques, stars, chains, bipartite …). No learning of new macros, but evidence that parametrised basic forms (star with n leaves) are very effective: a star is a macro whose hole is "number of leaves".
- **[established, mention only]** GraphMDL+ / KG-MDL knows *ports* (nodes at which patterns may be connected to others) - that is the interface concept in mining language. **[unverified]**: details of the cost formula, as the HAL page was not readable.
- **[interpretation]** Our finding "product closure helps only on synthetic grids" fits: products are *one* special parametrised macro (interface = the two factors), not a general one.

## 4. Library learning and anti-unification (the programming sister)

- **[established]** DreamCoder (Ellis et al.), Stitch (Bowers et al.), Babble (Cao et al.): *abstractions* are λ-terms with holes ("macros"), found by anti-unification (Babble: on e-graphs) and scored by compression/MDL. This is the closest analogue: abstraction = macro with parameters; application = insertion.
- **[established]** Term-graph anti-unification (Baumgartner et al., FSCD 2018) computes the most specific common generalisation of term graphs - formally our "pattern from two occurrences with holes at the differences".
- **[established, now read in full text]** ten Cate-Dalmau-Funk-Lutz, *Extremal Fitting Problems for Conjunctive Queries* (arXiv 2206.05080v3): the direct (categorical) product of two instances is the greatest lower bound in the homomorphism preorder (Prop. 2.7: projections + universal property). If any fitting query exists, the canonical query of the product of all positive examples is a fitting one (Thm 3.3); it is the (strongly/weakly) *most-specific fitting* query (intro characterisation: q is most-specific iff the product of the positive examples maps to I_q). This is the well-known role of the product as *least general generalisation*. Dually, the disjoint union is the least upper bound (coproduct).
- **Limits/caveats [established]:** (i) it is about *homomorphism* semantics on relational structures/CQs, not our embedding/subgraph semantics. (ii) The product must be a "data example" (distinguished elements must occur; Ex. 2.6). (iii) The size grows multiplicatively (exponentially in the product of many examples); the paper itself notes that the naive candidate UCQ does not "compress or generalise" (p. 15) - for compression the *core* of the product would be relevant, not the product itself.
- **[interpretation, correction to my first version]** Our product closure is *not* a special case of this: the same operation (× in the presheaf category), but a different role. We multiply *factor patterns* (grid = path × path) to generate a larger pattern; ten Cate et al. multiply *examples* to extract their commonality. For macros with holes the latter is the relevant one: lgg(window₁, window₂) = the pattern into which both occurrences map, the deviations are the holes. Pushout = "unification" remains my duality reading (the source speaks of coproduct/product, not of pushouts).

## 5. Category theory

**Rewriting.**
- **[established]** Double-pushout (DPO) rewriting on adhesive categories: rule L <- K -> R; K is the *interface* that is preserved. Application = two pushouts. Hyperedge replacement is the special case in hypergraphs (Pshenitsyn uses this for the hypergraph Lambek grammars).
- **[established]** *Structured cospans* (Cicala): open systems/graphs as cospans A -> X <- B with boundary A, B; composition = pushout. A macro with k holes is an object with k boundary points, insertion is composition.
- **[established]** Hypergraph categories / cospan algebras (Fong-Spivak): cospans of finite sets form the free hypergraph category; a graph with interface = morphism. Compact vocabulary for "glue": the pushout composition we implemented is composition in Cospan(FinSet)-like categories.

**Exponential objects.**
- **[fact, standard]** Presheaf topoi are cartesian closed: (B^A)(c) = Hom(y(c) × A, B). Exactly this product × appears in our product closure.
- **[established]** Vigna: explicit description of exponentials in the topos of (directed, multi-)graphs (presheaves on the category • ⇉ •). An element of B^A is a "graph homomorphism with parameter c". Vigna does *not* connect this to macros/compression.
- **[established]** Fiore-Plotkin-Turi (Abstract Syntax and Variable Binding): presheaf category Set^F with context extension δ (adjoints), exponentials for binding. There a "term with a free variable" *is* an element of δ(X) - the mathematical original of "macro with hole" in syntax.
- **[established]** Pshenitsyn: hypergraph Lambek calculus HL with residuals (÷) and a "!" modality. **Note:** he does not formulate it category-theoretically (no CCC connection); the residuals play the role of "hypergraph with a hole that must be completed".
- **[interpretation, core thesis]** *Currying reading of macros*: a macro with a hole of sort A in an environment B corresponds to an arrow A -> B (resp. an element of B^A); insertion = evaluation ev: B^A × A -> B. A macro *without* a hole is a point 1 -> B. The learning task "find good macros" becomes "find a family of arrows with which the data can be written as an evaluation composition". Pushout gluing (our state) is the *colimit part*; the exponential part only comes when interfaces become typed and insertions higher-order (macros in macros).
- **[interpretation, caution]** The cospan reading (interface = boundary) and the exponential reading (interface = argument) are **not identical**. Cospans live in a compact closed/hypergraph structure (argument and result symmetric, no real functionality); exponentials are asymmetric. For graph compression the cospan reading is the directly applicable one; the exponential reading is the more elegant, but so far not exploited in the compression literature (**nothing found**).

## 6. Conclusion: what role does the macro idea play?

1. In compression practice (gRePair, SUBDUE, library learning) macros with interfaces are standard. Pure "holeless" patterns are the exception. In this respect the step to macros with holes is not a unique selling point but catching up with the state of the art - the gain is therefore to be expected rather *against our current glue* than against gRePair.
2. Possible unique selling point: a *uniform* frame (presheaves: colimit for gluing, × and exponential for parametrising and insertion) instead of separate heuristics. That is a theory hypothesis; I found **no** source that formulates graph compression in this language.
3. Relation to the earlier results: c6288 gate level (gluing beats growing by 23-25%) and cell level are cases where instances differ in *attachments*, not in shape - exactly where an interface macro should save (cells with k ports, instance cost k instead of n_nodes pointers).

## 7. Proposed tests (A: lab notebook 4c; B: 4f/4g; C: 4h; all carried out)

- **Test A (interface costs):** same `glue` learner, but patterns with interface: instance cost only external nodes (the rest is implicitly allocated "fresh", connection only via ports). Question: how many bits does this save on c6288 (gate and cell level) and streets? This tests whether the gain comes from interface typing. Cheap, uses existing code.
- **Test B (anti-unification):** pattern = lgg of two windows (product of two windows, then take the core; mind the hom semantics); holes = deleted/different node labels. Question: gain with noisy repetitions (e18 noise sweep).
- **Test C (higher-order):** macro contains a nonterminal (recursion à la Kukluk et al.), e.g. n-bit adder chain. Most expensive test, only after A/B.

## 8. Verification status (short)

| Statement | Status |
|---|---|
| gRePair = SL-HR, digram replacement, rank | abstract/search read; details of digram selection **[unverified]** |
| DreamCoder/Stitch/Babble = abstraction via (anti-)unification | established (abstracts); MDL details of DreamCoder **[unverified]** |
| Product = glb in hom order = most-specific fitting CQ (ten Cate et al.) | **established** (full text: Prop. 2.7, Thm 3.3, intro); transfer to embedding semantics/compression is interpretation |
| GraphMDL+ ports | read as a mention only |
| Aguiñaga et al. (CIKM 2016) | search hit only, not read |
| Pshenitsyn: no CCC connection | established |
| Macro ≈ cospan / evaluation ≈ ev | **own interpretation** |

## Sources
- gRePair / SL-HR grammar compression (Maneth et al.), via search
- Pshenitsyn, Hypergraph Lambek calculus (HL), expressiveness/DPO relation
- Fong & Spivak, Hypergraph Categories
- Cicala, Rewriting structured cospans
- Vigna, A guided tour in the topos of graphs
- Fiore, Plotkin, Turi, Abstract Syntax and Variable Binding (via arXiv 2505.24812 as secondary source)
- Ellis et al., DreamCoder; Bowers et al., Stitch; Cao et al., Babble
- Baumgartner et al., Anti-unification for term graphs (FSCD 2018)
- Koutra et al., VoG
- Kukluk, Holder, Cook, Inference of node replacement recursive graph grammars
- ten Cate & Dalmau (arXiv 2206.05080v3, full text read)
- Aguiñaga et al., arXiv 1608.03192 (not read)
