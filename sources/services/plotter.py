# sources/plotter.py
import plotly.graph_objs as go

def create_plot(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["x"],
        y=df["y"],
        mode="lines+markers",
        name="Beispielplot"
    ))
    fig.update_layout(title="Datenvisualisierung")
    return fig
