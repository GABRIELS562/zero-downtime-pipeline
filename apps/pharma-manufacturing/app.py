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
    """Root endpoint"""
    return jsonify({
        **pharma_data,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "api_health": "/api/v1/health/live",
            "batches": "/api/v1/batches",
            "metrics": "/metrics",
            "system": "/api/v1/system/info"
        }
    })

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