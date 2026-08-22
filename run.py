from app.ui_init import app, server, socketio
from app.layout import create_layout
from app.callbacks.register_calls import register_callbacks

from sources.services.binance_worker import start_binance_polling
from threading import Thread

import os

#print(">>> CSS-Dateien im assets/:", os.listdir("assets"))

# Layout setzen
app.layout = create_layout()

# Callbacks registrieren
register_callbacks(app, socketio)



#switches between modes if code is tested locally
if __name__ == "__main__":

    # Binance Worker starten, thread is used to not block the server
    #Thread(target=start_binance_polling, daemon=True).start()   --not used bc blocks
    socketio.start_background_task(start_binance_polling)

    # Lokaler Testmodus
    LOCAL_MODE = True

    if LOCAL_MODE:        
        socketio.run(
            server,
            host="127.0.0.1",
            port=8050,
            debug=False,
            use_reloader = False,
        )
    else:
        # Produktionsmodus (z. B. Render, Heroku, etc.)
        socketio.run(
            server,
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 8050)),
            debug=False,
            use_reloader = False,
        )

        
