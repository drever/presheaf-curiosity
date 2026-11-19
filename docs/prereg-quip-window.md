# Pre-registration: why do the wide multiplexers look like their rewiring? (Quip, window size and hub edges)

Written 19 November 2026, after the Quip measurement (lab notebook, section 17) and after looking at the label counts and out-degree histograms of mux8_64bit, mux32_16bit and mux64_16bit, **before** any run of `src/quip_window.py` was inspected. Three timing runs (mux32_16bit seed 0: window 20 without hubs, window 40 without hubs, window 20 with hubs) were started before this file was written to estimate run time; their output was not looked at before this file was committed. Later changes go under "Amendments" with a date.

## Observation that prompts this

In section 17 gluing beats the label- and degree-preserving rewiring by 16-22 points (share of the empty file) on the narrow multiplexers mux8_64bit and mux8_128bit, but by -3 to +5 points on the wide ones, mux32_16bit and mux64_16bit. Judging from label counts and out-degrees, Yosys builds the three we looked at the same way (mux8_128bit was not inspected): a one-hot select decoder whose lines fan out to every output bit (mux8_64bit: 8 lines with fan-out 64; mux32_16bit: 32 lines with fan-out 16; mux64_16bit: 64 lines with fan-out 16), NAND gates combining data and select, and per output bit an AND tree over 8, 32 or 64 inputs, with registers around. In the presheaf view this is a product (output bit x select line) glued along the shared select lines.

## Two hypotheses about the measurement, not about the theory

* **H-W (window size).** A 20-node window holds a whole 8-input slice of mux8 but only a fragment of a 32- or 64-input slice. Fragments of AND trees are almost fixed by labels and degrees, which the rewiring keeps. Larger windows should open the gap to the control for the wide multiplexers.
* **H-H (hub edges).** The hub-aware split (amendment 2 of `docs/prereg-quip.md`) leaves out every edge from a node with fan-out above 8, which removes exactly the select lines along which the slices are glued. Adding those edges back should open the gap.

## Procedure

`python src/quip_window.py CIRCUIT SEED NMAX HUBS`, gluing only, otherwise as `quip_run.py` (40 training windows from region A, 100 test windows from region B, `learn_h` mode hier, maxe 12, dictionary limit 40, `coder2` boundary mode with verified round trip, control = `rewire` with 20 swaps per edge, same split and window procedure).

* Circuits: mux32_16bit and mux64_16bit (wide), mux8_64bit (narrow, comparison). Seeds 0 and 1.
* NMAX (nodes per window) 20, 40, 60; node alphabet NN = NMAX + 11 (31 at NMAX 20, as before).
* HUBS 0: as in section 17. HUBS 1: the regions are defined by the same walk, then every non-input edge whose driver has fan-out above 8 is added to the region that contains its sink. Edges stay disjoint between regions; a hub node can occur in both.
* Run order: all HUBS 0 runs first, then HUBS 1 at NMAX 20, then HUBS 1 at NMAX 40 and 60 as time allows. Limit 3 hours per run; a run that does not finish is reported as not finished.
* Measure: gap = control share of empty minus circuit share of empty (positive = circuit compresses better than its rewiring).
* Check: NMAX 20, HUBS 0 must reproduce the shares of section 17 exactly.

## Expectations

* **W1 (H-W).** For both wide multiplexers and both seeds, gap at NMAX 60 exceeds gap at NMAX 20 by at least 10 points (HUBS 0).
* **W2 (comparison).** For mux8_64bit, gap at NMAX 60 differs from gap at NMAX 20 by less than 10 points in both seeds (HUBS 0).
* **H1 (H-H).** For both wide multiplexers and both seeds, gap at NMAX 20 with HUBS 1 exceeds gap with HUBS 0 by at least 10 points.

My prior is weak for both hypotheses. A known confound, fixed in advance: patterns are capped at 12 edges (maxe 12), so even a 60-node window cannot be covered by one pattern for a whole 32-input slice. If W1 fails, this refutes "window size alone, with the current pattern cap", not the hypothesis that the structure is larger than what the learner can see; a follow-up with a larger cap would need its own pre-registration. With hub edges in the windows, stars of more than 6 identical edges are skipped by the learner (`und.TWIN_MAX = 6`), which may blunt H1.

## Amendments

(none)
