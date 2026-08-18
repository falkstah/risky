from dash import html, dcc
from config.settings import APP_TITLE
from sources.services.loader import load_initial_candles
from sources.services.processor import process_data
from sources.services.plotter import create_plot

def create_layout():
    # ---------------------------------------------------------
    # Globale Variablen
    # ---------------------------------------------------------
    current_interval = "1m"  # Standard-Timeframe
    df = load_initial_candles(current_interval)
    df_processed = process_data(df)
    fig = create_plot(df_processed)


    return html.Div(
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
        
                #dummy:
                dcc.Store(id="dummy-store"),
        
        
                #timer to stat callback every 2 scnds:
                dcc.Interval(id="interval", interval=2000, n_intervals=0)
            ]
    )
