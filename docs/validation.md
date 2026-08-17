# Validation guide

This repository releases **part of the operating-point table** so that the
source code can be validated. A successful run shows that the pipeline
installs, splits data, fits the surrogate, records an agent trace, and writes
dispatch and figure artefacts.

The remaining research data are available **on request** for non-commercial
academic use. See [`DATA_USE.md`](../DATA_USE.md) and
[`data/DATA_STATEMENT.md`](../DATA_STATEMENT.md).

## Environment

- Python 3.10 or later
- From the repository root:

```bash
python -m pip install -r requirements.txt
```

No network access is required after the packages are installed.

## 1. Unit checks

```bash
python tests/test_smoke.py
```

A passing run prints `smoke tests passed`. The checks confirm that:

- `data/public/operating_points.csv` loads and has unique `(T, p, N)` rows
- the train / oracle / holdout split is non-empty and disjoint
- a short surrogate fit stays inside the physics bounds (non-negative power;
  efficiency in \([0.40, 0.60]\))
- `PhysicsConstraintAgent` rejects out-of-bound candidates

## 2. End-to-end pipeline

```bash
python run_pipeline.py
```

The script writes:

| Artefact | Role |
|---|---|
| `results/metrics.json` | Validation diagnostics and an explicit caveat |
| `results/llm_agent_trace.json` | Ranked-case protocol (no numeric labels from an LLM) |
| `results/train_cases.csv` | Baseline training rows |
| `results/holdout_cases.csv` | Held-out rows (never used in the fit) |
| `results/agent_selected_cases.csv` | Cases queried from the public table |
| `results/confidence_aware_dispatch.csv` | One-day dispatch on synthetic profiles |
| `figures/*.png` and `figures/*.pdf` | Method and diagnostic figures |

`results/` and `figures/` are generated locally and are not stored in git.

## 3. How to read a successful validation

Open `results/metrics.json` and confirm that:

1. `caveat` is present and states that these numbers are for code validation.
2. `n_train_cases` and `n_holdout_cases` are positive.
3. `baseline` and `agent_augmented` each contain power and efficiency residuals.
4. `method_boundary` records that numeric labels do not come from an LLM.

The residual values in that file are **validation outputs** for this public
run.

## Fixed seeds

| Object | Seed |
|---|---|
| Baseline surrogate | 21 |
| Augmented surrogate | 22 |
| Candidate proposer | 7 |
| Synthetic daily profiles | 17 |

## Method boundary checked by this guide

- Language-model or agent text may propose and rank operating cases.
- Power and efficiency labels come from the released table or, for off-grid
  proposals, from inverse-distance interpolation on that table.
- Device bounds are enforced by the physics reviewer.
- PV and load traces used in dispatch are synthetic.

## What this guide does not certify

- That the synthetic London-like PV and load traces are metered site data
- That the public label path is a full second-order Stirling integration
