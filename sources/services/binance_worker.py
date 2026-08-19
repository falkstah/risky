import time
import json
import requests
import ssl
from app.ui_init import socketio
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager

class SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

# SSL‑Kontext mit niedrigerem Security‑Level
tls = ssl.create_default_context()
tls.set_ciphers("DEFAULT@SECLEVEL=1")

# Session mit angepasstem Adapter
session = requests.Session()
session.mount("https://", SSLAdapter(ssl_context=tls))

def fetch_latest_candle(interval="1m"):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": interval, "limit": 1}
    response = session.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()[0]

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
