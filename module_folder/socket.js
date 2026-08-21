// module_folder/socket.js

export async function initSocket() {
    // 1. Prüfen, ob io (z. B. via Script-Tag im HTML) global verfügbar ist
    const ioFunc = window.io || (await import('/socket.io/socket.io.js')).default;

    console.log('[socket] Verbinde mit SocketIO...');
    
    // Eine einzige Instanz erzeugen
    const socket = ioFunc("http://127.0.0.1:8050", {
        transports: ["websocket"]
    });

    let candles = [];

    // Promise zurückgeben, damit modules.js auf 'connect' warten kann
    return new Promise((resolve) => {
        socket.on("connect", () => {
            console.log("[socket] Erfolgreich verbunden! ID:", socket.id);

            // Listener erst registrieren, wenn der Socket bereit ist
            socket.on("binance_candle", (candle) => {
                if (!candle || !candle.t || !candle.c) return;

                candles.push(candle);
                if (candles.length > 100) {
                    candles = candles.slice(-100);
                }

                const chartEl = document.getElementById("live-chart");
                if (chartEl && window.Plotly) {
                    Plotly.react(chartEl, {
                        data: [{
                            x: candles.map(c => new Date(c.t)),
                            y: candles.map(c => parseFloat(c.c)),
                            type: "scatter",
                            mode: "lines",
                            line: { color: "#00ccff" }
                        }],
                        layout: {
                            title: "BTCUSDT Live",
                            margin: { t: 40 }
                        }
                    });
                }
            });

            socket.on("timeframe_changed", () => {
                candles = [];
                const chartEl = document.getElementById("live-chart");
                if (chartEl && window.Plotly) {
                    Plotly.react(chartEl, {
                        data: [],
                        layout: {
                            title: "BTCUSDT Live",
                            margin: { t: 40 }
                        }
                    });
                }
            });

            resolve(socket);
        });
    });
}

export function onSocketEvent(socket, event, handler) {
    socket.on(event, handler);
}