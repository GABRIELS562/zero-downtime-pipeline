# Comprehensive Health Check System

A forensic-level health validation framework for business-critical deployments, designed by a DevOps engineer with forensic science background.

## Overview

This health check system applies forensic investigation principles to system validation:

- **Chain of Custody**: Immutable audit trail of all health checks
- **Evidence Collection**: Systematic gathering of system metrics and logs  
- **Timeline Analysis**: Chronological tracking of system state changes
- **Risk Assessment**: Quantified health scoring with threshold analysis
- **Incident Response**: Automated alerting and escalation procedures

## Architecture

```
health-checks/
├── common/
│   └── forensic_validator.py      # Base framework with forensic logging
├── infrastructure/
│   └── system_health.py           # Infrastructure-level validation
├── finance/
│   └── trading_validation.py     # Financial trading system checks
├── pharma/
│   └── manufacturing_validation.py # Pharmaceutical manufacturing checks
├── regression/
│   └── performance_detector.py   # Performance regression detection
├── reports/                       # Generated health reports
└── orchestrator.py               # Main orchestrator
```

## Industry-Specific Health Checks

### Financial Trading Systems

**Sub-50ms Latency Requirements**
- Market data feed connectivity validation
- Order processing pipeline integrity
- Risk management system validation
- Regulatory compliance checks (MiFID II, Dodd-Frank)

**Key Metrics:**
- Market data latency: <50ms
- Order success rate: >99.99%
- Market feed uptime: >99.95%

### Pharmaceutical Manufacturing

**FDA 21 CFR Part 11 Compliance**
- Manufacturing line efficiency monitoring (98% minimum)
- Environmental sensor validation (temperature, pressure, humidity)
- Batch integrity and traceability validation
- Equipment qualification status verification

**Key Metrics:**
- Manufacturing efficiency: ≥98%
- Sensor validation rate: >99.5%
- Batch integrity score: 100%
- Audit trail completeness: 100%

## Forensic Validation Principles

### 1. Evidence Chain of Custody
Every health check result includes:
- Immutable SHA-256 hash for integrity verification
- Timestamp with microsecond precision
- Digital signatures for FDA compliance
- Audit trail linking to previous checks

### 2. Multi-Tier Validation
```
Infrastructure Layer
├── System Resources (CPU, Memory, Disk, Network)
├── Kubernetes Cluster Health
└── Network Connectivity & Latency

Application Layer  
├── Service Health & Dependencies
├── API Response Times & Success Rates
└── Database Performance & Connectivity

Business Logic Layer
├── Industry-Specific Validations
├── Regulatory Compliance Checks
└── Performance Regression Detection
```

### 3. Statistical Baseline Analysis
- Establishes performance baselines using historical data
- Detects anomalies using multiple algorithms (statistical, ML, change-point)
- Provides confidence scores for all detections
- Correlates metrics across system components

### 4. Automated Incident Response
- Real-time alerting based on severity thresholds
- Escalation procedures for business-critical issues
- Integration with PagerDuty, Slack, and email notifications
- Automated runbook execution for known issues

## Usage

### Basic Health Check Execution

```python
from health_checks.orchestrator import BusinessCriticalHealthOrchestrator

# Initialize orchestrator
orchestrator = BusinessCriticalHealthOrchestrator()

# Run comprehensive health check
health_report = await orchestrator.run_comprehensive_health_check()

# Check overall status
print(f"System Status: {health_report['overall_status']}")
print(f"Critical Issues: {health_report['summary']['critical_count']}")
```

### Command Line Interface

```bash
# Single execution
python -m health_checks.orchestrator --config config.yaml --output report.json

# Continuous monitoring
python -m health_checks.orchestrator --continuous --interval 300

# Industry-specific checks only
python -m health_checks.orchestrator --config finance_only.yaml

# Generate compliance report
python -m health_checks.orchestrator --config pharma_fda.yaml --format yaml
```

### Configuration

