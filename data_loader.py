"""Load the public validation table and form an auditable train/holdout split."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PUBLIC_DATA = ROOT / "data" / "public" / "operating_points.csv"

FEATURE_COLUMNS = ["source_temperature", "mean_pressure", "engine_speed"]
TARGET_COLUMNS = ["power", "efficiency"]


def load_public_operating_data(path: str | Path = PUBLIC_DATA) -> pd.DataFrame:
    """Load the public validation operating points (SI units already applied)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Public operating-point file not found: {path}. "
            "Place the released CSV at data/public/operating_points.csv."
        )
    df = pd.read_csv(path)
    required = FEATURE_COLUMNS + ["power", "efficiency"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Public CSV is missing columns: {missing}")
    df = df.drop_duplicates(subset=FEATURE_COLUMNS, keep="last")
    df = df.sort_values(FEATURE_COLUMNS).reset_index(drop=True)
    return df


def temperature_levels(df: pd.DataFrame) -> tuple[float, ...]:
    return tuple(float(x) for x in sorted(df["source_temperature"].unique()))


# Populated after load so figure code can import a concrete triple.
TEMP_LEVELS_K: tuple[float, float, float] = (773.15, 923.15, 1073.15)
TEMP_K_LO, TEMP_K_MID, TEMP_K_HI = TEMP_LEVELS_K


def refresh_temperature_constants(df: pd.DataFrame) -> None:
    """Align module-level temperature constants with the loaded public grid."""
    global TEMP_LEVELS_K, TEMP_K_LO, TEMP_K_MID, TEMP_K_HI
    levels = temperature_levels(df)
    TEMP_LEVELS_K = levels if len(levels) >= 3 else (levels[0], levels[0], levels[-1])
    TEMP_K_LO, TEMP_K_MID, TEMP_K_HI = TEMP_LEVELS_K[0], TEMP_LEVELS_K[len(TEMP_LEVELS_K) // 2], TEMP_LEVELS_K[-1]


def sparse_active_learning_split(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Deterministic sparse-baseline / oracle-pool / holdout split.

    Baseline uses the coarse corner grid (outer pressures and speeds).
    Holdout uses interior pressures and intermediate speeds, when present.
    The oracle pool is every non-holdout point and may be queried by agents.
    """
    corner_p = {1500.0, 2500.0, 3000.0}
    corner_n = {400.0, 800.0, 1300.0}
    interior_p = {2000.0, 2800.0}
    interior_n = {550.0, 900.0, 1100.0}

    holdout_mask = df["mean_pressure"].isin(interior_p) & df["engine_speed"].isin(interior_n)
    baseline_mask = df["mean_pressure"].isin(corner_p) & df["engine_speed"].isin(corner_n)

    if int(holdout_mask.sum()) < 2 or int(baseline_mask.sum()) < 4:
        pressures = sorted(df["mean_pressure"].unique())
        speeds = sorted(df["engine_speed"].unique())
        p_idx = {v: i for i, v in enumerate(pressures)}
        s_idx = {v: i for i, v in enumerate(speeds)}
        pi = df["mean_pressure"].map(p_idx)
        si = df["engine_speed"].map(s_idx)
        n_p, n_s = len(pressures), len(speeds)
        holdout_mask = pi.isin({n_p // 2} if n_p >= 2 else set()) & si.isin(
            {i for i in (1, n_s // 2) if 0 < i < n_s} or ({n_s - 1} if n_s >= 2 else set())
        )
        baseline_mask = (~holdout_mask) & pi.isin({0, n_p - 1} if n_p >= 2 else {0}) & si.isin(
            {0, n_s - 1} if n_s >= 2 else {0}
        )
        if int(holdout_mask.sum()) < 2:
            holdout_mask = pd.Series(False, index=df.index)
            holdout_mask.iloc[-2:] = True
        if int(baseline_mask.sum()) < 4:
            baseline_mask = ~holdout_mask

    holdout = df.loc[holdout_mask].reset_index(drop=True)
    oracle_pool = df.loc[~holdout_mask].reset_index(drop=True)
    baseline_train = df.loc[baseline_mask].reset_index(drop=True)
    return baseline_train, oracle_pool, holdout


def feature_target_arrays(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    x = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df[TARGET_COLUMNS].to_numpy(dtype=float)
    return x, y
