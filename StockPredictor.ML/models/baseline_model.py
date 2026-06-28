from __future__ import annotations

import numpy as np


class PersistenceReturnRegressor:
    """Persistence baseline for next-return training targets.

    The model predicts a zero return, which maps to "next close equals current
    close" during evaluation and recursive forecasting.
    """

    def fit(self, X, y=None) -> "PersistenceReturnRegressor":
        return self

    def predict(self, X) -> np.ndarray:
        return np.zeros(len(X), dtype=float)


def create_baseline_model() -> PersistenceReturnRegressor:
    return PersistenceReturnRegressor()
