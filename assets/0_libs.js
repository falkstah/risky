// Socket.IO-Client laden
const socketioScript = document.createElement("script");
socketioScript.src = "https://cdn.socket.io/4.7.2/socket.io.min.js";
document.head.appendChild(socketioScript);

// Plotly laden
const plotlyScript = document.createElement("script");
plotlyScript.src = "https://cdn.plot.ly/plotly-latest.min.js";
document.head.appendChild(plotlyScript);

plotlyScript.onload = () => console.log("Plotly geladen");
