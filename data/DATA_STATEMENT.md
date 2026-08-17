# Data statement

## What is released

`data/public/operating_points.csv` is the **public validation table**. It is
released so that the code in this repository can be executed and checked.

Columns: `source_temperature`, `source_temperature_c`, `mean_pressure`,
`engine_speed`, `power`, `efficiency`.

Power is in watts. Efficiency is a fraction (not percent).

## What is not released

Raw laboratory logs, the remaining operating collection, the full solver
oracle table, multi-hour campus dispatch traces, and industrial heat-source
metering are **not** in this repository.

## How to obtain the remaining data

The remaining research data are **available on request** for non-commercial
academic use.

Commercial use, redistribution, model training for a product, or scraping of
on-request records is **not permitted**.

## How to interpret validation metrics

Numbers written to `results/metrics.json` after `python run_pipeline.py`
confirm that the code path executes. They describe this public run.

The procedure is in [`docs/validation.md`](../docs/validation.md).
