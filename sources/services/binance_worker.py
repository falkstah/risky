import time
import json
import requests
from app.ui_init import socketio


def fetch_latest_candle(interval="1m"):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": interval, "limit": 1}
    data = requests.get(url, params=params).json()
    return data[0]


def start_binance_polling(interval="1m"):
    while True:
        try:
            candle = fetch_latest_candle(interval)
            message = {
                "k": {
                    "t": candle[0],
                    "o": candle[1],
                    "h": candle[2],
                    "l": candle[3],
                    "c": candle[4]
                }
            }
            socketio.emit("binance_candle", json.dumps(message))
        except Exception as e:
            print("Polling error:", e)

        time.sleep(1)