```yaml
# config.yaml
enabled_industries: ["finance", "pharma"]

infrastructure:
  enabled: true
  system_thresholds:
    cpu_critical: 90
    memory_critical: 85
    disk_critical: 90

finance:
  enabled: true
  latency_threshold_ms: 50.0
  market_data_feeds:
    - name: "primary_feed"
      type: "websocket"
      endpoint: "wss://market-data.example.com/feed"
  regulations: ["MiFID_II", "Dodd_Frank"]

pharma:
  enabled: true
  efficiency_threshold: 98.0
  manufacturing_lines:
    - "http://line-001:8080"
    - "http://line-002:8080"

compliance:
  fda_21cfr11: true
  sox_compliance: true
  audit_retention_days: 2555  # 7 years
```

## Health Check Examples

### Financial Trading System

```python
from health_checks.finance.trading_validation import MarketDataFeedCheck

# Configure market data feeds
feeds = [
    {
        "name": "bloomberg",
        "type": "websocket",
        "endpoint": "wss://feed.bloomberg.com/market-data",
        "symbols": ["EURUSD", "GBPUSD"]
    }
]

# Execute check
check = MarketDataFeedCheck(logger, feeds, latency_threshold_ms=50.0)
result = await check.execute()

# Validate requirements
assert result.status == HealthStatus.HEALTHY
assert result.metrics["average_latency_ms"] < 50.0
assert result.metrics["success_rate_percent"] > 99.99
```

### Pharmaceutical Manufacturing

```python
from health_checks.pharma.manufacturing_validation import SensorValidationCheck

# Configure sensor endpoints  
sensors = [
    "http://sensor-gateway:8080/temperature",
    "http://sensor-gateway:8080/pressure",
    "http://sensor-gateway:8080/humidity"
]

# Execute validation
check = SensorValidationCheck(logger, sensors)
result = await check.execute()

# FDA compliance validation
assert result.metrics["validation_success_rate"] > 99.5
assert result.metrics["critical_alerts"] == 0
assert result.evidence["calibration_status"]["overdue_count"] == 0
```

## Performance Regression Detection

The system includes advanced performance regression detection using:

### Statistical Methods
- Z-score analysis with configurable thresholds
- Percentile-based anomaly detection (P95, P99)
- Confidence intervals with statistical significance testing

### Machine Learning
- Isolation Forest for multivariate anomaly detection
- Adaptive thresholds based on historical patterns
- Cross-correlation analysis for root cause identification

### Change Point Detection
- Sliding window analysis for trend identification
- T-tests for statistical significance of changes
- Automatic baseline adaptation

```python
from health_checks.regression.performance_detector import PerformanceRegressionDetector

config = {
    "baseline_window_hours": 24,
    "regression_threshold_percent": 10.0,
    "confidence_threshold": 0.8
}

detector = PerformanceRegressionDetector(logger, config)
result = await detector.execute()

# Check for regressions
if result.metrics["regressions_detected"] > 0:
    print(f"Performance regression detected!")
    print(f"Confidence: {result.metrics['average_confidence']:.2f}")
    print(f"Max deviation: {result.metrics['max_deviation_percent']:.1f}%")
```

## Compliance and Auditing

### FDA 21 CFR Part 11 Compliance
- Electronic records with digital signatures
- Audit trails with 7-year retention
- User access controls and validation
- Data integrity verification

### SOX Compliance  
- Separation of duties in deployment processes
- Immutable audit logs for financial systems
- Access control validation
- Change management tracking

### Forensic Evidence Preservation
- All health check results include cryptographic hashes
- Chain of custody maintained throughout execution
- Automated evidence collection and preservation
- Compliance reporting with digital signatures

## Integration Examples

