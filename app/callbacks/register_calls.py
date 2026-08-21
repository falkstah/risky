import plotly.graph_objects as go
import pandas as pd


from app.ui_init import socketio

from sources.services import stream
from sources.services import loader

from dash import Input, Output

def register_callbacks(app, socketio=None):
    @app.callback(
        Output("live-plot", "figure"),
        Input("control-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def on_control(n_clicks):
        # Beispiel: bei Klick etwas am Plot ändern oder Daten neu laden
        from sources.services.loader import load_initial_candles
        from sources.services.processor import process_data
        from sources.services.plotter import create_plot

        df = load_initial_candles(stream.get_interval)
        df_processed = process_data(df)
        fig = create_plot(df_processed)
        return fig



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
            Input("tool-entry", "n_clicks"),
            Input("tool-tp", "n_clicks"),
            Input("tool-sl", "n_clicks"),
        ],
    )

    def update_chart(_, timeframe, entry_clicks, tp_clicks, sl_clicks):
        #inherit values from stream.py
        current_interval = stream.get_interval()
        df = stream.df

        # Wenn Timeframe geändert wurde → neuen Stream starten
        if timeframe != current_interval:
            current_interval = timeframe
            df = loader.load_initial_candles(current_interval)  # <-- historische Kerzen laden

        if df.empty:
            # Range der letzten 30 Kerzen
            return go.Figure()

        #scaling default line levels for reasonable scaling
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


    @app.callback(
        Output("dummy-store", "data"),
        Input("live-chart", "relayoutData")
    )

    def handle_drop(relayoutData):
        return relayoutData

