"""
Health Monitoring Service
Ultra-low latency health checks and business-critical monitoring for trading systems
"""

import asyncio
import time
import statistics
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import logging

from prometheus_client import Counter, Histogram, Gauge, Summary
from src.services.market_data_service import MarketDataService
from src.services.order_processor import OrderProcessor
from src.services.sox_compliance import SOXComplianceService

logger = logging.getLogger(__name__)

# Prometheus metrics for health monitoring
health_check_duration = Histogram('health_check_duration_seconds', 'Health check duration', ['check_type'])
health_check_success = Counter('health_check_success_total', 'Successful health checks', ['check_type'])
health_check_failures = Counter('health_check_failure_total', 'Failed health checks', ['check_type'])

# Business metrics
trading_volume_gauge = Gauge('trading_volume_current', 'Current trading volume')
revenue_gauge = Gauge('revenue_current', 'Current revenue')
order_success_rate = Gauge('order_success_rate', 'Order success rate percentage')
portfolio_accuracy = Gauge('portfolio_accuracy', 'Portfolio calculation accuracy')
market_data_latency = Histogram('market_data_latency_seconds', 'Market data feed latency')
risk_exposure = Gauge('risk_exposure_current', 'Current risk exposure')

# System metrics
cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('memory_usage_percent', 'Memory usage percentage')
response_time_p95 = Gauge('response_time_p95_ms', '95th percentile response time')
response_time_p99 = Gauge('response_time_p99_ms', '99th percentile response time')

class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

