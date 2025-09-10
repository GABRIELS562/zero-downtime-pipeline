"""
Singleton metrics registry to prevent duplicate registrations
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Use a custom registry to avoid conflicts
METRICS_REGISTRY = CollectorRegistry()

# Create metrics once
_metrics_created = False

if not _metrics_created:
    # Health monitoring metrics
    health_check_duration = Histogram('health_check_duration_seconds', 'Health check duration', ['check_type'], registry=METRICS_REGISTRY)
    health_check_success = Counter('health_check_success_total', 'Successful health checks', ['check_type'], registry=METRICS_REGISTRY)
    health_check_failures = Counter('health_check_failure_total', 'Failed health checks', ['check_type'], registry=METRICS_REGISTRY)
    
    # Business metrics
    trading_volume_gauge = Gauge('trading_volume_current', 'Current trading volume', registry=METRICS_REGISTRY)
    revenue_gauge = Gauge('revenue_current', 'Current revenue', registry=METRICS_REGISTRY)
    order_success_rate = Gauge('order_success_rate', 'Order success rate percentage', registry=METRICS_REGISTRY)
    portfolio_accuracy = Gauge('portfolio_accuracy', 'Portfolio calculation accuracy', registry=METRICS_REGISTRY)
    market_data_latency = Histogram('market_data_latency_seconds', 'Market data feed latency', registry=METRICS_REGISTRY)
    risk_exposure = Gauge('risk_exposure_current', 'Current risk exposure', registry=METRICS_REGISTRY)
    
    # System metrics
    cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage', registry=METRICS_REGISTRY)
    memory_usage = Gauge('memory_usage_percent', 'Memory usage percentage', registry=METRICS_REGISTRY)
    response_time_p95 = Gauge('response_time_p95_ms', '95th percentile response time', registry=METRICS_REGISTRY)
    response_time_p99 = Gauge('response_time_p99_ms', '99th percentile response time', registry=METRICS_REGISTRY)
    
    _metrics_created = True