// assets/module_folder/script.js

// 1. Sofortige Ausführung als ES6-Modul (da der DOM durch den Footer-Platz unter {%renderer%} bereits steht)
(async () => {
    
    console.log('[script.js] Starte Modul-Ladevorgang...');

    try {
        // 2. Relative Imports aus dem selben Ordner (assets/module_folder/)
        const [modules, chart] = await Promise.all([
            import('./modules.js'),
            import('./chart.js')
        ]);

        // 3. Modul-Verifizierung
        if (!modules || typeof modules.initModules !== 'function') {
            throw new Error('modules.js konnte initModules() nicht bereitstellen!');
        }

        if (!chart || typeof chart.updateLiveChart !== 'function') {
            throw new Error('chart.js konnte updateLiveChart() nicht bereitstellen!');
        }

        // 4. Module initialisieren & Socket-Instanz abrufen
        const { libs, socket } = await modules.initModules();

        if (!libs || !socket) {
            throw new Error('Module unvollständig: libs oder socket fehlen!');
        }

        console.log('✅ ALLE MODULE ERFOLGREICH GELADEN & VERIFIZIERT');

        // 5. Hauptanwendung starten
        startApp(libs, socket, chart);

    } catch (err) {
        console.error('❌ KRITISCHER LADEFEHLER IN SCRIPT.JS:', err);
    }
})();

// 6. Hauptfunktion für App-Steuerung & Event-Handling
function startApp(libs, socket, chart) {
    
    libs.log('Anwendung startet jetzt sauber...');

    // Ping-Event loggen
    socket.on('ping', data => {
        console.log('PING empfangen:', data);
    });

    // Binance-Candles empfangen, parsen & an chart.js weiterleiten
    socket.on('binance_candle', candle => {
        console.log('[DEBUG script.js] Binance Candle empfangen:', candle);

        try {
            // Konvertierung von Binance-Strings (e.g. "77220.00") in Numbers
            const formattedCandle = {
                time: Math.floor(candle.t / 1000), // UNIX-Timestamp in Sek. (für Lightweight Charts)
                open: parseFloat(candle.o),
                high: parseFloat(candle.h),
                low: parseFloat(candle.l),
                close: parseFloat(candle.c)
            };

            // Sicheres Update des Charts
            chart.updateLiveChart(formattedCandle);

        } catch (err) {
            console.error('❌ FEHLER BEIM VERARBEITEN DER CANDLE IN CHART.JS:', err, candle);
        }
    });

    // Timeframe-Wechsel verwalten
    socket.on('timeframe_changed', () => {
        if (typeof chart.resetChart === 'function') {
            chart.resetChart();
        }
    });
}