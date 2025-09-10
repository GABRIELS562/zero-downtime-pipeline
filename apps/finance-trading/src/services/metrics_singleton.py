"""
Singleton pattern for Prometheus metrics to prevent duplicate registrations
"""

import os
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, REGISTRY

# Use environment variable to detect if metrics are already initialized
_METRICS_INITIALIZED = os.environ.get('FINANCE_METRICS_INITIALIZED', 'false')

class MetricsSingleton:
    _instance = None
    _metrics = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_metrics()
        return cls._instance
    
    def _initialize_metrics(self):
        """Initialize all metrics once"""
        if _METRICS_INITIALIZED == 'true':
            return
            
        try:
            # Health monitoring metrics
            self._metrics['health_check_duration'] = Histogram('health_check_duration_seconds', 'Health check duration', ['check_type'])
            self._metrics['health_check_success'] = Counter('health_check_success_total', 'Successful health checks', ['check_type'])
            self._metrics['health_check_failures'] = Counter('health_check_failure_total', 'Failed health checks', ['check_type'])
            
            # Business metrics
            self._metrics['trading_volume_gauge'] = Gauge('trading_volume_current', 'Current trading volume')
            self._metrics['revenue_gauge'] = Gauge('revenue_current', 'Current revenue')
            self._metrics['order_success_rate'] = Gauge('order_success_rate', 'Order success rate percentage')
            self._metrics['portfolio_accuracy'] = Gauge('portfolio_accuracy', 'Portfolio calculation accuracy')
            self._metrics['market_data_latency'] = Histogram('market_data_latency_seconds', 'Market data feed latency')
            self._metrics['risk_exposure'] = Gauge('risk_exposure_current', 'Current risk exposure')
            
            # System metrics
            self._metrics['cpu_usage'] = Gauge('cpu_usage_percent', 'CPU usage percentage')
            self._metrics['memory_usage'] = Gauge('memory_usage_percent', 'Memory usage percentage')
            self._metrics['response_time_p95'] = Gauge('response_time_p95_ms', '95th percentile response time')
            self._metrics['response_time_p99'] = Gauge('response_time_p99_ms', '99th percentile response time')
            
            # Business performance metrics
            self._metrics['trading_volume_24h'] = Gauge('trading_volume_24h_usd', 'Trading volume in last 24 hours (USD)')
            self._metrics['revenue_24h'] = Gauge('revenue_24h_usd', 'Revenue in last 24 hours (USD)')
            self._metrics['active_traders'] = Gauge('active_traders_count', 'Number of active traders')
            self._metrics['avg_order_latency'] = Gauge('avg_order_latency_ms', 'Average order processing latency (ms)')
            self._metrics['compliance_score'] = Gauge('compliance_score_percent', 'SOX compliance score percentage')
            self._metrics['risk_score'] = Gauge('risk_score_normalized', 'Normalized risk score (0-1)')
            self._metrics['fraud_alerts'] = Counter('fraud_alerts_total', 'Total fraud alerts generated')
            self._metrics['audit_events'] = Counter('audit_events_total', 'Total audit events logged')
            self._metrics['position_value'] = Gauge('position_value_usd', 'Total position value (USD)')
            self._metrics['pnl_realized'] = Gauge('pnl_realized_usd', 'Realized P&L (USD)')
            self._metrics['pnl_unrealized'] = Gauge('pnl_unrealized_usd', 'Unrealized P&L (USD)')
            
            # SOX Compliance metrics
            self._metrics['sox_audit_entries'] = Counter('sox_audit_entries_total', 'Total SOX audit entries created', ['event_type'])
            self._metrics['sox_integrity_checks'] = Counter('sox_integrity_checks_total', 'SOX data integrity checks', ['status'])
            self._metrics['sox_violations'] = Counter('sox_violations_total', 'SOX compliance violations detected', ['violation_type'])
            self._metrics['sox_audit_latency'] = Histogram('sox_audit_latency_seconds', 'SOX audit logging latency')
            self._metrics['sox_data_retention'] = Gauge('sox_data_retention_days', 'SOX data retention period in days')
            
            # System info
            self._metrics['system_info'] = Info('trading_system_info', 'Trading system information')
            self._metrics['system_info'].info({
                'version': '1.0.0',
                'build_id': 'production',
                'environment': 'production',
                'compliance_level': 'SOX',
                'deployment_type': 'zero_downtime'
            })
            
            # Mark as initialized
            os.environ['FINANCE_METRICS_INITIALIZED'] = 'true'
            
        except ValueError as e:
            # Metrics already registered, skip
            pass
    
    def get_metric(self, name):
        """Get a specific metric by name"""
        return self._metrics.get(name)
    
    def get_all_metrics(self):
        """Get all metrics"""
        return self._metrics

# Create singleton instance
metrics = MetricsSingleton()

# Export commonly used metrics
health_check_duration = metrics.get_metric('health_check_duration')
health_check_success = metrics.get_metric('health_check_success')
health_check_failures = metrics.get_metric('health_check_failures')
trading_volume_gauge = metrics.get_metric('trading_volume_gauge')
revenue_gauge = metrics.get_metric('revenue_gauge')
order_success_rate = metrics.get_metric('order_success_rate')
portfolio_accuracy = metrics.get_metric('portfolio_accuracy')
market_data_latency = metrics.get_metric('market_data_latency')
risk_exposure = metrics.get_metric('risk_exposure')
cpu_usage = metrics.get_metric('cpu_usage')
memory_usage = metrics.get_metric('memory_usage')
response_time_p95 = metrics.get_metric('response_time_p95')
response_time_p99 = metrics.get_metric('response_time_p99')

# Business metrics
business_metrics = {
    'trading_volume_24h': metrics.get_metric('trading_volume_24h'),
    'revenue_24h': metrics.get_metric('revenue_24h'),
    'active_traders': metrics.get_metric('active_traders'),
    'order_success_rate': metrics.get_metric('order_success_rate'),
    'avg_order_latency': metrics.get_metric('avg_order_latency'),
    'compliance_score': metrics.get_metric('compliance_score'),
    'risk_score': metrics.get_metric('risk_score'),
    'fraud_alerts': metrics.get_metric('fraud_alerts'),
    'audit_events': metrics.get_metric('audit_events'),
    'position_value': metrics.get_metric('position_value'),
    'pnl_realized': metrics.get_metric('pnl_realized'),
    'pnl_unrealized': metrics.get_metric('pnl_unrealized')
}

system_info = metrics.get_metric('system_info')