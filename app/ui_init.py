import os
from flask import Flask
from flask_socketio import SocketIO
from dash import Dash

server = Flask(__name__)
server.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "replace-with-secure-key")

# socketio optional, falls du es brauchst
#ggfs. asynch_mode = gevent erzwingen, wenn auf render dopleyed, auf windows lokal nur threading!
socketio = SocketIO(server, cors_allowed_origins="*", async_mode="threading")


# Dash app gebunden an Flask server
#the type ignore is used to ignore th arg error that is a bug?
import os
from dash import Dash

app = Dash(
    __name__,
    server=server, # type: ignore[arg-type]
    suppress_callback_exceptions=True,
    assets_folder=os.path.join(os.path.dirname(__file__), "..", "assets"),
    assets_url_path="/assets"
)
