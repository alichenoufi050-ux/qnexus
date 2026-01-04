# core/regime.py
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class MarketRegime:
    name: str
    confidence: float

class RegimeDetector:
    """
    Institutional-grade market regime detection
    - Deterministic
    - Smooth confidence
    - No magic constants abuse
    """

    @staticmethod
    def detect(momentum: float, volatility: float, entropy: float) -> MarketRegime:

        # Normalize inputs
        m = abs(momentum)
        v = volatility
        e = entropy

        # ⚫ DEAD: no structure, no energy
        if v < 0.006 and m < 0.008:
            confidence = 1.0 - (v + m)
            return MarketRegime("DEAD", round(confidence, 3))

        # ⚡ VOLATILE: unstable, high uncertainty
        if v > 0.04 and e > 1.5:
            confidence = np.tanh(v + e / 2)
            return MarketRegime("VOLATILE", round(confidence, 3))

        # 📈 TRENDING: directional conviction
        if m > 0.03 and v < 0.03:
            confidence = np.tanh(m * 4)
            return MarketRegime("TRENDING", round(confidence, 3))

        # 🔁 RANGING / MEAN REVERTING
        confidence = np.clip(1.0 - m * 10, 0.5, 0.9)
        return MarketRegime("RANGING", round(confidence, 3))
