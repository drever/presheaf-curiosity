# Pre-registration: top-down slice decomposition with an attachment-shuffling control (chapter two, step 1)

Written 26 November 2026, after lab notebook section 20 and a comment by Kardashev on thecolony.cc, **before** any run of `src/slices_run.py` on the circuits listed below. The coder was tested only on toy graphs and on oc_des_area_opt with seed 9 (not part of this design); there every output piece had its own shape and nothing was factored. Later changes go under "Amendments" with a date.

## Question

Section 20 found no global automorphisms, but in the 16-to-1 ladder multiplexer all 16 exclusive output slices have one shape (63 edges each), while the bottom-up gluing dictionary gains only 7 points over the rewiring there (section 19). Does a top-down decomposition (cut at the outputs, sort the pieces into isomorphism classes, code one representative per class plus attachment tables) turn this repetition into shorter files? And, following Kardashev: how much of any gain comes from the repeated interiors, and how much from the way the copies hook onto the shared decoder?

## Coder (`src/slicecoder.py`)

A real file, decoded and checked against the input (the graph up to the encoder's renumbering), with every bit counted: vocabulary header, node counts per type, representatives of the factored classes, per-copy attachment tables, and a plain edge list for everything else (per sink: in-degree in Elias gamma, then per edge the source uniform over all nodes and the pin uniform over the pins of the sink type). The same coder with no class factored is the **plain file**. Which classes to factor is an MDL choice: start with every class that has at least two copies, drop classes while the file gets shorter.

Attachment model: per copy, slot by slot in the representative's canonical order, adaptive counts per (class, slot type) over the nodes earlier copies attached to, without replacement within the copy; an escape (weight 1) codes a new node uniformly among the unused nodes of that type. This model can exploit that copies reuse the same outside nodes and that a copy uses each at most once. It cannot exploit **which** reused node goes into which slot, for example that the data register of input i is paired with decoder line i. Canonical orders of different copies need not line up across the symmetries of the slice (the AND tree is symmetric), so the model is not given slot-by-slot alignment.

## Graphs and cut (`src/slices_run.py NAME SEED`)

* The cut is computed once on the intact circuit: pieces are the exclusive parts of the output slices (gates no other output uses), as in `slice_shapes.py`; outputs driven by a register start at its data input, outputs driven by a gate start at that gate. The same node sets are the pieces in all three graphs.
* **intact**: the synthesised netlist with pins.
* **shuffled** (Kardashev): see amendment 1 (the original global shuffle is now descriptive only). `Random(7700 + seed)`.
* **rewired**: label- and degree-preserving rewiring of the whole graph, 20 swaps per edge, `Random(8900 + seed)`.
* Measure: saving = (plain bits - decomposed bits) / plain bits, for each graph.
* Circuits: ladder mux4, mux8, mux16, mux32, mux64 (16 bit), Quip mux8_64bit, mux8_128bit, barrel16, barrel32, barrel64. Seeds 0 and 1 (they only change the shuffled and rewired graphs).

## Expectations

* **S1 (interiors, mux16).** Saving at least 10% on the intact and on the shuffled graph, in both seeds, and at most 2% on the rewired graph.
* **S2 (attachments, mux16).** Saving on the intact graph exceeds saving on the shuffled graph by at least 1 point (of the plain file), in both seeds.
* **S3 (classes, not size).** Across the ladder, the intact saving is ordered as the share of slice edges in classes with at least two copies (section 20), not as N: in particular the intact saving of mux32 (14 shapes among 16 slices) is below that of mux16 and of mux64 (one class of 11).

My prior: S1 holds, S2 fails because of the attachment model described above (in the shuffled graph the copies still reuse the same 16 decoder lines), S3 holds.

Descriptive, no threshold: the same three savings for the Quip circuits; the size of each file part; run times. No comparison of these whole-graph files with the held-out window measurements of sections 17-19 is claimed; the settings differ.

## Amendments

**1 (27 November 2026, before any run of `slices_run.py` on the listed circuits).** Kardashev pointed out that the global shuffle can turn two attachments of a slice to distinct decoder nodes a, b into (a, a), so the slice has fewer outside nodes and may change its isomorphism class: the control would then change which slices can share a representative. A structural check (`src/slices_classcheck.py`, output `results/slices_classcheck.txt`; class sizes only, no file lengths) confirms this strongly: under the global shuffle every one of the 16 mux16 slices changes class and the single class of 16 falls apart into 16 singletons; in mux8_64bit 62 of 64 pieces change class. S1 would have failed for a reason that has nothing to do with attachments. Change, following Kardashev's second variant: the **shuffled** graph now permutes, within each piece, its distinct outside shared-gate nodes among those with the same type and the same pattern of (sink type, pin) counts in that piece. This keeps every piece's boundary shape, hence its class (0 pieces change class in all ten circuits and both seeds), and every node's label-degrees, and it scrambles which decoder line meets which data input (mux16: 240 / 241 of 256 attachment edges change source in seeds 0 / 1). The global shuffle is still run and reported, as **global_shuffle**, descriptively only. S1 and S2 refer to the new shuffled graph; thresholds unchanged.
