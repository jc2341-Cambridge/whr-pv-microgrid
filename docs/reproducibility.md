# Reproducibility note for reviewers

## Intended claim of this repository

This package reproduces the **method**, not the manuscript's full numerical
table. The public CSV is a small example set so the code can be run. Headline
MAE, annual energy, and complementarity figures in the IEEE TIA submission use
the complete research set, which is available on request for non-commercial
academic use.

## Fixed seeds

| Object | Seed |
|---|---|
| Baseline surrogate | 21 |
| Augmented surrogate | 22 |
| Candidate proposer | 7 (in `CandidateProposerAgent`) |
| Synthetic daily profiles | 17 |

## What a successful public run shows

1. The physics reviewer admits only in-bound candidates.
2. The critic ranks candidates by sparsity and bootstrap uncertainty.
3. Labels for newly selected points come from the released operating-point
   table when the critic queries an unused public-grid row, otherwise from
   the inverse-distance proxy. They never come from an LLM.
4. The dispatch loop commits a weekly (pressure, speed) pair and updates
   storage SOC.

## What a successful public run does **not** show

- That public-example MAPE equals the paper.
- That the synthetic London-like PV/load traces are metered.
- That the public label path is a full second-order Stirling integration.
  Unused released-grid rows keep their table values. Off-grid proposals, if
  any, use inverse-distance labels so the loop stays closed without the
  withheld records.
