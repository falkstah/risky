import pandas as pd
import requests


def load_initial_candles(interval):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": interval,
        "limit": 30
    }
    data = requests.get(url, params=params).json()

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

