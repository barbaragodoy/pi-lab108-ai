# backend/models/cep.py
from dataclasses import dataclass
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime
import numpy as np


@dataclass
class CepStats:
    mean: float
    std: float
    r: float
    cp: float | None
    cpk: float | None
    lsl: float
    usl: float
    n: int


def compute_cp_cpk(values: List[float], lsl: float, usl: float) -> CepStats:
    x = np.array(values, dtype=float)
    n = len(x)
    if n == 0:
        return CepStats(0.0, 0.0, 0.0, None, None, lsl, usl, 0)

    mean = float(x.mean())
    std = float(x.std(ddof=1)) if n > 1 else 0.0
    r = float(x.max() - x.min()) if n > 1 else 0.0

    if std == 0:
        cp = None
        cpk = None
    else:
        cp = (usl - lsl) / (6 * std)
        cpu = (usl - mean) / (3 * std)
        cpl = (mean - lsl) / (3 * std)
        cpk = min(cpu, cpl)

    return CepStats(mean, std, r, cp, cpk, lsl, usl, n)


def group_by_day(measurements: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for m in measurements:
        ts = m.get("timestamp")
        val = m.get("value_real")
        if ts is None or val is None:
            continue
        # Suporta datetime object ou string ISO
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        elif not isinstance(ts, datetime):
            continue
        day = ts.date().isoformat()
        grouped[day].append(float(val))
    return grouped


def compute_daily_cep(
    measurements: List[Dict[str, Any]],
    lsl: float,
    usl: float,
) -> List[Dict[str, Any]]:
    grouped = group_by_day(measurements)
    result: List[Dict[str, Any]] = []

    for day, vals in sorted(grouped.items(), key=lambda kv: kv[0]):
        stats = compute_cp_cpk(vals, lsl, usl)
        result.append(
            {
                "day": day,
                "n": stats.n,
                "mean": stats.mean,
                "std": stats.std,
                "r": stats.r,
                "cp": stats.cp,
                "cpk": stats.cpk,
                "lsl": stats.lsl,
                "usl": stats.usl,
            }
        )
    return result


def detect_run_rules(values: List[float]) -> Dict[str, Any]:
    """
    Regras simples de Shewhart:
    - Regra 1: 1 ponto fora de 3σ
    - Regra 4 (simplificada): 8 pontos do mesmo lado da média
    """
    if len(values) < 8:
        return {"rule1": [], "rule4": []}

    x = np.array(values, dtype=float)
    mean = float(x.mean())
    std = float(x.std(ddof=1)) if len(x) > 1 else 0.0

    rule1_idx = []
    rule4_idx = []

    if std > 0:
        for i, v in enumerate(x):
            if abs(v - mean) > 3 * std:
                rule1_idx.append(i)

        side = np.sign(x - mean)
        streak_start = 0
        for i in range(1, len(side)):
            if side[i] == 0:
                streak_start = i + 1
                continue
            if side[i] != side[i - 1]:
                streak_start = i
            if i - streak_start + 1 >= 8:
                rule4_idx.extend(list(range(streak_start, i + 1)))

    return {
        "rule1": sorted(set(rule1_idx)),
        "rule4": sorted(set(rule4_idx)),
    }