### Kubernetes Deployment Validation

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pre-deployment-health-check
spec:
  template:
    spec:
      containers:
      - name: health-checker
        image: health-checks:latest
        command: ["python", "-m", "health_checks.orchestrator"]
        args: ["--config", "/config/health-check.yaml"]
        volumeMounts:
        - name: config
          mountPath: /config
      restartPolicy: Never
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/deployment.yml
- name: Pre-deployment Health Check
  run: |
    python -m health_checks.orchestrator \
      --config .github/health-check-config.yaml \
      --output health-report.json
    
    # Fail deployment if critical issues detected
    if [ $(jq '.summary.critical_count' health-report.json) -gt 0 ]; then
      echo "Critical health issues detected - failing deployment"
      exit 1
    fi

- name: Post-deployment Validation
  run: |
    sleep 60  # Allow system to stabilize
    python -m health_checks.orchestrator \
      --config .github/post-deployment-config.yaml
```

### Monitoring and Alerting

```python
# Integration with monitoring systems
import json
from health_checks.orchestrator import BusinessCriticalHealthOrchestrator

async def scheduled_health_check():
    orchestrator = BusinessCriticalHealthOrchestrator()
    report = await orchestrator.run_comprehensive_health_check()
    
    # Send metrics to Prometheus
    for check_name, result in report["detailed_results"].items():
        send_metric(f"health_check_score", result["score"], {"check": check_name})
        send_metric(f"health_check_duration_ms", result["duration_ms"], {"check": check_name})
    
    # Alert on critical issues
    if report["summary"]["critical_count"] > 0:
        send_alert("Critical health check failures detected", report)
```

## Best Practices

### 1. Baseline Management
- Establish baselines during stable periods
- Update baselines regularly (weekly/monthly)
- Maintain separate baselines for different time periods
- Consider seasonal and business cycle variations

### 2. Threshold Configuration
- Set conservative thresholds initially
- Adjust based on false positive/negative rates
- Use different thresholds for different environments
- Consider business impact when setting thresholds

### 3. Incident Response
- Define clear escalation procedures
- Automate responses for known issues
- Maintain runbooks for common problems
- Practice incident response procedures regularly

### 4. Compliance Management
- Regular audit of health check configurations
- Validation of digital signatures and audit trails
- Backup and archive of compliance data
- Regular compliance report generation

## Troubleshooting

### Common Issues

**Health Check Timeouts**
```python
# Increase timeout values in configuration
config = {
    "infrastructure": {
        "network_targets": [
            {"name": "api", "url": "https://api.example.com", "timeout": 10}
        ]
    }
}
```

**Missing Dependencies**
```bash
# Install required packages
pip install -r requirements.txt

# For machine learning features
pip install scikit-learn numpy scipy
```

**Kubernetes API Access**
```bash
# Ensure proper RBAC permissions
kubectl create clusterrolebinding health-check-binding \
  --clusterrole=view \
  --serviceaccount=default:health-check-sa
```

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run health checks with verbose output
orchestrator = BusinessCriticalHealthOrchestrator()
result = await orchestrator.run_comprehensive_health_check()
```

## Contributing

When adding new health checks:

1. Inherit from `BaseHealthCheck`
2. Implement forensic evidence collection
3. Include statistical baseline analysis
4. Add comprehensive error handling
5. Write tests with mock data
6. Update documentation

Example:
```python
class CustomHealthCheck(BaseHealthCheck):
    def __init__(self, logger: ForensicLogger, config: Dict[str, Any]):
        super().__init__("custom.component", logger)
        self.config = config
    
    async def execute(self):
        start_time = time.perf_counter()
        
        try:
            # Implement health check logic
            metrics = await self._collect_metrics()
            evidence = await self._collect_evidence()
            
            # Calculate health score
            score, status, severity = self._calculate_health_score(metrics)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return self._create_result(
                check_type="custom_check",
                status=status,
                score=score,
                metrics=metrics,
                evidence=evidence,
                duration_ms=duration_ms,
                severity=severity
            )
        except Exception as e:
            # Handle errors with forensic logging
            return self._create_error_result(e, start_time)
```

This comprehensive health check system provides enterprise-grade validation suitable for business-critical deployments in financial and pharmaceutical industries, with full forensic audit capabilities.