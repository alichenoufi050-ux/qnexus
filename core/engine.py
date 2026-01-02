# qnexus/core/engine.py
"""
Q-NEXUS OMEGA — Decision Intelligence Core
- Explainable, adaptive, production-grade
- Self-learning via constrained bandit weighting (safe)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import time
import math
from core.evaluator import LearningGate
import copy
EPS = 1e-9

# =========================
# MARKET STATE
# =========================
@dataclass
class MarketState:
    momentum: float
    volatility: float
    entropy: float
    volume_pressure: float
    trend_strength: float

class MarketStateEngine:
    @staticmethod
    def compute(prices: List[float], volumes: List[float]) -> MarketState:
        if len(prices) < 10 or len(volumes) != len(prices):
            raise ValueError("Invalid market data")

        p = np.array(prices, dtype=float)
        v = np.array(volumes, dtype=float)

        rets = np.diff(p) / (p[:-1] + EPS)
        momentum = (p[-1] - p[0]) / (p[0] + EPS)
        volatility = float(np.std(rets))

        probs = np.abs(rets)
        probs = probs / (np.sum(probs) + EPS)
        entropy = float(-np.sum(probs * np.log(probs + EPS)))

        vol_norm = (v - v.mean()) / (v.std() + EPS)
        volume_pressure = float(np.tanh(vol_norm[-5:].mean()))

        trend_strength = float(np.abs(momentum) / (volatility + EPS))

        return MarketState(
            momentum=momentum,
            volatility=volatility,
            entropy=entropy,
            volume_pressure=volume_pressure,
            trend_strength=trend_strength,
        )

# =========================
# STRATEGIES
# =========================
class Strategy:
    name: str
    def signal(self, s: MarketState) -> float:
        raise NotImplementedError

class TrendFollowing(Strategy):
    name = "trend"
    def signal(self, s: MarketState) -> float:
        return np.tanh(2.0 * s.momentum) * np.clip(s.trend_strength, 0, 2)

class MeanReversion(Strategy):
    name = "mean_reversion"
    def signal(self, s: MarketState) -> float:
        return -np.tanh(3.0 * s.momentum) * (1.0 / (1.0 + s.volatility))

class VolatilityBreakout(Strategy):
    name = "volatility"
    def signal(self, s: MarketState) -> float:
        return np.tanh(s.volatility * 5.0) * np.sign(s.momentum)

class Defensive(Strategy):
    name = "defensive"
    def signal(self, s: MarketState) -> float:
        return -np.tanh(s.entropy) * (1.0 if s.volatility > 0.02 else 0.2)

# =========================
# SELF-LEARNING (SAFE)
# =========================
@dataclass
class StrategyStats:
    weight: float = 1.0
    ewma_return: float = 0.0
    plays: int = 0

class BanditWeighter:
    """
    Constrained self-learning:
    - Updates only weights (no model mutation)
    - EWMA performance + UCB exploration
    """
    def __init__(self, strategies: List[Strategy], alpha: float = 0.1):
        self.alpha = alpha
        self.stats: Dict[str, StrategyStats] = {
            s.name: StrategyStats(weight=1.0) for s in strategies
        }
        self.t = 0

    def score(self, name: str) -> float:
        st = self.stats[name]
        ucb = math.sqrt(2 * math.log(self.t + 1) / (st.plays + 1))
        return st.ewma_return + 0.1 * ucb

    def normalized_weights(self) -> Dict[str, float]:
        scores = {k: max(self.score(k), 0.0) for k in self.stats}
        s = sum(scores.values()) + EPS
        return {k: v / s for k, v in scores.items()}

    def update(self, name: str, realized_return: float):
        st = self.stats[name]
        st.plays += 1
        st.ewma_return = (1 - self.alpha) * st.ewma_return + self.alpha * realized_return
        self.t += 1

# =========================
# RISK ENGINE
# =========================
class RiskEngine:
    @staticmethod
    def assess(s: MarketState, raw_score: float) -> Tuple[str, float]:
        risk = "LOW"
        if s.volatility > 0.03 or s.entropy > 1.5:
            risk = "HIGH"
        elif s.volatility > 0.02:
            risk = "MEDIUM"

        confidence = float(np.clip(abs(raw_score), 0.0, 1.0))
        return risk, confidence

# =========================
# DECISION CORE
# =========================
class DecisionEngine:
    def __init__(self):
        self.strategies: List[Strategy] = [
            TrendFollowing(),
            MeanReversion(),
            VolatilityBreakout(),
            Defensive(),
        ]
        self.weighter = BanditWeighter(self.strategies)

        # ✅ هنا بالضبط
        self.gate = LearningGate()
        self.history = []

    def decide(self, prices: List[float], volumes: List[float]) -> Dict:
        s = MarketStateEngine.compute(prices, volumes)

        weights = self.weighter.normalized_weights()
        agg = 0.0
        contrib = {}

        for st in self.strategies:
            sig = st.signal(s)
            w = weights.get(st.name, 0.0)
            agg += w * sig
            contrib[st.name] = float(w * sig)

        risk, confidence = RiskEngine.assess(s, agg)

        if agg > 0.15:
            decision = "BUY"
        elif agg < -0.15:
            decision = "SELL"
        else:
            decision = "HOLD"

        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "risk": risk,
            "explain": contrib,
            "timestamp": int(time.time()),
        }

    # ✅ هذه داخل الكلاس
    def learn(
        self,
        prices,
        old_decisions,
        new_decisions,
        executed_strategy: str,
        realized_return: float
    ):
        verdict = self.gate.approve(
            prices=prices,
            old_decisions=old_decisions,
            new_decisions=new_decisions
        )

        if not verdict["approved"]:
            self.history.append({
                "status": "rejected",
                "reason": verdict.get("reason"),
                "details": verdict
            })
            return {"status": "rejected", "verdict": verdict}

        # ✅ التحديث يتم فقط بعد الموافقة
        self.weighter.update(executed_strategy, realized_return)

        self.history.append({
            "status": "approved",
            "strategy": executed_strategy,
            "return": realized_return,
            "metrics": verdict.get("metrics")
        })

        return {"status": "approved", "verdict": verdict}

# =========================
# USAGE EXAMPLE (paper)
# =========================
if __name__ == "__main__":
    engine = DecisionEngine()
    prices = list(np.cumsum(np.random.normal(0, 0.5, 200)) + 100)
    volumes = list(np.random.randint(100, 1000, 200))

    out = engine.decide(prices, volumes)
    print(out)

    # Simulated feedback (paper trading)
    
