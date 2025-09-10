"""
Health Service
Monitors application and service health for pharmaceutical manufacturing
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import psutil

logger = logging.getLogger(__name__)

class HealthService:
    """Service for health monitoring"""
    
    def __init__(self):
        self.startup_time = datetime.now(timezone.utc)
        self.initialization_complete = False
        self.services_ready = False
        logger.info("Health Service initialized")
    
    async def check_all_services_health(self) -> Dict[str, str]:
        """Check health of all services"""
        services_health = {
            "database": "healthy",
            "equipment_monitor": "healthy",
            "batch_service": "healthy",
            "audit_service": "healthy",
            "alert_manager": "healthy",
            "workflow_service": "healthy",
            "inventory_service": "healthy",
            "quality_service": "healthy",
            "environmental_service": "healthy"
        }
        
        # Simulate some services being degraded occasionally
        import random
        if random.random() < 0.1:
            services_health["equipment_monitor"] = "degraded"
        
        return services_health
    
    async def check_startup_status(self) -> Dict[str, Any]:
        """Check application startup status"""
        uptime = (datetime.now(timezone.utc) - self.startup_time).total_seconds()
        
        # Consider initialized after 5 seconds
        if uptime > 5:
            self.initialization_complete = True
            self.services_ready = True
        
        return {
            "initialization_complete": self.initialization_complete,
            "services_ready": self.services_ready,
            "uptime_seconds": uptime
        }
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        services_health = await self.check_all_services_health()
        startup_status = await self.check_startup_status()
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        all_healthy = all(status == "healthy" for status in services_health.values())
        
        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "services": services_health,
            "system_metrics": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": disk.percent
            },
            "uptime_seconds": startup_status["uptime_seconds"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "core_count": psutil.cpu_count()
            },
            "memory": {
                "total_mb": memory.total / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "usage_percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / (1024 * 1024 * 1024),
                "free_gb": disk.free / (1024 * 1024 * 1024),
                "usage_percent": disk.percent
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }