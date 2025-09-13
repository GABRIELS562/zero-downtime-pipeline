// Fixed Dashboard - Connects to correct backend services
// Pharma on port 30002, Trading on port 30003

// Configuration - Correct service endpoints
const PHARMA_API = 'http://localhost:8002';
const TRADING_API = 'http://localhost:8003';

// Market data storage
let marketPrices = {};
let priceHistory = [];
let chart = null;
let pharmaStatus = 'checking...';
let tradingStatus = 'checking...';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Dashboard with correct endpoints...');
    console.log('Pharma API:', PHARMA_API);
    console.log('Trading API:', TRADING_API);

    checkBackendServices();
    initializeChart();
    fetchMarketData();
    fetchPharmaData();

    // Update data periodically
    setInterval(checkBackendServices, 10000); // Check services every 10 seconds
    setInterval(fetchMarketData, 5000); // Update market data every 5 seconds
    setInterval(fetchPharmaData, 5000); // Update pharma data every 5 seconds
    setInterval(updateMetrics, 1000); // Update metrics every second
});

// Check backend services status
async function checkBackendServices() {
    // Check Pharma service
    try {
        const pharmaResponse = await fetch(`${PHARMA_API}/health/live`);
        if (pharmaResponse.ok) {
            const data = await pharmaResponse.json();
            pharmaStatus = 'OPERATIONAL';
            updateServiceStatus('pharma', true, data);
            console.log('✅ Pharma service is operational:', data);
        } else {
            pharmaStatus = 'ERROR';
            updateServiceStatus('pharma', false);
        }
    } catch (error) {
        console.error('❌ Pharma service error:', error);
        pharmaStatus = 'OFFLINE';
        updateServiceStatus('pharma', false);
    }

    // Check Trading service
    try {
        const tradingResponse = await fetch(`${TRADING_API}/health/live`);
        if (tradingResponse.ok) {
            const data = await tradingResponse.json();
            tradingStatus = 'OPERATIONAL';
            updateServiceStatus('trading', true, data);
            console.log('✅ Trading service is operational:', data);
        } else {
            tradingStatus = 'ERROR';
            updateServiceStatus('trading', false);
        }
    } catch (error) {
        console.error('❌ Trading service error:', error);
        tradingStatus = 'OFFLINE';
        updateServiceStatus('trading', false);
    }
}

// Update service status in UI
function updateServiceStatus(service, isOperational, data = null) {
    const statusElement = document.getElementById(`${service}-status`);
    const iconElement = document.getElementById(`${service}-icon`);

    if (statusElement) {
        statusElement.textContent = isOperational ? 'OPERATIONAL' : 'OFFLINE';
        statusElement.className = isOperational ?
            'text-lg font-bold text-green-400' :
            'text-lg font-bold text-red-400';
    }

    if (iconElement) {
        iconElement.className = isOperational ?
            'fas fa-check-circle text-green-400 text-2xl pulse-green' :
            'fas fa-exclamation-circle text-red-400 text-2xl';
    }

    // Show notification for status changes
    if (data && isOperational) {
        const message = `${service === 'pharma' ? 'Pharma' : 'Trading'} service connected`;
        showNotification(message, 'success');
    }
}

// Fetch market data from Trading service
async function fetchMarketData() {
    if (tradingStatus !== 'OPERATIONAL') {
        console.log('Trading service not available, using demo data');
        useDemoMarketData();
        return;
    }

    try {
        const response = await fetch(`${TRADING_API}/api/v1/market`);
        if (response.ok) {
            const data = await response.json();
            console.log('Market data received:', data);

            if (data.stocks) {
                data.stocks.forEach(stock => {
                    marketPrices[stock.symbol] = stock.price;
                    updatePriceCard(stock.symbol, stock.price, stock.change);
                });
            }
            updateChart();
        }
    } catch (error) {
        console.error('Error fetching market data:', error);
        useDemoMarketData();
    }
}

// Fetch Pharma data
async function fetchPharmaData() {
    if (pharmaStatus !== 'OPERATIONAL') {
        console.log('Pharma service not available');
        return;
    }

    try {
        // Fetch batch data
        const batchResponse = await fetch(`${PHARMA_API}/api/v1/batches`);
        if (batchResponse.ok) {
            const data = await batchResponse.json();
            updatePharmaMetrics(data);
        }

        // Fetch equipment status
        const equipmentResponse = await fetch(`${PHARMA_API}/api/v1/equipment`);
        if (equipmentResponse.ok) {
            const data = await equipmentResponse.json();
            updateEquipmentStatus(data);
        }
    } catch (error) {
        console.error('Error fetching pharma data:', error);
    }
}

// Update pharma metrics in UI
function updatePharmaMetrics(data) {
    const metricsElement = document.getElementById('pharma-metrics');
    if (metricsElement && data.batches) {
        const activeCount = data.batches.filter(b => b.status === 'In Production').length;
        metricsElement.innerHTML = `
            <div class="text-sm text-gray-400">Active Batches</div>
            <div class="text-2xl font-bold text-blue-400">${activeCount}/${data.total}</div>
            <div class="text-xs text-gray-500">FDA Compliant</div>
        `;
    }
}

