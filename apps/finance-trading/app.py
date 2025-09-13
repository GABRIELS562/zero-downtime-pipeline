#!/usr/bin/env python3
"""
Zero-Downtime Trading Platform - Simple Flask Placeholder
Provides a working API for the Trading app on port 8000
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from datetime import datetime
import os
import random
import time

app = Flask(__name__)
CORS(app)

# Metrics storage for Prometheus
order_latencies = []  # Store latencies for histogram
order_counters = {
    "executed": 0,
    "pending": 0,
    "failed": 0,
    "cancelled": 0
}

# Simulated data
trading_data = {
    "service": "Zero-Downtime Trading Platform",
    "status": "Demo Mode",
    "latency": "< 10ms",
    "version": "1.0.0",
    "environment": os.getenv("ENVIRONMENT", "production")
}

# Simulated market data
stocks = [
    {"symbol": "AAPL", "name": "Apple Inc.", "price": 175.43, "change": 2.15},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 138.21, "change": -1.32},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "price": 378.91, "change": 3.48},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "price": 145.32, "change": 0.87},
    {"symbol": "TSLA", "name": "Tesla Inc.", "price": 242.64, "change": -5.21}
]

orders = []

@app.route('/')
def home():
    """Finance Trading Dashboard HTML Frontend"""
    # Calculate system metrics
    latency = random.uniform(1, 10)
    success_rate = random.uniform(95, 99.9)
    daily_volume = random.randint(50000000, 200000000)

    # Get current stock prices
    aapl_price = stocks[0]['price']
    googl_price = stocks[1]['price']
    msft_price = stocks[2]['price']

    aapl_change = stocks[0]['change']
    googl_change = stocks[1]['change']
    msft_change = stocks[2]['change']

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zero-Downtime Trading Platform</title>
        <style>
            body {{
                margin: 0;
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}

            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 20px 0;
            }}

            .header h1 {{
                font-size: 2.5em;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}

            .header p {{
                font-size: 1.2em;
                margin: 10px 0;
                opacity: 0.9;
            }}

            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .card {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }}

            .card h3 {{
                margin-top: 0;
                font-size: 1.3em;
                border-bottom: 2px solid rgba(255, 255, 255, 0.3);
                padding-bottom: 10px;
            }}

            .stock-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 15px 0;
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }}

            .stock-symbol {{
                font-weight: bold;
                font-size: 1.1em;
            }}

            .stock-price {{
                font-size: 1.2em;
                font-weight: bold;
            }}

            .stock-change {{
                font-size: 0.9em;
                padding: 4px 8px;
                border-radius: 4px;
                margin-left: 10px;
            }}

            .positive {{ background: #28a745; }}
            .negative {{ background: #dc3545; }}

            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
            }}

            .metric-label {{
                font-size: 0.9em;
                opacity: 0.8;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            .status-indicator {{
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #28a745;
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 10px rgba(40, 167, 69, 0.6);
            }}

            .api-endpoints {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                margin-top: 30px;
            }}

            .api-endpoints h3 {{
                margin-top: 0;
                border-bottom: 2px solid rgba(255, 255, 255, 0.3);
                padding-bottom: 10px;
            }}

            .endpoint-item {{
                margin: 10px 0;
                font-family: 'Courier New', monospace;
                background: rgba(0, 0, 0, 0.2);
                padding: 8px 12px;
                border-radius: 5px;
                border-left: 4px solid #667eea;
            }}

            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
                100% {{ opacity: 1; }}
            }}

            .live-indicator {{
                animation: pulse 2s infinite;
                color: #28a745;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Zero-Downtime Trading Platform</h1>
                <p><span class="status-indicator"></span>System Status: <span class="live-indicator">LIVE</span></p>
                <p>Last Update: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
            </div>

            <div class="dashboard-grid">
                <div class="card">
                    <h3>📈 Market Data</h3>
                    <div class="stock-item">
                        <div>
                            <div class="stock-symbol">AAPL</div>
                            <div style="font-size: 0.9em; opacity: 0.8;">Apple Inc.</div>
                        </div>
                        <div>
                            <span class="stock-price">${aapl_price:.2f}</span>
                            <span class="stock-change {'positive' if aapl_change >= 0 else 'negative'}">
                                {'+' if aapl_change >= 0 else ''}{aapl_change:.2f}%
                            </span>
                        </div>
                    </div>

                    <div class="stock-item">
                        <div>
                            <div class="stock-symbol">GOOGL</div>
                            <div style="font-size: 0.9em; opacity: 0.8;">Alphabet Inc.</div>
                        </div>
                        <div>
                            <span class="stock-price">${googl_price:.2f}</span>
                            <span class="stock-change {'positive' if googl_change >= 0 else 'negative'}">
                                {'+' if googl_change >= 0 else ''}{googl_change:.2f}%
                            </span>
                        </div>
                    </div>

                    <div class="stock-item">
                        <div>
                            <div class="stock-symbol">MSFT</div>
                            <div style="font-size: 0.9em; opacity: 0.8;">Microsoft Corp.</div>
                        </div>
                        <div>
                            <span class="stock-price">${msft_price:.2f}</span>
                            <span class="stock-change {'positive' if msft_change >= 0 else 'negative'}">
                                {'+' if msft_change >= 0 else ''}{msft_change:.2f}%
                            </span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h3>⚡ System Metrics</h3>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Average Latency</div>
                        <div class="metric-value">{latency:.1f}ms</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-value">{success_rate:.2f}%</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Daily Volume</div>
                        <div class="metric-value">${daily_volume:,}</div>
                    </div>
                </div>

                <div class="card">
                    <h3>📊 Trading Stats</h3>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Active Orders</div>
                        <div class="metric-value">{len(orders)}</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Executed Orders</div>
                        <div class="metric-value">{order_counters['executed']}</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Market Status</div>
                        <div class="metric-value" style="color: #28a745;">OPEN</div>
                    </div>
                </div>
            </div>

            <div class="api-endpoints">
                <h3>🔗 API Endpoints</h3>
                <div class="endpoint-item">GET /api/v1/market - Live market data</div>
                <div class="endpoint-item">GET /api/v1/orders - Trading orders</div>
                <div class="endpoint-item">POST /api/v1/orders - Place new order</div>
                <div class="endpoint-item">GET /api/v1/portfolio - Portfolio information</div>
                <div class="endpoint-item">GET /health - System health check</div>
                <div class="endpoint-item">GET /metrics - Prometheus metrics</div>
            </div>
        </div>

        <script>
            // Auto-refresh the page every 30 seconds to show live data
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """
    return html

