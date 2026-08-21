
import { io } from 'https://cdn.socket.io/4.7.5/socket.io.esm.min.js';

export async function initSocket() {
    console.log('[socket] Verbinde mit SocketIO...');
    
    const socket = io({
        transports: ["websocket"]
    });

    return new Promise((resolve, reject) => {
        socket.on("connect", () => {
            console.log("[socket] Erfolgreich verbunden! ID:", socket.id);
            resolve(socket);
        });

        socket.on("connect_error", (err) => {
            console.error("[socket] Verbindungsfehler:", err);
            reject(err);
        });
    });
}