"""
Batch and Lot Tracking Schemas
Pydantic schemas for batch and lot tracking in pharmaceutical manufacturing
"""

from pydantic import BaseModel, Field, validator, UUID4
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

from .base_schemas import (
    BaseSchema, StatusSchema, ApprovalSchema, BatchTrackingSchema,
    validate_json_field, validate_positive_number, validate_batch_number,
    validate_lot_number, validate_concentration
)

class ProductTypeEnum(str, Enum):
    """Product type enumeration"""
    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    INJECTION = "injection"
    CREAM = "cream"
    OINTMENT = "ointment"

class BatchStatusEnum(str, Enum):
    """Batch status enumeration"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RELEASED = "released"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class QualityStatusEnum(str, Enum):
    """Quality status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    CONDITIONAL = "conditional"

# Product schemas
class ProductCreateSchema(BaseSchema):
    """Product creation schema"""
    product_code: str = Field(..., pattern=r'^[A-Z0-9]{3,50}$')
    product_name: str = Field(..., min_length=1, max_length=200)
    product_type: ProductTypeEnum
    nda_number: Optional[str] = Field(None, pattern=r'^[0-9]{6}$')
    anda_number: Optional[str] = Field(None, pattern=r'^[0-9]{6}$')
    active_ingredient: str = Field(..., min_length=1, max_length=100)
    strength: str = Field(..., min_length=1, max_length=50)
    dosage_form: str = Field(..., min_length=1, max_length=50)
    manufacturing_process: str = Field(..., min_length=1, max_length=100)
    standard_batch_size: float = Field(..., gt=0)
    batch_size_units: str = Field(..., min_length=1, max_length=20)
    shelf_life_months: int = Field(..., gt=0)
    storage_conditions: Dict[str, Any] = Field(..., description="Storage conditions as JSON")
    bom_version: str = Field("1.0", pattern=r'^[0-9]+\.[0-9]+$')
    bom_data: Dict[str, Any] = Field(..., description="Bill of materials as JSON")
    
    @validator('strength')
    def validate_strength(cls, v):
        return validate_concentration(v)
    
    @validator('storage_conditions', 'bom_data')
    def validate_json_fields(cls, v):
        return validate_json_field(v)
    
    @validator('standard_batch_size')
    def validate_batch_size(cls, v):
        return validate_positive_number(v)

class ProductUpdateSchema(BaseModel):
    """Product update schema"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_type: Optional[ProductTypeEnum] = None
    nda_number: Optional[str] = Field(None, pattern=r'^[0-9]{6}$')
    anda_number: Optional[str] = Field(None, pattern=r'^[0-9]{6}$')
    active_ingredient: Optional[str] = Field(None, min_length=1, max_length=100)
    strength: Optional[str] = Field(None, min_length=1, max_length=50)
    dosage_form: Optional[str] = Field(None, min_length=1, max_length=50)
    manufacturing_process: Optional[str] = Field(None, min_length=1, max_length=100)
    standard_batch_size: Optional[float] = Field(None, gt=0)
    batch_size_units: Optional[str] = Field(None, min_length=1, max_length=20)
    shelf_life_months: Optional[int] = Field(None, gt=0)
    storage_conditions: Optional[Dict[str, Any]] = None
    bom_version: Optional[str] = Field(None, pattern=r'^[0-9]+\.[0-9]+$')
    bom_data: Optional[Dict[str, Any]] = None
    
    @validator('strength')
    def validate_strength(cls, v):
        if v:
            return validate_concentration(v)
        return v
    
    @validator('storage_conditions', 'bom_data')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class ProductResponseSchema(ProductCreateSchema):
    """Product response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    
    class Config:
        orm_mode = True

# Batch schemas
class BatchCreateSchema(BaseSchema, BatchTrackingSchema, StatusSchema, ApprovalSchema):
    """Batch creation schema"""
    product_id: UUID4
    manufacturing_line: str = Field(..., min_length=1, max_length=50)
    manufacturing_order: str = Field(..., min_length=1, max_length=100)
    planned_start_date: datetime
    planned_completion_date: datetime
    theoretical_yield: float = Field(..., gt=0)
    quality_review_required: bool = True
    
    @validator('batch_number')
    def validate_batch_number(cls, v):
        return validate_batch_number(v)
    
    @validator('lot_number')
    def validate_lot_number(cls, v):
        return validate_lot_number(v)
    
    @validator('planned_completion_date')
    def validate_planned_dates(cls, v, values):
        if v and 'planned_start_date' in values:
            if v <= values['planned_start_date']:
                raise ValueError('Planned completion date must be after start date')
        return v
    
    @validator('theoretical_yield')
    def validate_theoretical_yield(cls, v):
        return validate_positive_number(v)

