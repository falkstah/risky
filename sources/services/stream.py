import json
import pandas as pd
from flask_socketio import emit
from app.ui_init import socketio
import threading
from sources.services.binance_worker import fetch_latest_candle, create_session

current_interval = None
worker_thread = None
stop_event = threading.Event()
lock = threading.Lock()

df = pd.DataFrame(columns=["t", "open", "high", "low", "close"]) # wird vom Worker aktualisiert

def get_interval():
    return current_interval

def set_interval(interval):
    global current_interval
    with lock:
        current_interval = interval

def restart_stream():
    global worker_thread, stop_event

    with lock:
        # alten Stream stoppen
        stop_event.set()
        if worker_thread and worker_thread.is_alive():
            worker_thread.join(timeout=2)

        # neuen Stop-Event erzeugen
        stop_event = threading.Event()

        # neuen Worker starten
        worker_thread = threading.Thread(
            target=run_stream,
            args=(current_interval, stop_event),
            daemon=True
        )
        worker_thread.start()

def run_stream(interval, stop_event):
    global df
    print(f"Starte Stream für", interval)

    # Session aus binance_worker holen
    session = create_session()

    while not stop_event.is_set():
        k = fetch_latest_candle(session, interval)
        if k is None:
            continue

        # Binance liefert ein RAW-Array → in Dict umwandeln
        candle = {
            "t": k[0],
            "o": k[1],
            "h": k[2],
            "l": k[3],
            "c": k[4]
        }

        # df aktualisieren
        update_df_from_binance(candle)

        # Live-Update an UI senden
        socketio.emit("binance_candle", candle)



def update_df_from_binance(k):
    global df

    candle = {
        "t": pd.to_datetime(k["t"], unit="ms"),
        "open": float(k["o"]),
        "high": float(k["h"]),
        "low": float(k["l"]),
        "close": float(k["c"])
    }

    # alte Kerze ersetzen
    df = df[df["t"] != candle["t"]]
    df = pd.concat([df, pd.DataFrame([candle])]).sort_values("t")

    # nur 30 Kerzen behalten
    if len(df) > 30:
        df = df.tail(30)

    return candle

# SocketIO Event: Binance Worker sendet neue Candle
@socketio.on("binance_candle")
def handle_binance_candle(message):
    candle = json.loads(message)

    # Broadcast an alle Clients
    emit("binance_candle", candle, broadcast=True)

