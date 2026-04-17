from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class PersistenceRegressor:
    def __init__(self, reference_column: str = "close_current") -> None:
        self.reference_column = reference_column

    def fit(self, X, y=None) -> "PersistenceRegressor":
        return self

    def predict(self, X) -> np.ndarray:
        if self.reference_column not in X.columns:
            raise ValueError(
                f"Reference column '{self.reference_column}' missing from feature frame."
            )

        return X[self.reference_column].to_numpy(dtype=float)


@dataclass(frozen=True)
class RandomForestConfig:
    n_estimators: int = 300
    max_depth: int | None = 12
    min_samples_leaf: int = 5
    random_state: int = 42
    n_jobs: int = 1


@dataclass(frozen=True)
class DecisionTreeConfig:
    max_depth: int | None = 8
    min_samples_leaf: int = 5
    random_state: int = 42


@dataclass(frozen=True)
class RidgeConfig:
    alpha: float = 1.0


def build_random_forest_regressor(config: RandomForestConfig):
    from sklearn.ensemble import RandomForestRegressor

    return RandomForestRegressor(
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        min_samples_leaf=config.min_samples_leaf,
        random_state=config.random_state,
        n_jobs=config.n_jobs,
    )


def build_decision_tree_regressor(config: DecisionTreeConfig):
    from sklearn.tree import DecisionTreeRegressor

    return DecisionTreeRegressor(
        max_depth=config.max_depth,
        min_samples_leaf=config.min_samples_leaf,
        random_state=config.random_state,
    )


def build_ridge_regressor(config: RidgeConfig):
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=config.alpha)),
        ]
    )
