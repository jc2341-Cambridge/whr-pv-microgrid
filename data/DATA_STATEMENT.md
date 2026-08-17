# Data statement

## What is released

`data/public/operating_points.csv` is a **small public example set** so that
the pipeline can be executed and audited. It is not the full research
collection used in the manuscript.

Columns: `source_temperature`, `source_temperature_c`, `mean_pressure`,
`engine_speed`, `power`, `efficiency`.

Power is in watts. Efficiency is a fraction (not percent).

## What is not released

Raw laboratory logs, the complete operating collection, the full solver
oracle table, multi-hour campus dispatch traces, and industrial heat-source
metering are **not** in this repository.

## How to obtain the complete dataset

The complete research dataset is **available on request** from the
corresponding author for non-commercial academic review and reproduction of
the IEEE TIA manuscript only.

Commercial use, redistribution, model training for a product, or scraping of
withheld records is **not permitted**.

## How to interpret public-example metrics

Numbers written to `results/metrics.json` after `python run_pipeline.py` verify
that the code path executes. They are **not** the manuscript headline KPIs.
Do not cite public-example MAE/MAPE as the paper result.
