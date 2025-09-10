"""
Alert Manager Service
Handles alert generation, routing, and notifications for pharmaceutical manufacturing
"""

import logging
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Alert types for pharmaceutical manufacturing"""
    EQUIPMENT_FAILURE = "equipment_failure"
    TEMPERATURE_DEVIATION = "temperature_deviation"
    BATCH_QUALITY = "batch_quality"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ERROR = "system_error"

class Alert:
    """Alert data structure"""
    def __init__(self, alert_type: AlertType, severity: AlertSeverity, message: str, 
                 source: str = None, metadata: Dict = None):
        self.id = f"alert_{int(datetime.now().timestamp() * 1000)}"
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.source = source or "system"
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)
        self.acknowledged = False
        self.resolved = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved
        }

class AlertManager:
    """Manages alerts for pharmaceutical manufacturing system"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        self.initialized = False
    
    async def initialize(self):
        """Initialize alert manager"""
        try:
            logger.info("Initializing Alert Manager")
            
            # Set up default alert handlers
            self.add_handler(self._log_alert)
            
            # Start background cleanup task
            asyncio.create_task(self._cleanup_task())
            
            self.initialized = True
            logger.info("Alert Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Alert Manager: {e}")
            self.initialized = False
    
    def add_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler"""
        self.alert_handlers.append(handler)
    
    async def create_alert(self, alert_type: AlertType, severity: AlertSeverity, 
                          message: str, source: str = None, metadata: Dict = None) -> str:
        """Create and process new alert"""
        try:
            alert = Alert(alert_type, severity, message, source, metadata)
            
            # Store active alert
            self.active_alerts[alert.id] = alert
            
            # Add to history
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history:
                self.alert_history.pop(0)
            
            # Process through handlers
            for handler in self.alert_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
            
            logger.info(f"Alert created: {alert.id} - {alert.severity.value} - {alert.message}")
            return alert.id
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None
    
    async def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.active_alerts[alert_id].metadata["acknowledged_by"] = user
            self.active_alerts[alert_id].metadata["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False
    
    async def resolve_alert(self, alert_id: str, user: str = "system") -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.metadata["resolved_by"] = user
            alert.metadata["resolved_at"] = datetime.now(timezone.utc).isoformat()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved by {user}")
            return True
        return False
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[dict]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return [alert.to_dict() for alert in alerts]
    
    def get_alert_history(self, limit: int = 100) -> List[dict]:
        """Get alert history"""
        recent_alerts = self.alert_history[-limit:]
        return [alert.to_dict() for alert in recent_alerts]
    
    async def _log_alert(self, alert: Alert):
        """Default alert handler - logs to system log"""
        level_map = {
            AlertSeverity.LOW: logging.INFO,
            AlertSeverity.MEDIUM: logging.WARNING,
            AlertSeverity.HIGH: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }
        
        logger.log(
            level_map.get(alert.severity, logging.INFO),
            f"ALERT [{alert.severity.value.upper()}] {alert.alert_type.value}: {alert.message} (Source: {alert.source})"
        )
    
    async def _cleanup_task(self):
        """Background task to clean up old resolved alerts"""
        while True:
            try:
                # Clean up resolved alerts older than 24 hours
                cutoff = datetime.now(timezone.utc).timestamp() - (24 * 3600)
                
                # This is a simple implementation - in production you'd want database persistence
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Alert cleanup task error: {e}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """Shutdown alert manager"""
        logger.info("Shutting down Alert Manager")
        # In a real implementation, you'd persist active alerts to database
        self.initialized = False
    
    async def health_check(self) -> dict:
        """Check alert manager health"""
        if not self.initialized:
            return {"status": "unhealthy", "error": "Not initialized"}
        
        return {
            "status": "healthy",
            "active_alerts_count": len(self.active_alerts),
            "critical_alerts": len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL]),
            "handlers_count": len(self.alert_handlers)
        }