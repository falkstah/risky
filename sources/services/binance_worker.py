import time
import json
import requests
import ssl
from app.ui_init import socketio
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
import traceback

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
    tls = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    tls.set_ciphers("DEFAULT@SECLEVEL=1")

    session = requests.Session()
    session.mount("https://", SSLAdapter(ssl_context=tls))
    return session


def fetch_latest_candle(session, interval="1m"):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": interval, "limit": 1}

    try:
        print("Hole Candle von Binance…")
        response = session.get(url, params=params, timeout=10)

        print("Antwort erhalten")
        response.raise_for_status()
        return response.json()[0]

    except requests.exceptions.RequestException as e:
        print("Request error:", type(e).__name__, "-", e)
        return None

    #für besondere fehler:
    except Exception as e:
        print("Unerwarteter Fehler:", type(e).__name__, "-", e)
        traceback.print_exc()
        return None




def start_binance_polling(interval="1m"):
    print("Binance Worker (polling) wurde gestartet")

    session = create_session()

    while True:
        print("Worker Loop tick")

        c = fetch_latest_candle(session, interval)
        if c is None:
            time.sleep(2)   #leaves more time for binance to fix error
            continue

        candle = {
            "t": c[0],
            "o": c[1],
            "h": c[2],
            "l": c[3],
            "c": c[4]
        }

        socketio.emit("binance_candle", candle)
        time.sleep(1)

