# core/regime.py
from dataclasses import dataclass
import numpy as np

@dataclass
class MarketRegime:
    name: str
    confidence: float

class RegimeDetector:
    """
    Institutional-grade market regime detection
    """

    @staticmethod
    def detect(momentum: float, volatility: float, entropy: float) -> MarketRegime:

        # 🔴 سوق خطر
        if volatility > 0.04 and entropy > 1.6:
            return MarketRegime("VOLATILE", 0.9)

        # 🟢 ترند واضح
        if abs(momentum) > 0.02 and volatility < 0.025:
            return MarketRegime("TRENDING", 0.8)

        # 🔵 Mean-reversion
        if abs(momentum) < 0.01 and volatility < 0.02:
            return MarketRegime("MEAN_REVERTING", 0.7)

        # ⚫ سوق ميت
        return MarketRegime("DEAD", 0.6)
