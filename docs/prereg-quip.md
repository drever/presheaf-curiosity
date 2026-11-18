# Pre-registration: higher-order dictionaries on circuits designed by others (Quip)

Written 18 November 2026, **after** synthesising the circuits and looking only at their sizes and label counts (printed by `python src/quip.py`), **before** any learner was run on them. Later changes go under "Amendments" with a date.

## Question

Do the constructions of the presheaf view (product closure, macros with holes) find structure in real circuits that we did not design, and does it show up in actual file sizes? And do the learned patterns behave like a basis (stable across halves, clearly better than on a structureless graph with the same labels and degrees)?

## Data

Ten Quip circuits from `ispras/hdl-benchmarks` (Altera and OpenCores designs, LGPL/FIP licences): barrel shifters barrel16/32/64, multiplexers mux8_64bit, mux8_128bit, mux32_16bit, mux64_16bit, AES core (oc_aes_core), DES (oc_des_area_opt, oc_des_perf_opt). Synthesised with Yosys 0.71 (yowasp-yosys), default `synth -flatten -top NAME`, nothing tuned (`scripts/synth_quip.sh`). Graph as for ISCAS: node per cell and primary input, edge per driven cell input, label = (driver type, sink type). 1,613 to 30,795 edges, 15 to 140 labels.

A residual home advantage is acknowledged: the synthesiser may itself produce regular structure; it is a third-party tool run with default settings.

## Procedure (per circuit, seeds 0 and 1)

* Split with `split.gate_walk_split` (no walk through inputs) into regions A and B. 40 training windows from A, 100 test windows from B, 20 nodes each (`windows_from`). R = max(64, number of labels).
* Models, all learned on the training windows only:
  * **gluing**: `learn_h`, mode hier, maxe 12, dictionary limit 40;
  * **product closure**: `learn_prod_auto` with the gluing dictionary as D0, size cap 24;
  * **holes**: `holes2.refine`, interface costs, maxF 5, 2 rounds, dictionary limit 40.
* All test windows written with `coder2` in mode `boundary`, decoded and verified. Reported: data bits per test window from the file, dictionary bits from the file. "Empty" = the same coder with an empty dictionary.
* **Control:** the same circuit after label- and degree-preserving rewiring (`basis.rewire`, 20 swaps per edge), same split and window procedure, gluing only.
* **Stability:** a second gluing dictionary learned on 40 windows of B; shared use = share of the covered edges of the test windows that the A-dictionary covers with patterns that also occur in the B-dictionary (as in lab notebook section 14), for the circuit and for the control.
* **Size family:** the barrel16 gluing dictionary (seed 0) used to code 100 windows of barrel32 and barrel64, against their own dictionaries.

## Expectations (directions and thresholds fixed now)

* **P1** Gluing compresses every circuit clearly better than its rewired control: the share of the empty file that remains is lower by at least 10 percentage points, in every circuit and seed.
* **P2** Product closure: selects factors in at most 2 of the 10 circuits, and nowhere saves more than 5% of the gluing file (data part) on the test windows.
* **P3** Holes: found in at least one circuit; nowhere saves more than 5% of the gluing file. If anywhere, then in the AES or DES circuits (repeated S-boxes) or the multiplexers.
* **P4** Stability: shared use is higher on the circuit than on its control, in at least 8 of 10 circuits (seed 0).
* **P5** Size family: coding barrel32 and barrel64 with the barrel16 dictionary costs at most 10% more data bits per window than with their own dictionaries.

These are priors, not hopes: P2 and P3 expect the presheaf constructions to contribute little on real circuits, as on streets and c6288.

## Amendments

* **18 November 2026, before any result was seen.** The first runs hung in the subgraph matcher (`und.embed_u`): windows of these circuits contain many identical edges at high-fan-out nodes, and the backtracking search explodes (no output after 18 minutes for the smallest circuit). An opt-in step budget was added (`und.EMBED_BUDGET`, default off, so every earlier result is unaffected); `quip_run.py` sets 2,000 steps per embedding attempt. An attempt that exceeds the budget counts as "no embedding": the learner may then miss some instances, and the files stay lossless but can only get longer. Measured on barrel16 seed 0 (learning time only): budget 2,000 -> 146 s and 18 patterns, budget 500 -> 47 s and 16 patterns. Star patterns with more than 6 identical edges at one node are skipped as before (`und.TWIN_MAX = 6`).
* **18 November 2026, second amendment, after the first two results.** The first two finished runs (mux8_64bit and mux32_16bit, seed 0; kept in `results/quip_first_split/`) showed a gluing file on the test windows exactly as long as the empty file: the dictionary from region A did not apply to region B at all, while it compressed the rewired control. The cause is the split, not the learner, and it is the same defect Reticuli found for c6288 with the inputs: in these synthesised circuits select, enable and register nets fan out to hundreds of gates, so the single walk of `gate_walk_split` collects whole functional blocks. Measured without any learner (label mix of the two regions, total-variation distance; seed 0): 0.51-0.89 for the barrel shifters and multiplexers, region B in 7-136 pieces. New split `split.hub_walk_split`: nodes with more than 8 outgoing edges are treated like inputs (their fan-out edges belong to neither region, the walk does not pass through them). This gives distances of 0.01-0.08 for barrel shifters and multiplexers; 22-40% of the edges are left out. For AES and DES the distance stays at 0.23-0.43 with either split: a contiguous half of these circuits is a different functional block (key schedule, rounds); their results will be reported with that distance next to them, and they are not counted as same-kind held-out tests. All runs are repeated with the new split; nothing else changes.
