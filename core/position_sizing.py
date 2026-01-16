# core/position_sizing.py
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSize:
    fraction: float   # نسبة من رأس المال (0.0 → 1.0)
    reason: str


class PositionSizer:
    """
    Institutional-grade position sizing
    - Regime-aware
    - Risk-aware
    - Confidence-aware
    """

    @staticmethod
    def size(
        *,
        regime: str,
        risk: str,
        confidence: float
    ) -> PositionSize:

        # 🚫 لا تداول أصلًا
        if regime == "DEAD":
            return PositionSize(0.0, "Market dead")

        # ⚡ سوق خطير
        if regime == "VOLATILE":
            base = 0.1
        elif regime == "TRENDING":
            base = 0.4
        elif regime == "RANGING":
            base = 0.25
        else:
            base = 0.15

        # ⚠️ تخفيض حسب المخاطرة
        if risk == "HIGH":
            base *= 0.4
        elif risk == "MEDIUM":
            base *= 0.7

        # 🧠 تضخيم/تقليص حسب الثقة
        base *= confidence

        # 🧱 حدود أمان
        base = max(0.01, min(base, 0.5))

        return PositionSize(
            fraction=round(base, 3),
            reason=f"{regime} | {risk} | conf={confidence}"
        )
