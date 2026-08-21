
let candles = [];

export function updateLiveChart(candle) {
    if (!candle || !candle.t || !candle.c) return;

    candles.push(candle);
    if (candles.length > 100) {
        candles = candles.slice(-100);
    }

    const chartEl = document.getElementById("live-chart");
    if (chartEl && window.Plotly) {
        Plotly.react(chartEl, {
            data: [{
                x: candles.map(c => new Date(c.t)),
                y: candles.map(c => parseFloat(c.c)),
                type: "scatter",
                mode: "lines",
                line: { color: "#00ccff" }
            }],
            layout: {
                title: "BTCUSDT Live",
                margin: { t: 40 }
            }
        });
    }
}

export function resetChart() {
    candles = [];
    const chartEl = document.getElementById("live-chart");
    if (chartEl && window.Plotly) {
        Plotly.react(chartEl, {
            data: [],
            layout: {
                title: "BTCUSDT Live",
                margin: { t: 40 }
            }
        });
    }
}