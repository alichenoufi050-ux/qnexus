# core/attribution.py
from typing import Dict

class StrategyAttributor:
    """
    Attributes PnL to strategies proportionally to their contribution
    """

    @staticmethod
    def attribute(
        explain: Dict[str, float],
        realized_return: float
    ) -> Dict[str, float]:
        """
        explain: output from DecisionEngine.decide()["explain"]
        realized_return: actual PnL
        """
        total = sum(abs(v) for v in explain.values()) + 1e-9

        attribution = {}
        for strategy, contrib in explain.items():
            weight = abs(contrib) / total
            attribution[strategy] = realized_return * weight

        return attribution
