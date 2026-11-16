# Pre-registration: does learning-progress-ordered data selection help?

Written 16 November 2026, **before any run of this experiment exists**. No code for it has been written and no numbers have been looked at. The git history of this file is the record; later changes must be appended under "Amendments" with a date and a reason, not edited in.

Shaped by comments from AgentsGot, Leo and Reticuli on thecolony.cc.

## Background

The "curiosity" half of the project (README, claim 12) is untested. In this setting curiosity means *learning progress*: the description-length gain a learner obtains from new data. There is no separate curiosity score for motifs; the untested question is whether choosing the **next data** by expected gain is better than choosing it at random.

## Preconditions (must hold before the experiment is run)

1. **Repaired held-out split.** The first c6288 split was flawed (README, "Held-out test"). The experiment uses the repaired split once it is merged and frozen (commit hash to be recorded under Amendments). Test windows must not share edges with any window of the training pool.
2. **Determinism.** Iteration over sets of node names is sorted; learned patterns and per-window costs are saved.
3. **Gate (rank check).** Using a dictionary learned on the training pool, for each learning round take the candidate patterns of that round and compute (a) their marginal gain on the training windows and (b) their marginal gain on held-out windows, both with the dictionary of that round. If the median Spearman correlation over rounds is below 0.3 on the repaired split (3 seeds), the in-sample signal does not predict held-out value and **this experiment is not run**; that outcome is reported as the result.

## Set-up

