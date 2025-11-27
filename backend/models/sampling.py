# backend/models/sampling.py
from typing import Optional


class SamplingDecision:
    def __init__(self, level: str, reason: str):
        self.level = level          # "normal", "atencao", "critico"
        self.reason = reason

    def dict(self):
        return {"level": self.level, "reason": self.reason}


class SamplingEngine:
    """
    Decide o nível de amostragem com base no score de anomalia.
    """

    def decide(
        self,
        is_anomaly: bool,
        zscore_residual: Optional[float],
    ) -> SamplingDecision:
        if is_anomaly:
            return SamplingDecision(
                level="critico",
                reason="Anomalia detectada (IsolationForest ou |z| alto).",
            )

        if zscore_residual is None:
            return SamplingDecision(
                level="normal",
                reason="Sem estatística suficiente.",
            )

        z = abs(zscore_residual)
        if z >= 2:
            return SamplingDecision(
                level="atencao",
                reason="Resíduo moderadamente distante da média (|z| ≥ 2).",
            )

        return SamplingDecision(
            level="normal",
            reason="Resíduo dentro de faixa esperada.",
        )