class MarketStatus(str, Enum):
    """Market status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    HOLIDAY = "holiday"

@dataclass
class HealthCheckResult:
    """Health check result"""
    check_name: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    details: Dict[str, Any]
    critical: bool = False
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

@dataclass
class BusinessMetrics:
    """Business metrics snapshot"""
    timestamp: datetime
    trading_volume_24h: Decimal
    revenue_24h: Decimal
    active_orders: int
    successful_orders: int
    failed_orders: int
    average_order_size: Decimal
    largest_order_size: Decimal
    order_success_rate: float
    portfolio_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    risk_exposure: Decimal
    var_95: Decimal

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_bytes: int
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    active_connections: int
    queue_depth: int
    error_rate: float

@dataclass
class MarketDataHealth:
    """Market data health status"""
    timestamp: datetime
    feed_status: HealthStatus
    symbols_active: int
    updates_per_second: float
    average_latency_ms: float
    last_update: datetime
    stale_data_symbols: List[str]
    feed_errors: int

class HealthMonitor:
    """
    Comprehensive health monitoring service
    Provides ultra-low latency health checks and business-critical monitoring
    """
    
    def __init__(self):
        self.market_data_service: Optional[MarketDataService] = None
        self.order_processor: Optional[OrderProcessor] = None
        self.sox_compliance: Optional[SOXComplianceService] = None
        
        # Health check history
        self.health_history: List[HealthCheckResult] = []
        self.business_metrics_history: List[BusinessMetrics] = []
        self.system_metrics_history: List[SystemMetrics] = []
        
        # Response time tracking
        self.response_times: List[float] = []
        self.max_response_time_history = 1000
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 30.0,  # 30ms
            'response_time_critical': 50.0,  # 50ms
            'cpu_usage_warning': 70.0,  # 70%
            'cpu_usage_critical': 90.0,  # 90%
            'memory_usage_warning': 80.0,  # 80%
            'memory_usage_critical': 95.0,  # 95%
            'order_success_rate_warning': 99.0,  # 99%
            'order_success_rate_critical': 95.0,  # 95%
            'market_data_latency_warning': 100.0,  # 100ms
            'market_data_latency_critical': 500.0,  # 500ms
            'portfolio_accuracy_warning': 99.9,  # 99.9%
            'portfolio_accuracy_critical': 99.0,  # 99%
            'risk_exposure_warning': 80.0,  # 80% of limit
            'risk_exposure_critical': 95.0,  # 95% of limit
        }
        
        # Business hours (NYSE/NASDAQ)
        self.market_hours = {
            'open_time': '09:30',
            'close_time': '16:00',
            'timezone': 'US/Eastern',
            'pre_market_start': '04:00',
            'after_hours_end': '20:00'
        }
        
        # Monitoring intervals
        self.monitoring_active = False
        self.monitoring_task = None
        
        # Market data tracking
        self.market_data_updates = 0
        self.market_data_errors = 0
        self.last_market_data_update = datetime.now(timezone.utc)
    
    def set_dependencies(self, market_data_service: MarketDataService, 
                        order_processor: OrderProcessor, 
                        sox_compliance: SOXComplianceService):
        """Set service dependencies"""
        self.market_data_service = market_data_service
        self.order_processor = order_processor
        self.sox_compliance = sox_compliance
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                # Update system metrics
                await self._update_system_metrics()
                
                # Update business metrics
                await self._update_business_metrics()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep for monitoring interval
                await asyncio.sleep(5)  # 5-second intervals
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def perform_ultra_low_latency_check(self) -> HealthCheckResult:
        """
        Ultra-low latency health check (<50ms requirement)
        Critical for zero-downtime deployment validation
        """
        start_time = time.time()
        
        try:
            # Minimal checks for maximum speed
            checks = []
            
            # 1. Basic connectivity (1ms)
            basic_check = await self._basic_connectivity_check()
            checks.append(basic_check)
            
            # 2. Market data freshness (5ms)
            if self.market_data_service:
                market_check = await self._quick_market_data_check()
                checks.append(market_check)
            
            # 3. Order processing capability (10ms)
            if self.order_processor:
                order_check = await self._quick_order_processing_check()
                checks.append(order_check)
            
            # 4. System resources (5ms)
            system_check = await self._quick_system_check()
            checks.append(system_check)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Determine overall status
            critical_failures = [c for c in checks if c['status'] == HealthStatus.CRITICAL]
            unhealthy_checks = [c for c in checks if c['status'] == HealthStatus.UNHEALTHY]
            
            if critical_failures:
                status = HealthStatus.CRITICAL
            elif unhealthy_checks:
                status = HealthStatus.UNHEALTHY
            elif response_time > self.thresholds['response_time_warning']:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            # Track response time
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_time_history:
                self.response_times.pop(0)
            
            result = HealthCheckResult(
                check_name="ultra_low_latency",
                status=status,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'checks': checks,
                    'response_time_threshold': self.thresholds['response_time_critical'],
                    'sla_met': response_time < self.thresholds['response_time_critical']
                },
                critical=response_time > self.thresholds['response_time_critical'],
                threshold_warning=self.thresholds['response_time_warning'],
                threshold_critical=self.thresholds['response_time_critical']
            )
            
            # Update metrics
            health_check_duration.labels(check_type="ultra_low_latency").observe(response_time / 1000)
            if status == HealthStatus.HEALTHY:
                health_check_success.labels(check_type="ultra_low_latency").inc()
            else:
                health_check_failures.labels(check_type="ultra_low_latency").inc()
            
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Ultra-low latency health check failed: {e}")
            health_check_failures.labels(check_type="ultra_low_latency").inc()
            
            return HealthCheckResult(
                check_name="ultra_low_latency",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={'error': str(e)},
                critical=True
            )
    
    async def _basic_connectivity_check(self) -> Dict[str, Any]:
        """Basic connectivity check"""
        try:
            # Simulate basic connectivity check
            await asyncio.sleep(0.001)  # 1ms
            return {
                'name': 'basic_connectivity',
                'status': HealthStatus.HEALTHY,
                'details': {'connected': True}
            }
        except Exception as e:
            return {
                'name': 'basic_connectivity',
                'status': HealthStatus.CRITICAL,
                'details': {'error': str(e)}
            }
    
    async def _quick_market_data_check(self) -> Dict[str, Any]:
        """Quick market data freshness check"""
        try:
            start_time = time.time()
            
            # Check if market data is fresh
            if self.market_data_service:
                symbols = self.market_data_service.get_all_symbols()
                if not symbols:
                    return {
                        'name': 'market_data',
                        'status': HealthStatus.CRITICAL,
                        'details': {'error': 'No market data available'}
                    }
                
                # Check a sample symbol
                sample_data = self.market_data_service.get_symbol_data(symbols[0])
                if not sample_data:
                    return {
                        'name': 'market_data',
                        'status': HealthStatus.UNHEALTHY,
                        'details': {'error': 'Market data stale'}
                    }
                
                # Check data freshness
                data_age = (datetime.now(timezone.utc) - sample_data.timestamp).total_seconds()
                if data_age > 10:  # 10 seconds threshold
                    return {
                        'name': 'market_data',
                        'status': HealthStatus.DEGRADED,
                        'details': {'data_age_seconds': data_age}
                    }
            
            latency = (time.time() - start_time) * 1000
            market_data_latency.observe(latency / 1000)
            
            return {
                'name': 'market_data',
                'status': HealthStatus.HEALTHY,
                'details': {'latency_ms': latency}
            }
            
        except Exception as e:
            return {
                'name': 'market_data',
                'status': HealthStatus.CRITICAL,
                'details': {'error': str(e)}
            }
    
    async def _quick_order_processing_check(self) -> Dict[str, Any]:
        """Quick order processing capability check"""
        try:
            if self.order_processor:
                stats = self.order_processor.get_processing_stats()
                
                success_rate = stats.get('fill_rate_percent', 0)
                if success_rate < self.thresholds['order_success_rate_critical']:
                    return {
                        'name': 'order_processing',
                        'status': HealthStatus.CRITICAL,
                        'details': {'success_rate': success_rate}
                    }
                elif success_rate < self.thresholds['order_success_rate_warning']:
                    return {
                        'name': 'order_processing',
                        'status': HealthStatus.DEGRADED,
                        'details': {'success_rate': success_rate}
                    }
                
                return {
                    'name': 'order_processing',
                    'status': HealthStatus.HEALTHY,
                    'details': {
                        'success_rate': success_rate,
                        'pending_orders': stats.get('pending_orders', 0)
                    }
                }
            
            return {
                'name': 'order_processing',
                'status': HealthStatus.HEALTHY,
                'details': {'processor_available': False}
            }
            
        except Exception as e:
            return {
                'name': 'order_processing',
                'status': HealthStatus.CRITICAL,
                'details': {'error': str(e)}
            }
    
    async def _quick_system_check(self) -> Dict[str, Any]:
        """Quick system resource check"""
        try:
            # Quick CPU and memory check
            cpu_percent = psutil.cpu_percent(interval=0.01)
            memory_percent = psutil.virtual_memory().percent
            
            # Update metrics
            cpu_usage.set(cpu_percent)
            memory_usage.set(memory_percent)
            
            # Determine status
            if (cpu_percent > self.thresholds['cpu_usage_critical'] or 
                memory_percent > self.thresholds['memory_usage_critical']):
                return {
                    'name': 'system_resources',
                    'status': HealthStatus.CRITICAL,
                    'details': {'cpu': cpu_percent, 'memory': memory_percent}
                }
            elif (cpu_percent > self.thresholds['cpu_usage_warning'] or 
                  memory_percent > self.thresholds['memory_usage_warning']):
                return {
                    'name': 'system_resources',
                    'status': HealthStatus.DEGRADED,
                    'details': {'cpu': cpu_percent, 'memory': memory_percent}
                }
            
            return {
                'name': 'system_resources',
                'status': HealthStatus.HEALTHY,
                'details': {'cpu': cpu_percent, 'memory': memory_percent}
            }
            
        except Exception as e:
            return {
                'name': 'system_resources',
                'status': HealthStatus.CRITICAL,
                'details': {'error': str(e)}
            }
    
    async def perform_market_data_health_check(self) -> HealthCheckResult:
        """Comprehensive market data feed health check"""
        start_time = time.time()
        
        try:
            details = {}
            
            if not self.market_data_service:
                return HealthCheckResult(
                    check_name="market_data_feed",
                    status=HealthStatus.CRITICAL,
                    response_time_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc),
                    details={'error': 'Market data service not available'},
                    critical=True
                )
            
            # Get market status
            market_status = self.market_data_service.get_market_status()
            details['market_status'] = market_status
            
            # Check symbol count
            symbols = self.market_data_service.get_all_symbols()
            details['symbols_count'] = len(symbols)
            
            # Check data freshness for multiple symbols
            stale_symbols = []
            total_latency = 0
            valid_symbols = 0
            
            for symbol in symbols[:10]:  # Check first 10 symbols
                data = self.market_data_service.get_symbol_data(symbol)
                if data:
                    age = (datetime.now(timezone.utc) - data.timestamp).total_seconds()
                    if age > 30:  # 30 second threshold
                        stale_symbols.append(symbol)
                    else:
                        total_latency += age
                        valid_symbols += 1
            
            avg_latency = total_latency / valid_symbols if valid_symbols > 0 else 0
            details['average_latency_ms'] = avg_latency * 1000
            details['stale_symbols'] = stale_symbols
            details['valid_symbols'] = valid_symbols
            
            # Determine health status
            if len(stale_symbols) > len(symbols) * 0.5:  # >50% stale
                status = HealthStatus.CRITICAL
            elif len(stale_symbols) > len(symbols) * 0.1:  # >10% stale
                status = HealthStatus.DEGRADED
            elif avg_latency > self.thresholds['market_data_latency_critical'] / 1000:
                status = HealthStatus.CRITICAL
            elif avg_latency > self.thresholds['market_data_latency_warning'] / 1000:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_name="market_data_feed",
                status=status,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details=details,
                critical=status == HealthStatus.CRITICAL
            )
            
            # Update metrics
            health_check_duration.labels(check_type="market_data_feed").observe(response_time / 1000)
            if status == HealthStatus.HEALTHY:
                health_check_success.labels(check_type="market_data_feed").inc()
            else:
                health_check_failures.labels(check_type="market_data_feed").inc()
            
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Market data health check failed: {e}")
            
            return HealthCheckResult(
                check_name="market_data_feed",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={'error': str(e)},
                critical=True
            )
    
    async def perform_order_processing_health_check(self) -> HealthCheckResult:
        """Comprehensive order processing health check"""
        start_time = time.time()
        
        try:
            details = {}
            
            if not self.order_processor:
                return HealthCheckResult(
                    check_name="order_processing",
                    status=HealthStatus.CRITICAL,
                    response_time_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc),
                    details={'error': 'Order processor not available'},
                    critical=True
                )
            
            # Get processing statistics
            stats = self.order_processor.get_processing_stats()
            details.update(stats)
            
            # Calculate derived metrics
            success_rate = stats.get('fill_rate_percent', 0)
            avg_processing_time = stats.get('avg_processing_time_ms', 0)
            pending_orders = stats.get('pending_orders', 0)
            
            # Check queue depth
            if pending_orders > 1000:
                details['queue_warning'] = f"High pending orders: {pending_orders}"
            
            # Check processing time
            if avg_processing_time > 100:  # 100ms threshold
                details['latency_warning'] = f"High processing time: {avg_processing_time}ms"
            
            # Determine health status
            if success_rate < self.thresholds['order_success_rate_critical']:
                status = HealthStatus.CRITICAL
            elif success_rate < self.thresholds['order_success_rate_warning']:
                status = HealthStatus.DEGRADED
            elif avg_processing_time > 50:  # 50ms threshold
                status = HealthStatus.DEGRADED
            elif pending_orders > 500:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_name="order_processing",
                status=status,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details=details,
                critical=status == HealthStatus.CRITICAL
            )
            
            # Update metrics
            order_success_rate.set(success_rate)
            health_check_duration.labels(check_type="order_processing").observe(response_time / 1000)
            
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Order processing health check failed: {e}")
            
            return HealthCheckResult(
                check_name="order_processing",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={'error': str(e)},
                critical=True
            )
    
    async def perform_portfolio_accuracy_check(self) -> HealthCheckResult:
        """Portfolio calculation accuracy check"""
        start_time = time.time()
        
        try:
            details = {}
            
            # Simulate portfolio accuracy calculation
            # In production, this would validate against actual positions
            calculated_positions = 125  # Simulated
            verified_positions = 124   # Simulated
            
            accuracy = (verified_positions / calculated_positions) * 100 if calculated_positions > 0 else 0
            details['accuracy_percent'] = accuracy
            details['calculated_positions'] = calculated_positions
            details['verified_positions'] = verified_positions
            
            # Portfolio value validation
            calculated_value = Decimal('1000000.00')  # $1M
            verified_value = Decimal('999500.00')     # $999.5K
            value_difference = abs(calculated_value - verified_value)
            value_accuracy = (1 - (value_difference / calculated_value)) * 100
            
            details['value_accuracy_percent'] = float(value_accuracy)
            details['value_difference'] = float(value_difference)
            
            # Determine health status
            if accuracy < self.thresholds['portfolio_accuracy_critical']:
                status = HealthStatus.CRITICAL
            elif accuracy < self.thresholds['portfolio_accuracy_warning']:
                status = HealthStatus.DEGRADED
            elif value_accuracy < 99.5:  # 99.5% threshold
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_name="portfolio_accuracy",
                status=status,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details=details,
                critical=status == HealthStatus.CRITICAL
            )
            
            # Update metrics
            portfolio_accuracy.set(accuracy)
            
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Portfolio accuracy check failed: {e}")
            
            return HealthCheckResult(
                check_name="portfolio_accuracy",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={'error': str(e)},
                critical=True
            )
    
    def get_market_status(self) -> MarketStatus:
        """Get current market status with business hours awareness"""
        try:
            from datetime import datetime
            import pytz
            
            # Get current time in market timezone
            market_tz = pytz.timezone(self.market_hours['timezone'])
            current_time = datetime.now(market_tz)
            current_hour_minute = current_time.strftime('%H:%M')
            
            # Check if it's a weekend
            if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return MarketStatus.CLOSED
            
            # Check market hours
            if (current_hour_minute >= self.market_hours['open_time'] and 
                current_hour_minute < self.market_hours['close_time']):
                return MarketStatus.OPEN
            elif (current_hour_minute >= self.market_hours['pre_market_start'] and 
                  current_hour_minute < self.market_hours['open_time']):
                return MarketStatus.PRE_MARKET
            elif (current_hour_minute >= self.market_hours['close_time'] and 
                  current_hour_minute < self.market_hours['after_hours_end']):
                return MarketStatus.AFTER_HOURS
            else:
                return MarketStatus.CLOSED
                
        except Exception as e:
            logger.error(f"Error determining market status: {e}")
            return MarketStatus.CLOSED
    
    async def _update_system_metrics(self):
        """Update system performance metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate response time statistics
            if self.response_times:
                avg_response_time = statistics.mean(self.response_times)
                p95_response_time = statistics.quantiles(self.response_times, n=20)[18]  # 95th percentile
                p99_response_time = statistics.quantiles(self.response_times, n=100)[98]  # 99th percentile
            else:
                avg_response_time = 0
                p95_response_time = 0
                p99_response_time = 0
            
            # Update Prometheus metrics
            cpu_usage.set(cpu_percent)
            memory_usage.set(memory.percent)
            response_time_p95.set(p95_response_time)
            response_time_p99.set(p99_response_time)
            
            # Store metrics
            system_metrics = SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_io_bytes=1024 * 1024 * 10,  # Simulated
                response_time_avg=avg_response_time,
                response_time_p95=p95_response_time,
                response_time_p99=p99_response_time,
                active_connections=25,  # Simulated
                queue_depth=5,  # Simulated
                error_rate=0.01  # Simulated
            )
            
            self.system_metrics_history.append(system_metrics)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    async def _update_business_metrics(self):
        """Update business performance metrics"""
        try:
            # Simulate business metrics calculation
            # In production, these would come from actual trading data
            
            business_metrics = BusinessMetrics(
                timestamp=datetime.now(timezone.utc),
                trading_volume_24h=Decimal('25000000.00'),  # $25M
                revenue_24h=Decimal('125000.00'),  # $125K
                active_orders=125,
                successful_orders=15620,
                failed_orders=32,
                average_order_size=Decimal('5000.00'),
                largest_order_size=Decimal('500000.00'),
                order_success_rate=99.79,
                portfolio_value=Decimal('1000000.00'),
                unrealized_pnl=Decimal('25000.00'),
                realized_pnl=Decimal('50000.00'),
                risk_exposure=Decimal('750000.00'),
                var_95=Decimal('45000.00')
            )
            
            # Update Prometheus metrics
            trading_volume_gauge.set(float(business_metrics.trading_volume_24h))
            revenue_gauge.set(float(business_metrics.revenue_24h))
            order_success_rate.set(business_metrics.order_success_rate)
            risk_exposure.set(float(business_metrics.risk_exposure))
            
            self.business_metrics_history.append(business_metrics)
            
        except Exception as e:
            logger.error(f"Error updating business metrics: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            # Keep last 1000 entries for each metric type
            max_entries = 1000
            
            if len(self.health_history) > max_entries:
                self.health_history = self.health_history[-max_entries:]
            
            if len(self.business_metrics_history) > max_entries:
                self.business_metrics_history = self.business_metrics_history[-max_entries:]
            
            if len(self.system_metrics_history) > max_entries:
                self.system_metrics_history = self.system_metrics_history[-max_entries:]
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        try:
            market_status = self.get_market_status()
            
            # Calculate average response time
            avg_response_time = statistics.mean(self.response_times) if self.response_times else 0
            
            # Get latest metrics
            latest_business = self.business_metrics_history[-1] if self.business_metrics_history else None
            latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
            
            return {
                'timestamp': datetime.now(timezone.utc),
                'market_status': market_status.value,
                'overall_health': 'healthy',  # This would be calculated based on all checks
                'performance': {
                    'avg_response_time_ms': avg_response_time,
                    'p95_response_time_ms': statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0,
                    'p99_response_time_ms': statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else 0,
                    'sla_compliance': avg_response_time < self.thresholds['response_time_critical']
                },
                'business_metrics': asdict(latest_business) if latest_business else None,
                'system_metrics': asdict(latest_system) if latest_system else None,
                'thresholds': self.thresholds
            }
            
        except Exception as e:
            logger.error(f"Error generating health summary: {e}")
            return {'error': str(e), 'timestamp': datetime.now(timezone.utc)}
    
    def get_deployment_readiness(self) -> Dict[str, Any]:
        """Get deployment readiness assessment"""
        try:
            # Perform quick checks for deployment readiness
            checks = []
            
            # Check response times
            avg_response_time = statistics.mean(self.response_times) if self.response_times else 0
            response_check = {
                'name': 'response_time',
                'status': 'pass' if avg_response_time < self.thresholds['response_time_critical'] else 'fail',
                'value': avg_response_time,
                'threshold': self.thresholds['response_time_critical']
            }
            checks.append(response_check)
            
            # Check system resources
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_percent = psutil.virtual_memory().percent
                
                system_check = {
                    'name': 'system_resources',
                    'status': 'pass' if (cpu_percent < self.thresholds['cpu_usage_warning'] and 
                                       memory_percent < self.thresholds['memory_usage_warning']) else 'fail',
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent
                }
                checks.append(system_check)
            except Exception:
                checks.append({'name': 'system_resources', 'status': 'unknown'})
            
            # Check market data availability
            market_check = {
                'name': 'market_data',
                'status': 'pass' if self.market_data_service else 'fail',
                'available': bool(self.market_data_service)
            }
            checks.append(market_check)
            
            # Check order processing
            order_check = {
                'name': 'order_processing',
                'status': 'pass' if self.order_processor else 'fail',
                'available': bool(self.order_processor)
            }
            checks.append(order_check)
            
            # Overall readiness
            failed_checks = [c for c in checks if c['status'] == 'fail']
            overall_status = 'ready' if not failed_checks else 'not_ready'
            
            return {
                'timestamp': datetime.now(timezone.utc),
                'overall_status': overall_status,
                'checks': checks,
                'failed_checks': len(failed_checks),
                'market_status': self.get_market_status().value,
                'deployment_recommended': overall_status == 'ready'
            }
            
        except Exception as e:
            logger.error(f"Error assessing deployment readiness: {e}")
            return {
                'timestamp': datetime.now(timezone.utc),
                'overall_status': 'unknown',
                'error': str(e)
            }