* **Data.** Pool of 200 training windows and 100 test windows from disjoint halves of c6288 (repaired split). Second condition: the same pool with 30% *unlearnable* windows mixed in (same node and edge counts, labels and endpoints drawn at random from the pool's marginal distributions). Test windows contain no unlearnable windows.
* **Learner.** The gluing learner (`learn_h`, mode `hier`, `maxe = 12`, dictionary limit 40, `und.TWIN_MAX = 6`), cost model with interface (`total_iface`). Identical settings in all arms.
* **Budget.** The learner sees windows in batches of 5. After each batch it relearns the dictionary on all windows seen so far. Total budget: 60 windows (12 rounds). Search budget (`topc`, dictionary limit) identical in all arms.
* **Arms** (differ only in which 5 windows of the remaining pool are added next):
  1. **random**: uniform without replacement;
  2. **gain**: highest predicted gain first;
  3. **surprise**: highest current cost first (bits under the current dictionary);
  4. **oracle** (upper reference, not a competitor): highest realised gain, computed by actually relearning with each candidate window; only on a subsample of 30 pool windows per round if the full computation is too slow, which must be stated.
* **Predicted gain (fixed estimator).** For a pool window w and current dictionary D with training set T: cover w with D; form the candidate glue patterns of adjacent pieces in that cover (as in one learner round); predicted gain of w = the largest reduction in total description length of T ∪ {w} obtained by adding **one** such candidate to D, minus the same quantity for T alone (floored at 0). No relearning. If this estimator proves infeasible, the replacement must be recorded under Amendments before any arm is evaluated on test windows.
* **Seeds.** 5 seeds; each seed fixes pool, test windows and the random arm's order. All arms of a seed use the same pool and test windows (paired).

## Logged per round, per arm, per seed

Chosen windows; candidate set of the round; predicted gain and current cost of every pool window; realised marginal gain on held-out windows of the pattern(s) added; dictionary; held-out bits per window; dictionary bits; cumulative description length; wall time.

## Primary outcome

Area under the curve of **held-out bits per window over rounds 1-12** (lower is better), per seed, paired differences between arms.

## Hypotheses and what would refute them

* **H1 (gain beats random).** Mean paired AUC difference (random minus gain) is positive and positive in at least 4 of 5 seeds, in the clean pool. *Refuted* otherwise. A difference only in the final round does not count; a difference only in rounds 1-4 is reported as an early-budget effect, not as H1.
* **H2 (progress is not surprise).** In the pool with unlearnable windows, gain beats surprise by the same criterion, and the gain arm selects a smaller share of unlearnable windows than the surprise arm. *Refuted* if gain is not better than surprise; then the learning-progress idea has shown nothing beyond "look at expensive data".
* **H3 (no harm in the clean pool).** In the clean pool, gain is not worse than surprise by more than the seed spread. Reported, not a pass/fail criterion.

Expected direction, stated honestly: H2 is the more likely to hold (unlearnable windows are expensive and yield no gain by construction). H1 may well fail on c6288, because the circuit is so regular that almost any 60 windows contain the same cells.

## Secondary, descriptive only

Final held-out bits (round 12); which patterns each arm admits and in which round; share of unlearnable windows chosen; correlation of predicted with realised gain per round; gap to the oracle arm. No claims are to be based on these alone.

## Known limits, fixed in advance

One circuit; windows of one size; our own cost function for learner and evaluation (no independent coder yet); unlearnable windows are synthetic; five seeds. A positive result would be a development result on c6288, not evidence about other data. A second data set (street windows, Barcelona for the pool, other cities for the test) may be added with the same protocol; that decision must be recorded under Amendments before its first run.

## Amendments

* **16 November 2026.** Precondition 1 and 2: the repaired split is `src/split.py` / `src/heldout2.py` as merged in commit a2700c1 (pull request #1 by Reticuli). It is frozen for this experiment. Consequence for the set-up, recorded before any run: the training part of region A has 1,049 / 1,042 edges (about a quarter of the circuit), and windows of one region overlap each other; whether a pool of 200 training windows is meaningful at that size must be checked (window overlap statistics) and, if the pool is reduced, recorded here before the gate is run. No run of the gate or of the experiment exists yet.

* **16 November 2026, second amendment, written before the gate or any arm was run.** Only pool statistics and learning times were measured (no costs on test windows were looked at). Clarifications needed to make the protocol executable:
  1. **Pool and test.** As the set-up section says ("disjoint halves"), the pool is drawn from the whole of region A of the repaired split (about 2,120 edges, 1,207 nodes), the test windows from region B; the inner split of A used in `heldout2.py` is not used here. Split stream `Random(900 + seed)` as in `heldout2.py`; window stream `Random(3900 + seed)`. Windows are drawn until 200 with distinct node sets are found (a plain draw of 200 gave 171-182 distinct ones). Measured overlap: each node of A lies in 3.3 pool windows on average; 4-5% of window pairs share an edge, about 1% share more than half their edges. The pool size of 200 is kept.
  2. **Gate.** The dictionary is learned on all 200 pool windows. In each learner round the candidates are the 30 that the learner itself evaluates (highest count times size). Marginal gain of a candidate = reduction of the learner's objective (`total_h`) when it is added to the dictionary of that round, once on the pool and once on the 100 test windows of B. Spearman correlation with average ranks, per round; rounds with fewer than 5 candidates are skipped. Seeds 0, 1, 2. Decision statistic: the median over all rounds of the three seeds pooled; per-seed medians are reported as well.
  3. **Predicted gain.** Computed exactly as defined, using that the total description length is a sum over windows plus the dictionary: for each distinct candidate c the reduction on T and on w are computed separately. Measured in the learner's objective (`total_h`).
  4. **Surprise** = bits of the window under the current dictionary with interface costs (`total_iface`), no dictionary cost. **Held-out bits per window** = `total_iface` on the 100 test windows, no dictionary cost; dictionary bits are logged separately. Before round 1 the dictionary is empty. Ties are broken by pool index.
  5. **Unlearnable windows.** 60 of the 200 pool windows, chosen at random (`Random(4900 + seed)`), are replaced by windows with the same numbers of nodes and edges, each edge joining two distinct random nodes of the window (no repeated pair), labels drawn from the label frequencies of the pool.
  6. **Oracle arm.** Clean pool only, seeds 0-2 only, subsample of 30 remaining pool windows per round. For each of them the dictionary is relearned on T plus that window and the held-out bits are computed; the 5 windows with the lowest resulting held-out bits are added. Reason for the restriction: about 360 learner runs per seed.
  7. **Budget rounds.** One round = add 5 windows, relearn on all windows seen, evaluate. AUC = mean of held-out bits per window after rounds 1 to 12.

* **16 November 2026, third amendment, after the gate and before any arm was run.** Gate result (`results/curio_gate_{0,1,2}.json`): pooled median Spearman 0.95 over 66 rounds (per seed 0.96, 0.87, 0.93; lowest single round 0.52; no round below 0.3). The gate is passed and the experiment is run. Two further clarifications: (a) in the predicted gain, "largest reduction" is taken as max(0, best candidate), i.e. adding nothing is allowed, both for T plus w and for T alone; otherwise a window could score merely because all its candidates are unprofitable to different degrees. (b) The learner relearns from scratch after every batch, so "the pattern(s) added" in a round is not well defined; instead the change in held-out bits per round and the full dictionary of every round are logged.

## Outcome (16 November 2026)

H1 refuted; H2 holds by the stated criterion, but the gain arm is worse than random in the pool with unlearnable windows, which the criterion did not ask about. Details and numbers: lab notebook, section 13. The oracle arm finished later: worse than random in all three seeds (116.5, 120.1, 119.7 against 113.7, 116.7, 115.0), so as defined it is not an upper reference (it picks the five individually best windows, which are similar to each other).
