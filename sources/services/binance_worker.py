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
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)

# SSL‑Kontext mit niedrigerem Security‑Level
def create_session():
    tls = ssl.create_default_context()
    tls.set_ciphers("DEFAULT@SECLEVEL=1")

    session = requests.Session()
    session.mount("https://", SSLAdapter(ssl_context=tls))
    return session


def fetch_latest_candle(session, interval="1m"):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": interval, "limit": 1}
    response = session.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()[0]

def start_binance_polling(interval="1m"):
    print("Binance Worker (polling) wurde gestartet")

    session = create_session()

    while True:
        print("Worker Loop tick")

        try:
            candle = fetch_latest_candle(session, interval)
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
