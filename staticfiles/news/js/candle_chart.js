const socket = new WebSocket('ws://127.0.0.1:8000/ws/candlestick/');

const chart = LightweightCharts.createChart(document.getElementById('chart-container'), {
    width: 800,
    height: 400,
    layout: { backgroundColor: '#FFFFFF', textColor: 'black' },
    grid: { vertLines: { color: '#E0E3EB' }, horzLines: { color: '#E0E3EB' } }
});

const candleSeries = chart.addCandlestickSeries();

let data = [];

socket.onmessage = function(event) {
    const candle = JSON.parse(event.data);
    
    const newCandle = {
        time: Math.floor(new Date(candle.time).getTime() / 1000),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close
    };

    data.push(newCandle);
    candleSeries.setData(data);
};
