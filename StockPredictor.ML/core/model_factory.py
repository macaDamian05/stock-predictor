from __future__ import annotations


def build_lstm_model(lstm_units: int, lookback_days: int):
    try:
        from tensorflow.keras.layers import Dense, Input, LSTM
        from tensorflow.keras.models import Sequential
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "TensorFlow is not installed. Create a Python 3.11 environment and install "
            "StockPredictor.ML/requirements.txt before training."
        ) from exc

    model = Sequential(
        [
            Input(shape=(lookback_days, 1)),
            LSTM(units=lstm_units, return_sequences=False),
            Dense(units=1),
        ]
    )
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model
