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
    className="chart-wrapper",
    children=[
        #heading
        html.H2("Live BTCUSDT Candles (Binance)", className="chart-title"),

        #chart area
        html.Div(
            className="chart-area",
            children=[
                #candles
                dcc.Graph(
                    id="live-chart",
                    config = {"editable": True, "scrollZoom": True}
                ),

                #toolbox
                html.Div(
                    className="chart-controls",
                    children=[
                        #tf-selection
                        dcc.Dropdown(
                            id="timeframe-dropdown",
                            options=[
                                {"label": "1 Minute", "value": "1m"},
                                {"label": "5 Minuten", "value": "5m"},
                                {"label": "15 Minuten", "value": "15m"},
                                {"label": "1 Stunde", "value": "1h"},
                            ],
                            value="1m",
                            clearable=False,
                            className="timeframe-dropdown"
                        ),

                        #drag-menu
                        html.Div(
                            className="drag-menu",
                            children=[
                                html.Div("Entry", id="tool-entry", className="tool-item", draggable= "true"),
                                html.Div("TP", id="tool-tp", className="tool-item", draggable= "true"),
                                html.Div("SL", id="tool-sl", className="tool-item", draggable= "true"),
                            ]
                        )
                    ]
                )
            ]
        ),

        #timer to stat callback every 2 scnds:
        dcc.Interval(id="interval", interval=2000, n_intervals=0)
    ]
)


# ---------------------------------------------------------
# Callback für Timeframe-Wechsel
# ---------------------------------------------------------
@app.callback(
    Output("live-chart", "figure"),

    #input-list:
    [
        Input("interval", "n_intervals"),
        Input("timeframe-dropdown", "value"),

        #chat interaction inputs:
        #Buttons:
        Input("live-chart", "relayoutData"),
        Input("tool-entry", "n_clicks"),
        Input("tool-tp", "n_clicks"),
        Input("tool-sl", "n_clicks"),
    ],
    prevent_initial_call= True
)

def update_chart(_, timeframe, relayoutData, entry_clicks, tp_clicks, sl_clicks):
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

    #line buttons clicks.
    shapes = []

    # Wenn Entry geklickt wurde
    if entry_clicks and entry_clicks > 0:
        shapes.append(dict(
            type="line",
            xref="x",
            yref="y",
            x0=df["t"].max(),
            x1=df["t"].max() + pd.Timedelta(minutes=120),
            y0=df["close"].iloc[-1],
            y1=df["close"].iloc[-1],
            line=dict(color="blue", width=2),
            editable=True
        ))

    # Wenn TP geklickt wurde
    if tp_clicks and tp_clicks > 0:
        shapes.append(dict(
            type="line",
            xref="x",
            yref="y",
            x0=df["t"].max(),
            x1=df["t"].max() + pd.Timedelta(minutes=120),
            y0=df["close"].iloc[-1] * 1.01,
            y1=df["close"].iloc[-1] * 1.01,
            line=dict(color="green", width=2),
            editable=True
        ))

    # Wenn SL geklickt wurde
    if sl_clicks and sl_clicks > 0:
        shapes.append(dict(
            type="line",
            xref="x",
            yref="y",
            x0=df["t"].max(),
            x1=df["t"].max() + pd.Timedelta(minutes=120),
            y0=df["close"].iloc[-1] * 0.99,
            y1=df["close"].iloc[-1] * 0.99,
            line=dict(color="red", width=2),
            editable=True
        ))


    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=None,
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),
        shapes = shapes
    )



    return fig

# ---------------------------------------------------------
# Starten
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
