import os
from flask import Flask
from flask_socketio import SocketIO
from dash import Dash

server = Flask(__name__)
server.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "replace-with-secure-key")

# socketio optional, falls du es brauchst
socketio = SocketIO(server, async_mode= "gevent", cors_allowed_origins="*")

# Dash app gebunden an Flask server
#the type ignore is used to ignore th arg error that is a bug?
app = Dash(__name__, server, suppress_callback_exceptions = True) # type: ignore[arg-type]
