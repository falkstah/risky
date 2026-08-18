import os
from dash import Dash, html, dcc
import plotly.graph_objs as go

# --- Eigene Module laden ---
from sources.services.loader import load_data
from sources.services.processor import process_data
from sources.services.plotter import create_plot
from config.settings import APP_TITLE


# --- Dash App initialisieren ---
app = Dash(__name__)

# --- Datenpipeline ---
df = load_data()
df_processed = process_data(df)
fig = create_plot(df_processed)

# --- Layout ---
app.layout = html.Div(
    children=[
        html.H1(APP_TITLE),
        dcc.Graph(figure=fig)
    ],
    style={"padding": "20px"}
)

# --- Serverstart für Render ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port)
