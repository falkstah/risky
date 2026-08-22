import { io } from 'https://cdn.socket.io/4.7.5/socket.io.esm.min.js';

let socketInstance = null;

export async function initSocket() {
    // 1. Wenn die Verbindung schon existiert, bestehende Instanz zurückgeben
    if (socketInstance) {
        console.log('[socket] Bestehende SocketIO-Verbindung wird wiederverwendet.');
        return socketInstance;
    }

    console.log('[socket] Verbinde mit SocketIO...');

    // 2. Neue Instanz erstellen und im Singleton speichern
    socketInstance = io({
        transports: ["websocket"]
    });

    // 3. Globale Event-Listener nur einmalig registrieren
    socketInstance.on("connect", () => {
        console.log("[socket] Erfolgreich verbunden! ID:", socketInstance.id);
    });

    socketInstance.on("connect_error", (err) => {
        console.error("[socket] Verbindungsfehler:", err);
    });

    socketInstance.on("disconnect", (reason) => {
        console.warn("[socket] Verbindung getrennt:", reason);
    });

    // 4. Warten, bis die Verbindung beim ersten Start bereit ist
    if (!socketInstance.connected) {
        await new Promise((resolve) => {
            socketInstance.once("connect", resolve);
        });
    }

    return socketInstance;
}