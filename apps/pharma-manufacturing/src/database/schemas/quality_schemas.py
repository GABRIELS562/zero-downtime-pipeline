"""
Quality Control and Testing Schemas
Pydantic schemas for quality control and testing operations
"""

from pydantic import BaseModel, Field, validator, UUID4
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

from .base_schemas import (
    BaseSchema, StatusSchema, ApprovalSchema, TestResultSchema,
    validate_json_field, validate_positive_number, validate_percentage
)

class TestCategoryEnum(str, Enum):
    """Test category enumeration"""
    ANALYTICAL = "analytical"
    MICROBIOLOGICAL = "microbiological"
    PHYSICAL = "physical"
    CHEMICAL = "chemical"

class TestFrequencyEnum(str, Enum):
    """Test frequency enumeration"""
    PER_BATCH = "per_batch"
    PER_LOT = "per_lot"
    PERIODIC = "periodic"
    SKIP_LOT = "skip_lot"

class LaboratoryTypeEnum(str, Enum):
    """Laboratory type enumeration"""
    IN_HOUSE = "in_house"
    CONTRACT = "contract"
    BOTH = "both"

class TestPriorityEnum(str, Enum):
    """Test priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class TestResultStatusEnum(str, Enum):
    """Test result status enumeration"""
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"
    INVALID = "invalid"

class SampleTypeEnum(str, Enum):
    """Sample type enumeration"""
    BATCH = "batch"
    LOT = "lot"
    MATERIAL = "material"
    STABILITY = "stability"
    RETAIN = "retain"

class ParameterTypeEnum(str, Enum):
    """Parameter type enumeration"""
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    LIMIT = "limit"

class ResultStatusEnum(str, Enum):
    """Result status enumeration"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    INFO = "info"

# Test type schemas
class TestTypeCreateSchema(BaseSchema):
    """Test type creation schema"""
    test_type_code: str = Field(..., min_length=1, max_length=50)
    test_type_name: str = Field(..., min_length=1, max_length=200)
    test_category: TestCategoryEnum
    test_frequency: TestFrequencyEnum
    regulatory_requirement: bool = True
    standard_test_method: str = Field(..., min_length=1, max_length=100)
    test_procedure: str = Field(..., min_length=1, max_length=200)
    default_specifications: Dict[str, Any] = Field(..., description="Default test specifications")
    laboratory_type: LaboratoryTypeEnum
    required_equipment: Optional[Dict[str, Any]] = None
    standard_test_duration_hours: float = Field(..., gt=0)
    sample_stability_hours: Optional[float] = Field(None, gt=0)
    accuracy_requirement: Optional[float] = Field(None, gt=0)
    precision_requirement: Optional[float] = Field(None, gt=0)
    
    @validator('default_specifications', 'required_equipment')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v
    
    @validator('standard_test_duration_hours', 'sample_stability_hours', 'accuracy_requirement', 'precision_requirement')
    def validate_positive_values(cls, v):
        if v is not None:
            return validate_positive_number(v)
        return v

