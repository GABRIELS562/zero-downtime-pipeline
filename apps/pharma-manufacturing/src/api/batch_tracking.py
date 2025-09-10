"""
Batch Tracking API
GMP-compliant batch production tracking and management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.manufacturing import Batch, BatchStatus, WorkflowStage
from src.services.batch_service import BatchService
from src.services.audit_service import AuditService

router = APIRouter()

# Pydantic models for API
class BatchResponse(BaseModel):
    id: UUID
    batch_number: str
    product_id: UUID
    planned_quantity: int
    actual_quantity: int
    status: str
    current_stage: str
    planned_start_date: datetime
    actual_start_date: Optional[datetime]
    planned_completion_date: datetime
    actual_completion_date: Optional[datetime]
    manufacturing_instructions: Optional[str]
    deviations: Optional[dict]
    environmental_conditions: Optional[dict]
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BatchCreate(BaseModel):
    batch_number: str = Field(..., description="Unique batch identifier")
    product_id: UUID = Field(..., description="Product being manufactured")
    planned_quantity: int = Field(..., gt=0, description="Planned production quantity")
    planned_start_date: datetime = Field(..., description="Planned start date")
    planned_completion_date: datetime = Field(..., description="Planned completion date")
    manufacturing_instructions: Optional[str] = Field(None, description="Manufacturing instructions")
    created_by: str = Field(..., description="User creating the batch")

class BatchUpdate(BaseModel):
    status: Optional[BatchStatus] = Field(None, description="Batch status")
    current_stage: Optional[WorkflowStage] = Field(None, description="Current workflow stage")
    actual_quantity: Optional[int] = Field(None, ge=0, description="Actual production quantity")
    actual_start_date: Optional[datetime] = Field(None, description="Actual start date")
    actual_completion_date: Optional[datetime] = Field(None, description="Actual completion date")
    manufacturing_instructions: Optional[str] = Field(None, description="Updated manufacturing instructions")

class BatchDeviationCreate(BaseModel):
    deviation_type: str = Field(..., description="Type of deviation")
    description: str = Field(..., description="Deviation description")
    severity: str = Field(..., description="Deviation severity (low, medium, high, critical)")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    corrective_action: Optional[str] = Field(None, description="Corrective action taken")
    reported_by: str = Field(..., description="Person reporting the deviation")

class EnvironmentalConditionsUpdate(BaseModel):
    conditions: dict = Field(..., description="Environmental conditions during production")
    recorded_at: datetime = Field(default_factory=datetime.utcnow, description="When conditions were recorded")
    recorded_by: str = Field(..., description="Person recording the conditions")

@router.get("/", response_model=List[BatchResponse])
async def get_all_batches(
    status: Optional[BatchStatus] = Query(None, description="Filter by batch status"),
    stage: Optional[WorkflowStage] = Query(None, description="Filter by current stage"),
    product_id: Optional[UUID] = Query(None, description="Filter by product ID"),
    start_date: Optional[datetime] = Query(None, description="Filter batches started after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter batches started before this date"),
    limit: int = Query(100, le=1000, description="Maximum number of batches to return"),
    batch_service: BatchService = Depends()
):
    """Get list of all batches with optional filtering"""
    try:
        batches = await batch_service.get_batches(
            status=status,
            stage=stage,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return batches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batches: {str(e)}")

@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch_details(
    batch_id: UUID,
    batch_service: BatchService = Depends()
):
    """Get detailed information about a specific batch"""
    try:
        batch = await batch_service.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch: {str(e)}")

@router.get("/batch-number/{batch_number}", response_model=BatchResponse)
async def get_batch_by_number(
    batch_number: str,
    batch_service: BatchService = Depends()
):
    """Get batch information by batch number"""
    try:
        batch = await batch_service.get_batch_by_number(batch_number)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch: {str(e)}")

@router.post("/", response_model=BatchResponse)
async def create_batch(
    batch_data: BatchCreate,
    batch_service: BatchService = Depends(),
    audit_service: AuditService = Depends()
):
    """Create a new batch for production"""
    try:
        # Check if batch number already exists
        existing_batch = await batch_service.get_batch_by_number(batch_data.batch_number)
        if existing_batch:
            raise HTTPException(status_code=400, detail="Batch number already exists")
        
        # Create the batch
        new_batch = await batch_service.create_batch(batch_data)
        
        # Log audit trail
        await audit_service.log_batch_creation(new_batch.id, batch_data.created_by)
        
        return new_batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")

@router.put("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: UUID,
    batch_update: BatchUpdate,
    updated_by: str = Query(..., description="User making the update"),
    batch_service: BatchService = Depends(),
    audit_service: AuditService = Depends()
):
    """Update batch information"""
    try:
        # Verify batch exists
        existing_batch = await batch_service.get_batch_by_id(batch_id)
        if not existing_batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Update the batch
        updated_batch = await batch_service.update_batch(batch_id, batch_update)
        
        # Log audit trail
        await audit_service.log_batch_update(batch_id, updated_by, batch_update.dict(exclude_none=True))
        
        return updated_batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update batch: {str(e)}")

@router.post("/{batch_id}/start")
async def start_batch_production(
    batch_id: UUID,
    started_by: str = Query(..., description="User starting the batch"),
    batch_service: BatchService = Depends(),
    audit_service: AuditService = Depends()
):
    """Start batch production"""
    try:
        # Verify batch exists and is in planned status
        batch = await batch_service.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if batch.status != BatchStatus.PLANNED:
            raise HTTPException(status_code=400, detail=f"Cannot start batch with status: {batch.status}")
        
        # Start the batch
        started_batch = await batch_service.start_batch(batch_id, started_by)
        
        # Log audit trail
        await audit_service.log_batch_start(batch_id, started_by)
        
        return {
            "message": "Batch production started successfully",
            "batch_id": batch_id,
            "batch_number": started_batch.batch_number,
            "started_at": started_batch.actual_start_date,
            "started_by": started_by
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch: {str(e)}")

@router.post("/{batch_id}/complete")
async def complete_batch_production(
    batch_id: UUID,
    completed_by: str = Query(..., description="User completing the batch"),
    actual_quantity: Optional[int] = Query(None, description="Final production quantity"),
    batch_service: BatchService = Depends(),
    audit_service: AuditService = Depends()
):
    """Complete batch production"""
    try:
        # Verify batch exists and is in progress
        batch = await batch_service.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if batch.status not in [BatchStatus.IN_PROGRESS, BatchStatus.QC_PASSED]:
            raise HTTPException(status_code=400, detail=f"Cannot complete batch with status: {batch.status}")
        
        # Complete the batch
        completed_batch = await batch_service.complete_batch(batch_id, completed_by, actual_quantity)
        
        # Log audit trail
        await audit_service.log_batch_completion(batch_id, completed_by)
        
        return {
            "message": "Batch production completed successfully",
            "batch_id": batch_id,
            "batch_number": completed_batch.batch_number,
            "completed_at": completed_batch.actual_completion_date,
            "final_quantity": completed_batch.actual_quantity,
            "completed_by": completed_by
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete batch: {str(e)}")

@router.post("/{batch_id}/deviations")
async def record_batch_deviation(
    batch_id: UUID,
    deviation: BatchDeviationCreate,
    batch_service: BatchService = Depends(),
    audit_service: AuditService = Depends()
):
    """Record a deviation for a batch"""
    try:
        # Verify batch exists
        batch = await batch_service.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Record the deviation
        deviation_record = await batch_service.record_deviation(batch_id, deviation)
        
        # Log audit trail
        await audit_service.log_batch_deviation(batch_id, deviation.reported_by, deviation.dict())
        
        return {
            "message": "Deviation recorded successfully",
            "batch_id": batch_id,
            "deviation_id": deviation_record["deviation_id"],
            "recorded_at": datetime.utcnow(),
            "reported_by": deviation.reported_by
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record deviation: {str(e)}")

@router.get("/{batch_id}/deviations")
async def get_batch_deviations(
    batch_id: UUID,
    batch_service: BatchService = Depends()
):
    """Get all deviations for a batch"""
    try:
        batch = await batch_service.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        deviations = await batch_service.get_batch_deviations(batch_id)
        
        return {
            "batch_id": batch_id,
            "batch_number": batch.batch_number,
            "deviations": deviations,
            "deviation_count": len(deviations)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve deviations: {str(e)}")

@router.put("/{batch_id}/environmental-conditions")
async def update_environmental_conditions(
    batch_id: UUID,
    environmental_update: EnvironmentalConditionsUpdate,
    batch_service: BatchService = Depends(),
    audit_service: AuditService = Depends()
):
    """Update environmental conditions for a batch"""
    try:
        batch = await batch_service.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Update environmental conditions
        updated_batch = await batch_service.update_environmental_conditions(
            batch_id, 
            environmental_update.conditions,
            environmental_update.recorded_by
        )
        
        # Log audit trail
        await audit_service.log_environmental_conditions_update(
            batch_id, 
            environmental_update.recorded_by, 
            environmental_update.conditions
        )
        
        return {
            "message": "Environmental conditions updated successfully",
            "batch_id": batch_id,
            "conditions": environmental_update.conditions,
            "recorded_at": environmental_update.recorded_at,
            "recorded_by": environmental_update.recorded_by
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update environmental conditions: {str(e)}")

@router.get("/{batch_id}/genealogy")
async def get_batch_genealogy(
    batch_id: UUID,
    batch_service: BatchService = Depends()
):
    """Get complete batch genealogy including materials, equipment, and personnel"""
    try:
        batch = await batch_service.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        genealogy = await batch_service.get_batch_genealogy(batch_id)
        
        return {
            "batch_id": batch_id,
            "batch_number": batch.batch_number,
            "genealogy": genealogy,
            "generated_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch genealogy: {str(e)}")

@router.get("/status/{status}/summary")
async def get_batches_by_status_summary(
    status: BatchStatus,
    batch_service: BatchService = Depends()
):
    """Get summary of batches by status"""
    try:
        summary = await batch_service.get_batches_by_status_summary(status)
        
        return {
            "status": status,
            "summary": summary,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch summary: {str(e)}")

@router.get("/stage/{stage}/summary")
async def get_batches_by_stage_summary(
    stage: WorkflowStage,
    batch_service: BatchService = Depends()
):
    """Get summary of batches by workflow stage"""
    try:
        summary = await batch_service.get_batches_by_stage_summary(stage)
        
        return {
            "stage": stage,
            "summary": summary,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch stage summary: {str(e)}")

@router.get("/health/batch-tracking")
async def batch_tracking_health_check(
    batch_service: BatchService = Depends()
):
    """Health check endpoint for batch tracking system"""
    try:
        health_status = await batch_service.perform_health_check()
        
        return {
            "service": "batch_tracking",
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "details": health_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "service": "batch_tracking",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }