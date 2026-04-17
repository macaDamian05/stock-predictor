from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_rsi(close_prices: pd.Series, window: int = 14) -> pd.Series:
    if window <= 0:
        raise ValueError(f"window must be positive, got {window}.")

    delta = close_prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = gain.rolling(window=window, min_periods=window).mean()
    average_loss = loss.rolling(window=window, min_periods=window).mean()
    relative_strength = average_gain / average_loss.replace(0, np.nan)

    return 100 - (100 / (1 + relative_strength))


def average_recent_rsi(rsi_values: pd.Series, days: int) -> float | None:
    recent_values = rsi_values.dropna().tail(days)
    if recent_values.empty:
        return None

    return float(recent_values.mean())
