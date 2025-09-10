"""
Base Pydantic Schemas for Pharmaceutical Manufacturing
FDA 21 CFR Part 11 compliant data validation schemas
"""

from pydantic import BaseModel, Field, validator, UUID4
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
from enum import Enum
import json

class StatusEnum(str, Enum):
    """Standard status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class SeverityEnum(str, Enum):
    """Severity level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PriorityEnum(str, Enum):
    """Priority level enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ApprovalStatusEnum(str, Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

class RegulatoryStatusEnum(str, Enum):
    """Regulatory status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: Optional[UUID4] = None
    created_at: Optional[datetime] = None
    created_by: Optional[UUID4] = None
    modified_at: Optional[datetime] = None
    modified_by: Optional[UUID4] = None
    version: Optional[str] = "1.0"
    is_deleted: Optional[bool] = False
    regulatory_status: Optional[RegulatoryStatusEnum] = RegulatoryStatusEnum.ACTIVE
    comments: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID4: lambda v: str(v) if v else None
        }
        orm_mode = True

class TimestampSchema(BaseModel):
    """Timestamp mixin schema"""
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class StatusSchema(BaseModel):
    """Status mixin schema"""
    status: Optional[StatusEnum] = StatusEnum.ACTIVE
    status_changed_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_changed_by: Optional[UUID4] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID4: lambda v: str(v) if v else None
        }

class ApprovalSchema(BaseModel):
    """Approval mixin schema"""
    approval_required: Optional[bool] = True
    approved: Optional[bool] = False
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID4] = None
    approval_signature_id: Optional[UUID4] = None
    approval_comments: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID4: lambda v: str(v) if v else None
        }

class BatchTrackingSchema(BaseModel):
    """Batch tracking mixin schema"""
    batch_number: str = Field(..., pattern=r'^[A-Z0-9]{6,20}$')
    lot_number: str = Field(..., pattern=r'^[A-Z0-9]{6,20}$')
    manufacturing_date: datetime
    expiry_date: Optional[datetime] = None
    batch_size: str
    batch_units: str
    batch_status: Optional[str] = "in_progress"
    quality_status: Optional[str] = "pending"
    released: Optional[bool] = False
    release_date: Optional[datetime] = None
    released_by: Optional[UUID4] = None
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if v and 'manufacturing_date' in values:
            if v <= values['manufacturing_date']:
                raise ValueError('Expiry date must be after manufacturing date')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID4: lambda v: str(v) if v else None
        }

class TestResultSchema(BaseModel):
    """Test result mixin schema"""
    test_method: str
    test_procedure: str
    test_started_at: Optional[datetime] = None
    test_completed_at: Optional[datetime] = None
    tested_by: UUID4
    reviewed_by: Optional[UUID4] = None
    test_results: Optional[Dict[str, Any]] = None
    specifications: Dict[str, Any]
    test_passed: Optional[bool] = None
    deviations: Optional[Dict[str, Any]] = None
    
    @validator('test_completed_at')
    def validate_test_dates(cls, v, values):
        if v and 'test_started_at' in values and values['test_started_at']:
            if v < values['test_started_at']:
                raise ValueError('Test completion date must be after start date')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID4: lambda v: str(v) if v else None
        }

class CalibrationSchema(BaseModel):
    """Calibration mixin schema"""
    calibration_date: datetime
    next_calibration_date: datetime
    calibration_frequency_days: str
    calibration_procedure: str
    calibration_standard: str
    calibration_certificate: Optional[str] = None
    calibration_results: Optional[Dict[str, Any]] = None
    calibration_passed: Optional[bool] = False
    calibrated_by: UUID4
    verified_by: Optional[UUID4] = None
    
    @validator('next_calibration_date')
    def validate_calibration_dates(cls, v, values):
        if v and 'calibration_date' in values:
            if v <= values['calibration_date']:
                raise ValueError('Next calibration date must be after current calibration date')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID4: lambda v: str(v) if v else None
        }

