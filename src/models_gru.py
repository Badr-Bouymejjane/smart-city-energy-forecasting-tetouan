from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def create_sequences(
    X: np.ndarray,
    y: np.ndarray,
    sequence_length: int = 24,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Transforme des matrices tabulaires en séquences 3D pour GRU.

    X_seq : (samples, sequence_length, n_features)
    y_seq : (samples,)
    """
    X_seq, y_seq = [], []

    for i in range(sequence_length, len(X)):
        X_seq.append(X[i - sequence_length:i])
        y_seq.append(y[i])

    return np.asarray(X_seq), np.asarray(y_seq)

def scale_for_gru(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_val: pd.Series,
    y_test: pd.Series,
):
    """
    Normalise features et cible pour GRU sans data leakage.
    """
    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()

    X_train_scaled = feature_scaler.fit_transform(X_train)
    X_val_scaled = feature_scaler.transform(X_val)
    X_test_scaled = feature_scaler.transform(X_test)

    y_train_scaled = target_scaler.fit_transform(y_train.to_numpy().reshape(-1, 1)).ravel()
    y_val_scaled = target_scaler.transform(y_val.to_numpy().reshape(-1, 1)).ravel()
    y_test_scaled = target_scaler.transform(y_test.to_numpy().reshape(-1, 1)).ravel()

    return {
        "X_train": X_train_scaled,
        "X_val": X_val_scaled,
        "X_test": X_test_scaled,
        "y_train": y_train_scaled,
        "y_val": y_val_scaled,
        "y_test": y_test_scaled,
        "feature_scaler": feature_scaler,
        "target_scaler": target_scaler,
    }

def build_gru_model(
    sequence_length: int,
    n_features: int,
    units_1: int = 64,
    units_2: int = 32,
    dropout: float = 0.20,
    learning_rate: float = 0.001,
):
    """
    Construit une architecture GRU simple pour régression.
    """
    try:
        import tensorflow as tf
        from tensorflow.keras.layers import GRU, Dense, Dropout
        from tensorflow.keras.models import Sequential
    except ImportError as exc:
        raise ImportError(
            "tensorflow n'est pas installé. Exécuter : pip install tensorflow"
        ) from exc

    model = Sequential(
        [
            GRU(units_1, return_sequences=True, input_shape=(sequence_length, n_features)),
            Dropout(dropout),
            GRU(units_2, return_sequences=False),
            Dropout(dropout),
            Dense(32, activation="relu"),
            Dense(1, activation="linear"),
        ]
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])

    return model

def train_gru_model(
    model,
    X_train_seq: np.ndarray,
    y_train_seq: np.ndarray,
    X_val_seq: np.ndarray,
    y_val_seq: np.ndarray,
    epochs: int = 50,
    batch_size: int = 64,
):
    """
    Entraîne le GRU avec Early Stopping.
    """
    import tensorflow as tf

    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True,
    )

    history = model.fit(
        X_train_seq,
        y_train_seq,
        validation_data=(X_val_seq, y_val_seq),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stopping],
        verbose=1,
    )

    return history

def predict_gru(
    model,
    X_seq: np.ndarray,
    target_scaler: MinMaxScaler | None = None,
) -> np.ndarray:
    """
    Prédit avec le GRU et inverse le scaling de la cible si le scaler est fourni.
    """
    pred_scaled = model.predict(X_seq).reshape(-1, 1)

    if target_scaler is not None:
        return target_scaler.inverse_transform(pred_scaled).ravel()

    return pred_scaled.ravel()

def save_gru_model(model, path: str | Path = "models/gru_model.keras") -> None:
    """
    Sauvegarde le modèle GRU.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save(path)
