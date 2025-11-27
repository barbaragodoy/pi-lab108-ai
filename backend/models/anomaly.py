# backend/models/anomaly.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass
class AnomalyConfig:
    contamination: float = 0.03       # porcentagem esperada de anomalias
    zscore_threshold: float = 3.0     # |z| > 3 => suspeito


class AnomalyDetector:
    """
    Detector de anomalias baseado em:
    - IsolationForest sobre os resíduos
    - Z-score simples para reforçar decisão
    """

    def __init__(self, config: Optional[AnomalyConfig] = None):
        self.config = config or AnomalyConfig()
        self._model: Optional[IsolationForest] = None
        self._fitted: bool = False
        self._residuals_history: List[float] = []

    def fit(self, residuals: List[float]):
        """Treina o IsolationForest com a lista de resíduos."""
        if len(residuals) < 10:
            self._fitted = False
            return

        X = np.array(residuals, dtype=float).reshape(-1, 1)
        self._model = IsolationForest(
            contamination=self.config.contamination,
            random_state=42,
        )
        self._model.fit(X)
        self._fitted = True
        self._residuals_history = list(residuals)

    def partial_update(self, residual: float):
        """Atualiza histórico e re-treina eventualmente (auto-tuning)."""
        self._residuals_history.append(float(residual))
        # a cada 50 pontos, re-treina o modelo
        if len(self._residuals_history) % 50 == 0:
            self.fit(self._residuals_history)

    def score_point(self, residual: float) -> Dict[str, Any]:
        """
        Retorna:
        - residual
        - zscore_residual
        - iforest_score
        - is_anomaly
        """
        res = float(residual)
        hist = np.array(self._residuals_history + [res], dtype=float)
        mean = float(hist.mean()) if len(hist) > 0 else 0.0
        std = float(hist.std(ddof=1)) if len(hist) > 1 else 0.0
        z = (res - mean) / std if std > 0 else 0.0

        score_if = 0.0
        is_iforest = False
        if self._fitted and self._model is not None:
            score_if = float(self._model.decision_function([[res]])[0])
            pred = int(self._model.predict([[res]])[0])  # 1 normal, -1 anomalia
            is_iforest = pred == -1

        is_z = abs(z) >= self.config.zscore_threshold
        is_anomaly = is_iforest or is_z

        return {
            "residual": res,
            "zscore_residual": z,
            "iforest_score": score_if,
            "is_anomaly": is_anomaly,
        }
