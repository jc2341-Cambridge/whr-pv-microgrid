# Physics-guided WHR–PV–storage microgrid pipeline

Companion code for an IEEE Transactions on Industry Applications (TIA) style
study of **waste-heat recovery (WHR)** Stirling units coupled to a
**PV–storage microgrid**.

The numerical authority is experimental / solver-labelled operating data and a
physics reviewer. Language-model agents, when used, **propose and rank
operating cases**. They do **not** generate power or efficiency labels.

This repository releases **part of the operating-point table for code
validation**. The remaining research data are **available on request** and
**may not be used for commercial purposes**. Follow the
[validation guide](docs/validation.md). Data terms are in
[`DATA_USE.md`](DATA_USE.md) and
[`data/DATA_STATEMENT.md`](data/DATA_STATEMENT.md).

---

## What this repository claims — and what it does not

| Supported | Not claimed |
|---|---|
| A closed, inspectable loop: data → physics review → bootstrap surrogate → agent ranking → confidence-aware dispatch | That public validation MAE/MAPE equals the manuscript table |
| That coupling of charge/discharge-style storage with WHR output is an operational control problem, not a separable greedy rule | Wall-clock superiority over a commercial EMS |
| That LLM/agent output is an auditable JSON protocol | That an LLM is a thermodynamic oracle |
| That the public table is sufficient to **validate** the code | That the public table is the archival study collection |

Treat `results/metrics.json` from a public run as a **validation artefact**,
not as a citation number.

---

## Repository tree

```text
whr-pv-microgrid/
├── README.md                 This file
├── LICENSE                   MIT for source code only
├── DATA_USE.md               Non-commercial data terms
├── CITATION.cff
├── requirements.txt
├── run_pipeline.py           End-to-end validation run
├── data_loader.py            Public CSV I/O and deterministic split
├── physics_constraints.py    Bound / monotonicity reviewer
├── surrogate_models.py       Bootstrap polynomial ridge ensemble
├── agents.py                 Propose → review → score → label
├── llm_protocol.py           Machine-readable agent schema and trace
├── microgrid_dispatch.py     Weekly-commitment WHR–PV–storage policy
├── make_figures.py           IEEE-style PNG/PDF writers
├── data/
│   ├── DATA_STATEMENT.md     Released versus on-request data
│   └── public/
│       └── operating_points.csv   public validation table
├── docs/
│   ├── validation.md         How to validate the code
│   └── reproducibility.md    Seeds and claim boundary
├── tests/
│   └── test_smoke.py         Offline unit checks
├── results/                  Created by run_pipeline.py (gitignored)
└── figures/                  Created by run_pipeline.py (gitignored)
```

---

## Method in one page

1. **Operating evidence.** Each row is a `(T, p, N)` point with power (W) and
   efficiency (fraction), spanning heater temperature, mean pressure, and
   engine speed.
2. **Split.** `sparse_active_learning_split` holds out interior points, keeps a
   coarse **baseline** training set, and treats all non-holdout points as an
   **oracle pool**. Holdout never enters fitting.
3. **Surrogate.** A bootstrap polynomial-ridge ensemble predicts power and
   efficiency jointly and returns an epistemic standard deviation.
4. **Agents.** A proposer samples the box; the physics reviewer drops
   out-of-bound points; a critic ranks sparsity + uncertainty. Unused
   released-table rows are queried first and keep their table labels. Off-grid
   proposals, if the pool is exhausted, are labelled by inverse-distance
   interpolation. The LLM protocol in `llm_protocol.py` records *why* a region
   was proposed. It does not write `power` or `efficiency`.
5. **Dispatch.** Daily synthetic PV, load, and waste-heat traces feed a
   confidence-aware policy: residual load is tracked while a penalty on
   surrogate uncertainty discourages over-confident WHR set-points. Storage SOC
   is updated with a power limit. PV/load traces are **synthetic**, not metered.

---

## Quick start

Python 3.10+ recommended. The full procedure, expected artefacts, and
acceptance checks are in [`docs/validation.md`](docs/validation.md).

```bash
python -m pip install -r requirements.txt
python tests/test_smoke.py
python run_pipeline.py
```

---

## Data policy

- **Released:** part of the operating-point table, for code validation.
- **On request:** the remaining research data, from the corresponding author,
  for academic review and non-commercial research only.
- **Not in this repository:** raw laboratory logs, the full solver oracle, and
  multi-hour campus traces.
- **Commercial use is not permitted** for research data associated with this
  study.

If you are an IEEE TIA reviewer and need the study collection to check a
table, email the corresponding author. Do not treat this public tree as the
archival dataset.

---

## Design choices a careful reviewer should see

- **Labels ≠ language model.** `SolverLabelAgent` and the released table are
  the sources of `power` / `efficiency` for new queries.
- **Hard constraints stay classical.** Temperature, pressure, speed, and
  efficiency bounds are enforced by `PhysicsConstraintAgent`, not folded into a
  single unconstrained loss.
- **Storage is coupled.** Dispatch commits pressure and speed for a week and
  then moves SOC. A separable “discharge the peak hours only” rule is not the
  controller.
- **Validation metrics are not paper metrics.** `run_pipeline.py` writes this
  caveat into `metrics.json` on every run.

---

## Citation

Please cite the IEEE TIA manuscript when using the method. Use `CITATION.cff`
once the paper has a DOI. Until then, cite this repository and the author
list on the manuscript title page.

---

## Licence

- Source code: MIT (`LICENSE`).
- Data files under `data/`: [`DATA_USE.md`](DATA_USE.md) (non-commercial;
  remaining data on request).
