/*0_ in name bc has to be loaded first. makes io globally available:*/
// Socket.IO‑Client dynamisch laden
const script = document.createElement("script");
script.src = "https://cdn.socket.io/4.7.2/socket.io.min.js";
script.onload = () => console.log("Socket.IO‑Client geladen");
document.head.appendChild(script);
