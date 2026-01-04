# core/paper_trader.py
from typing import List
from core.engine import DecisionEngine
from core.attribution import StrategyAttributor
from core.risk_control import KillSwitch
from db.history import log_trade

class PaperTrader:
    """
    Executes paper trades and feeds results back to the engine
    """

    def __init__(self, engine: DecisionEngine, symbol: str, market: str = "crypto"):
        self.engine = engine
        self.symbol = symbol
        self.market = market

        self.position = None        # None | "LONG"
        self.entry_price = None

        self.decisions_buffer: List[str] = []
        self.kill_switch = KillSwitch()
    def step(self, prices, volumes):
        # 1️⃣ قرار الذكاء
        decision_payload = self.engine.decide(prices, volumes)
        decision = decision_payload["decision"]
        confidence = decision_payload["confidence"]
        explain = decision_payload["explain"]

        current_price = prices[-1]
        pnl = 0.0

        # 2️⃣ تنفيذ وهمي (Paper Execution)
        if decision == "BUY" and self.position is None:
            self.position = "LONG"
            self.entry_price = current_price

        elif decision == "SELL" and self.position == "LONG":
            pnl = current_price - self.entry_price
            self.position = None
            self.entry_price = None
       # تحديث Kill-Switch
       self.kill_switch.update(
            pnl=pnl,
             volatility=decision_payload["risk"] == "HIGH"
       )

       if not self.kill_switch.can_trade():
           self.engine.history.append({
               "status": "KILLED",
               "reason": "Risk limits breached"
           })
           return
        # 3️⃣ تسجيل الصفقة (حتى HOLD)
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

        # 4️⃣ حفظ القرارات للاختبار
        self.decisions_buffer.append(decision)

        # 5️⃣ التعلم فقط عند إغلاق صفقة
        if pnl != 0.0 and len(self.decisions_buffer) > 10:

            # 🛑 أولًا: Gate (القاضي)
            verdict = self.engine.gate.approve(
                prices=prices[-len(self.decisions_buffer):],
                old_decisions=self.decisions_buffer[:-1],
                new_decisions=self.decisions_buffer
            )

            # ✅ فقط إذا وافق القاضي
            if verdict["approved"]:
                attribution = StrategyAttributor.attribute(
                    explain=explain,
                    realized_return=pnl
                )

                # 🔁 تحديث الأوزان
                for strategy, strat_pnl in attribution.items():
                    self.engine.weighter.update(strategy, strat_pnl)

            # 🧾 تسجيل النتيجة بوضوح
            self.engine.history.append({
                "status": "approved" if verdict["approved"] else "rejected",
                "pnl": pnl,
                "reason": verdict.get("reason"),
                "improvement": verdict.get("improvement"),
                "details": verdict
            })

            self.decisions_buffer.clear()
