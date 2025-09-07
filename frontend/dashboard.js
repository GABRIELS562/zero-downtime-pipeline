// Zero-Downtime Trading Dashboard
// Real-time market data and deployment monitoring

// Configuration
const API_BASE = 'http://localhost:8080';
const WS_URL = 'ws://localhost:8082/feed';
// API key should be fetched from backend for security
// In production, never expose API keys in frontend code
const ALPHA_VANTAGE_KEY = 'DEMO_KEY'; // Replace with backend API call

// Market data storage
let marketPrices = {};
let priceHistory = [];
let chart = null;

// WebSocket connection for real-time updates
let ws = null;
let reconnectDelay = 1000; // For exponential backoff

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Zero-Downtime Trading Dashboard...');
    
    initializeWebSocket();
    initializeChart();
    fetchMarketData();
    fetchSystemMetrics();
    
    // Update data periodically
    setInterval(fetchMarketData, 15000); // Every 15 seconds (respect rate limits)
    setInterval(updateMetrics, 1000); // Every second for live metrics
    setInterval(simulateActivity, 2000); // Simulate some activity
});

// Initialize WebSocket connection
function initializeWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            showNotification('Connected to real-time feed', 'success');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleRealtimeUpdate(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting...');
            // Implement exponential backoff for reconnection
            reconnectDelay = Math.min((reconnectDelay || 1000) * 2, 30000);
            setTimeout(initializeWebSocket, reconnectDelay);
        };
    } catch (error) {
        console.log('WebSocket not available, using polling instead');
    }
}

// Fetch market data from Alpha Vantage
async function fetchMarketData() {
    const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];
    const marketDataDiv = document.getElementById('marketData');
    
    // For demo, use simulated data to avoid rate limits
    // In production, you'd call Alpha Vantage API
    symbols.forEach(symbol => {
        const price = marketPrices[symbol] || generatePrice(symbol);
        const change = ((Math.random() - 0.5) * 5).toFixed(2);
        const changePercent = ((Math.random() - 0.5) * 2).toFixed(2);
        
        marketPrices[symbol] = price;
        
        const priceCard = document.getElementById(`price-${symbol}`) || createPriceCard(symbol);
        updatePriceCard(priceCard, symbol, price, change, changePercent);
    });
    
    updateChart();
}

// Create price card element
function createPriceCard(symbol) {
    const card = document.createElement('div');
    card.id = `price-${symbol}`;
    card.className = 'bg-gray-700 rounded-lg p-3 slide-in';
    card.innerHTML = `
        <div class="flex justify-between items-start mb-2">
            <span class="font-bold text-lg">${symbol}</span>
            <i class="fas fa-chart-line text-gray-400"></i>
        </div>
        <div class="text-2xl font-bold">$<span class="price">0.00</span></div>
        <div class="text-sm">
            <span class="change">0.00</span>
            (<span class="change-percent">0.00</span>%)
        </div>
    `;
    document.getElementById('marketData').appendChild(card);
    return card;
}

// Update price card with new data
function updatePriceCard(card, symbol, price, change, changePercent) {
    const priceElement = card.querySelector('.price');
    const changeElement = card.querySelector('.change');
    const percentElement = card.querySelector('.change-percent');
    
    priceElement.textContent = price.toFixed(2);
    changeElement.textContent = change > 0 ? `+${change}` : change;
    percentElement.textContent = changePercent > 0 ? `+${changePercent}` : changePercent;
    
    // Color coding
    const color = change > 0 ? 'text-green-400' : 'text-red-400';
    changeElement.className = `change ${color}`;
    percentElement.className = `change-percent ${color}`;
    
    // Flash animation on update
    card.classList.add('scale-105');
    setTimeout(() => card.classList.remove('scale-105'), 200);
}

// Generate realistic price for demo
function generatePrice(symbol) {
    const basePrices = {
        'AAPL': 150,
        'GOOGL': 140,
        'MSFT': 380,
        'TSLA': 250
    };
    const base = basePrices[symbol] || 100;
    return base + (Math.random() - 0.5) * 10;
}

// Initialize price chart
function initializeChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    chart = new Chart(ctx, {
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
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
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
    
    // Keep only last 20 points
    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    chart.update('none'); // Update without animation for smooth real-time feel
}

// Fetch system metrics
async function fetchSystemMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/metrics/summary`);
        if (response.ok) {
            const data = await response.json();
            updateSystemMetrics(data);
        }
    } catch (error) {
        console.log('Using simulated metrics');
        // Use simulated metrics for demo
    }
}

// Update live metrics
function updateMetrics() {
    // Update latency
    const latency = 10 + Math.random() * 40; // 10-50ms
    document.getElementById('latency').textContent = `${latency.toFixed(0)}ms`;
    document.getElementById('latency').className = 
        latency < 50 ? 'font-bold text-green-400' : 'font-bold text-yellow-400';
    
    // Update orders per second
    const orders = 100 + Math.floor(Math.random() * 100);
    document.getElementById('ordersPerSec').textContent = orders;
    
    // Update volume
    const volume = 2.0 + Math.random() * 1.0;
    document.getElementById('volume').textContent = `$${volume.toFixed(1)}M`;
}

// Simulate activity for demo
function simulateActivity() {
    // Randomly update a metric
    if (Math.random() > 0.7) {
        const notifications = [
            'New order executed: BUY 100 AAPL @ $150.25',
            'Risk check passed for portfolio rebalance',
            'Canary deployment completed successfully',
            'Health check: All systems operational',
            'Compliance scan: No violations detected'
        ];
        const message = notifications[Math.floor(Math.random() * notifications.length)];
        showNotification(message, 'info');
    }
}

// Handle real-time updates from WebSocket
function handleRealtimeUpdate(data) {
    if (data.type === 'price') {
        marketPrices[data.symbol] = data.price;
        updatePriceCard(
            document.getElementById(`price-${data.symbol}`),
            data.symbol,
            data.price,
            data.change,
            data.changePercent
        );
    } else if (data.type === 'deployment') {
        showNotification(`Deployment ${data.status}: ${data.message}`, data.status);
    }
}

// Trigger deployment demonstration
function triggerDeployment() {
    showNotification('Initiating zero-downtime deployment...', 'info');
    
    // Animate pipeline
    const stages = ['Source', 'Build', 'Test', 'Deploy', 'Monitor'];
    let currentStage = 0;
    
    const interval = setInterval(() => {
        if (currentStage >= stages.length) {
            clearInterval(interval);
            showNotification('Deployment completed successfully! Zero downtime achieved.', 'success');
            return;
        }
        
        showNotification(`Pipeline Stage: ${stages[currentStage]}`, 'info');
        currentStage++;
    }, 2000);
}

// Show notification
function showNotification(message, type = 'info') {
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

// Initialize on load
console.log('Zero-Downtime Trading Dashboard initialized');
showNotification('Dashboard connected successfully', 'success');