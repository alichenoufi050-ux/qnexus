# db/history.py
from typing import List, Dict, Optional
import time
import uuid

# =========================
# IN-MEMORY STORAGE (Phase 3)
# =========================
TRADE_HISTORY: List[Dict] = []

# =========================
# LOGGING
# =========================
def log_trade(
    *,
    market: str,
    symbol: str,
    strategy: str,
    decision: str,
    price: float,
    confidence: float,
    volume: float,
    pnl: float = 0.0,
    meta: Optional[Dict] = None
) -> Dict:
    """
    Immutable trade record
    """
    record = {
        "id": str(uuid.uuid4()),
        "market": market,
        "symbol": symbol,
        "strategy": strategy,
        "decision": decision,
        "price": price,
        "volume": volume,
        "confidence": confidence,
        "pnl": pnl,
        "meta": meta or {},
        "timestamp": int(time.time())
    }

    TRADE_HISTORY.append(record)
    return record

# =========================
# QUERY
# =========================
def get_history(
    market: Optional[str] = None,
    strategy: Optional[str] = None
) -> List[Dict]:
    data = TRADE_HISTORY

    if market:
        data = [t for t in data if t["market"] == market]

    if strategy:
        data = [t for t in data if t["strategy"] == strategy]

    return data

# =========================
# METRICS
# =========================
def calculate_pnl() -> float:
    return sum(t["pnl"] for t in TRADE_HISTORY)

def win_rate() -> float:
    wins = [t for t in TRADE_HISTORY if t["pnl"] > 0]
    return len(wins) / len(TRADE_HISTORY) if TRADE_HISTORY else 0.0
