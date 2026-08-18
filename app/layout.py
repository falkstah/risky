from dash import html, dcc
from config.settings import APP_TITLE
from sources.services.loader import load_data
from sources.services.processor import process_data
from sources.services.plotter import create_plot

def create_layout():
    df = load_data()
    df_processed = process_data(df)
    fig = create_plot(df_processed)

    return html.Div(
        children=[
            dcc.Graph(id="live-plot", figure=fig, style={"height": "100vh"}),
            html.Div(
                id="chat-controls",
                className="chart-controls",
                children=[
                    html.Div(APP_TITLE, style={"fontWeight": "600", "marginBottom": "6px"}),
                    html.Button("Action", id="control-btn"),
                ],
                style={
                    "width": "150px",
                    "height": "80px",
                    "backgroundColor": "#333",
                    "color": "white",
                    "padding": "10px",
                    "borderRadius": "8px",
                    "position": "absolute",
                    "top": "20px",
                    "left": "20px",
                    "zIndex": "9999",
                    "cursor": "grab"
                }
            )
        ]
    )