class TestTypeUpdateSchema(BaseModel):
    """Test type update schema"""
    test_type_name: Optional[str] = Field(None, min_length=1, max_length=200)
    test_category: Optional[TestCategoryEnum] = None
    test_frequency: Optional[TestFrequencyEnum] = None
    regulatory_requirement: Optional[bool] = None
    standard_test_method: Optional[str] = Field(None, min_length=1, max_length=100)
    test_procedure: Optional[str] = Field(None, min_length=1, max_length=200)
    default_specifications: Optional[Dict[str, Any]] = None
    laboratory_type: Optional[LaboratoryTypeEnum] = None
    required_equipment: Optional[Dict[str, Any]] = None
    standard_test_duration_hours: Optional[float] = Field(None, gt=0)
    sample_stability_hours: Optional[float] = Field(None, gt=0)
    accuracy_requirement: Optional[float] = Field(None, gt=0)
    precision_requirement: Optional[float] = Field(None, gt=0)
    
    @validator('default_specifications', 'required_equipment')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class TestTypeResponseSchema(TestTypeCreateSchema):
    """Test type response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    
    class Config:
        orm_mode = True

# Test plan schemas
class TestPlanCreateSchema(BaseSchema, StatusSchema, ApprovalSchema):
    """Test plan creation schema"""
    plan_number: str = Field(..., min_length=1, max_length=100)
    plan_name: str = Field(..., min_length=1, max_length=200)
    plan_version: str = Field("1.0", regex=r'^[0-9]+\.[0-9]+$')
    test_type_id: UUID4
    product_id: Optional[UUID4] = None
    material_id: Optional[UUID4] = None
    sampling_requirements: Dict[str, Any] = Field(..., description="Sampling requirements")
    test_specifications: Dict[str, Any] = Field(..., description="Test specifications")
    analytical_method: str = Field(..., min_length=1, max_length=100)
    method_validation_status: str = Field("pending", regex=r'^(pending|in_progress|completed|failed)$')
    test_frequency: TestFrequencyEnum
    test_schedule: Optional[Dict[str, Any]] = None
    assigned_laboratory: str = Field(..., min_length=1, max_length=200)
    backup_laboratory: Optional[str] = Field(None, max_length=200)
    acceptance_criteria: Dict[str, Any] = Field(..., description="Acceptance criteria")
    critical_quality_attributes: Optional[Dict[str, Any]] = None
    regulatory_references: Optional[Dict[str, Any]] = None
    compendial_method: Optional[str] = Field(None, max_length=100)
    effective_date: datetime
    expiry_date: Optional[datetime] = None
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if v and 'effective_date' in values:
            if v <= values['effective_date']:
                raise ValueError('Expiry date must be after effective date')
        return v
    
    @validator('sampling_requirements', 'test_specifications', 'test_schedule', 'acceptance_criteria', 'critical_quality_attributes', 'regulatory_references')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class TestPlanUpdateSchema(BaseModel):
    """Test plan update schema"""
    plan_name: Optional[str] = Field(None, min_length=1, max_length=200)
    plan_version: Optional[str] = Field(None, regex=r'^[0-9]+\.[0-9]+$')
    sampling_requirements: Optional[Dict[str, Any]] = None
    test_specifications: Optional[Dict[str, Any]] = None
    analytical_method: Optional[str] = Field(None, min_length=1, max_length=100)
    method_validation_status: Optional[str] = Field(None, regex=r'^(pending|in_progress|completed|failed)$')
    test_frequency: Optional[TestFrequencyEnum] = None
    test_schedule: Optional[Dict[str, Any]] = None
    assigned_laboratory: Optional[str] = Field(None, min_length=1, max_length=200)
    backup_laboratory: Optional[str] = Field(None, max_length=200)
    acceptance_criteria: Optional[Dict[str, Any]] = None
    critical_quality_attributes: Optional[Dict[str, Any]] = None
    regulatory_references: Optional[Dict[str, Any]] = None
    compendial_method: Optional[str] = Field(None, max_length=100)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
    @validator('sampling_requirements', 'test_specifications', 'test_schedule', 'acceptance_criteria', 'critical_quality_attributes', 'regulatory_references')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class TestPlanResponseSchema(TestPlanCreateSchema):
    """Test plan response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    
    class Config:
        orm_mode = True

