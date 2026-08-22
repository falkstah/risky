// assets/module_folder/chart.js

let candles = [];
let isInitialized = false;

export function updateLiveChart(candle) {
    if (!candle || !candle.t || !candle.c) return;

    candles.push(candle);
    if (candles.length > 100) {
        candles = candles.slice(-100);
    }

    const chartEl = document.getElementById("live-chart");
    if (!chartEl || !window.Plotly) return;

    const xVal = new Date(candle.t);
    const yVal = parseFloat(candle.c);

    // Erstes Rendering: Chart initial aufbauen
    if (!isInitialized || !chartEl.data) {
        Plotly.react(chartEl, [{
            x: candles.map(c => new Date(c.t)),
            y: candles.map(c => parseFloat(c.c)),
            type: "scatter",
            mode: "lines",
            line: { color: "#00ccff" }
        }], {
            title: "BTCUSDT Live",
            margin: { t: 40 },
            uirevision: 'true' // Behält Zoom & Pan bei Updates bei
        });
        isInitialized = true;
        return;
    }

    // Effizientes Anhängen des neuen Datenpunkts (100 Punkte max)
    Plotly.extendTraces(chartEl, {
        x: [[xVal]],
        y: [[yVal]]
    }, [0], 100);
}

export function resetChart() {
    candles = [];
    isInitialized = false;
    
    const chartEl = document.getElementById("live-chart");
    if (chartEl && window.Plotly) {
        Plotly.react(chartEl, [{
            x: [],
            y: [],
            type: "scatter",
            mode: "lines",
            line: { color: "#00ccff" }
        }], {
            title: "BTCUSDT Live",
            margin: { t: 40 }
        });
    }
}