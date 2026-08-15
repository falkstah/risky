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
    #timeframe selecion
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

        #Toolbox
        html.Div(
            className="content-area",
            children=[
                dcc.Graph(id="live-chart"),
                html.Div(
                    className="toolbox",
                    children=[
                        html.Div("Linien", className="toolbox-title"),
                        html.Div("Entry", id="tool-entry", className="tool-item"),
                        html.Div("TP", id="tool-tp", className="tool-item"),
                        html.Div("SL", id="tool-sl", className="tool-item"),
                    ]
                )
            ]
        ),

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
        # Range der letzten 30 Kerzen
        return go.Figure()

    #scaling default line levels for easonable scaling
    low_range = df["low"].min()
    high_range = df["high"].max()
    entry_price = df["close"].iloc[-1]
    tp_price = entry_price * 1.0001  # optional: leicht über Entry
    # SL innerhalb der sichtbaren Range
    sl_price = max(low_range, entry_price * 0.99995)
    
    fig = go.Figure()

    # Candles
    fig.add_trace(
        go.Candlestick(
            x=df["t"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="BTCUSDT"
        )
    )

    # Unsichtbarer Punkt für Platz rechts, to draw entry lines
    extra_time = df["t"].max() + pd.Timedelta(minutes=10)

    #drag and drop menu:
    entry_price = df["close"].iloc[-1]
    tp_price = entry_price * 1.01
    sl_price = entry_price * 0.99

    fig.add_trace(
        go.Scatter(
            x=[extra_time],
            y=[df["close"].iloc[-1]],
            mode="markers",
            marker=dict(opacity=0),
            showlegend=False,
            hoverinfo="skip"
        )
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=None,
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),

        #drag menu
        shapes=[
            dict(
                type="line",
                xref="x",  # echte Zeitachse
                yref="y",
                x0=df["t"].max(),  # Start bei letzter Kerze
                x1=df["t"].max() + pd.Timedelta(minutes=120),  # weit nach rechts
                y0=entry_price,
                y1=entry_price,
                line=dict(color="blue", width=2),
                editable=True
            ),
            # TP
            dict(
                type="line",
                xref="x",
                yref="y",
                x0=df["t"].max(),
                x1=df["t"].max() + pd.Timedelta(minutes=120),
                y0=tp_price,
                y1=tp_price,
                line=dict(color="green", width=2),
                editable=True
            ),
            # SL
            dict(
                type="line",
                xref="x",
                yref="y",
                x0=df["t"].max(),
                x1=df["t"].max() + pd.Timedelta(minutes=120),
                y0=sl_price,
                y1=sl_price,
                line=dict(color="red", width=2),
                editable=True
            )
        ]
    )

    return fig

# ---------------------------------------------------------
# Starten
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