class EnvironmentalConditionsSchema(BaseModel):
    """Environmental conditions schema"""
    temperature: Optional[float] = Field(None, ge=-80, le=60)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    pressure: Optional[float] = Field(None, ge=0)
    air_quality: Optional[Dict[str, Any]] = None
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < -80 or v > 60):
            raise ValueError('Temperature must be between -80°C and 60°C')
        return v
    
    @validator('humidity')
    def validate_humidity(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Humidity must be between 0% and 100%')
        return v

class DataIntegritySchema(BaseModel):
    """Data integrity validation schema"""
    data_integrity_hash: Optional[str] = None
    hash_algorithm: Optional[str] = "SHA-256"
    verification_status: Optional[bool] = None
    last_verification: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class AuditTrailSchema(BaseModel):
    """Audit trail schema"""
    event_type: str
    event_category: str
    event_description: str
    table_name: Optional[str] = None
    record_id: Optional[UUID4] = None
    user_id: UUID4
    user_name: str
    user_role: str
    action: str
    action_status: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: str
    user_agent: str
    session_id: str
    regulatory_significance: Optional[bool] = False
    gmp_critical: Optional[bool] = False
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID4: lambda v: str(v) if v else None
        }

class PaginationSchema(BaseModel):
    """Pagination schema"""
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)
    total: Optional[int] = None
    total_pages: Optional[int] = None
    
    class Config:
        use_enum_values = True

class FilterSchema(BaseModel):
    """Base filter schema"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[List[str]] = None
    search: Optional[str] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date must be after start date')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class SortSchema(BaseModel):
    """Sorting schema"""
    field: str
    direction: str = Field("asc", pattern=r'^(asc|desc)$')
    
    class Config:
        use_enum_values = True

class ResponseSchema(BaseModel):
    """Standard API response schema"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    pagination: Optional[PaginationSchema] = None
    
    class Config:
        use_enum_values = True

class ErrorSchema(BaseModel):
    """Error response schema"""
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ValidationErrorSchema(BaseModel):
    """Validation error schema"""
    field: str
    message: str
    invalid_value: Optional[Any] = None
    
    class Config:
        use_enum_values = True

class HealthCheckSchema(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    version: Optional[str] = None
    environment: Optional[str] = None
    dependencies: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class MetricsSchema(BaseModel):
    """Metrics response schema"""
    metric_name: str
    metric_value: float
    metric_unit: str
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Validation helpers
def validate_json_field(v: Any) -> Any:
    """Validate JSON field"""
    if v is None:
        return v
    
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON format')
    
    if isinstance(v, dict):
        return v
    
    raise ValueError('JSON field must be a dictionary or valid JSON string')

def validate_positive_number(v: float) -> float:
    """Validate positive number"""
    if v is not None and v <= 0:
        raise ValueError('Value must be positive')
    return v

def validate_percentage(v: float) -> float:
    """Validate percentage (0-100)"""
    if v is not None and (v < 0 or v > 100):
        raise ValueError('Percentage must be between 0 and 100')
    return v

def validate_email(v: str) -> str:
    """Validate email format"""
    import re
    if v and not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
        raise ValueError('Invalid email format')
    return v

def validate_phone(v: str) -> str:
    """Validate phone number format"""
    import re
    if v and not re.match(r'^\+?[\d\s\-\(\)]{10,}$', v):
        raise ValueError('Invalid phone number format')
    return v

def validate_batch_number(v: str) -> str:
    """Validate batch number format"""
    import re
    if v and not re.match(r'^[A-Z0-9]{6,20}$', v):
        raise ValueError('Batch number must be 6-20 alphanumeric characters')
    return v

def validate_lot_number(v: str) -> str:
    """Validate lot number format"""
    import re
    if v and not re.match(r'^[A-Z0-9]{6,20}$', v):
        raise ValueError('Lot number must be 6-20 alphanumeric characters')
    return v

def validate_equipment_id(v: str) -> str:
    """Validate equipment ID format"""
    import re
    if v and not re.match(r'^[A-Z0-9\-]{5,50}$', v):
        raise ValueError('Equipment ID must be 5-50 alphanumeric characters with hyphens')
    return v

def validate_sensor_id(v: str) -> str:
    """Validate sensor ID format"""
    import re
    if v and not re.match(r'^[A-Z0-9\-]{5,50}$', v):
        raise ValueError('Sensor ID must be 5-50 alphanumeric characters with hyphens')
    return v

def validate_material_code(v: str) -> str:
    """Validate material code format"""
    import re
    if v and not re.match(r'^[A-Z0-9\-]{3,50}$', v):
        raise ValueError('Material code must be 3-50 alphanumeric characters with hyphens')
    return v

def validate_concentration(v: str) -> str:
    """Validate concentration format"""
    import re
    if v and not re.match(r'^[0-9.]+[a-zA-Z%/]+$', v):
        raise ValueError('Concentration must be in format like "10mg/ml" or "5%"')
    return v