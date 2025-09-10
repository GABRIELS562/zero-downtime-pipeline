"""
Audit Service
Service layer for FDA-compliant audit logging
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
import logging
import json

logger = logging.getLogger(__name__)

class AuditService:
    """Service for managing audit trails"""
    
    def __init__(self):
        """Initialize audit service"""
        self.audit_logs = []
        logger.info("AuditService initialized")
    
    async def log_event(self, 
                       event_type: str,
                       user_id: str,
                       action: str,
                       entity_type: str,
                       entity_id: str,
                       details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Log an audit event"""
        audit_entry = {
            "id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "ip_address": "127.0.0.1",  # Would get from request context
            "user_agent": "API Client"   # Would get from request headers
        }
        
        self.audit_logs.append(audit_entry)
        logger.info(f"Audit event logged: {event_type} - {action} on {entity_type}:{entity_id}")
        return audit_entry
    
    async def get_audit_logs(self, 
                            entity_type: Optional[str] = None,
                            entity_id: Optional[str] = None,
                            user_id: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with optional filters"""
        logs = self.audit_logs
        
        if entity_type:
            logs = [l for l in logs if l.get("entity_type") == entity_type]
        
        if entity_id:
            logs = [l for l in logs if l.get("entity_id") == entity_id]
        
        if user_id:
            logs = [l for l in logs if l.get("user_id") == user_id]
        
        # Return most recent first
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    async def log_batch_event(self, batch_id: str, action: str, user_id: str, details: Optional[Dict[str, Any]] = None):
        """Log batch-specific audit event"""
        return await self.log_event(
            event_type="BATCH_OPERATION",
            user_id=user_id,
            action=action,
            entity_type="Batch",
            entity_id=batch_id,
            details=details
        )
    
    async def log_compliance_event(self, event_type: str, details: Dict[str, Any]):
        """Log compliance-related event"""
        return await self.log_event(
            event_type="COMPLIANCE",
            user_id="system",
            action=event_type,
            entity_type="System",
            entity_id="compliance",
            details=details
        )
    
    async def export_audit_trail(self, start_date: datetime, end_date: datetime) -> str:
        """Export audit trail for specified date range"""
        logs = []
        for log in self.audit_logs:
            log_date = datetime.fromisoformat(log["timestamp"])
            if start_date <= log_date <= end_date:
                logs.append(log)
        
        return json.dumps(logs, indent=2)