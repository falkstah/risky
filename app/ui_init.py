import os
from flask import Flask
from flask_socketio import SocketIO
from dash import Dash

# Flask-Server & SocketIO Initialisierung
server = Flask(__name__)
server.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "replace-with-secure-key")

socketio = SocketIO(server, cors_allowed_origins="*", async_mode="threading")

# Absoluter Pfad zum Assets-Ordner (behebt etwaige Pfad-Mismatches)
ASSETS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

# Dash-Instanz
app = Dash(
    __name__,
    server=server,  # type: ignore[arg-type]
    suppress_callback_exceptions=True,
    assets_folder=ASSETS_PATH,
    assets_url_path="/assets"
)

# Custom Index Template mit type="module" für script.js
app.index_string = '''<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
            <script type="module" src="/assets/module_folder/script.js"></script>
        </footer>
    </body>
</html>
'''