import json
import pandas as pd
from flask_socketio import emit
from app.ui_init import socketio

current_interval = "1m"
df = pd.DataFrame()

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
    k = json.loads(message)["k"]
    candle = update_df_from_binance(k)

    # Broadcast an alle Clients
    emit("update_chart", candle, broadcast=True)
