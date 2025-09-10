#!/usr/bin/env python3
"""
Forensic Evidence Chain Web Interface
Provides real-time view of evidence chain with cryptographic verification
"""

from flask import Flask, jsonify, render_template_string, request
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import subprocess

app = Flask(__name__)

EVIDENCE_DIR = Path("/var/forensics/evidence")
DB_PATH = Path("/var/forensics/chain_of_custody.db")

# HTML template for evidence viewer
VIEWER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Forensic Evidence Chain Viewer</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
        }
        h1 {
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 10px;
        }
        .incident {
            background: #1a1a1a;
            border: 1px solid #00ff00;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 0 20px rgba(0,255,0,0.1);
        }
        .critical {
            border-color: #ff0000;
            box-shadow: 0 0 20px rgba(255,0,0,0.3);
        }
        .hash {
            font-family: monospace;
            color: #ffff00;
            word-break: break-all;
        }
        .chain-link {
            color: #00ffff;
            text-decoration: none;
        }
        .metadata {
            background: #0f0f0f;
            padding: 10px;
            border-radius: 3px;
            margin-top: 10px;
        }
        .status {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        .status.verified {
            background: #00ff00;
            color: #000;
        }
        .status.broken {
            background: #ff0000;
            color: #fff;
        }
        button {
            background: #00ff00;
            color: #000;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
        }
        button:hover {
            background: #00cc00;
        }
        .trigger-section {
            background: #1a1a1a;
            border: 2px solid #ffff00;
            padding: 20px;
            margin: 20px 0;
        }
    </style>
    <script>
        function triggerIncident(type) {
            fetch('/trigger/' + type, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert('Incident triggered: ' + data.incident_id);
                    location.reload();
                });
        }
        
        function verifyChain() {
            fetch('/verify')
                .then(response => response.json())
                .then(data => {
                    alert(data.verified ? 
                        '✓ Chain verified: ' + data.entries + ' entries intact' : 
                        '✗ Chain compromised!');
                });
        }
        
        setInterval(() => {
            location.reload();
        }, 30000); // Auto-refresh every 30 seconds
    </script>
</head>
<body>
    <h1>🔬 Forensic Evidence Chain Viewer</h1>
    
    <div class="trigger-section">
        <h2>Demo Incident Triggers</h2>
        <button onclick="triggerIncident('lims')">Trigger FDA Violation</button>
        <button onclick="triggerIncident('finance')">Trigger SOX Alert</button>
        <button onclick="triggerIncident('pharma')">Trigger GMP Breach</button>
        <button onclick="triggerIncident('dr_test')">Trigger DR Test</button>
        <button onclick="verifyChain()">Verify Chain Integrity</button>
    </div>
    
    <h2>Evidence Chain ({{ total_entries }} entries)</h2>
    
    {% for incident in incidents %}
    <div class="incident {% if incident.severity == 'CRITICAL' %}critical{% endif %}">
        <h3>{{ incident.incident_id }}</h3>
        <div><strong>Type:</strong> {{ incident.incident_type }}</div>
        <div><strong>Application:</strong> {{ incident.application }}</div>
        <div><strong>Severity:</strong> 
            <span class="status {% if incident.severity == 'CRITICAL' %}broken{% else %}verified{% endif %}">
                {{ incident.severity }}
            </span>
        </div>
        <div><strong>Timestamp:</strong> {{ incident.timestamp }}</div>
        <div><strong>Evidence Hash:</strong> <span class="hash">{{ incident.evidence_hash }}</span></div>
        {% if incident.previous_hash %}
        <div><strong>Previous Hash:</strong> 
            <a href="#{{ incident.previous_id }}" class="chain-link">{{ incident.previous_hash[:16] }}...</a>
        </div>
        {% endif %}
        <div class="metadata">
            <strong>Evidence Path:</strong> {{ incident.evidence_path }}
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def index():
    """Display evidence chain viewer"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM evidence_chain 
        ORDER BY id DESC 
        LIMIT 50
    """)
    incidents = cursor.fetchall()
    conn.close()
    
    return render_template_string(
        VIEWER_TEMPLATE,
        incidents=incidents,
        total_entries=len(incidents)
    )

@app.route('/api/incidents')
def get_incidents():
    """API endpoint for incident list"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evidence_chain ORDER BY id DESC")
    incidents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(incidents)

@app.route('/api/incident/<incident_id>')
def get_incident(incident_id):
    """Get specific incident details"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM evidence_chain WHERE incident_id = ?",
        (incident_id,)
    )
    incident = cursor.fetchone()
    conn.close()
    
    if incident:
        # Load full evidence from file
        evidence_file = Path(incident['evidence_path']) / "evidence.json"
        if evidence_file.exists():
            with open(evidence_file) as f:
                evidence = json.load(f)
            return jsonify({
                "chain_entry": dict(incident),
                "evidence": evidence
            })
    
    return jsonify({"error": "Incident not found"}), 404

@app.route('/trigger/<app_type>', methods=['POST'])
def trigger_incident(app_type):
    """Trigger demo incidents"""
    from forensic_collector import ForensicCollector
    
    collector = ForensicCollector()
    
    incidents = {
        'lims': {
            'type': 'FDA_VALIDATION_FAILURE',
            'app': 'lims-backend',
            'severity': 'CRITICAL',
            'metadata': {
                'regulation': '21 CFR Part 11',
                'audit_trail': 'Missing electronic signature',
                'impact': 'Batch release blocked'
            }
        },
        'finance': {
            'type': 'SOX_COMPLIANCE_ALERT',
            'app': 'finance-trading',
            'severity': 'HIGH',
            'metadata': {
                'regulation': 'Sarbanes-Oxley Act',
                'issue': 'Unauthorized transaction modification attempt',
                'amount': '$1,247,892.00'
            }
        },
        'pharma': {
            'type': 'GMP_DEVIATION',
            'app': 'pharma-manufacturing',
            'severity': 'HIGH',
            'metadata': {
                'regulation': 'Good Manufacturing Practice',
                'deviation': 'Temperature excursion in Clean Room A',
                'duration': '47 minutes',
                'batches_affected': 3
            }
        },
        'dr_test': {
            'type': 'DISASTER_RECOVERY_TEST',
            'app': 'infrastructure',
            'severity': 'INFO',
            'metadata': {
                'test_type': 'Full system failover',
                'initiated_by': 'Interview Demo',
                'expected_recovery': '30 minutes'
            }
        }
    }
    
    if app_type in incidents:
        incident = incidents[app_type]
        incident_id = collector.capture_incident(
            incident_type=incident['type'],
            application=incident['app'],
            severity=incident['severity'],
            metadata=incident['metadata']
        )
        return jsonify({
            'incident_id': incident_id,
            'status': 'captured'
        })
    
    return jsonify({'error': 'Unknown incident type'}), 400

@app.route('/verify')
def verify_chain():
    """Verify evidence chain integrity"""
    from forensic_collector import ForensicCollector
    
    collector = ForensicCollector()
    verified = collector.verify_chain()
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM evidence_chain")
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({
        'verified': verified,
        'entries': count,
        'message': 'Chain intact' if verified else 'Chain compromised'
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'forensic-api'})

if __name__ == '__main__':
    # Ensure directories exist
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize database if needed
    from forensic_collector import ForensicCollector
    collector = ForensicCollector()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8888, debug=False)