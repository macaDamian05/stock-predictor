from __future__ import annotations


def create_legacy_lstm_model(lstm_units: int, lookback_days: int):
    """Return the existing project LSTM model.

    The stable core suite does not train this model by default because it pulls
    in the heavier TensorFlow runtime. It stays available for later controlled
    integration.
    """

    from core.model_factory import build_lstm_model

    return build_lstm_model(lstm_units=lstm_units, lookback_days=lookback_days)
