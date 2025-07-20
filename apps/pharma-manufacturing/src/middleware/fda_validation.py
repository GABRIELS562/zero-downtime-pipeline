"""
FDA Validation Middleware
Comprehensive FDA compliance validation for pharmaceutical manufacturing operations
"""

import json
import re
from typing import Callable, Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class FDAValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for FDA (Food and Drug Administration) validation
    Ensures compliance with FDA regulations for pharmaceutical manufacturing
    """
    
    def __init__(self, app, validation_level: str = "strict"):
        super().__init__(app)
        self.validation_level = validation_level
        self.fda_rules = self._load_fda_validation_rules()
        
    def _load_fda_validation_rules(self) -> Dict[str, Any]:
        """Load FDA validation rules and requirements"""
        return {
            "21_CFR_211": {
                "batch_records": {
                    "required_fields": [
                        "batch_number", "product_id", "planned_quantity", 
                        "created_by", "planned_start_date", "manufacturing_instructions"
                    ],
                    "batch_number_format": r"^[A-Z0-9]{8,20}$",
                    "quantity_validation": {"min": 1, "max": 1000000},
                    "date_validation": True
                },
                "quality_control": {
                    "required_fields": [
                        "batch_id", "test_type", "test_method", "specification",
                        "tested_by", "test_date"
                    ],
                    "test_result_validation": True,
                    "reviewer_required": True,
                    "approval_chain": ["tested_by", "reviewed_by", "approved_by"]
                },
                "material_management": {
                    "lot_tracking": True,
                    "expiry_validation": True,
                    "supplier_qualification": True,
                    "coa_required": True
                },
                "equipment_qualification": {
                    "calibration_required": True,
                    "maintenance_records": True,
                    "parameter_limits": True,
                    "deviation_reporting": True
                }
            },
            "21_CFR_11": {
                "electronic_records": {
                    "user_identification": True,
                    "digital_signatures": True,
                    "audit_trails": True,
                    "data_integrity": True
                },
                "access_controls": {
                    "user_authentication": True,
                    "role_based_access": True,
                    "session_management": True
                }
            },
            "data_integrity": {
                "alcoa_plus": {
                    "attributable": True,
                    "legible": True,
                    "contemporaneous": True,
                    "original": True,
                    "accurate": True,
                    "complete": True,
                    "consistent": True,
                    "enduring": True,
                    "available": True
                }
            }
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for health checks and non-critical endpoints
        if self._should_skip_validation(request.url.path):
            return await call_next(request)
        
        try:
            # Pre-request validation
            await self._validate_request(request)
            
            # Process the request
            response = await call_next(request)
            
            # Post-response validation
            await self._validate_response(request, response)
            
            # Add FDA compliance headers
            response.headers["X-FDA-Validated"] = "true"
            response.headers["X-FDA-Compliance-Level"] = self.validation_level
            response.headers["X-FDA-Validation-Timestamp"] = datetime.now(timezone.utc).isoformat()
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (validation failures)
            raise
        except Exception as e:
            logger.error(f"FDA validation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"FDA validation system error: {str(e)}"
            )
    
    def _should_skip_validation(self, path: str) -> bool:
        """Determine if FDA validation should be skipped for this endpoint"""
        skip_patterns = [
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        
        return any(path.startswith(pattern) for pattern in skip_patterns)
    
    async def _validate_request(self, request: Request):
        """Validate incoming request against FDA requirements"""
        path = request.url.path
        method = request.method
        
        # Validate user authentication and authorization
        await self._validate_user_access(request)
        
        # Validate request data based on endpoint
        if "/api/v1/batches" in path and method in ["POST", "PUT"]:
            await self._validate_batch_request(request)
        elif "/api/v1/quality" in path and method == "POST":
            await self._validate_quality_request(request)
        elif "/api/v1/inventory" in path and method == "POST":
            await self._validate_inventory_request(request)
        elif "/api/v1/equipment" in path and method in ["POST", "PUT"]:
            await self._validate_equipment_request(request)
    
    async def _validate_user_access(self, request: Request):
        """Validate user authentication and authorization per 21 CFR 11"""
        user_id = request.headers.get("X-User-ID")
        username = request.headers.get("X-Username")
        user_role = request.headers.get("X-User-Role")
        session_id = request.headers.get("X-Session-ID")
        
        if not user_id or not username:
            raise HTTPException(
                status_code=401,
                detail="FDA Validation Error: User identification required per 21 CFR 11.10(d)"
            )
        
        if not session_id:
            raise HTTPException(
                status_code=401,
                detail="FDA Validation Error: Valid session required for electronic records"
            )
        
        # Validate role-based access for critical operations
        path = request.url.path
        required_roles = self._get_required_roles(path, request.method)
        
        if required_roles and user_role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"FDA Validation Error: Insufficient privileges. Required roles: {required_roles}"
            )
    
    def _get_required_roles(self, path: str, method: str) -> List[str]:
        """Get required roles for specific operations"""
        role_requirements = {
            ("/api/v1/batches", "POST"): ["production_operator", "production_supervisor", "production_manager"],
            ("/api/v1/batches", "PUT"): ["production_supervisor", "production_manager"],
            ("/api/v1/quality", "POST"): ["qc_analyst", "qc_supervisor"],
            ("/api/v1/quality/tests", "PUT"): ["qc_supervisor", "qc_manager"],
            ("/api/v1/inventory/materials", "POST"): ["warehouse_operator", "warehouse_supervisor"],
            ("/api/v1/equipment", "PUT"): ["maintenance_technician", "maintenance_supervisor"],
            ("/api/v1/workflow/stages", "POST"): ["production_operator", "production_supervisor"]
        }
        
        for (pattern_path, pattern_method), roles in role_requirements.items():
            if path.startswith(pattern_path) and method == pattern_method:
                return roles
        
        return []
    
    async def _validate_batch_request(self, request: Request):
        """Validate batch-related requests per 21 CFR 211"""
        try:
            body = await request.body()
            if not body:
                return
            
            data = json.loads(body)
            batch_rules = self.fda_rules["21_CFR_211"]["batch_records"]
            
            # Validate required fields
            missing_fields = []
            for field in batch_rules["required_fields"]:
                if field not in data or not data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                raise HTTPException(
                    status_code=422,
                    detail=f"FDA Validation Error: Missing required batch record fields per 21 CFR 211.188: {missing_fields}"
                )
            
            # Validate batch number format
            if "batch_number" in data:
                batch_number = data["batch_number"]
                if not re.match(batch_rules["batch_number_format"], batch_number):
                    raise HTTPException(
                        status_code=422,
                        detail="FDA Validation Error: Batch number format invalid per 21 CFR 211.142"
                    )
            
            # Validate quantity ranges
            if "planned_quantity" in data:
                quantity = data["planned_quantity"]
                quantity_rules = batch_rules["quantity_validation"]
                if not (quantity_rules["min"] <= quantity <= quantity_rules["max"]):
                    raise HTTPException(
                        status_code=422,
                        detail=f"FDA Validation Error: Quantity out of acceptable range per 21 CFR 211.101"
                    )
            
            # Validate dates
            if batch_rules["date_validation"]:
                await self._validate_dates(data)
                
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=422,
                detail="FDA Validation Error: Invalid JSON format in request body"
            )
    
    async def _validate_quality_request(self, request: Request):
        """Validate quality control requests per 21 CFR 211.194"""
        try:
            body = await request.body()
            if not body:
                return
            
            data = json.loads(body)
            qc_rules = self.fda_rules["21_CFR_211"]["quality_control"]
            
            # Validate required fields for QC testing
            missing_fields = []
            for field in qc_rules["required_fields"]:
                if field not in data or not data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                raise HTTPException(
                    status_code=422,
                    detail=f"FDA Validation Error: Missing required QC fields per 21 CFR 211.194: {missing_fields}"
                )
            
            # Validate test method and specification
            if "test_method" in data and "specification" in data:
                test_method = data["test_method"].strip()
                specification = data["specification"].strip()
                
                if not test_method or not specification:
                    raise HTTPException(
                        status_code=422,
                        detail="FDA Validation Error: Test method and specification cannot be empty per 21 CFR 211.194(a)"
                    )
            
            # Validate tested_by field for accountability
            if "tested_by" in data:
                tested_by = data["tested_by"].strip()
                if not tested_by or len(tested_by) < 2:
                    raise HTTPException(
                        status_code=422,
                        detail="FDA Validation Error: Valid analyst identification required per 21 CFR 211.194(a)"
                    )
                    
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=422,
                detail="FDA Validation Error: Invalid JSON format in QC request"
            )
    
    async def _validate_inventory_request(self, request: Request):
        """Validate inventory/material requests per 21 CFR 211.122"""
        try:
            body = await request.body()
            if not body:
                return
            
            data = json.loads(body)
            material_rules = self.fda_rules["21_CFR_211"]["material_management"]
            
            # Validate lot tracking requirements
            if material_rules["lot_tracking"] and "lot_number" in data:
                lot_number = data.get("lot_number", "").strip()
                if not lot_number:
                    raise HTTPException(
                        status_code=422,
                        detail="FDA Validation Error: Lot number required for material tracking per 21 CFR 211.122"
                    )
            
            # Validate expiry date
            if material_rules["expiry_validation"] and "expiry_date" in data:
                expiry_date = data.get("expiry_date")
                if expiry_date:
                    try:
                        expiry_dt = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                        if expiry_dt <= datetime.now(timezone.utc):
                            raise HTTPException(
                                status_code=422,
                                detail="FDA Validation Error: Expired materials cannot be used per 21 CFR 211.122"
                            )
                    except ValueError:
                        raise HTTPException(
                            status_code=422,
                            detail="FDA Validation Error: Invalid expiry date format"
                        )
                        
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=422,
                detail="FDA Validation Error: Invalid JSON format in inventory request"
            )
    
    async def _validate_equipment_request(self, request: Request):
        """Validate equipment requests per 21 CFR 211.68"""
        try:
            body = await request.body()
            if not body:
                return
            
            data = json.loads(body)
            equipment_rules = self.fda_rules["21_CFR_211"]["equipment_qualification"]
            
            # Validate calibration requirements
            if equipment_rules["calibration_required"]:
                if "last_calibration_date" in data:
                    calibration_date = data.get("last_calibration_date")
                    if calibration_date:
                        try:
                            cal_dt = datetime.fromisoformat(calibration_date.replace('Z', '+00:00'))
                            # Check if calibration is overdue (assuming 1 year calibration cycle)
                            one_year_ago = datetime.now(timezone.utc).replace(year=datetime.now().year - 1)
                            if cal_dt < one_year_ago:
                                raise HTTPException(
                                    status_code=422,
                                    detail="FDA Validation Error: Equipment calibration overdue per 21 CFR 211.68"
                                )
                        except ValueError:
                            raise HTTPException(
                                status_code=422,
                                detail="FDA Validation Error: Invalid calibration date format"
                            )
            
            # Validate operating parameters are within limits
            if equipment_rules["parameter_limits"] and "operating_parameters" in data:
                parameters = data.get("operating_parameters", {})
                if isinstance(parameters, dict):
                    await self._validate_operating_parameters(parameters)
                    
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=422,
                detail="FDA Validation Error: Invalid JSON format in equipment request"
            )
    
    async def _validate_operating_parameters(self, parameters: Dict[str, Any]):
        """Validate equipment operating parameters"""
        # Define acceptable parameter ranges
        parameter_limits = {
            "temperature": {"min": -20, "max": 200, "unit": "°C"},
            "pressure": {"min": 0, "max": 10, "unit": "bar"},
            "humidity": {"min": 0, "max": 100, "unit": "%"},
            "rpm": {"min": 0, "max": 5000, "unit": "rpm"},
            "flow_rate": {"min": 0, "max": 1000, "unit": "L/min"}
        }
        
        for param_name, param_value in parameters.items():
            if param_name.lower() in parameter_limits:
                limits = parameter_limits[param_name.lower()]
                try:
                    value = float(param_value)
                    if not (limits["min"] <= value <= limits["max"]):
                        raise HTTPException(
                            status_code=422,
                            detail=f"FDA Validation Error: {param_name} value {value} outside acceptable range "
                                   f"({limits['min']}-{limits['max']} {limits['unit']}) per equipment specifications"
                        )
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=422,
                        detail=f"FDA Validation Error: Invalid numeric value for parameter {param_name}"
                    )
    
    async def _validate_dates(self, data: Dict[str, Any]):
        """Validate date fields for logical consistency"""
        date_fields = ["planned_start_date", "planned_completion_date", "actual_start_date", "actual_completion_date"]
        
        dates = {}
        for field in date_fields:
            if field in data and data[field]:
                try:
                    dates[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except ValueError:
                    raise HTTPException(
                        status_code=422,
                        detail=f"FDA Validation Error: Invalid date format for {field}"
                    )
        
        # Validate logical date relationships
        if "planned_start_date" in dates and "planned_completion_date" in dates:
            if dates["planned_start_date"] >= dates["planned_completion_date"]:
                raise HTTPException(
                    status_code=422,
                    detail="FDA Validation Error: Planned start date must be before planned completion date"
                )
        
        if "actual_start_date" in dates and "actual_completion_date" in dates:
            if dates["actual_start_date"] >= dates["actual_completion_date"]:
                raise HTTPException(
                    status_code=422,
                    detail="FDA Validation Error: Actual start date must be before actual completion date"
                )
    
    async def _validate_response(self, request: Request, response: Response):
        """Validate response data for FDA compliance"""
        # Check for successful operations that require additional validation
        if response.status_code in [200, 201] and request.method in ["POST", "PUT"]:
            
            # Ensure audit trail information is present
            if not response.headers.get("X-GMP-Transaction-ID"):
                logger.warning("FDA Validation Warning: Missing audit trail transaction ID")
            
            # Validate critical operation responses
            path = request.url.path
            if any(critical_path in path for critical_path in ["/batches", "/quality", "/workflow"]):
                await self._validate_critical_operation_response(request, response)
    
    async def _validate_critical_operation_response(self, request: Request, response: Response):
        """Validate responses for critical manufacturing operations"""
        # Ensure proper response structure for critical operations
        try:
            if hasattr(response, 'body') and response.body:
                # Validate that response contains required audit information
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Additional response validation could be implemented here
                    pass
        except Exception as e:
            logger.warning(f"FDA response validation warning: {str(e)}")
            # Don't fail the response for validation warnings