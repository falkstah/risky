from dash import Input, Output

def register_callbacks(app, socketio=None):
    @app.callback(
        Output("live-plot", "figure"),
        Input("control-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def on_control(n_clicks):
        # Beispiel: bei Klick etwas am Plot ändern oder Daten neu laden
        from sources.services.loader import load_data
        from sources.services.processor import process_data
        from sources.services.plotter import create_plot

        df = load_data()
        df_processed = process_data(df)
        fig = create_plot(df_processed)
        return fig