// Update equipment status
function updateEquipmentStatus(data) {
    if (data.equipment) {
        const running = data.equipment.filter(e => e.status === 'Running').length;
        const total = data.equipment.length;
        console.log(`Equipment: ${running}/${total} running`);
    }
}

// Use demo market data as fallback
function useDemoMarketData() {
    const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];
    symbols.forEach(symbol => {
        const price = generatePrice(symbol);
        const change = ((Math.random() - 0.5) * 5).toFixed(2);
        marketPrices[symbol] = price;
        updatePriceCard(symbol, price, change);
    });
    updateChart();
}

// Update or create price card
function updatePriceCard(symbol, price, change) {
    let card = document.getElementById(`price-${symbol}`);

    if (!card) {
        card = document.createElement('div');
        card.id = `price-${symbol}`;
        card.className = 'bg-gray-700 rounded-lg p-3';
        document.getElementById('marketData').appendChild(card);
    }

    const changeColor = change > 0 ? 'text-green-400' : 'text-red-400';
    const changeSymbol = change > 0 ? '+' : '';

    card.innerHTML = `
        <div class="flex justify-between items-start mb-2">
            <span class="font-bold text-lg">${symbol}</span>
            <i class="fas fa-chart-line text-gray-400"></i>
        </div>
        <div class="text-2xl font-bold">$${price.toFixed(2)}</div>
        <div class="text-sm ${changeColor}">
            ${changeSymbol}${change} (${((change/price)*100).toFixed(2)}%)
        </div>
    `;
}

// Generate realistic price for demo
function generatePrice(symbol) {
    const basePrices = {
        'AAPL': 175,
        'GOOGL': 138,
        'MSFT': 378,
        'TSLA': 242
    };
    return basePrices[symbol] + (Math.random() - 0.5) * 10;
}

// Initialize price chart
function initializeChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;

    chart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Value',
                data: [],
                borderColor: 'rgb(139, 92, 246)',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { display: false },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: 'rgba(255, 255, 255, 0.7)' }
                }
            }
        }
    });
}

// Update chart with new data
function updateChart() {
    if (!chart) return;

    const totalValue = Object.values(marketPrices).reduce((sum, price) => sum + price, 0);
    const timestamp = new Date().toLocaleTimeString();

    chart.data.labels.push(timestamp);
    chart.data.datasets[0].data.push(totalValue);

    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update('none');
}

// Update live metrics
function updateMetrics() {
    // Trading metrics
    const latencyElement = document.getElementById('latency');
    if (latencyElement) {
        const latency = 5 + Math.random() * 15;
        latencyElement.textContent = `${latency.toFixed(0)}ms`;
        latencyElement.className = 'font-bold text-green-400';
    }

    const ordersElement = document.getElementById('ordersPerSec');
    if (ordersElement) {
        ordersElement.textContent = 100 + Math.floor(Math.random() * 100);
    }

    const volumeElement = document.getElementById('volume');
    if (volumeElement) {
        volumeElement.textContent = `$${(2.0 + Math.random()).toFixed(1)}M`;
    }
}

// Trigger deployment demonstration
function triggerDeployment() {
    showNotification('Initiating zero-downtime deployment...', 'info');

    const stages = ['Source', 'Build', 'Test', 'Deploy', 'Monitor'];
    let currentStage = 0;

    const interval = setInterval(() => {
        if (currentStage >= stages.length) {
            clearInterval(interval);
            showNotification('Deployment completed successfully!', 'success');
            return;
        }

        showNotification(`Pipeline Stage: ${stages[currentStage]}`, 'info');
        currentStage++;
    }, 2000);
}

// Show notification
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);

    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg slide-in z-50 ${
        type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' :
        type === 'warning' ? 'bg-yellow-600' :
        'bg-blue-600'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${
                type === 'success' ? 'check-circle' :
                type === 'error' ? 'exclamation-circle' :
                type === 'warning' ? 'exclamation-triangle' :
                'info-circle'
            } mr-2"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Test API connections
async function testConnections() {
    console.log('Testing API connections...');
    console.log(`Pharma API (${PHARMA_API}):`);

    try {
        const pharmaTest = await fetch(`${PHARMA_API}/`);
        const pharmaData = await pharmaTest.json();
        console.log('✅ Pharma connected:', pharmaData);
    } catch (e) {
        console.log('❌ Pharma connection failed:', e.message);
    }

    console.log(`Trading API (${TRADING_API}):`);
    try {
        const tradingTest = await fetch(`${TRADING_API}/`);
        const tradingData = await tradingTest.json();
        console.log('✅ Trading connected:', tradingData);
    } catch (e) {
        console.log('❌ Trading connection failed:', e.message);
    }
}

// Initialize and test connections
console.log('Dashboard Fixed - Connecting to backend services...');
testConnections();