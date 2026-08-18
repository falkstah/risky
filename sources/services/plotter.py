import plotly.graph_objects as go


def create_plot(df):
    """Erstellt aus einem Pandas DataFrame mit Binance-Kerzen ein Plotly Candlestick-Figure.

    Erwartete Spalten: 't' (Datetime), 'open', 'high', 'low', 'close'
    """
    fig = go.Figure()

    # Falls der DataFrame leer ist, leeres Figure zurückgeben
    if df is None or df.empty:
        fig.update_layout(template="plotly_dark")
        return fig

    # Candlestick Trace hinzufügen
    fig.add_trace(
        go.Candlestick(
            x=df["t"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="BTCUSDT",
        )
    )

    # Dark-Mode Layout & kompakte Ränder
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=10, b=10),
        autosize=True,
    )

    return fig