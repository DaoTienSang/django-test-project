// daphne -b 0.0.0.0 -p 8000 financeProjectManager.asgi:application



// ========== CREATE CHART AREA ==========

const chartContainer = document.getElementById('chart-container');
const chart = LightweightCharts.createChart(chartContainer, {
    width: 800,
    height: 400,
    layout: { backgroundColor: '#FFFFFF', textColor: 'black' },
    grid: { vertLines: { color: '#E0E3EB' }, horzLines: { color: '#E0E3EB' } },
    timeScale: { timeVisible: true, secondsVisible: true }
});

const candleSeries = chart.addCandlestickSeries();


// ========== CONNECT SOCKET FUNCTION ============
let socket = null; // Initialize socket as null
function connectWebSocket(stockCode) {
    let data = [];
    if (socket) {
        console.log('Close old socket...');
        socket.close(); // Close any existing connection
    }
    // Construct the WebSocket URL dynamically with the stock code
    console.log('- start connect socket.');
    socket = new WebSocket(`ws://127.0.0.1:8000/ws/candlestick/${stockCode}/`);
    // console.log(`Socket: ${socket}`);
    socket.onopen = function() {
        console.log('WebSocket connection established for stock:', stockCode);
    };

    socket.onmessage = function(event) {
        // console.log('socket onmessage');
        const message = JSON.parse(event.data);
        console.log('Received message:', message);

        if (message.historical) {
            // Handle historical data
            message.historical.forEach(candle => {
                const newCandle = {
                    time: Math.floor(new Date(candle.time).getTime() / 1000),
                    open: parseFloat(candle.open),
                    high: parseFloat(candle.high),
                    low: parseFloat(candle.low),
                    close: parseFloat(candle.close)
                };
                data.push(newCandle);
            });
            candleSeries.setData(data); // Render historical data
            console.log('Historical data loaded:', data);
        } else {
//             // Handle real-time data (if implemented)
//             // const newCandle = {
//             //     time: Math.floor(new Date(candle.time).getTime() / 1000),
//             //     open: parseFloat(candle.open),
//             //     high: parseFloat(candle.high),
//             //     low: parseFloat(candle.low),
//             //     close: parseFloat(candle.close)
//             // };
//             // data.push(newCandle);
//             // candleSeries.update(newCandle);
//             // console.log('Realtime candle added:', newCandle);
        }
    };

    socket.onerror = function(error) {
        console.error('WebSocket Error:', error);
    };

    socket.onclose = function() {
        console.log('WebSocket connection closed');
    };
}



console.log(document.querySelector("form"));
document.getElementById("form-search-stock-code").addEventListener('submit', function(event){
    // console.log('form submit');
    event.preventDefault();

    const stockCode = document.querySelector("#stock-code").value.trim();
    // console.log(`Stock code: ${stockCode}`);
    if (stockCode){
        // console.log('sdfhsdfadsfssssss');
        connectWebSocket(stockCode);
    }else{
        console.error('Stock code is empty');
    }
    // console.log(`Socket: ${socket}`);
});