class BatchUpdateSchema(BaseModel):
    """Batch update schema"""
    manufacturing_line: Optional[str] = Field(None, min_length=1, max_length=50)
    manufacturing_order: Optional[str] = Field(None, min_length=1, max_length=100)
    planned_start_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    planned_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    theoretical_yield: Optional[float] = Field(None, gt=0)
    actual_yield: Optional[float] = Field(None, ge=0)
    quality_review_required: Optional[bool] = None
    quality_review_completed: Optional[bool] = None
    quality_reviewed_by: Optional[UUID4] = None
    quality_review_date: Optional[datetime] = None
    
    @validator('actual_yield')
    def validate_actual_yield(cls, v):
        if v is not None:
            return validate_positive_number(v)
        return v

class BatchResponseSchema(BatchCreateSchema):
    """Batch response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    actual_start_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    actual_yield: Optional[float] = None
    yield_percentage: Optional[float] = None
    quality_review_completed: bool = False
    quality_reviewed_by: Optional[UUID4] = None
    quality_review_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Batch genealogy schemas
class BatchGenealogyCreateSchema(BaseSchema):
    """Batch genealogy creation schema"""
    parent_batch_id: UUID4
    child_batch_id: UUID4
    relationship_type: str = Field(..., min_length=1, max_length=50)
    quantity_transferred: float = Field(..., gt=0)
    quantity_units: str = Field(..., min_length=1, max_length=20)
    transfer_date: datetime
    transfer_reason: str = Field(..., min_length=1)
    
    @validator('quantity_transferred')
    def validate_quantity(cls, v):
        return validate_positive_number(v)
    
    @validator('parent_batch_id', 'child_batch_id')
    def validate_different_batches(cls, v, values):
        if 'parent_batch_id' in values and v == values['parent_batch_id']:
            raise ValueError('Parent and child batch cannot be the same')
        return v

class BatchGenealogyResponseSchema(BatchGenealogyCreateSchema):
    """Batch genealogy response schema"""
    id: UUID4
    created_at: datetime
    
    class Config:
        orm_mode = True

# Batch stage schemas
class BatchStageCreateSchema(BaseSchema, StatusSchema):
    """Batch stage creation schema"""
    batch_id: UUID4
    stage_name: str = Field(..., min_length=1, max_length=100)
    stage_order: int = Field(..., gt=0)
    planned_start_time: datetime
    planned_end_time: datetime
    stage_parameters: Optional[Dict[str, Any]] = None
    equipment_id: Optional[UUID4] = None
    equipment_name: Optional[str] = Field(None, max_length=100)
    operator_id: UUID4
    supervisor_id: Optional[UUID4] = None
    
    @validator('planned_end_time')
    def validate_planned_times(cls, v, values):
        if v and 'planned_start_time' in values:
            if v <= values['planned_start_time']:
                raise ValueError('Planned end time must be after start time')
        return v
    
    @validator('stage_parameters')
    def validate_stage_parameters(cls, v):
        if v:
            return validate_json_field(v)
        return v
    
    @validator('stage_order')
    def validate_stage_order(cls, v):
        return validate_positive_number(v)

class BatchStageUpdateSchema(BaseModel):
    """Batch stage update schema"""
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    stage_parameters: Optional[Dict[str, Any]] = None
    equipment_id: Optional[UUID4] = None
    equipment_name: Optional[str] = Field(None, max_length=100)
    supervisor_id: Optional[UUID4] = None
    stage_results: Optional[Dict[str, Any]] = None
    stage_passed: Optional[bool] = None
    
    @validator('actual_end_time')
    def validate_actual_times(cls, v, values):
        if v and 'actual_start_time' in values and values['actual_start_time']:
            if v <= values['actual_start_time']:
                raise ValueError('Actual end time must be after start time')
        return v
    
    @validator('stage_parameters', 'stage_results')
    def validate_json_fields(cls, v):
        if v:
            return validate_json_field(v)
        return v

class BatchStageResponseSchema(BatchStageCreateSchema):
    """Batch stage response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    stage_results: Optional[Dict[str, Any]] = None
    stage_passed: Optional[bool] = None
    
    class Config:
        orm_mode = True

