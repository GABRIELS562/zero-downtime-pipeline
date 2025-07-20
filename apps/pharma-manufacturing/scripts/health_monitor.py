#!/usr/bin/env python3
"""
Health Monitoring Script for Pharmaceutical Manufacturing System
Real-time monitoring of system health, performance, and compliance
"""

import asyncio
import os
import sys
import time
import json
import psutil
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

import httpx
import asyncpg
from prometheus_client import CollectorRegistry, Gauge, Counter, start_http_server

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PharmaHealthMonitor:
    """Comprehensive health monitor for pharmaceutical manufacturing system"""
    
    def __init__(self):
        # Configuration from environment
        self.app_host = os.getenv('APP_HOST', 'app')
        self.app_port = int(os.getenv('APP_PORT', '8000'))
        self.db_host = os.getenv('DB_HOST', 'postgres')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_user = os.getenv('DB_USER', 'pharma_user')
        self.db_password = os.getenv('DB_PASSWORD', 'pharma_password')
        self.db_name = os.getenv('DB_NAME', 'pharma_manufacturing_db')
        self.redis_host = os.getenv('REDIS_HOST', 'redis')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        
        # Health check configuration
        self.check_interval = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
        self.alert_threshold_cpu = float(os.getenv('ALERT_THRESHOLD_CPU', '80'))
        self.alert_threshold_memory = float(os.getenv('ALERT_THRESHOLD_MEMORY', '85'))
        self.alert_threshold_disk = float(os.getenv('ALERT_THRESHOLD_DISK', '90'))
        
        # Prometheus metrics
        self.registry = CollectorRegistry()
        self.setup_metrics()
        
        # Health status storage
        self.health_status = {
            'timestamp': None,
            'overall_status': 'unknown',
            'components': {}
        }
    
    def setup_metrics(self):
        """Setup Prometheus metrics for health monitoring"""
        self.metrics = {
            'system_cpu_usage': Gauge(
                'pharma_system_cpu_usage_percent',
                'System CPU usage percentage',
                registry=self.registry
            ),
            'system_memory_usage': Gauge(
                'pharma_system_memory_usage_percent',
                'System memory usage percentage',
                registry=self.registry
            ),
            'system_disk_usage': Gauge(
                'pharma_system_disk_usage_percent',
                'System disk usage percentage',
                registry=self.registry
            ),
            'database_connections': Gauge(
                'pharma_database_connections_active',
                'Active database connections',
                registry=self.registry
            ),
            'application_response_time': Gauge(
                'pharma_application_response_time_seconds',
                'Application response time',
                registry=self.registry
            ),
            'health_check_failures': Counter(
                'pharma_health_check_failures_total',
                'Total health check failures',
                ['component'],
                registry=self.registry
            ),
            'manufacturing_batches_active': Gauge(
                'pharma_manufacturing_batches_active',
                'Number of active manufacturing batches',
                registry=self.registry
            ),
            'equipment_status': Gauge(
                'pharma_equipment_operational',
                'Equipment operational status',
                ['equipment_id'],
                registry=self.registry
            ),
            'audit_trail_entries': Counter(
                'pharma_audit_trail_entries_total',
                'Total audit trail entries',
                registry=self.registry
            )
        }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource utilization"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network statistics
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Update Prometheus metrics
            self.metrics['system_cpu_usage'].set(cpu_percent)
            self.metrics['system_memory_usage'].set(memory_percent)
            self.metrics['system_disk_usage'].set(disk_percent)
            
            status = 'healthy'
            alerts = []
            
            # Check thresholds
            if cpu_percent > self.alert_threshold_cpu:
                status = 'warning'
                alerts.append(f'High CPU usage: {cpu_percent:.1f}%')
            
            if memory_percent > self.alert_threshold_memory:
                status = 'warning'
                alerts.append(f'High memory usage: {memory_percent:.1f}%')
            
            if disk_percent > self.alert_threshold_disk:
                status = 'critical'
                alerts.append(f'High disk usage: {disk_percent:.1f}%')
            
            return {
                'component': 'system_resources',
                'status': status,
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv,
                    'process_count': process_count
                },
                'alerts': alerts,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"System resources check failed: {str(e)}")
            self.metrics['health_check_failures'].labels(component='system_resources').inc()
            return {
                'component': 'system_resources',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def check_application_health(self) -> Dict[str, Any]:
        """Check pharmaceutical application health"""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check main health endpoint
                response = await client.get(f'http://{self.app_host}:{self.app_port}/api/v1/health/live')
                response_time = time.time() - start_time
                
                # Update metrics
                self.metrics['application_response_time'].set(response_time)
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    status = 'healthy'
                    alerts = []
                    
                    # Check response time threshold
                    if response_time > 5.0:
                        status = 'warning'
                        alerts.append(f'Slow response time: {response_time:.2f}s')
                    
                    return {
                        'component': 'application',
                        'status': status,
                        'metrics': {
                            'response_time': response_time,
                            'status_code': response.status_code
                        },
                        'alerts': alerts,
                        'data': health_data,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                else:
                    raise Exception(f'Health check failed with status {response.status_code}')
            
        except Exception as e:
            logger.error(f"Application health check failed: {str(e)}")
            self.metrics['health_check_failures'].labels(component='application').inc()
            return {
                'component': 'application',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance"""
        try:
            db_url = f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'
            
            conn = await asyncpg.connect(db_url)
            
            # Check basic connectivity
            await conn.execute('SELECT 1')
            
            # Check active connections
            active_connections = await conn.fetchval(
                'SELECT count(*) FROM pg_stat_activity WHERE state = $1', 'active'
            )
            
            await conn.close()
            
            # Update metrics
            self.metrics['database_connections'].set(active_connections)
            
            status = 'healthy'
            alerts = []
            
            # Check connection threshold
            if active_connections > 80:
                status = 'warning'
                alerts.append(f'High database connections: {active_connections}')
            
            return {
                'component': 'database',
                'status': status,
                'metrics': {
                    'active_connections': active_connections
                },
                'alerts': alerts,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            self.metrics['health_check_failures'].labels(component='database').inc()
            return {
                'component': 'database',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and compile overall status"""
        logger.info("Running pharmaceutical manufacturing health checks...")
        
        # Run all health checks concurrently
        checks = await asyncio.gather(
            self.check_system_resources(),
            self.check_application_health(),
            self.check_database_health(),
            return_exceptions=True
        )
        
        # Compile results
        components = {}
        overall_status = 'healthy'
        all_alerts = []
        
        for check in checks:
            if isinstance(check, Exception):
                logger.error(f"Health check failed with exception: {str(check)}")
                continue
                
            component_name = check['component']
            components[component_name] = check
            
            # Determine overall status
            if check['status'] == 'error' or check['status'] == 'critical':
                overall_status = 'critical'
            elif check['status'] == 'warning' and overall_status != 'critical':
                overall_status = 'warning'
            
            # Collect alerts
            all_alerts.extend(check.get('alerts', []))
        
        # Update health status
        self.health_status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': overall_status,
            'components': components,
            'alerts': all_alerts,
            'summary': {
                'total_components': len(components),
                'healthy_components': len([c for c in components.values() if c['status'] == 'healthy']),
                'warning_components': len([c for c in components.values() if c['status'] == 'warning']),
                'critical_components': len([c for c in components.values() if c['status'] in ['error', 'critical']])
            }
        }
        
        return self.health_status
    
    async def save_health_report(self, health_data: Dict[str, Any]):
        """Save health report to file"""
        try:
            reports_dir = Path('/tmp/health-reports')
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = reports_dir / f'health_report_{timestamp}.json'
            
            with open(report_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            
            logger.info(f"Health report saved: {report_file}")
                    
        except Exception as e:
            logger.error(f"Failed to save health report: {str(e)}")
    
    async def run_monitoring_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting pharmaceutical health monitoring (interval: {self.check_interval}s)")
        
        # Start Prometheus metrics server
        try:
            start_http_server(9091, registry=self.registry)
            logger.info("Prometheus metrics server started on port 9091")
        except Exception as e:
            logger.warning(f"Could not start Prometheus server: {str(e)}")
        
        while True:
            try:
                # Run health checks
                health_data = await self.run_health_checks()
                
                # Save report
                await self.save_health_report(health_data)
                
                # Log summary
                summary = health_data['summary']
                logger.info(
                    f"Health Check Summary - Overall: {health_data['overall_status'].upper()} | "
                    f"Healthy: {summary['healthy_components']}/{summary['total_components']} | "
                    f"Warnings: {summary['warning_components']} | "
                    f"Critical: {summary['critical_components']} | "
                    f"Alerts: {len(health_data['alerts'])}"
                )
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

async def main():
    """Main function"""
    monitor = PharmaHealthMonitor()
    await monitor.run_monitoring_loop()

if __name__ == "__main__":
    asyncio.run(main())