@app.route('/health')
@app.route('/health/live')
def health_live():
    """Health check endpoint"""
    start_time = time.time()
    return jsonify({
        "status": "healthy",
        "service": "trading-platform",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": random.randint(1000, 10000),
        "latency_ms": f"{(time.time() - start_time) * 1000:.2f}",
        "market_connection": "active",
        "order_engine": "running"
    })

@app.route('/health/ready')
def health_ready():
    """Readiness check endpoint"""
    return jsonify({
        "status": "ready",
        "service": "trading-platform",
        "timestamp": datetime.utcnow().isoformat(),
        "initialized": True,
        "market_data": "connected",
        "order_system": "ready"
    })

@app.route('/api/v1/market')
def get_market_data():
    """Get current market data"""
    # Simulate price fluctuations
    for stock in stocks:
        stock['price'] += random.uniform(-2, 2)
        stock['change'] = random.uniform(-5, 5)

    return jsonify({
        "market": "US",
        "status": "OPEN",
        "stocks": stocks,
        "timestamp": datetime.utcnow().isoformat(),
        "update_frequency": "real-time"
    })

@app.route('/api/v1/market/<symbol>')
def get_stock(symbol):
    """Get specific stock information"""
    stock = next((s for s in stocks if s["symbol"] == symbol), None)
    if stock:
        return jsonify({
            **stock,
            "volume": random.randint(1000000, 50000000),
            "market_cap": f"${random.randint(100, 3000)}B",
            "pe_ratio": f"{random.uniform(10, 35):.2f}",
            "timestamp": datetime.utcnow().isoformat()
        })
    return jsonify({"error": "Symbol not found"}), 404

