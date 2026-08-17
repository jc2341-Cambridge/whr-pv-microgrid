"""Rule-based physics reviewer used as the constraint-checking agent."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_loader import TEMP_K_HI, TEMP_K_LO


class PhysicsConstraintAgent:
    """Rejects infeasible candidates and clips non-physical predictions.

    Bounds match the released public grid (heater temperature 773.15-1073.15 K,
    mean pressure 1500-3000 kPa-equivalent study units, speed 400-1300 rpm,
    efficiency 0.40-0.60). They are not soft-penalised into the surrogate loss.
    """

    def __init__(
        self,
        temperature_bounds: tuple[float, float] = (TEMP_K_LO, TEMP_K_HI),
        pressure_bounds: tuple[float, float] = (1500.0, 3000.0),
        speed_bounds: tuple[float, float] = (400.0, 1300.0),
        efficiency_bounds: tuple[float, float] = (0.40, 0.60),
    ) -> None:
        self.temperature_bounds = temperature_bounds
        self.pressure_bounds = pressure_bounds
        self.speed_bounds = speed_bounds
        self.efficiency_bounds = efficiency_bounds

    def validate_candidates(self, candidates: pd.DataFrame) -> pd.DataFrame:
        mask = (
            candidates["source_temperature"].between(*self.temperature_bounds)
            & candidates["mean_pressure"].between(*self.pressure_bounds)
            & candidates["engine_speed"].between(*self.speed_bounds)
        )
        return candidates.loc[mask].drop_duplicates().reset_index(drop=True)

    def clip_predictions(self, y: np.ndarray) -> np.ndarray:
        out = np.asarray(y, dtype=float).copy()
        out[:, 0] = np.maximum(out[:, 0], 0.0)
        out[:, 1] = np.clip(out[:, 1], *self.efficiency_bounds)
        return out

    def monotonicity_penalty(
        self,
        grid: pd.DataFrame,
        predictions: np.ndarray,
        group_col: str = "source_temperature",
    ) -> float:
        """Mean downward violation of predicted power versus pressure."""
        tmp = grid.copy()
        tmp["power_pred"] = predictions[:, 0]
        penalties: list[float] = []
        for _, part in tmp.groupby([group_col, "engine_speed"]):
            ordered = part.sort_values("mean_pressure")
            diffs = np.diff(ordered["power_pred"].to_numpy())
            if len(diffs):
                penalties.extend(np.maximum(-diffs, 0.0))
        return float(np.mean(penalties)) if penalties else 0.0


def residual_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    err = predicted - actual
    denom = np.maximum(np.abs(actual), 1e-9)
    return {
        "power_mae": float(np.mean(np.abs(err[:, 0]))),
        "power_rmse": float(np.sqrt(np.mean(err[:, 0] ** 2))),
        "power_mape": float(np.mean(np.abs(err[:, 0]) / denom[:, 0]) * 100.0),
        "efficiency_mae_pct_point": float(np.mean(np.abs(err[:, 1])) * 100.0),
        "efficiency_rmse_pct_point": float(np.sqrt(np.mean(err[:, 1] ** 2)) * 100.0),
        "efficiency_mape": float(np.mean(np.abs(err[:, 1]) / denom[:, 1]) * 100.0),
    }
