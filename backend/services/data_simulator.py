# backend/services/data_simulator.py
import random
from typing import Tuple


class DataSimulator:
    """
    Simulador simples: gera valores em torno de uma média com desvio padrão.
    Ocasionalmente injeta um pico (anomalia) para testar o sistema.
    """

    def __init__(self, mean: float = 1028.0, std: float = 1.0, spike_chance: float = 0.05):
        self.mean = mean
        self.std = std
        self.spike_chance = spike_chance

    def generate_point(self) -> Tuple[float, bool]:
        base = random.gauss(self.mean, self.std)
        is_spike = random.random() < self.spike_chance
        if is_spike:
            # adiciona um desvio grande
            base += random.choice([-1, 1]) * self.std * random.uniform(3, 5)
        return base, is_spike
