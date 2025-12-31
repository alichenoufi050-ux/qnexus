import requests
import time
from typing import List, Tuple

# =========================
# CONFIG
# =========================
Q_NEXUS_URL = "https://qnexus.onrender.com/api/decide"
API_KEY = "PUT_YOUR_API_KEY_HERE"

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

# =========================
# MARKET FETCHERS
# =========================
def fetch_crypto(
    symbol: str = "BTCUSDT",
    interval: str = "1m",
    limit: int = 50
) -> Tuple[List[float], List[float]]:

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    r = requests.get(BINANCE_KLINES, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    prices = [float(c[4]) for c in data]   # close
    volumes = [float(c[5]) for c in data]  # volume

    return prices, volumes


# =========================
# Q-NEXUS CLIENT
# =========================
def request_decision(
    prices: List[float],
    volumes: List[float],
    market_type: str
) -> dict:

    payload = {
        "prices": prices,
        "volumes": volumes,
        "context": {
            "market": market_type
        }
    }

    r = requests.post(
        Q_NEXUS_URL,
        json=payload,
        headers=HEADERS,
        timeout=10
    )
    r.raise_for_status()
    return r.json()


# =========================
# EXECUTION LOOP
# =========================
def run():
    while True:
        try:
            prices, volumes = fetch_crypto("BTCUSDT", "1m")
            decision = request_decision(
                prices=prices,
                volumes=volumes,
                market_type="crypto"
            )

            print("Q-NEXUS:", decision)

        except Exception as e:
            print("ERROR:", str(e))

        time.sleep(60)


if __name__ == "__main__":
    run()
