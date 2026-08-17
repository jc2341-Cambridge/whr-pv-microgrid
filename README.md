# Physics-guided WHR–PV–storage microgrid pipeline

Companion code for an IEEE Transactions on Industry Applications (TIA) style
study of **waste-heat recovery (WHR)** Stirling units coupled to a
**PV–storage microgrid**.

The numerical authority is experimental / solver-labelled operating data and a
physics reviewer. Language-model agents, when used, **propose and rank
operating cases**. They do **not** generate power or efficiency labels.

This public repository ships a **30% stratified subset** (36 of 120 operating
points) so the pipeline can be executed and audited. The complete research
dataset is **available on request** and **may not be used for commercial
purposes**. See [`DATA_USE.md`](DATA_USE.md) and
[`data/DATA_STATEMENT.md`](data/DATA_STATEMENT.md).

---

## What this repository claims — and what it does not

| Supported | Not claimed |
|---|---|
| A closed, inspectable loop: data → physics review → bootstrap surrogate → agent ranking → confidence-aware dispatch | That the public-subset MAE/MAPE equals the manuscript table |
| That coupling of charge/discharge-style storage with WHR output is an operational control problem, not a separable greedy rule | Wall-clock superiority over a commercial EMS |
| That LLM/agent output is an auditable JSON protocol | That an LLM is a thermodynamic oracle |
| That a 36-point release is enough to **run** the code | That 36 points replace the 120-point study grid |

Reviewers and automated agents should treat `results/metrics.json` from a
public run as a **smoke-test artefact**, not as a citation number.

---

## Repository tree

```text
whr-pv-microgrid/
├── README.md                 This file
├── LICENSE                   MIT for source code only
├── DATA_USE.md               Non-commercial data terms
├── CITATION.cff
├── requirements.txt
├── run_pipeline.py           One-command public demonstration
├── data_loader.py            Public CSV I/O and deterministic split
├── physics_constraints.py    Bound / monotonicity reviewer
├── surrogate_models.py       Bootstrap polynomial ridge ensemble
├── agents.py                 Propose → review → score → label
├── llm_protocol.py           Machine-readable agent schema and trace
├── microgrid_dispatch.py     Weekly-commitment WHR–PV–storage policy
├── make_figures.py           IEEE-style PNG/PDF writers
├── data/
│   ├── DATA_STATEMENT.md     What is released vs withheld
│   └── public/
│       └── operating_points.csv   36 / 120 stratified points
├── docs/
│   └── reproducibility.md    Seeds, claim boundary, reviewer checklist
├── tests/
│   └── test_smoke.py         No-network unit checks
├── results/                  Created by run_pipeline.py (gitignored)
└── figures/                  Created by run_pipeline.py (gitignored)
```

---

## Method in one page

1. **Operating evidence.** Each row is a `(T, p, N)` point with power (W) and
   efficiency (fraction). The public file is a sub-grid of three heater
   temperatures, three pressures, and four speeds.
2. **Split.** `sparse_active_learning_split` holds out interior points, keeps a
   coarse **baseline** training set, and treats all non-holdout points as an
   **oracle pool**. Holdout never enters fitting.
3. **Surrogate.** A bootstrap polynomial-ridge ensemble predicts power and
   efficiency jointly and returns an epistemic standard deviation.
4. **Agents.** A proposer samples the box; the physics reviewer drops
   out-of-bound points; a critic ranks sparsity + uncertainty; a **solver-label
   agent** (inverse-distance on the oracle pool in this public demo) writes
   numeric labels. The LLM protocol in `llm_protocol.py` records *why* a region
   was proposed. It does not write `power` or `efficiency`.
5. **Dispatch.** Daily synthetic PV, load, and waste-heat traces feed a
   confidence-aware policy: residual load is tracked while a penalty on
   surrogate uncertainty discourages over-confident WHR set-points. Storage SOC
   is updated with a power limit. PV/load traces are **synthetic**, not metered.

The public demo uses a lighter ensemble (`n_estimators=40`, `degree=2`) so a
reviewer laptop finishes in minutes. The manuscript study uses the full grid
and a denser ensemble.

---

## Quick start

Python 3.10+ recommended.

```bash
python -m pip install -r requirements.txt
python tests/test_smoke.py
python run_pipeline.py
```

Expected artefacts:

- `results/metrics.json` — public-subset diagnostics plus an explicit caveat
- `results/llm_agent_trace.json` — protocol and top-ranked case reasons
- `figures/fig01_*.png` … dispatch figure (names follow `make_figures.py`)

---

## Data policy (read this before citing numbers)

- **Released:** 36 operating points, 30% of the 120-point study grid.
- **Withheld:** the other 84 points, raw logs, full RK4 oracle, 8760 h campus
  traces.
- **Complete dataset:** made available **on request** to the corresponding
  author for academic review and non-commercial research only.
- **Commercial use is not permitted** for any research data associated with
  this study, including the public subset if it is extracted from the paper
  context and reused as a product.

If you are an IEEE TIA reviewer and need the full grid to check a table, email
the corresponding author. Do not treat this GitHub/public tree as the archival
dataset.

---

## Design choices a careful reviewer should see

- **Labels ≠ language model.** `SolverLabelAgent` and the oracle pool are the
  only sources of `power` / `efficiency` for new queries.
- **Hard constraints stay classical.** Temperature, pressure, speed, and
  efficiency bounds are enforced by `PhysicsConstraintAgent`, not folded into a
  single unconstrained loss.
- **Storage is coupled.** Dispatch commits pressure and speed for a week and
  then moves SOC. A separable “discharge the peak hours only” rule is not the
  controller.
- **Public metrics are not paper metrics.** `run_pipeline.py` writes this
  caveat into `metrics.json` on every run.

---

## Citation

Please cite the IEEE TIA manuscript when using the method. Use `CITATION.cff`
once the paper has a DOI. Until then, cite this repository and the author
list on the manuscript title page.

---

## Licence

- Source code: MIT (`LICENSE`).
- Data files under `data/`: [`DATA_USE.md`](DATA_USE.md) (non-commercial,
  complete set on request).
