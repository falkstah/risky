// assets/script.js

// 1. Wartet, bis die HTML-Struktur (DOM) vollständig vom Browser geladen wurde.
window.addEventListener('DOMContentLoaded', async () => {
    
    // 2. Kontroll-Log zur Verfolgung der Ausführungsreihenfolge.
    console.log('[script.js] Starte Modul-Ladevorgang...');

    // 3. Schutzblock für fehlerfreie Ausführung.
    try {
        
        // 4. Lädt modules.js und chart.js parallel per dynamischem Import.
        const [modules, chart] = await Promise.all([
            import('/assets/module_folder/modules.js'),
            import('/assets/module_folder/chart.js')
        ]);

        // 5. Sicherheitsprüfung: Existieren alle benötigten Funktionen/Module?
        if (!modules || typeof modules.initModules !== 'function') {
            throw new Error('modules.js konnte initModules() nicht bereitstellen!');
        }

        if (!chart || typeof chart.updateLiveChart !== 'function') {
            throw new Error('chart.js konnte updateLiveChart() nicht bereitstellen!');
        }

        // 6. Führt initModules() aus und wartet auf libs.js & Socket-Verbindung.
        const { libs, socket } = await modules.initModules();

        // 7. Vollständigkeits-Guard für libs und socket.
        if (!libs || !socket) {
            throw new Error('Module unvollständig: libs oder socket fehlen!');
        }

        // 8. Erfolgsbestätigung in der Konsole.
        console.log('✅ ALLE MODULE ERFOLGREICH GELADEN & VERIFIZIERT');

        // 9. Übergibt libs, socket und die Chart-Funktionen an die Hauptfunktion.
        startApp(libs, socket, chart);

    // 10. Fängt alle Lade- und Netzwerkfehler ab.
    } catch (err) {
        console.error('❌ KRITISCHER LADEFEHLER:', err);
    }
});

// 11. Hauptfunktion für deine App-Steuerung.
function startApp(libs, socket, chart) {
    
    libs.log('Anwendung startet jetzt sauber...');

    // 12. Ping-Event vom Server loggen.
    socket.on('ping', data => {
        console.log('PING empfangen:', data);
    });

    // 13. Live-Candles vom Backend direkt an den Chart weiterleiten.
    socket.on('binance_candle', candle => {
        console.log('[DEBUG script.js] Binance Candle empfangen:', candle);
        chart.updateLiveChart(candle);
    });

    // 14. Chart bei Timeframe-Wechsel zurücksetzen.
    socket.on('timeframe_changed', () => {
        chart.resetChart();
    });
}