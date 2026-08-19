import pandas as pd
import requests
from requests.adapters import HTTPAdapter

session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=3))

def load_initial_candles(interval):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": interval,
        "limit": 30
    }
    
     # stable HTTPS‑Request
    response = session.get(url, params=params, timeout=5)
    response.raise_for_status()   # wirft klaren Fehler statt SSL‑Chaos
    data = response.json()

    rows = []
    for value in data:
        rows.append({
                "t": pd.to_datetime(value[0], unit="ms"),
            "open": float(value[1]),
            "high": float(value[2]),
            "low": float(value[3]),
            "close": float(value[4])
        })

    return pd.DataFrame(rows)


def fetch_latest_candle(interval="1m"):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": interval, "limit": 1}
    response = session.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()[0]
