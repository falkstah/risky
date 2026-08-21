const socket = io();   // automatisch korrekt verbinden

let candles = [];      // hier speichern wir alle Candles

socket.on("connect", () => {
    console.log("Connected to SocketIO");
});

// Worker sendet Candle
socket.on("binance_candle", (candle) => {
    console.log("Neue Candle empfangen:", candle);

    // Schutz gegen kaputte Candles
    if (!candle || !candle.t || !candle.c) return;

    candles.push(candle);

    // nur die letzten 100 behalten
    if (candles.length > 100) {
        candles = candles.slice(-100);
    }

    // Plotly-Chart aktualisieren
    Plotly.react("live-chart", {
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
});

// Timeframe-Wechsel → Candle-Array leeren + Chart resetten
socket.on("timeframe_changed", () => {
    candles = [];

    Plotly.react("live-chart", {
        data: [],
        layout: {
            title: "BTCUSDT Live",
            margin: { t: 40 }
        }
    });
});
