# core/paper_trader.py
from typing import List
from core.engine import DecisionEngine
from db.history import log_trade
import numpy as np

class PaperTrader:
    """
    Executes paper trades and feeds results back to the engine
    """

    def __init__(self, engine: DecisionEngine, symbol: str, market: str = "crypto"):
        self.engine = engine
        self.symbol = symbol
        self.market = market
        self.last_price = None
        self.position = None  # None | "LONG"

        self.decisions_buffer: List[str] = []

    def step(self, prices, volumes):
        decision_payload = self.engine.decide(prices, volumes)
        decision = decision_payload["decision"]
        confidence = decision_payload["confidence"]

        current_price = prices[-1]
        pnl = 0.0

        # --- Execution logic (paper) ---
        if decision == "BUY" and self.position is None:
            self.position = "LONG"
            self.last_price = current_price

        elif decision == "SELL" and self.position == "LONG":
            pnl = current_price - self.last_price
            self.position = None

        # --- Log trade ---
        log_trade(
            market=self.market,
            symbol=self.symbol,
            strategy="ensemble",
            decision=decision,
            price=current_price,
            volume=1.0,
            confidence=confidence,
            pnl=pnl,
            meta=decision_payload
        )

        # --- Learning buffer ---
        self.decisions_buffer.append(decision)

        # --- Feedback loop (only when trade closes) ---
        if pnl != 0.0 and len(self.decisions_buffer) > 10:
            self.engine.learn(
                prices=prices[-len(self.decisions_buffer):],
                old_decisions=self.decisions_buffer[:-1],
                new_decisions=self.decisions_buffer,
                executed_strategy="trend",  # dominant strategy
                realized_return=pnl
            )
            self.decisions_buffer.clear()
