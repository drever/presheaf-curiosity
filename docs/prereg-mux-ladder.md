# Pre-registration: multiplexer ladder with raised pattern cap (reach or no gain?)

Written 25 November 2026, after the window test (lab notebook, section 18) and after a comment by Centaur on thecolony.cc, **before** any run with the seeds used here. Two timing runs on seed 9 (not used below; their results are discarded and only their run times were looked at) were made to size the design. Later changes go under "Amendments" with a date.

## Question

In section 18 the largest learned pattern sat at the 12-edge cap in 27 of 36 runs. Two stories remain:

* **Reach (R).** The learner cannot represent a whole slice of a wide multiplexer; with a cap large enough to hold a slice, the circuit would pull away from its rewiring.
* **No gain (G).** Representing more does not help; the gap to the rewiring does not depend on the cap.

## Circuits: an N-to-1, 16-bit ladder in the Quip style

`scripts/gen_mux_ladder.py` writes N-to-1, 16-bit multiplexers line for line in the style of Quip's mux32_16bit and mux64_16bit (input shift registers, select register, registered case statement) and synthesises them with the same Yosys command. Check: for N = 32 and 64 the generated netlists have exactly the edge and label counts of the Quip originals (3,190 and 6,360 edges). The Verilog is ours, but it reproduces the third-party template; we wrote no structure in.

Size of one output slice (cells used only by that output bit, and the edges into them including the edge into the output register), measured on the synthesised netlists before any learning run:

| N | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|
| cells per slice | 1 (a MUX cell) | 7 | 15 | 31 | 63 | 127 |
| edges per slice | 4 | 16 | 32 | 64 | 128 | 256 |

Consequence noted in advance: at the current cap of 12 edges, only the N = 2 slice fits, and it is built from a different cell type (MUX) than the rest. The narrow Quip multiplexer mux8_64bit already beat its rewiring by 16-19 points with 32-edge slices (section 17), so the simple form of R ("gain only when a whole slice fits") is strained before we start.

## Procedure

`python src/mux_ladder_run.py CIRCUIT SEED NMAX MAXE` = `quip_window.py` with hub edges left out, gluing only, and the pattern cap `maxe` as parameter (pattern node cap MAXN = max(32, MAXE + 1)). Same split, windows, coder (boundary mode, verified round trip) and rewired control as sections 17 and 18.

* Circuits: ladder N = 4, 8, 16 (the slice crosses the cap at every step). N = 2 descriptive only (different cell type).
* Windows of 60 nodes (NMAX 60).
* Caps MAXE 12, 32, 64. A whole slice fits for N = 4 at 32 and 64, for N = 8 at 32 (exactly) and 64, for N = 16 at 64 (exactly).
* Seeds 0 and 1. Time limit 3 hours per run; a run that does not finish is reported as not finished.
* Measure as before: gap = control share of empty minus circuit share of empty, in points.

## Expectations

Let gap(N, c) be the gap at cap c, averaged over the two seeds.

* **L1 (R).** For each of N = 4, 8, 16: gap at the smallest cap that holds a whole slice (N = 4: 32; N = 8: 32; N = 16: 64) exceeds gap(N, 12) by at least 10 points.
* **L2 (G).** For each of N = 4, 8, 16: gap(N, 64) and gap(N, 12) differ by less than 5 points.

L1 and L2 cannot both hold. If neither holds for an N, the result for that N is "cap matters somewhat, below the threshold for R".

Descriptive, no threshold: gap(N, 12) as a function of N (does the lead fall off between N = 8 and N = 16 at fixed cap and window, as between the Quip circuits mux8_64bit and mux32_16bit?); largest learned pattern per run; run times.

My prior: G is more likely than R, because mux8_64bit wins without holding a slice, and because gluing can already cover a slice with several instances of smaller patterns.

## Amendments

**1 (25 November 2026, before any run with seeds 0 or 1).** The first two timing runs (seed 9, caps 32 and 64) did not finish within 50 minutes. A stack dump showed them stuck in pynauty's canonical labelling (`und.canon_u`) of 24-32-edge candidate patterns; on one captured 32-edge pattern the time per call jumped between 0.0001 s and 9 s and beyond 60 s depending on which prefix of edges was used. This is the same family of problem as the 12-leaf star of section 4 (`und.TWIN_MAX`). Fix: an opt-in `und.CANON_UNDIRECTED` that hands nauty the same labelled digraph as an undirected graph (each directed edge a -> b becomes a - w - h - b, with an edge node w coloured by the label and a marker node h for the head). Checks before use: on 800 random small patterns (400 pairs of relabelled copies) both forms induce the same isomorphism classes (0 disagreeing pairs out of about 320,000, 173 classes each); random relabellings of the captured pattern give the same key (0 mismatches), reversing all edges gives a different key; the captured pattern is canonised in under 1 ms at every length. `src/mux_ladder_run.py` sets it; all earlier scripts keep the directed form, so earlier results are unaffected. The smoke tests pass. The timing runs are repeated on seed 9 with the fix.
