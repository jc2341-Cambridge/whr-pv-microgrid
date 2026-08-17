# Data statement

## What is released

`data/public/operating_points.csv` contains **36 of 120** study operating points
(exactly 30%). The subset is a stratified sub-grid:

| Axis | Released levels | Full-study levels (not released) |
|---|---|---|
| Source temperature / K | 773.15, 923.15, 1073.15 | same three levels |
| Mean pressure | 1500, 2500, 3000 | 1500, 2000, 2500, 2800, 3000 |
| Engine speed / rpm | 400, 700, 1000, 1300 | 400, 550, 700, 800, 900, 1000, 1100, 1300 |

Columns: `source_temperature`, `source_temperature_c`, `mean_pressure`,
`engine_speed`, `power`, `efficiency`.

Power is in watts. Efficiency is a fraction (not percent).

## What is not released

The remaining 84 operating points, any raw laboratory logs, the full RK4
oracle table, 8760-hour campus dispatch traces, and industrial heat-source
metering are **not** in this repository.

## How to obtain the complete dataset

The complete research dataset is **available on request** from the corresponding
author for non-commercial academic review and reproduction of the IEEE TIA
manuscript only.

Commercial use, redistribution, model training for a product, or scraping of
the withheld records is **not permitted**.

## How to interpret public-subset metrics

Numbers written to `results/metrics.json` after `python run_pipeline.py` verify
that the code path executes. They are **not** the manuscript headline KPIs.
Do not cite public-subset MAE/MAPE as the paper result.
