# core/backtest.py
from typing import List, Dict
import math

class BacktestEngine:
    def __init__(self, initial_capital: float = 10_000):
        self.initial_capital = initial_capital

    def run(
        self,
        prices: List[float],
        decisions: List[str]
    ) -> Dict:

        capital = self.initial_capital
        peak = capital
        drawdown = 0.0

        position = None
        entry_price = 0.0
        returns = []
        wins = 0
        trades = 0

        for price, decision in zip(prices, decisions):

            if decision == "BUY" and position is None:
                position = "LONG"
                entry_price = price
                trades += 1

            elif decision == "SELL" and position == "LONG":
                pnl = price - entry_price
                capital += pnl
                returns.append(pnl)
                wins += 1 if pnl > 0 else 0
                position = None

                peak = max(peak, capital)
                drawdown = max(drawdown, (peak - capital))

        sharpe = self._sharpe_ratio(returns)

        return {
            "initial_capital": self.initial_capital,
            "final_capital": capital,
            "net_profit": capital - self.initial_capital,
            "trades": trades,
            "win_rate": wins / trades if trades else 0.0,
            "max_drawdown": drawdown,
            "sharpe_ratio": sharpe
        }

    def _sharpe_ratio(self, returns: List[float]) -> float:
        if len(returns) < 2:
            return 0.0

        avg = sum(returns) / len(returns)
        std = math.sqrt(sum((r - avg) ** 2 for r in returns) / len(returns))
        return avg / std if std != 0 else 0.0
