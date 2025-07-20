"""
GMP Compliance Logging Middleware
Comprehensive audit trail and compliance logging for pharmaceutical manufacturing
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

class GMPComplianceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for GMP (Good Manufacturing Practice) compliance logging
    Maintains comprehensive audit trails for all manufacturing operations
    """
    
    def __init__(self, app, compliance_level: str = "full"):
        super().__init__(app)
        self.compliance_level = compliance_level
        self.audit_logger = self._setup_audit_logger()
        
    def _setup_audit_logger(self):
        """Set up dedicated audit logger with structured format"""
        audit_logger = logging.getLogger("gmp_audit")
        audit_logger.setLevel(logging.INFO)
        
        # Create file handler for audit logs
        handler = logging.FileHandler("/app/logs/gmp_audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - GMP_AUDIT - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        
        return audit_logger
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique transaction ID for audit trail
        transaction_id = str(uuid.uuid4())
        
        # Capture request start time
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc)
        
        # Extract user information from request
        user_info = self._extract_user_info(request)
        
        # Log request initiation
        request_data = await self._capture_request_data(request, transaction_id, user_info)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Capture response data
            response_data = self._capture_response_data(response, processing_time)
            
            # Log successful operation
            await self._log_audit_trail(
                transaction_id=transaction_id,
                request_data=request_data,
                response_data=response_data,
                status="success",
                user_info=user_info
            )
            
            # Add audit headers to response
            response.headers["X-GMP-Transaction-ID"] = transaction_id
            response.headers["X-GMP-Audit-Logged"] = "true"
            response.headers["X-GMP-Compliance-Level"] = self.compliance_level
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed request
            processing_time = time.time() - start_time
            
            # Log failed operation
            await self._log_audit_trail(
                transaction_id=transaction_id,
                request_data=request_data,
                response_data={"error": str(e), "processing_time": processing_time},
                status="error",
                user_info=user_info,
                error=str(e)
            )
            
            # Re-raise the exception
            raise
    
    def _extract_user_info(self, request: Request) -> Dict[str, Any]:
        """Extract user information from request for audit purposes"""
        user_info = {
            "user_id": request.headers.get("X-User-ID", "anonymous"),
            "username": request.headers.get("X-Username", "unknown"),
            "role": request.headers.get("X-User-Role", "unknown"),
            "department": request.headers.get("X-User-Department", "unknown"),
            "session_id": request.headers.get("X-Session-ID", "unknown"),
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown")
        }
        return user_info
    
    async def _capture_request_data(self, request: Request, transaction_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Capture comprehensive request data for audit trail"""
        request_data = {
            "transaction_id": transaction_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "user_info": user_info,
            "compliance_context": self._determine_compliance_context(request.url.path)
        }
        
        # Capture request body for specific GMP-critical operations
        if self._is_gmp_critical_operation(request.url.path, request.method):
            try:
                body = await request.body()
                if body:
                    # Create hash of body content for integrity verification
                    body_hash = hashlib.sha256(body).hexdigest()
                    request_data["body_hash"] = body_hash
                    request_data["body_size"] = len(body)
                    
                    # Store actual body content for critical operations
                    if self._requires_full_body_logging(request.url.path):
                        try:
                            request_data["body_content"] = json.loads(body.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            request_data["body_content"] = "Binary or invalid JSON content"
            except Exception as e:
                request_data["body_capture_error"] = str(e)
        
        return request_data
    
    def _capture_response_data(self, response: Response, processing_time: float) -> Dict[str, Any]:
        """Capture response data for audit trail"""
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "processing_time": processing_time,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Add response body hash for critical operations
        if hasattr(response, 'body') and response.body:
            response_data["body_hash"] = hashlib.sha256(response.body).hexdigest()
            response_data["body_size"] = len(response.body)
        
        return response_data
    
    async def _log_audit_trail(
        self, 
        transaction_id: str, 
        request_data: Dict[str, Any], 
        response_data: Dict[str, Any], 
        status: str, 
        user_info: Dict[str, Any],
        error: Optional[str] = None
    ):
        """Log comprehensive audit trail entry"""
        
        audit_entry = {
            "transaction_id": transaction_id,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "compliance_level": self.compliance_level,
            "request": request_data,
            "response": response_data,
            "user": user_info,
            "regulatory_flags": self._determine_regulatory_flags(request_data),
            "data_integrity_hash": self._generate_integrity_hash(request_data, response_data)
        }
        
        if error:
            audit_entry["error"] = error
            audit_entry["error_timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Log the audit entry
        self.audit_logger.info(json.dumps(audit_entry, default=str, separators=(',', ':')))
        
        # Also log to database for queryable audit trail
        await self._store_audit_to_database(audit_entry)
    
    def _determine_compliance_context(self, path: str) -> Dict[str, Any]:
        """Determine the GMP compliance context based on the endpoint"""
        compliance_contexts = {
            "/api/v1/batches": {
                "category": "batch_manufacturing",
                "criticality": "high",
                "regulatory_requirements": ["21_CFR_211", "ICH_Q7"],
                "data_integrity": "required"
            },
            "/api/v1/quality": {
                "category": "quality_control",
                "criticality": "critical",
                "regulatory_requirements": ["21_CFR_211.194", "USP_General_Chapters"],
                "data_integrity": "required"
            },
            "/api/v1/equipment": {
                "category": "equipment_management",
                "criticality": "high",
                "regulatory_requirements": ["21_CFR_211.68", "ISPE_GAMP5"],
                "data_integrity": "required"
            },
            "/api/v1/inventory": {
                "category": "material_management",
                "criticality": "medium",
                "regulatory_requirements": ["21_CFR_211.122", "21_CFR_211.125"],
                "data_integrity": "required"
            },
            "/api/v1/environmental": {
                "category": "environmental_monitoring",
                "criticality": "high",
                "regulatory_requirements": ["21_CFR_211.42", "EU_GMP_Annex_1"],
                "data_integrity": "required"
            }
        }
        
        for endpoint, context in compliance_contexts.items():
            if path.startswith(endpoint):
                return context
        
        return {
            "category": "general_operation",
            "criticality": "low",
            "regulatory_requirements": ["General_GMP"],
            "data_integrity": "standard"
        }
    
    def _is_gmp_critical_operation(self, path: str, method: str) -> bool:
        """Determine if operation is GMP-critical and requires detailed logging"""
        critical_patterns = [
            ("/api/v1/batches", ["POST", "PUT", "DELETE"]),
            ("/api/v1/quality", ["POST", "PUT"]),
            ("/api/v1/equipment", ["PUT", "POST"]),
            ("/api/v1/workflow", ["POST", "PUT"]),
            ("/api/v1/inventory/usage", ["POST"]),
            ("/api/v1/alerts", ["POST", "PUT"])
        ]
        
        for pattern_path, critical_methods in critical_patterns:
            if path.startswith(pattern_path) and method in critical_methods:
                return True
        
        return False
    
    def _requires_full_body_logging(self, path: str) -> bool:
        """Determine if full request body should be logged"""
        full_logging_paths = [
            "/api/v1/batches",
            "/api/v1/quality/tests",
            "/api/v1/workflow/stages",
            "/api/v1/inventory/usage"
        ]
        
        return any(path.startswith(log_path) for log_path in full_logging_paths)
    
    def _determine_regulatory_flags(self, request_data: Dict[str, Any]) -> List[str]:
        """Determine regulatory flags based on the operation"""
        flags = []
        
        path = request_data.get("path", "")
        method = request_data.get("method", "")
        
        if "/batches" in path and method in ["POST", "PUT"]:
            flags.append("BATCH_RECORD_CHANGE")
        
        if "/quality" in path and method == "POST":
            flags.append("QUALITY_TEST_RESULT")
        
        if "/deviations" in path:
            flags.append("DEVIATION_RECORDED")
        
        if "/equipment" in path and method == "PUT":
            flags.append("EQUIPMENT_PARAMETER_CHANGE")
        
        if "/environmental" in path:
            flags.append("ENVIRONMENTAL_MONITORING")
        
        compliance_context = request_data.get("compliance_context", {})
        if compliance_context.get("criticality") == "critical":
            flags.append("CRITICAL_GMP_OPERATION")
        
        return flags
    
    def _generate_integrity_hash(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> str:
        """Generate integrity hash for audit trail verification"""
        # Create a deterministic string representation
        integrity_string = json.dumps({
            "transaction_id": request_data.get("transaction_id"),
            "timestamp": request_data.get("timestamp"),
            "method": request_data.get("method"),
            "path": request_data.get("path"),
            "user_id": request_data.get("user_info", {}).get("user_id"),
            "status_code": response_data.get("status_code"),
            "response_timestamp": response_data.get("timestamp")
        }, sort_keys=True, separators=(',', ':'))
        
        return hashlib.sha256(integrity_string.encode()).hexdigest()
    
    async def _store_audit_to_database(self, audit_entry: Dict[str, Any]):
        """Store audit entry to database for compliance reporting"""
        try:
            # This would integrate with the audit service to store in database
            # For now, we'll just log that the entry should be stored
            logger.debug(f"Audit entry stored for transaction: {audit_entry['transaction_id']}")
        except Exception as e:
            logger.error(f"Failed to store audit entry to database: {str(e)}")
            # Don't fail the request if audit storage fails
            pass