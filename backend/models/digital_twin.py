# backend/models/digital_twin.py
from collections import deque
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class EmaConfig:
    alpha: float = 0.3  # fator de suavização (0–1)


class DigitalTwinModel:
    """
    Gêmeo digital usando EMA (Exponential Moving Average).

    - update(value): atualiza o modelo com o valor medido
    - predict(): retorna a previsão para o próximo ponto (EMA atual)
    - get_residual(value): diferença entre o valor e a previsão
    """

    def __init__(self, config: Optional[EmaConfig] = None):
        self.config = config or EmaConfig()
        self._last_ema: Optional[float] = None
        self._history: deque[float] = deque(maxlen=1000)

    def reset(self):
        self._last_ema = None
        self._history.clear()

    def update(self, value: float) -> None:
        """Atualiza a EMA com o novo valor."""
        self._history.append(value)
        if self._last_ema is None:
            self._last_ema = value
        else:
            a = self.config.alpha
            self._last_ema = a * value + (1 - a) * self._last_ema

    def predict(self) -> Optional[float]:
        """Previsão para o próximo ponto é a EMA atual."""
        return self._last_ema

    def get_residual(self, value: float) -> float:
        """Retorna o resíduo (valor - previsão)."""
        if self._last_ema is None:
            return 0.0
        return float(value - self._last_ema)

    def fit_from_series(self, series: List[float]) -> None:
        """Inicializa EMA a partir de uma série existente."""
        self.reset()
        for v in series:
            self.update(float(v))