# Laboratory schemas
class LaboratoryCreateSchema(BaseSchema, StatusSchema):
    """Laboratory creation schema"""
    laboratory_code: str = Field(..., min_length=1, max_length=50)
    laboratory_name: str = Field(..., min_length=1, max_length=200)
    laboratory_type: LaboratoryTypeEnum
    location: str = Field(..., min_length=1, max_length=200)
    facility_id: Optional[str] = Field(None, max_length=100)
    accreditation_body: Optional[str] = Field(None, max_length=100)
    accreditation_number: Optional[str] = Field(None, max_length=100)
    accreditation_scope: Optional[Dict[str, Any]] = None
    accreditation_expiry: Optional[datetime] = None
    testing_capabilities: Dict[str, Any] = Field(..., description="Testing capabilities")
    equipment_list: Optional[Dict[str, Any]] = None
    quality_system: Optional[str] = Field(None, max_length=100)
    last_audit_date: Optional[datetime] = None
    next_audit_date: Optional[datetime] = None
    turnaround_time_days: Optional[float] = Field(None, gt=0)
    accuracy_rating: Optional[float] = Field(None, ge=0, le=100)
    on_time_delivery_rate: Optional[float] = Field(None, ge=0, le=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    
    @validator('testing_capabilities', 'equipment_list', 'accreditation_scope')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v
    
    @validator('accuracy_rating', 'on_time_delivery_rate')
    def validate_percentage_fields(cls, v):
        if v is not None:
            return validate_percentage(v)
        return v

class LaboratoryUpdateSchema(BaseModel):
    """Laboratory update schema"""
    laboratory_name: Optional[str] = Field(None, min_length=1, max_length=200)
    laboratory_type: Optional[LaboratoryTypeEnum] = None
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    facility_id: Optional[str] = Field(None, max_length=100)
    accreditation_body: Optional[str] = Field(None, max_length=100)
    accreditation_number: Optional[str] = Field(None, max_length=100)
    accreditation_scope: Optional[Dict[str, Any]] = None
    accreditation_expiry: Optional[datetime] = None
    testing_capabilities: Optional[Dict[str, Any]] = None
    equipment_list: Optional[Dict[str, Any]] = None
    quality_system: Optional[str] = Field(None, max_length=100)
    last_audit_date: Optional[datetime] = None
    next_audit_date: Optional[datetime] = None
    turnaround_time_days: Optional[float] = Field(None, gt=0)
    accuracy_rating: Optional[float] = Field(None, ge=0, le=100)
    on_time_delivery_rate: Optional[float] = Field(None, ge=0, le=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    
    @validator('testing_capabilities', 'equipment_list', 'accreditation_scope')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class LaboratoryResponseSchema(LaboratoryCreateSchema):
    """Laboratory response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    
    class Config:
        orm_mode = True

# Quality test result schemas
class QualityTestResultCreateSchema(BaseSchema, TestResultSchema, ApprovalSchema):
    """Quality test result creation schema"""
    test_report_number: str = Field(..., min_length=1, max_length=100)
    test_type_id: UUID4
    test_plan_id: UUID4
    laboratory_id: UUID4
    sample_id: str = Field(..., min_length=1, max_length=100)
    sample_type: SampleTypeEnum
    sample_description: Optional[str] = Field(None, max_length=200)
    batch_id: Optional[UUID4] = None
    lot_id: Optional[UUID4] = None
    material_id: Optional[UUID4] = None
    sampling_date: datetime
    sampling_location: str = Field(..., min_length=1, max_length=200)
    sampling_method: str = Field(..., min_length=1, max_length=100)
    sampled_by: UUID4
    sample_container: str = Field(..., min_length=1, max_length=100)
    storage_conditions: Dict[str, Any] = Field(..., description="Storage conditions")
    sample_stability: str = Field("stable", regex=r'^(stable|unstable|degraded)$')
    test_request_date: datetime
    test_priority: TestPriorityEnum = TestPriorityEnum.NORMAL
    overall_result: TestResultStatusEnum
    test_conclusion: Optional[str] = None
    primary_analyst: UUID4
    secondary_analyst: Optional[UUID4] = None
    instruments_used: Optional[Dict[str, Any]] = None
    test_environment: Optional[Dict[str, Any]] = None
    
    @validator('storage_conditions', 'instruments_used', 'test_environment')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class QualityTestResultUpdateSchema(BaseModel):
    """Quality test result update schema"""
    sample_description: Optional[str] = Field(None, max_length=200)
    sample_stability: Optional[str] = Field(None, regex=r'^(stable|unstable|degraded)$')
    test_priority: Optional[TestPriorityEnum] = None
    overall_result: Optional[TestResultStatusEnum] = None
    test_conclusion: Optional[str] = None
    secondary_analyst: Optional[UUID4] = None
    instruments_used: Optional[Dict[str, Any]] = None
    test_environment: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None
    test_passed: Optional[bool] = None
    deviations: Optional[Dict[str, Any]] = None
    
    @validator('instruments_used', 'test_environment', 'test_results', 'deviations')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class QualityTestResultResponseSchema(QualityTestResultCreateSchema):
    """Quality test result response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    
    class Config:
        orm_mode = True

# Test parameter schemas
class TestParameterCreateSchema(BaseSchema):
    """Test parameter creation schema"""
    test_result_id: UUID4
    parameter_name: str = Field(..., min_length=1, max_length=100)
    parameter_code: str = Field(..., min_length=1, max_length=50)
    parameter_type: ParameterTypeEnum
    specification: Dict[str, Any] = Field(..., description="Parameter specification")
    specification_min: Optional[float] = None
    specification_max: Optional[float] = None
    specification_target: Optional[float] = None
    specification_units: Optional[str] = Field(None, max_length=20)
    result_value: Optional[float] = None
    result_text: Optional[str] = Field(None, max_length=200)
    result_units: Optional[str] = Field(None, max_length=20)
    calculation_method: Optional[str] = Field(None, max_length=100)
    calculation_formula: Optional[str] = Field(None, max_length=500)
    raw_data: Optional[Dict[str, Any]] = None
    result_status: ResultStatusEnum
    deviation_percentage: Optional[float] = None
    measurement_uncertainty: Optional[float] = None
    confidence_level: Optional[float] = Field(None, ge=0, le=100)
    instrument_id: Optional[UUID4] = None
    instrument_calibration_date: Optional[datetime] = None
    analyst_notes: Optional[str] = None
    
    @validator('specification_max')
    def validate_specification_range(cls, v, values):
        if v is not None and 'specification_min' in values and values['specification_min'] is not None:
            if v < values['specification_min']:
                raise ValueError('Specification max must be greater than or equal to min')
        return v
    
    @validator('specification', 'raw_data')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v
    
    @validator('confidence_level')
    def validate_confidence_level(cls, v):
        if v is not None:
            return validate_percentage(v)
        return v

class TestParameterUpdateSchema(BaseModel):
    """Test parameter update schema"""
    result_value: Optional[float] = None
    result_text: Optional[str] = Field(None, max_length=200)
    result_units: Optional[str] = Field(None, max_length=20)
    calculation_method: Optional[str] = Field(None, max_length=100)
    calculation_formula: Optional[str] = Field(None, max_length=500)
    raw_data: Optional[Dict[str, Any]] = None
    result_status: Optional[ResultStatusEnum] = None
    deviation_percentage: Optional[float] = None
    measurement_uncertainty: Optional[float] = None
    confidence_level: Optional[float] = Field(None, ge=0, le=100)
    instrument_id: Optional[UUID4] = None
    instrument_calibration_date: Optional[datetime] = None
    analyst_notes: Optional[str] = None
    
    @validator('raw_data')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class TestParameterResponseSchema(TestParameterCreateSchema):
    """Test parameter response schema"""
    id: UUID4
    created_at: datetime
    
    class Config:
        orm_mode = True

# Quality filter schemas
class QualityTestFilterSchema(BaseModel):
    """Quality test filtering schema"""
    test_type_id: Optional[UUID4] = None
    laboratory_id: Optional[UUID4] = None
    batch_id: Optional[UUID4] = None
    lot_id: Optional[UUID4] = None
    material_id: Optional[UUID4] = None
    sample_type: Optional[SampleTypeEnum] = None
    overall_result: Optional[List[TestResultStatusEnum]] = None
    test_priority: Optional[List[TestPriorityEnum]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date must be after start date')
        return v

class QualityTestSummarySchema(BaseModel):
    """Quality test summary schema"""
    id: UUID4
    test_report_number: str
    test_type_name: str
    laboratory_name: str
    sample_id: str
    sample_type: str
    overall_result: str
    test_priority: str
    test_completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class QualityMetricsSchema(BaseModel):
    """Quality metrics schema"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    pending_tests: int
    pass_rate: float
    average_turnaround_time: float
    tests_by_type: Dict[str, int]
    tests_by_priority: Dict[str, int]
    
    class Config:
        orm_mode = True