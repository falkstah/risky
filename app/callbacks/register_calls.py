import plotly.graph_objects as go
import pandas as pd


from app.ui_init import socketio

from sources.services import stream
from sources.services import loader

from dash import Input, Output

def register_callbacks(app, socketio=None):
    pass
