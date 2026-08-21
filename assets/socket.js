//erstmal local or developmen
const socket = io("http://127.0.0.1:8050");

socket.on("connect", () => {
    console.log("Connected to SocketIO");
});

socket.on("binance_candle", (candle) => {
    console.log("Neue Candle empfangen:", candle);
    // hier kannst du dein Chart aktualisieren
});