@app.route('/api/v1/orders', methods=['GET', 'POST'])
def handle_orders():
    """Handle order operations"""
    global order_counters, order_latencies

    if request.method == 'POST':
        start_time = time.time()

        # Simulate different order statuses (90% executed, 5% pending, 3% failed, 2% cancelled)
        rand = random.random()
        if rand < 0.90:
            status = "EXECUTED"
            order_counters["executed"] += 1
        elif rand < 0.95:
            status = "PENDING"
            order_counters["pending"] += 1
        elif rand < 0.98:
            status = "FAILED"
            order_counters["failed"] += 1
        else:
            status = "CANCELLED"
            order_counters["cancelled"] += 1

        execution_time = random.uniform(1, 10)
        order_latencies.append(execution_time)

        # Keep only last 100 latencies for histogram
        if len(order_latencies) > 100:
            order_latencies.pop(0)

        order = {
            "id": f"ORD-{random.randint(1000, 9999)}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "execution_time_ms": f"{execution_time:.2f}",
            **request.get_json()
        }
        orders.append(order)
        return jsonify(order), 201

    return jsonify({
        "orders": orders[-10:],  # Last 10 orders
        "total": len(orders),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/portfolio')
def get_portfolio():
    """Get portfolio information"""
    portfolio_stocks = random.sample(stocks, 3)
    return jsonify({
        "total_value": f"${random.randint(10000, 1000000):,}",
        "daily_change": f"{random.uniform(-2, 3):.2f}%",
        "positions": [
            {
                **stock,
                "shares": random.randint(10, 1000),
                "value": f"${stock['price'] * random.randint(10, 1000):,.2f}"
            }
            for stock in portfolio_stocks
        ],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus-style metrics endpoint"""
    metrics_text = f"""# HELP trading_orders_active Active trading orders
# TYPE trading_orders_active gauge
trading_orders_active {len(orders)}
# HELP trading_latency_milliseconds Average trading latency
# TYPE trading_latency_milliseconds gauge
trading_latency_milliseconds {random.uniform(1, 10):.2f}
# HELP trading_stock_price Current stock prices
# TYPE trading_stock_price gauge
trading_stock_price{{symbol="AAPL"}} {stocks[0]['price']:.2f}
trading_stock_price{{symbol="GOOGL"}} {stocks[1]['price']:.2f}
trading_stock_price{{symbol="MSFT"}} {stocks[2]['price']:.2f}
# HELP trading_volume_per_second Trading volume per second
# TYPE trading_volume_per_second gauge
trading_volume_per_second {random.randint(100, 500)}
# HELP trading_market_status Market status (1=open, 0=closed)
# TYPE trading_market_status gauge
trading_market_status 1
"""
    return Response(metrics_text, mimetype='text/plain', status=200)

@app.route('/api/v1/system/info')
def system_info():
    """System information endpoint"""
    return jsonify({
        "platform": {
            "name": "Zero-Downtime Trading Platform",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "production")
        },
        "capabilities": {
            "real_time_quotes": True,
            "algorithmic_trading": True,
            "risk_management": True,
            "compliance_monitoring": True,
            "high_frequency_trading": True
        },
        "performance": {
            "avg_latency_ms": f"{random.uniform(1, 10):.2f}",
            "orders_per_second": random.randint(1000, 5000),
            "uptime_percentage": "99.99%"
        },
        "compliance": {
            "sox_compliant": True,
            "mifid_ii": True,
            "reg_nms": True
        },
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)