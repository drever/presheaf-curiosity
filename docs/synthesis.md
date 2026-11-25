# Synthesis: what the presheaf view of graph compression did and did not deliver (25 November 2026)

This closes the first chapter of the lab notebook (sections 1-18). It adds no new measurement; every number below is in the notebook and the README claims table, with its section given in brackets.

## The question

Graph data can be read as glued together from small local pieces: in sheaf language, a colimit of patterns. On top of plain gluing (E1) the presheaf view offers richer constructions: products, which combine two patterns and so cover combinations never seen (E2a); holes, a frame with an exchangeable filler (E2b, the exponential); and fixpoints, a rule that repeats itself, such as a lattice (E3). The question was whether these constructions buy an honest gain in description length (MDL) on real graphs, and whether the learned dictionary behaves like a basis in the sense of PCA: stable across samples, specific to the data, transferable to similar data. The "curiosity" half asked whether choosing data by predicted learning progress speeds this up.

We never claimed to beat RePair or other grammar compressors, and do not now.

## What holds

* **Gluing finds real, held-out structure in regular circuits.** On held-out halves of the c6288 multiplier, gluing beats our growing variant by 71-86 bits per window, and by at least 71 bits under every edge order tried (8, 9; README claim 2). Growing is a weak baseline by construction, so this says gluing works, not that it beats good miners.
* **The numbers are file sizes, not model estimates.** Gluing, products and holes with subgraph fillers have real encoders and decoders; files are 2-13 bits per window above the computed lengths, all round trips verified, and the differences between models are preserved (11, 16).
* **On a very regular circuit the dictionary does behave like a basis.** On c6288 the working patterns recur across samples and halves (shared use 93-99%), clearly more than on a label- and degree-preserving rewiring of the same circuit (57-86%) (14, 15).
* **On circuits designed by others, gluing still sees structure in some of them.** Barrel shifters, narrow multiplexers and the area-optimised DES beat their rewiring by 10-22 points of the empty file size (17).
* **The higher constructions work where we put the structure in.** In synthetic worlds products generalise to unseen factor pairs, subgraph holes and holes in holes pay off, and lattice rules extrapolate (5-10). These worlds show the learner can find such structure, not that real data have it.

## What is refuted or did not carry over

* **Products and holes on real data.** On streets, c6288, RDF extracts and ten third-party circuits, product closure never selected a factor and holes almost never paid; the one hole found in the Quip circuits made the file longer (5-7, 17).
* **Basis properties beyond c6288.** On the Quip circuits stability was not better than on the rewired control in 6 of 10 circuits, and a dictionary learned on the 16-bit barrel shifter cost 38-61% more on the 32- and 64-bit versions than their own dictionaries (17).
* **The clearest test case.** Wide multiplexers are, by construction, identical bit slices sharing select lines: a product in the plain sense. Gluing does not tell them from their rewiring; larger windows do not change that, and adding the select lines makes the circuits look less structured than their rewiring (18).
* **Curiosity.** Ordering data by predicted gain was not better than random order (12, 13).
* **A comparison we had to withdraw.** Our lead over a RePair re-implementation turned out to depend on the order of edges inside a window; the claim was withdrawn (4, 9).
* **Not dependent on the pre-set thresholds.** Every Quip and window expectation that failed missed its pre-set threshold by a wide margin, or went the opposite way.

## The open gap

In 27 of 36 runs on the multiplexers the largest learned pattern sat at the cap of 12 edges (18). So it is open whether the learner cannot *represent* a whole 32- or 64-input slice, or whether it represents it and still finds no gain. More basically, the learner is bottom-up: it builds patterns from frequent small pieces, and a product can only appear if both factors are first found separately. PCA works the other way, from a global view of all the data. Our negative results are results about this learner, not about the presheaf view as such.

## What we learned about method

* **Use a control that keeps the easy statistics.** A label- and degree-preserving rewiring separated real structure from what label and degree counts already allow. Without it, a steep "spectrum" of pattern use looked like evidence of a basis, and it was not: the rewiring's spectrum was even steeper (15).
* **Report hidden parameters.** Edge order inside a window changed one baseline by a factor of three to four (9).
* **Use held-out splits that keep the kind of data the same.** Our first split was flawed and was withdrawn; synthesised netlists needed a hub-aware split, and where the two regions still differed in label mix we said so (7, 8, 17).
* **Pre-register, and amend in the open.** Thresholds written down before the runs kept the circuit results from being read kindly after the fact; every change is dated in the pre-registration files.
* **Outside review helped.** A pull request repaired the held-out split, and comments on thecolony.cc found the edge-order dependence and the robustness of the gluing-versus-growing result.

## Where a next chapter could start

Instead of finding repeated pieces bottom-up, read product structure top-down from the symmetries of the whole graph. In a wide multiplexer the bit slices can be permuted without changing the graph; the orbits of its automorphism group are the product, found without any pattern search, and a rewired control has almost no symmetry. The question would be how much shorter a file becomes that codes one slice plus the symmetry, against the same for the rewiring: a global decomposition, closer to what PCA does in the linear case. A cheaper step is a pattern cap of 24 or 32 edges on the same three multiplexers, which would close the gap above.
