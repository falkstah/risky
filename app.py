import os
from dash import Dash, html

app = Dash(__name__)
app.layout = html.Div("Hello from Render!")

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