# Batch material schemas
class BatchMaterialCreateSchema(BaseSchema):
    """Batch material creation schema"""
    batch_id: UUID4
    material_id: UUID4
    material_name: str = Field(..., min_length=1, max_length=200)
    material_type: str = Field(..., min_length=1, max_length=50)
    lot_number: str = Field(..., min_length=1, max_length=100)
    supplier: Optional[str] = Field(None, max_length=200)
    expiry_date: Optional[datetime] = None
    planned_quantity: float = Field(..., gt=0)
    quantity_units: str = Field(..., min_length=1, max_length=20)
    dispensed_at: datetime
    dispensed_by: UUID4
    verified_by: Optional[UUID4] = None
    coa_number: Optional[str] = Field(None, max_length=100)
    quality_approved: bool = False
    
    @validator('lot_number')
    def validate_lot_number(cls, v):
        return validate_lot_number(v)
    
    @validator('planned_quantity')
    def validate_planned_quantity(cls, v):
        return validate_positive_number(v)

class BatchMaterialUpdateSchema(BaseModel):
    """Batch material update schema"""
    actual_quantity: Optional[float] = Field(None, ge=0)
    verified_by: Optional[UUID4] = None
    coa_number: Optional[str] = Field(None, max_length=100)
    quality_approved: Optional[bool] = None
    
    @validator('actual_quantity')
    def validate_actual_quantity(cls, v):
        if v is not None:
            return validate_positive_number(v)
        return v

class BatchMaterialResponseSchema(BatchMaterialCreateSchema):
    """Batch material response schema"""
    id: UUID4
    created_at: datetime
    actual_quantity: Optional[float] = None
    
    class Config:
        orm_mode = True

# Lot schemas
class LotCreateSchema(BaseSchema, BatchTrackingSchema, StatusSchema):
    """Lot creation schema"""
    batch_id: UUID4
    lot_size: float = Field(..., gt=0)
    lot_units: str = Field(..., min_length=1, max_length=20)
    packaging_date: datetime
    packaging_line: str = Field(..., min_length=1, max_length=50)
    packaged_by: UUID4
    container_type: str = Field(..., min_length=1, max_length=50)
    container_size: str = Field(..., min_length=1, max_length=50)
    containers_count: int = Field(..., gt=0)
    label_version: str = Field(..., min_length=1, max_length=20)
    label_verified: bool = False
    stability_testing_required: bool = True
    
    @validator('lot_number')
    def validate_lot_number(cls, v):
        return validate_lot_number(v)
    
    @validator('lot_size')
    def validate_lot_size(cls, v):
        return validate_positive_number(v)
    
    @validator('containers_count')
    def validate_containers_count(cls, v):
        return validate_positive_number(v)

class LotUpdateSchema(BaseModel):
    """Lot update schema"""
    label_verified: Optional[bool] = None
    label_verified_by: Optional[UUID4] = None
    distributed: Optional[bool] = None
    distribution_date: Optional[datetime] = None
    distribution_records: Optional[Dict[str, Any]] = None
    stability_program_id: Optional[UUID4] = None
    
    @validator('distribution_records')
    def validate_distribution_records(cls, v):
        if v:
            return validate_json_field(v)
        return v

class LotResponseSchema(LotCreateSchema):
    """Lot response schema"""
    id: UUID4
    created_at: datetime
    modified_at: datetime
    label_verified_by: Optional[UUID4] = None
    distributed: bool = False
    distribution_date: Optional[datetime] = None
    distribution_records: Optional[Dict[str, Any]] = None
    stability_program_id: Optional[UUID4] = None
    
    class Config:
        orm_mode = True

# Batch filter schemas
class BatchFilterSchema(BaseModel):
    """Batch filtering schema"""
    product_id: Optional[UUID4] = None
    manufacturing_line: Optional[str] = None
    batch_status: Optional[List[BatchStatusEnum]] = None
    quality_status: Optional[List[QualityStatusEnum]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date must be after start date')
        return v

class BatchSummarySchema(BaseModel):
    """Batch summary schema"""
    id: UUID4
    batch_number: str
    lot_number: str
    product_name: str
    batch_status: str
    quality_status: str
    manufacturing_date: datetime
    yield_percentage: Optional[float] = None
    
    class Config:
        orm_mode = True

class BatchGenealogyTreeSchema(BaseModel):
    """Batch genealogy tree schema"""
    batch_id: UUID4
    batch_number: str
    parents: List['BatchGenealogyTreeSchema'] = []
    children: List['BatchGenealogyTreeSchema'] = []
    
    class Config:
        orm_mode = True

# Update forward references
BatchGenealogyTreeSchema.model_rebuild()