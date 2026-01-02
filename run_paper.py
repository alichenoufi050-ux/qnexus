"""
Q-NEXUS OMEGA — Paper Trading Runtime
- Fault-tolerant
- Observable
- Deterministic timing
- Ready for live upgrade
"""

import time
import logging
import signal
import sys
from datetime import datetime

from core.paper_trader import PaperTrader
from core.engine import DecisionEngine
from data.market_feed import fetch_crypto


# =========================
# CONFIG
# =========================
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
LOOP_SECONDS = 60
MAX_RETRIES = 3


# =========================
# LOGGING (Production Style)
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("Q-NEXUS")


# =========================
# GRACEFUL SHUTDOWN
# =========================
RUNNING = True

def shutdown_handler(sig, frame):
    global RUNNING
    logger.warning("⛔ Shutdown signal received. Stopping safely...")
    RUNNING = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# =========================
# ENGINE BOOTSTRAP
# =========================
def bootstrap():
    engine = DecisionEngine()
    trader = PaperTrader(engine, symbol=SYMBOL, market="crypto")
    logger.info("🚀 Q-NEXUS Paper Trader initialized")
    return engine, trader


# =========================
# MAIN LOOP
# =========================
def run():
    engine, trader = bootstrap()

    retry_count = 0
    last_tick = None

    while RUNNING:
        start = time.time()

        try:
            prices, volumes = fetch_crypto(SYMBOL, INTERVAL)

            # --- Safety check ---
            if len(prices) < 20:
                logger.warning("⚠️ Not enough market data, skipping tick")
                time.sleep(LOOP_SECONDS)
                continue

            trader.step(prices, volumes)
            retry_count = 0

            last_tick = datetime.utcnow().isoformat()
            logger.info("✅ Tick executed | last_tick=%s", last_tick)

        except Exception as e:
            retry_count += 1
            logger.exception("❌ Runtime error (%d/%d)", retry_count, MAX_RETRIES)

            if retry_count >= MAX_RETRIES:
                logger.critical("🔥 Max retries reached. Shutting down.")
                break

        # --- Deterministic timing ---
        elapsed = time.time() - start
        sleep_time = max(0.0, LOOP_SECONDS - elapsed)
        time.sleep(sleep_time)

    logger.info("🧠 Q-NEXUS stopped cleanly")
    sys.exit(0)


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run()
