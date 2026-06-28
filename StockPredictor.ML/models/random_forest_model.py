from __future__ import annotations


def create_random_forest_model(
    n_estimators: int = 300,
    max_depth: int | None = 12,
    min_samples_leaf: int = 5,
    random_state: int = 42,
    n_jobs: int = 1,
):
    from sklearn.ensemble import RandomForestRegressor

    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=n_jobs,
    )
