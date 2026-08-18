from app.ui_init import app, server, socketio
from app.layout import create_layout
from app.callbacks import register_callbacks

from sources.services.binance_worker import start_binance_polling
from threading import Thread


# Binance Worker starten
Thread(target=start_binance_polling, daemon=True).start()


# Layout setzen
app.layout = create_layout()

# Callbacks registrieren
register_callbacks(app, socketio)

if __name__ == "__main__":
    # socketio.run damit Dash + SocketIO zusammen laufen
    socketio.run(server, host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 8050)), debug=True)
