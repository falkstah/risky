import json
import threading
import pandas as pd
from websocket import WebSocketApp
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import requests


#shows last 30 candles of given tf
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

# ---------------------------------------------------------
# Globale Variablen
# ---------------------------------------------------------
current_interval = "1m"  # Standard-Timeframe
df = load_initial_candles(current_interval)


# ---------------------------------------------------------
# WebSocket Callback
# ---------------------------------------------------------
def on_message(ws, message):
    global df
    msg = json.loads(message)
    k = msg["k"]

    candle = {
        "t": pd.to_datetime(k["t"], unit="ms"),
        "open": float(k["o"]),
        "high": float(k["h"]),
        "low": float(k["l"]),
        "close": float(k["c"])
    }

    df = df[df["t"] != candle["t"]]
    df = pd.concat([df, pd.DataFrame([candle])]).sort_values("t")

    # Nur die letzten 30 Kerzen behalten
    if len(df) > 30:
        df = df.tail(30)

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed:", close_status_code, close_msg)

def start_ws():
    url = f"wss://stream.binance.com:9443/ws/btcusdt@kline_{current_interval}"
    ws = WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.run_forever()

# ---------------------------------------------------------
# WebSocket in separatem Thread starten
# ---------------------------------------------------------
ws_thread = threading.Thread(target=start_ws)
ws_thread.daemon = True
ws_thread.start()

# ---------------------------------------------------------
# Dash App
# ---------------------------------------------------------
app = Dash(__name__)

app.layout = html.Div(
    className="app-container",
    children=[
        html.H2("Live BTCUSDT Candles (Binance)"),
        dcc.Dropdown(
            id="timeframe",
            options=[
                {"label": "1 Minute", "value": "1m"},
                {"label": "5 Minuten", "value": "5m"},
                {"label": "15 Minuten", "value": "15m"},
                {"label": "1 Stunde", "value": "1h"},
            ],
            value="1m",
            clearable=False,
            style={"width": "200px", "margin": "10px"}
        ),
        dcc.Graph(id="live-chart"),
        dcc.Interval(id="interval", interval=2000, n_intervals=0)
    ]
)

# ---------------------------------------------------------
# Callback für Timeframe-Wechsel
# ---------------------------------------------------------
@app.callback(
    Output("live-chart", "figure"),
    Input("interval", "n_intervals"),
    Input("timeframe", "value")
)
def update_chart(_, timeframe):
    global df, current_interval

    # Wenn Timeframe geändert wurde → neuen Stream starten
    if timeframe != current_interval:
        current_interval = timeframe
        df = load_initial_candles(current_interval)  # <-- historische Kerzen laden
        threading.Thread(target=start_ws, daemon=True).start()

    if df.empty:
        return go.Figure()

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["t"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"]
            )
        ]
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=None,
        margin=dict(l=0, r=0, t=0, b=0),
        autosize = True

        #padding in chart, to have space for entry lines
        xaxis=dict(
        range=[
            df["t"].min(),
            df["t"].max() + pd.Timedelta(minutes=5)  # Platz rechts
        ]
    )
    )

    return fig

# ---------------------------------------------------------
# Starten
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
