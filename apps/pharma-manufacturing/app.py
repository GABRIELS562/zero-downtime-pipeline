#!/usr/bin/env python3
"""
Pharma Management System - Simple Flask Placeholder
Provides a working API for the Pharma app on port 8000
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from datetime import datetime
import os
import random

app = Flask(__name__)
CORS(app)

# Metrics storage for Prometheus
batch_temperatures = {}
fda_violations_counter = 0
quality_test_results = []

# Simulated data
pharma_data = {
    "service": "Pharma Management System",
    "status": "Demo Mode",
    "compliance": "FDA 21 CFR Part 11",
    "version": "1.0.0",
    "environment": os.getenv("ENVIRONMENT", "production")
}

batch_data = [
    {"id": "BATCH-001", "product": "Aspirin 100mg", "status": "In Production", "compliance": "GMP Compliant"},
    {"id": "BATCH-002", "product": "Ibuprofen 200mg", "status": "Quality Check", "compliance": "FDA Approved"},
    {"id": "BATCH-003", "product": "Paracetamol 500mg", "status": "Completed", "compliance": "ISO 9001"}
]

@app.route('/')
def home():
    """Pharmaceutical Manufacturing Dashboard HTML Frontend"""
    # Get batch information
    batches = batch_data

    # Calculate compliance metrics
    fda_compliance = 98.5
    gmp_compliance = 99.1
    iso_compliance = 97.8

    # System metrics
    active_batches = len([b for b in batches if b['status'] == 'In Production'])
    total_batches = len(batches)
    uptime = random.uniform(99.5, 99.9)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pharmaceutical Manufacturing System</title>
        <style>
            body {{
                margin: 0;
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #2196F3 0%, #1976D2 50%, #0D47A1 100%);
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
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
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

            .batch-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 15px 0;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }}

            .batch-id {{
                font-weight: bold;
                font-size: 1.1em;
                color: #FFD54F;
            }}

            .batch-product {{
                font-size: 0.9em;
                opacity: 0.8;
                margin: 5px 0;
            }}

            .batch-status {{
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: bold;
                text-align: center;
            }}

            .status-production {{ background: #FF9800; color: white; }}
            .status-quality {{ background: #FFC107; color: #333; }}
            .status-completed {{ background: #4CAF50; color: white; }}

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

            .compliance-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 15px 0;
                padding: 12px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }}

            .compliance-name {{
                font-weight: bold;
            }}

            .compliance-score {{
                font-size: 1.2em;
                font-weight: bold;
                color: #4CAF50;
            }}

            .status-indicator {{
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #4CAF50;
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 10px rgba(76, 175, 80, 0.6);
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
                border-left: 4px solid #2196F3;
            }}

            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
                100% {{ opacity: 1; }}
            }}

            .live-indicator {{
                animation: pulse 2s infinite;
                color: #4CAF50;
                font-weight: bold;
            }}

            .certification-badge {{
                display: inline-block;
                background: rgba(76, 175, 80, 0.2);
                border: 1px solid #4CAF50;
                color: #4CAF50;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.75em;
                margin: 2px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏭 Pharmaceutical Manufacturing System</h1>
                <p><span class="status-indicator"></span>Production Status: <span class="live-indicator">OPERATIONAL</span></p>
                <p>Last Update: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
                <div>
                    <span class="certification-badge">FDA 21 CFR Part 11</span>
                    <span class="certification-badge">GMP Certified</span>
                    <span class="certification-badge">ISO 9001</span>
                </div>
            </div>

            <div class="dashboard-grid">
                <div class="card">
                    <h3>📦 Production Batches</h3>
    """

    # Add batch information
    for batch in batches:
        status_class = "status-production" if batch['status'] == "In Production" else \
                      "status-quality" if batch['status'] == "Quality Check" else "status-completed"

        html += f"""
                    <div class="batch-item">
                        <div>
                            <div class="batch-id">{batch['id']}</div>
                            <div class="batch-product">{batch['product']}</div>
                        </div>
                        <div class="batch-status {status_class}">{batch['status']}</div>
                    </div>
        """

    html += f"""
                </div>

                <div class="card">
                    <h3>✅ Compliance Status</h3>
                    <div class="compliance-item">
                        <div class="compliance-name">FDA 21 CFR Part 11</div>
                        <div class="compliance-score">{fda_compliance}%</div>
                    </div>
                    <div class="compliance-item">
                        <div class="compliance-name">GMP Standards</div>
                        <div class="compliance-score">{gmp_compliance}%</div>
                    </div>
                    <div class="compliance-item">
                        <div class="compliance-name">ISO 9001</div>
                        <div class="compliance-score">{iso_compliance}%</div>
                    </div>
                </div>

                <div class="card">
                    <h3>📊 System Metrics</h3>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Active Batches</div>
                        <div class="metric-value">{active_batches}</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Total Batches</div>
                        <div class="metric-value">{total_batches}</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">System Uptime</div>
                        <div class="metric-value">{uptime:.2f}%</div>
                    </div>
                </div>

                <div class="card">
                    <h3>🌡️ Environmental Controls</h3>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Temperature</div>
                        <div class="metric-value">{random.uniform(20, 22):.1f}°C</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Humidity</div>
                        <div class="metric-value">{random.uniform(45, 55):.1f}%</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div class="metric-label">Air Quality</div>
                        <div class="metric-value" style="color: #4CAF50;">EXCELLENT</div>
                    </div>
                </div>
            </div>

            <div class="api-endpoints">
                <h3>🔗 API Endpoints</h3>
                <div class="endpoint-item">GET /api/v1/batches - Production batch data</div>
                <div class="endpoint-item">GET /api/v1/batches/{{id}} - Specific batch details</div>
                <div class="endpoint-item">GET /api/v1/equipment - Equipment status</div>
                <div class="endpoint-item">GET /api/v1/quality - Quality control results</div>
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
@app.route('/api/v1/health/live')
def health_live():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "pharma-management",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": random.randint(1000, 10000),
        "database": "connected",
        "compliance": "FDA 21 CFR Part 11"
    })

@app.route('/health/ready')
@app.route('/api/v1/health/ready')
def health_ready():
    """Readiness check endpoint"""
    return jsonify({
        "status": "ready",
        "service": "pharma-management",
        "timestamp": datetime.utcnow().isoformat(),
        "initialized": True
    })

@app.route('/api/v1/batches')
def get_batches():
    """Get batch information"""
    return jsonify({
        "batches": batch_data,
        "total": len(batch_data),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/batches/<batch_id>')
def get_batch(batch_id):
    """Get specific batch information"""
    batch = next((b for b in batch_data if b["id"] == batch_id), None)
    if batch:
        # Generate and store temperature for metrics
        temp = random.uniform(18, 22)
        batch_temperatures[batch_id] = temp

        return jsonify({
            **batch,
            "temperature": f"{temp:.1f}°C",
            "humidity": f"{random.uniform(45, 55):.1f}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    return jsonify({"error": "Batch not found"}), 404

@app.route('/api/v1/system/info')
def system_info():
    """System information endpoint"""
    return jsonify({
        "application": {
            "name": "Pharmaceutical Manufacturing Monitoring System",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "production")
        },
        "compliance": {
            "gmp_enabled": True,
            "fda_validation": True,
            "audit_trail": True,
            "data_integrity": True
        },
        "monitoring": {
            "equipment_sensors": True,
            "environmental_conditions": True,
            "batch_tracking": True,
            "quality_control": True
        },
        "capabilities": {
            "real_time_alerts": True,
            "zero_downtime_health": True,
            "regulatory_reporting": True,
            "equipment_integration": True
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus-style metrics endpoint"""
    metrics_text = f"""# HELP pharma_batches_active Active pharmaceutical batches
# TYPE pharma_batches_active gauge
pharma_batches_active 3
# HELP pharma_temperature_celsius Current reactor temperature
# TYPE pharma_temperature_celsius gauge
pharma_temperature_celsius{{reactor="REACTOR-01"}} {random.uniform(35,40):.2f}
# HELP pharma_temperature_celsius Current dryer temperature
pharma_temperature_celsius{{reactor="DRYER-01"}} {random.uniform(60,65):.2f}
# HELP pharma_quality_tests_passed Total quality tests passed
# TYPE pharma_quality_tests_passed counter
pharma_quality_tests_passed {random.randint(100, 200)}
# HELP pharma_compliance_score Current compliance percentage
# TYPE pharma_compliance_score gauge
pharma_compliance_score 99.5
"""
    return Response(metrics_text, mimetype='text/plain', status=200)

