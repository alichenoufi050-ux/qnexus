# core/evaluator.py
from core.backtest import BacktestEngine
from typing import Dict

class LearningGate:
    def __init__(self):
        self.backtester = BacktestEngine()

        # أوزان الحكم (قابلة للتطوير لاحقًا)
        self.weights = {
            "net_profit": 0.4,
            "sharpe_ratio": 0.3,
            "max_drawdown": 0.3
        }

        self.min_improvement = 0.05  # 5% تحسن إجباري

    def _score(self, metrics: Dict) -> float:
        """
        Score مركب (كلما زاد أفضل)
        """
        return (
            metrics["net_profit"] * self.weights["net_profit"]
            + metrics["sharpe_ratio"] * self.weights["sharpe_ratio"]
            - metrics["max_drawdown"] * self.weights["max_drawdown"]
        )

    def approve(
        self,
        prices,
        old_decisions,
        new_decisions
    ) -> Dict:
        old_metrics = self.backtester.run(prices, old_decisions)
        new_metrics = self.backtester.run(prices, new_decisions)

        old_score = self._score(old_metrics)
        new_score = self._score(new_metrics)

        improvement = (new_score - old_score) / abs(old_score + 1e-9)

        if improvement < self.min_improvement:
            return {
                "approved": False,
                "reason": "Insufficient improvement",
                "old_score": old_score,
                "new_score": new_score
            }

        if new_metrics["max_drawdown"] > 1.2 * old_metrics["max_drawdown"]:
            return {
                "approved": False,
                "reason": "Excessive drawdown"
            }

        return {
            "approved": True,
            "improvement": improvement,
            "metrics": new_metrics
      }
