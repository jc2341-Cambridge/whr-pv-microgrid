"""End-to-end public validation pipeline: surrogate, agents, dispatch, figures."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import json
from pathlib import Path

import pandas as pd

from agents import run_multi_agent_augmentation, unused_oracle_cases
from data_loader import (
    TARGET_COLUMNS,
    feature_target_arrays,
    load_public_operating_data,
    refresh_temperature_constants,
    sparse_active_learning_split,
)
from llm_protocol import build_agent_trace
from make_figures import (
    plot_data_coverage,
    plot_dispatch,
    plot_efficiency_surface,
    plot_framework,
    plot_parity,
    plot_residuals,
    plot_uncertainty_map,
)
from microgrid_dispatch import confidence_aware_dispatch, synthetic_london_daily_profiles
from physics_constraints import PhysicsConstraintAgent, residual_metrics
from surrogate_models import BootstrapSurrogate

HERE = Path(__file__).resolve().parent
RESULT_DIR = HERE / "results"


def fit_surrogate(train: pd.DataFrame, random_state: int) -> BootstrapSurrogate:
    x_train, y_train = feature_target_arrays(train)
    return BootstrapSurrogate(
        n_estimators=90,
        degree=3,
        alpha=0.08,
        random_state=random_state,
        physics_agent=PhysicsConstraintAgent(),
    ).fit(x_train, y_train)


def main() -> None:
    RESULT_DIR.mkdir(exist_ok=True)

    df = load_public_operating_data()
    refresh_temperature_constants(df)
    train, oracle_pool, test = sparse_active_learning_split(df)
    x_test, y_test = feature_target_arrays(test)

    baseline = fit_surrogate(train, random_state=21)
    y_base = baseline.predict(x_test)
    baseline_metrics = residual_metrics(y_test, y_base)

    n_unused = len(unused_oracle_cases(train, oracle_pool))
    n_select = max(4, min(16, n_unused if n_unused else max(1, len(train) // 2)))
    augmented_train, selected_cases = run_multi_agent_augmentation(
        train, baseline, n_select=n_select, oracle_reference=oracle_pool
    )
    model_training_cases = pd.concat(
        [train.assign(label_source="experiment"), selected_cases],
        ignore_index=True,
    )
    augmented = fit_surrogate(model_training_cases, random_state=22)
    y_aug = augmented.predict(x_test)
    augmented_metrics = residual_metrics(y_test, y_aug)

    profiles = synthetic_london_daily_profiles()
    dispatch = confidence_aware_dispatch(augmented, profiles, reference=df)

    df.to_csv(RESULT_DIR / "public_operating_data.csv", index=False)
    train.to_csv(RESULT_DIR / "train_cases.csv", index=False)
    test.to_csv(RESULT_DIR / "holdout_cases.csv", index=False)
    selected_cases.to_csv(RESULT_DIR / "agent_selected_cases.csv", index=False)
    augmented_train.to_csv(RESULT_DIR / "augmented_training_cases.csv", index=False)
    model_training_cases.to_csv(RESULT_DIR / "weighted_model_training_cases.csv", index=False)
    dispatch.to_csv(RESULT_DIR / "confidence_aware_dispatch.csv", index=False)

    metrics = {
        "release": "public-validation",
        "n_public_cases": int(len(df)),
        "n_train_cases": int(len(train)),
        "n_holdout_cases": int(len(test)),
        "n_agent_selected_cases": int(len(selected_cases)),
        "baseline": baseline_metrics,
        "agent_augmented": augmented_metrics,
        "targets": TARGET_COLUMNS,
        "caveat": (
            "Metrics on the public validation table confirm that the code path executes."
        ),
        "method_boundary": [
            "LLM/agent layer proposes and ranks operating cases",
            "Numeric labels come from unused released-grid rows, else the proxy-solver",
            "Hard device bounds stay in the physics reviewer, not in a QUBO penalty",
            "Dispatch uses surrogate mean and epistemic uncertainty jointly",
        ],
    }
    (RESULT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    build_agent_trace(selected_cases, metrics, RESULT_DIR / "llm_agent_trace.json")

    figure_jobs = [
        ("framework", plot_framework, ()),
        ("coverage", plot_data_coverage, (train, test, selected_cases)),
        ("parity", plot_parity, (y_test, y_base, y_aug)),
        ("residuals", plot_residuals, (y_test, y_aug)),
        ("efficiency", plot_efficiency_surface, (augmented,)),
        ("uncertainty", plot_uncertainty_map, (augmented,)),
        ("dispatch", plot_dispatch, (dispatch,)),
    ]
    for name, fn, args in figure_jobs:
        try:
            fn(*args)
        except Exception as exc:  # some environments lack a 3-D backend
            print(f"figure skipped ({name}): {exc}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
