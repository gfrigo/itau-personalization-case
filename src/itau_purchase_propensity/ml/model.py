import pickle
from pathlib import Path

import numpy as np


class PropensityModel:
    def __init__(self, model_path: Path):
        with open(model_path, "rb") as f:
            artifact = pickle.load(f)

        self._model = artifact["model"]
        self._scaler = artifact["scaler"]
        self.feature_cols: list[str] = artifact["feature_cols"]

    def predict_proba(self, feature_rows: list[list[float]]) -> list[float]:
        X = np.array(feature_rows, dtype=float)
        X_scaled = self._scaler.transform(X)
        return self._model.predict_proba(X_scaled)[:, 1].tolist()
