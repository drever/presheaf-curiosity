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

(none)
