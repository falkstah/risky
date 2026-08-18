import time
import json
import requests
import socketio

sio = socketio.Client()

def connect_to_server():
    try:
        sio.connect("http://localhost:8050")
        print("Connected to Flask-SocketIO server")
    except Exception as e:
        print("SocketIO connection failed:", e)

def fetch_latest_candle(interval="1m"):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": interval, "limit": 1}
    data = requests.get(url, params=params).json()
    return data[0]  # letzte Kerze

def start_binance_polling(interval="1m"):
    connect_to_server()

    while True:
        try:
            candle = fetch_latest_candle(interval)
            message = json.dumps({"k": {
                "t": candle[0],
                "o": candle[1],
                "h": candle[2],
                "l": candle[3],
                "c": candle[4]
            }})
            sio.emit("binance_candle", message)
        except Exception as e:
            print("Polling error:", e)

        time.sleep(1)  # Polling-Intervall
