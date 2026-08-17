"""Lightweight tests a reviewer or CI agent can run without the full dataset."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_loader import (  # noqa: E402
    FEATURE_COLUMNS,
    feature_target_arrays,
    load_public_operating_data,
    sparse_active_learning_split,
)
from physics_constraints import PhysicsConstraintAgent  # noqa: E402
from surrogate_models import BootstrapSurrogate  # noqa: E402


def test_public_example_set_is_runnable() -> None:
    df = load_public_operating_data()
    assert len(df) == 40
    assert set(df["source_temperature"].unique()) == {773.15, 923.15, 1073.15}
    assert df[FEATURE_COLUMNS].duplicated().sum() == 0


def test_split_is_disjoint_and_nonempty() -> None:
    df = load_public_operating_data()
    train, oracle, holdout = sparse_active_learning_split(df)
    assert len(train) >= 4
    assert len(holdout) >= 2
    assert len(oracle) >= len(train)
    train_keys = set(map(tuple, train[FEATURE_COLUMNS].to_numpy()))
    hold_keys = set(map(tuple, holdout[FEATURE_COLUMNS].to_numpy()))
    assert train_keys.isdisjoint(hold_keys)


def test_surrogate_fits_and_stays_physical() -> None:
    df = load_public_operating_data()
    train, _, holdout = sparse_active_learning_split(df)
    x, y = feature_target_arrays(train)
    model = BootstrapSurrogate(
        n_estimators=8, degree=2, alpha=0.2, random_state=0,
        physics_agent=PhysicsConstraintAgent(),
    ).fit(x, y)
    pred = model.predict(feature_target_arrays(holdout)[0])
    assert pred.shape[1] == 2
    assert np.all(pred[:, 0] >= 0.0)
    assert np.all((pred[:, 1] >= 0.40) & (pred[:, 1] <= 0.60))


def test_physics_reviewer_rejects_oob() -> None:
    physics = PhysicsConstraintAgent()
    bad = pd.DataFrame(
        [{"source_temperature": 200.0, "mean_pressure": 100.0, "engine_speed": 50.0}]
    )
    assert physics.validate_candidates(bad).empty


if __name__ == "__main__":
    test_public_example_set_is_runnable()
    test_split_is_disjoint_and_nonempty()
    test_surrogate_fits_and_stays_physical()
    test_physics_reviewer_rejects_oob()
    print("smoke tests passed")
