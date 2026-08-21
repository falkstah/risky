// Socket.IO‑Client laden
const socketioScript = document.createElement("script");
socketioScript.src = "https://cdn.socket.io/4.7.2/socket.io.min.js";
socketioScript.onload = () => {
  console.log("Socket.IO Client geladen");
};

// Plotly laden
const plotlyScript = document.createElement("script");
plotlyScript.src = "https://cdn.plot.ly/plotly-2.27.0.min.js";
plotlyScript.onload = () => console.log("Plotly geladen");

document.head.appendChild(socketioScript);
document.head.appendChild(plotlyScript);