@app.route('/api/v1/equipment')
def equipment_status():
    """Equipment monitoring endpoint"""
    return jsonify({
        "equipment": [
            {"id": "REACTOR-01", "status": "Running", "temperature": f"{random.uniform(35, 40):.1f}°C"},
            {"id": "MIXER-01", "status": "Idle", "rpm": 0},
            {"id": "DRYER-01", "status": "Running", "temperature": f"{random.uniform(60, 65):.1f}°C"}
        ],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/quality')
def quality_control():
    """Quality control endpoint"""
    global fda_violations_counter

    # Simulate occasional quality failures (10% chance)
    purity = random.uniform(99.5, 99.9)
    dissolution = random.uniform(85, 95)

    # Check for FDA violations
    tests = []
    if random.random() < 0.1:  # 10% chance of failure
        purity = random.uniform(95, 99.4)  # Below threshold
        tests.append({"test": "Purity", "result": f"{purity:.2f}%", "status": "FAIL"})
        fda_violations_counter += 1
    else:
        tests.append({"test": "Purity", "result": f"{purity:.2f}%", "status": "PASS"})

    tests.extend([
        {"test": "Dissolution", "result": f"{dissolution:.1f}%", "status": "PASS"},
        {"test": "Uniformity", "result": "Within limits", "status": "PASS"}
    ])

    overall_status = "COMPLIANT" if all(t["status"] == "PASS" for t in tests) else "NON-COMPLIANT"

    return jsonify({
        "tests": tests,
        "overall_status": overall_status,
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)