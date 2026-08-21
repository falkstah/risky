// assets/script.js

// 1. Wartet, bis die HTML-Struktur (DOM) vollständig vom Browser geladen wurde.
// async erlaubt uns, im Event-Handler das Keyword 'await' für asynchrone Imports zu nutzen.
window.addEventListener('DOMContentLoaded', async () => {
    
    // 2. Kontroll-Log zur Verfolgung der Ausführungsreihenfolge in den Browser-DevTools.
    console.log('[script.js] Starte Modul-Ladevorgang...');

    // 3. Öffnet einen Schutzblock: Jeder Fehler beim Laden fängt hier ab, ohne die App stumm abstürzen zu lassen.
    try {
        
        // 4. Lädt die modules.js dynamisch von der Flask-Route /module_folder/.
        // await pausiert die Ausführung an dieser Zeile, bis der HTTP-Download der Datei abgeschlossen ist.
        const modules = await import('/module_folder/modules.js');

        // 5. Sicherheitsprüfung: Überprüft, ob die Datei existiert und die Funktion initModules() auch wirklich exportiert wurde.
        if (!modules || typeof modules.initModules !== 'function') {
            
            // 6. Wirft explizit einen Fehler, falls die Funktion fehlt, und springt direkt in den catch-Block.
            throw new Error('modules.js konnte initModules() nicht bereitstellen!');
        }

        // 7. Führt initModules() aus modules.js aus und wartet per await, bis libs.js und der Socket-Handshake bereitstehen.
        // Das Ergebnis wird direkt in die zwei Variablen 'libs' und 'socket' entpackt (Destructuring).
        const { libs, socket } = await modules.initModules();

        // 8. Zweite Sicherheitsprüfung: Stellt sicher, dass weder libs noch socket undefined oder null zurückgegeben haben.
        if (!libs || !socket) {
            
            // 9. Wirft einen Fehler, wenn eines der Module bei der Initialisierung fehlgeschlagen ist.
            throw new Error('Module unvollständig: libs oder socket fehlen!');
        }

        // 10. Erfolgsbestätigung in der Konsole: Die gesamte Import- und Verbindungs-Kette steht zu 100 %.
        console.log('✅ ALLE MODULE ERFOLGREICH GELADEN & VERIFIZIERT');

        // 11. Übergibt die fertigen Instanzen an die Hauptfunktion und startet erst jetzt die Anwendungslogik.
        startApp(libs, socket);

    // 12. Fängt alle Fehler ab, die im try-Block aufgetreten sind (Network 404/500, Syntax-Fehler, abgebrochene Sockets).
    } catch (err) {
        
        // 13. Gibt die genaue Ursache rot hervorgehoben in der Browser-Konsole aus.
        console.error('❌ KRITISCHER LADEFEHLER:', err);
    }
});

// 14. Hauptfunktion für deine App-Steuerung. Sie empfängt libs und socket als geprüfte Argumente.
function startApp(libs, socket) {
    
    // 15. Nutzt die log()-Funktion aus deiner geladenen libs.js für eine saubere Konsolen-Ausgabe.
    libs.log('Anwendung startet jetzt sauber...');
    
    // 16. Registriert den Socket-Listener für das 'ping'-Event vom Flask-Backend.
    socket.on('ping', data => {
        
        // 17. Gibt empfangene Ping-Daten direkt in der Konsole aus.
        console.log('PING empfangen:', data);
    });
}