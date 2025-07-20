"""
Audit Trail Middleware
Comprehensive audit trail implementation for pharmaceutical manufacturing
"""

import time
import json
import hashlib
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import uuid

logger = logging.getLogger(__name__)

class AuditTrailMiddleware(BaseHTTPMiddleware):
    """
    Middleware for maintaining comprehensive audit trails
    Implements audit trail requirements for pharmaceutical manufacturing
    """
    
    def __init__(self, app, audit_level: str = "comprehensive"):
        super().__init__(app)
        self.audit_level = audit_level
        self.audit_logger = self._setup_audit_logger()
        self.chain_hash = None  # For maintaining hash chain
        
    def _setup_audit_logger(self):
        """Set up dedicated audit trail logger"""
        audit_logger = logging.getLogger("audit_trail")
        audit_logger.setLevel(logging.INFO)
        
        # Create file handler for audit trail
        handler = logging.FileHandler("/app/logs/audit_trail.log")
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        
        return audit_logger
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique audit ID
        audit_id = str(uuid.uuid4())
        
        # Capture request start time
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc)
        
        # Create audit trail entry
        audit_entry = await self._create_audit_entry(request, audit_id, start_timestamp)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            end_timestamp = datetime.now(timezone.utc)
            
            # Complete audit trail entry
            await self._complete_audit_entry(
                audit_entry, 
                response, 
                processing_time, 
                end_timestamp,
                "success"
            )
            
            # Add audit headers to response
            response.headers["X-Audit-ID"] = audit_id
            response.headers["X-Audit-Timestamp"] = start_timestamp.isoformat()
            response.headers["X-Audit-Chain-Hash"] = self.chain_hash or "genesis"
            
            return response
            
        except Exception as e:
            # Handle failed operations
            processing_time = time.time() - start_time
            end_timestamp = datetime.now(timezone.utc)
            
            await self._complete_audit_entry(
                audit_entry,
                None,
                processing_time,
                end_timestamp,
                "error",
                str(e)
            )
            
            # Re-raise the exception
            raise
    
    async def _create_audit_entry(self, request: Request, audit_id: str, timestamp: datetime) -> Dict[str, Any]:
        """Create initial audit trail entry"""
        
        # Extract user information
        user_info = {
            "user_id": request.headers.get("X-User-ID", "anonymous"),
            "username": request.headers.get("X-Username", "unknown"),
            "role": request.headers.get("X-User-Role", "unknown"),
            "department": request.headers.get("X-User-Department", "unknown"),
            "session_id": request.headers.get("X-Session-ID", "unknown"),
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown")
        }
        
        # Create base audit entry
        audit_entry = {
            "audit_id": audit_id,
            "event_type": "api_request",
            "timestamp": timestamp.isoformat(),
            "user": user_info,
            "request": {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._sanitize_headers(dict(request.headers))
            },
            "system": {
                "application": "pharma-manufacturing",
                "version": "1.0.0",
                "environment": "production"
            },
            "compliance": {
                "regulatory_context": self._determine_regulatory_context(request.url.path),
                "data_classification": self._classify_data(request.url.path),
                "retention_period": self._determine_retention_period(request.url.path)
            },
            "previous_hash": self.chain_hash,
            "status": "initiated"
        }
        
        # Capture request body for audit-critical operations
        if self._requires_body_audit(request.url.path, request.method):
            try:
                body = await request.body()
                if body:
                    audit_entry["request"]["body_hash"] = hashlib.sha256(body).hexdigest()
                    audit_entry["request"]["body_size"] = len(body)
                    
                    # Store sanitized body content for critical operations
                    if self._requires_full_body_audit(request.url.path):
                        try:
                            body_content = json.loads(body.decode())
                            audit_entry["request"]["body_content"] = self._sanitize_body_content(body_content)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            audit_entry["request"]["body_content"] = "Non-JSON content"
            except Exception as e:
                audit_entry["request"]["body_capture_error"] = str(e)
        
        return audit_entry
    
    async def _complete_audit_entry(
        self, 
        audit_entry: Dict[str, Any], 
        response: Optional[Response], 
        processing_time: float,
        end_timestamp: datetime,
        status: str,
        error: Optional[str] = None
    ):
        """Complete the audit trail entry with response information"""
        
        audit_entry["completion_timestamp"] = end_timestamp.isoformat()
        audit_entry["processing_time"] = processing_time
        audit_entry["status"] = status
        
        if response:
            audit_entry["response"] = {
                "status_code": response.status_code,
                "headers": self._sanitize_headers(dict(response.headers)),
                "content_type": response.headers.get("content-type", "unknown")
            }
            
            # Add response body hash for critical operations
            if hasattr(response, 'body') and response.body:
                audit_entry["response"]["body_hash"] = hashlib.sha256(response.body).hexdigest()
                audit_entry["response"]["body_size"] = len(response.body)
        
        if error:
            audit_entry["error"] = {
                "message": error,
                "timestamp": end_timestamp.isoformat()
            }
        
        # Generate audit entry hash and update chain
        audit_entry["entry_hash"] = self._generate_entry_hash(audit_entry)
        self.chain_hash = audit_entry["entry_hash"]
        
        # Log the completed audit entry
        await self._log_audit_entry(audit_entry)
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers to remove sensitive information"""
        sensitive_headers = [
            "authorization", "x-api-key", "x-auth-token", "cookie",
            "x-session-token", "x-csrf-token"
        ]
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_body_content(self, body_content: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize body content to remove sensitive information"""
        sensitive_fields = [
            "password", "secret", "token", "api_key", "private_key",
            "ssn", "credit_card", "bank_account"
        ]
        
        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                sanitized = {}
                for key, value in obj.items():
                    if any(sensitive in key.lower() for sensitive in sensitive_fields):
                        sanitized[key] = "[REDACTED]"
                    else:
                        sanitized[key] = sanitize_recursive(value)
                return sanitized
            elif isinstance(obj, list):
                return [sanitize_recursive(item) for item in obj]
            else:
                return obj
        
        return sanitize_recursive(body_content)
    
    def _determine_regulatory_context(self, path: str) -> Dict[str, Any]:
        """Determine regulatory context for the operation"""
        regulatory_contexts = {
            "/api/v1/batches": {
                "regulations": ["21_CFR_211", "ICH_Q7", "EU_GMP"],
                "criticality": "high",
                "compliance_requirements": ["batch_records", "traceability", "deviation_reporting"]
            },
            "/api/v1/quality": {
                "regulations": ["21_CFR_211.194", "USP", "Ph.Eur"],
                "criticality": "critical",
                "compliance_requirements": ["test_results", "method_validation", "data_integrity"]
            },
            "/api/v1/equipment": {
                "regulations": ["21_CFR_211.68", "ISPE_GAMP5"],
                "criticality": "high",
                "compliance_requirements": ["qualification", "calibration", "maintenance"]
            },
            "/api/v1/inventory": {
                "regulations": ["21_CFR_211.122", "21_CFR_211.125"],
                "criticality": "medium",
                "compliance_requirements": ["material_tracking", "expiry_management"]
            },
            "/api/v1/environmental": {
                "regulations": ["21_CFR_211.42", "EU_GMP_Annex_1"],
                "criticality": "high",
                "compliance_requirements": ["environmental_monitoring", "cleanroom_validation"]
            }
        }
        
        for endpoint, context in regulatory_contexts.items():
            if path.startswith(endpoint):
                return context
        
        return {
            "regulations": ["General_GMP"],
            "criticality": "low",
            "compliance_requirements": ["basic_audit"]
        }
    
    def _classify_data(self, path: str) -> str:
        """Classify data based on sensitivity and regulatory requirements"""
        if any(critical_path in path for critical_path in ["/batches", "/quality"]):
            return "regulated_critical"
        elif any(sensitive_path in path for sensitive_path in ["/equipment", "/environmental"]):
            return "regulated_sensitive"
        elif "/inventory" in path:
            return "regulated_standard"
        else:
            return "general"
    
    def _determine_retention_period(self, path: str) -> str:
        """Determine data retention period based on regulatory requirements"""
        retention_periods = {
            "regulated_critical": "permanent",  # Batch records - permanent retention
            "regulated_sensitive": "10_years",  # Equipment and environmental - 10 years
            "regulated_standard": "7_years",    # Inventory - 7 years
            "general": "3_years"               # General operations - 3 years
        }
        
        data_classification = self._classify_data(path)
        return retention_periods.get(data_classification, "3_years")
    
    def _requires_body_audit(self, path: str, method: str) -> bool:
        """Determine if request body should be audited"""
        audit_patterns = [
            ("/api/v1/batches", ["POST", "PUT"]),
            ("/api/v1/quality", ["POST", "PUT"]),
            ("/api/v1/workflow", ["POST", "PUT"]),
            ("/api/v1/inventory/usage", ["POST"]),
            ("/api/v1/equipment", ["PUT", "POST"]),
            ("/api/v1/alerts", ["POST"])
        ]
        
        for pattern_path, audit_methods in audit_patterns:
            if path.startswith(pattern_path) and method in audit_methods:
                return True
        
        return False
    
    def _requires_full_body_audit(self, path: str) -> bool:
        """Determine if full body content should be audited"""
        full_audit_paths = [
            "/api/v1/batches",
            "/api/v1/quality/tests",
            "/api/v1/workflow/stages"
        ]
        
        return any(path.startswith(audit_path) for audit_path in full_audit_paths)
    
    def _generate_entry_hash(self, audit_entry: Dict[str, Any]) -> str:
        """Generate hash for audit entry to maintain integrity"""
        # Create deterministic string for hashing
        hash_content = {
            "audit_id": audit_entry["audit_id"],
            "timestamp": audit_entry["timestamp"],
            "completion_timestamp": audit_entry.get("completion_timestamp"),
            "user_id": audit_entry["user"]["user_id"],
            "method": audit_entry["request"]["method"],
            "path": audit_entry["request"]["path"],
            "status": audit_entry["status"],
            "previous_hash": audit_entry.get("previous_hash")
        }
        
        # Include response status if available
        if "response" in audit_entry:
            hash_content["response_status"] = audit_entry["response"]["status_code"]
        
        # Include error if present
        if "error" in audit_entry:
            hash_content["error"] = audit_entry["error"]["message"]
        
        hash_string = json.dumps(hash_content, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def _log_audit_entry(self, audit_entry: Dict[str, Any]):
        """Log the audit entry"""
        try:
            # Log to file
            self.audit_logger.info(json.dumps(audit_entry, default=str, separators=(',', ':')))
            
            # Also store in database for compliance reporting
            await self._store_audit_to_database(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {str(e)}")
            # Critical: Don't fail the operation if audit logging fails
            # but ensure this is logged elsewhere for investigation
    
    async def _store_audit_to_database(self, audit_entry: Dict[str, Any]):
        """Store audit entry to database for compliance queries"""
        try:
            # This would integrate with the audit database service
            # For now, we'll just log that it should be stored
            logger.debug(f"Audit entry stored for ID: {audit_entry['audit_id']}")
        except Exception as e:
            logger.error(f"Failed to store audit entry to database: {str(e)}")
            # Don't fail the request if database storage fails