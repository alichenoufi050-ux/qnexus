# core/risk_control.py
from dataclasses import dataclass

@dataclass
class RiskLimits:
    max_drawdown: float = -0.05     # -5%
    max_consecutive_losses: int = 3
    max_volatility: float = 0.05    # 5%

class KillSwitch:
    """
    Hard risk stop – shuts down trading when limits are breached
    """

    def __init__(self, limits: RiskLimits = RiskLimits()):
        self.limits = limits
        self.equity = 0.0
        self.peak_equity = 0.0
        self.consecutive_losses = 0
        self.active = True

    def update(self, pnl: float, volatility: float):
        if not self.active:
            return

        self.equity += pnl
        self.peak_equity = max(self.peak_equity, self.equity)

        # 1️⃣ Drawdown
        drawdown = self.equity - self.peak_equity
        if drawdown <= self.limits.max_drawdown:
            self.active = False
            return

        # 2️⃣ Consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.limits.max_consecutive_losses:
                self.active = False
                return
        else:
            self.consecutive_losses = 0

        # 3️⃣ Volatility spike
        if volatility >= self.limits.max_volatility:
            self.active = False

    def can_trade(self) -> bool:
        return self.active
