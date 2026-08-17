"""Confidence-aware WHR-PV-storage dispatch on synthetic annual profiles."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_loader import FEATURE_COLUMNS, TEMP_K_HI, TEMP_K_LO, TEMP_K_MID


def synthetic_london_daily_profiles(n_days: int = 365, random_state: int = 17) -> pd.DataFrame:
    """Reproducible daily PV, load, and waste-heat traces for the public demo.

    These profiles are synthetic. They are not metered campus measurements.
    """
    rng = np.random.default_rng(random_state)
    day = np.arange(n_days)
    seasonal_solar = 0.60 + 0.35 * np.sin(2 * np.pi * (day - 80) / 365)
    pv_kw = 850.0 * np.clip(seasonal_solar + 0.12 * np.sin(2 * np.pi * day / 9), 0.10, 1.0)
    pv_kw = np.clip(pv_kw + rng.normal(0, 18.0, n_days), 0.0, None)

    weekday = day % 7
    weekday_factor = np.where(weekday < 5, 145.0, -185.0)
    winter_heating = 320.0 * np.cos(2 * np.pi * (day - 15) / 365)
    summer_cooling = 165.0 * np.maximum(0.0, np.sin(2 * np.pi * (day - 120) / 365))
    industrial_cycle = 135.0 * np.sin(2 * np.pi * day / 28 + 0.8) + 85.0 * np.sin(2 * np.pi * day / 13)
    production_ramp = 120.0 * np.sin(2 * np.pi * day / 52 + 1.7)

    ar_noise = np.zeros(n_days)
    innovations = rng.normal(0, 58.0, n_days)
    for i in range(1, n_days):
        ar_noise[i] = 0.68 * ar_noise[i - 1] + innovations[i]

    event_load = np.zeros(n_days)
    for center, magnitude, width in [
        (38, 330.0, 4.0),
        (86, -260.0, 4.5),
        (145, 280.0, 5.5),
        (207, 390.0, 6.0),
        (263, -230.0, 5.0),
        (301, 360.0, 4.5),
    ]:
        event_load += magnitude * np.exp(-0.5 * ((day - center) / width) ** 2)

    load_kw = np.clip(
        1850.0
        + weekday_factor
        + winter_heating
        + summer_cooling
        + industrial_cycle
        + production_ramp
        + ar_noise
        + event_load,
        1050.0,
        2950.0,
    )

    source_temperature = np.clip(
        TEMP_K_MID + 70.0 * (5.0 / 9.0) * np.sin(2 * np.pi * day / 365 + 0.5)
        + rng.normal(0, 22.0 * (5.0 / 9.0), n_days),
        TEMP_K_LO,
        TEMP_K_HI,
    )
    return pd.DataFrame(
        {
            "hour": day * 24 + 12,
            "hour_of_day": np.full(n_days, 12),
            "day": day,
            "pv_kw": pv_kw,
            "load_kw": load_kw,
            "source_temperature": source_temperature,
        }
    )


def _operating_grids(reference: pd.DataFrame | None) -> tuple[np.ndarray, np.ndarray]:
    if reference is None or reference.empty:
        return (
            np.array([1500.0, 2000.0, 2500.0, 3000.0]),
            np.array([400.0, 700.0, 1000.0, 1300.0]),
        )
    pressure = np.asarray(sorted(reference["mean_pressure"].unique()), dtype=float)
    speed = np.asarray(sorted(reference["engine_speed"].unique()), dtype=float)
    return pressure, speed


def confidence_aware_dispatch(
    model,
    profiles: pd.DataFrame,
    reference: pd.DataFrame | None = None,
    n_engines: int = 80,
    storage_capacity_kwh: float = 12000.0,
    storage_power_limit_kw: float = 750.0,
    commitment_window_days: int = 7,
) -> pd.DataFrame:
    """Select a weekly-committed (pressure, speed) pair that tracks residual load.

    Power labels in the public CSV are in watts. ``n_engines`` scales a bank of
    identical units into kilowatts for the synthetic campus balance.
    """
    pressure_grid, speed_grid = _operating_grids(reference)
    rows: list[dict[str, float]] = []
    committed_pressure: float | None = None
    committed_speed: float | None = None

    for i, (_, row) in enumerate(profiles.iterrows()):
        candidates = pd.DataFrame(
            [(row["source_temperature"], p, s) for p in pressure_grid for s in speed_grid],
            columns=FEATURE_COLUMNS,
        )
        mean, std = model.predict(candidates[FEATURE_COLUMNS].to_numpy(float), return_std=True)
        whr_kw = mean[:, 0] * n_engines / 1000.0
        uncertainty_kw = std[:, 0] * n_engines / 1000.0
        residual_need = np.maximum(row["load_kw"] - row["pv_kw"], 0.0)
        score = np.abs(whr_kw - residual_need) + 2.5 * uncertainty_kw
        if committed_pressure is None or i % commitment_window_days == 0:
            best = int(np.argmin(score))
            committed_pressure = float(candidates.iloc[best]["mean_pressure"])
            committed_speed = float(candidates.iloc[best]["engine_speed"])
        else:
            committed = candidates[
                candidates["mean_pressure"].eq(committed_pressure)
                & candidates["engine_speed"].eq(committed_speed)
            ]
            best = int(committed.index[0]) if not committed.empty else int(np.argmin(score))
        rows.append(
            {
                "hour": row["hour"],
                "hour_of_day": row["hour_of_day"],
                "day": row["day"],
                "load_kw": row["load_kw"],
                "pv_kw": row["pv_kw"],
                "source_temperature": row["source_temperature"],
                "selected_pressure": candidates.iloc[best]["mean_pressure"],
                "selected_speed": candidates.iloc[best]["engine_speed"],
                "whr_kw": whr_kw[best],
                "whr_uncertainty_kw": uncertainty_kw[best],
                "efficiency": mean[best, 1],
                "net_balance_kw": row["pv_kw"] + whr_kw[best] - row["load_kw"],
            }
        )

    dispatch = pd.DataFrame(rows)
    soc = 0.55 * storage_capacity_kwh
    storage_power: list[float] = []
    soc_trace: list[float] = []
    for net in dispatch["net_balance_kw"].to_numpy(float):
        if net >= 0:
            charge = min(net, storage_power_limit_kw, storage_capacity_kwh - soc)
            soc += charge
            storage_power.append(-charge)
        else:
            discharge = min(-net, storage_power_limit_kw, soc)
            soc -= discharge
            storage_power.append(discharge)
        soc_trace.append(soc)
    dispatch["storage_power_kw"] = storage_power
    dispatch["storage_soc_kwh"] = soc_trace
    dispatch["served_balance_kw"] = (
        dispatch["pv_kw"] + dispatch["whr_kw"] + dispatch["storage_power_kw"] - dispatch["load_kw"]
    )
    return dispatch
