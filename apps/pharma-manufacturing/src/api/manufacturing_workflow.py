"""
Manufacturing Workflow API
Management of pharmaceutical manufacturing workflow stages
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.manufacturing import BatchWorkflowStage, WorkflowStage
from src.services.workflow_service import WorkflowService
from src.services.audit_service import AuditService

router = APIRouter()

# Pydantic models for API
class BatchWorkflowStageResponse(BaseModel):
    id: UUID
    batch_id: UUID
    equipment_id: Optional[UUID]
    stage: str
    stage_order: int
    planned_start_time: Optional[datetime]
    actual_start_time: Optional[datetime]
    planned_end_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    status: str
    stage_yield: Optional[float]
    process_parameters: Optional[dict]
    target_parameters: Optional[dict]
    operator: str
    supervisor: Optional[str]
    batch_record_notes: Optional[str]
    deviations: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WorkflowStageCreate(BaseModel):
    batch_id: UUID = Field(..., description="Batch ID")
    equipment_id: Optional[UUID] = Field(None, description="Equipment ID for this stage")
    stage: WorkflowStage = Field(..., description="Workflow stage")
    stage_order: int = Field(..., ge=1, description="Order of this stage in the workflow")
    planned_start_time: Optional[datetime] = Field(None, description="Planned start time")
    planned_end_time: Optional[datetime] = Field(None, description="Planned end time")
    target_parameters: Optional[dict] = Field(None, description="Target process parameters")
    operator: str = Field(..., description="Operator assigned to this stage")
    supervisor: Optional[str] = Field(None, description="Supervisor for this stage")

class WorkflowStageUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Stage status")
    actual_start_time: Optional[datetime] = Field(None, description="Actual start time")
    actual_end_time: Optional[datetime] = Field(None, description="Actual end time")
    stage_yield: Optional[float] = Field(None, ge=0, le=100, description="Stage yield percentage")
    process_parameters: Optional[dict] = Field(None, description="Actual process parameters")
    operator: Optional[str] = Field(None, description="Operator")
    supervisor: Optional[str] = Field(None, description="Supervisor")
    batch_record_notes: Optional[str] = Field(None, description="Batch record notes")

class WorkflowStageDeviation(BaseModel):
    deviation_type: str = Field(..., description="Type of deviation")
    description: str = Field(..., description="Deviation description")
    severity: str = Field(..., description="Deviation severity")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    corrective_action: Optional[str] = Field(None, description="Corrective action")
    reported_by: str = Field(..., description="Person reporting the deviation")

class ProcessParametersUpdate(BaseModel):
    parameters: dict = Field(..., description="Process parameters as key-value pairs")
    recorded_by: str = Field(..., description="Person recording the parameters")
    notes: Optional[str] = Field(None, description="Additional notes")

@router.get("/stages", response_model=List[BatchWorkflowStageResponse])
async def get_all_workflow_stages(
    batch_id: Optional[UUID] = Query(None, description="Filter by batch ID"),
    stage: Optional[WorkflowStage] = Query(None, description="Filter by workflow stage"),
    status: Optional[str] = Query(None, description="Filter by status"),
    equipment_id: Optional[UUID] = Query(None, description="Filter by equipment ID"),
    operator: Optional[str] = Query(None, description="Filter by operator"),
    limit: int = Query(100, le=1000, description="Maximum number of stages to return"),
    workflow_service: WorkflowService = Depends()
):
    """Get list of workflow stages with optional filtering"""
    try:
        stages = await workflow_service.get_workflow_stages(
            batch_id=batch_id,
            stage=stage,
            status=status,
            equipment_id=equipment_id,
            operator=operator,
            limit=limit
        )
        return stages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow stages: {str(e)}")

@router.get("/stages/{stage_id}", response_model=BatchWorkflowStageResponse)
async def get_workflow_stage_details(
    stage_id: UUID,
    workflow_service: WorkflowService = Depends()
):
    """Get detailed information about a specific workflow stage"""
    try:
        stage = await workflow_service.get_workflow_stage_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Workflow stage not found")
        return stage
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow stage: {str(e)}")

@router.post("/stages", response_model=BatchWorkflowStageResponse)
async def create_workflow_stage(
    stage_data: WorkflowStageCreate,
    created_by: str = Query(..., description="User creating the stage"),
    workflow_service: WorkflowService = Depends(),
    audit_service: AuditService = Depends()
):
    """Create a new workflow stage for a batch"""
    try:
        # Create the workflow stage
        new_stage = await workflow_service.create_workflow_stage(stage_data)
        
        # Log audit trail
        await audit_service.log_workflow_stage_creation(new_stage.id, created_by)
        
        return new_stage
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow stage: {str(e)}")

@router.put("/stages/{stage_id}")
async def update_workflow_stage(
    stage_id: UUID,
    stage_update: WorkflowStageUpdate,
    updated_by: str = Query(..., description="User updating the stage"),
    workflow_service: WorkflowService = Depends(),
    audit_service: AuditService = Depends()
):
    """Update workflow stage information"""
    try:
        # Verify stage exists
        existing_stage = await workflow_service.get_workflow_stage_by_id(stage_id)
        if not existing_stage:
            raise HTTPException(status_code=404, detail="Workflow stage not found")
        
        # Update the stage
        updated_stage = await workflow_service.update_workflow_stage(stage_id, stage_update)
        
        # Log audit trail
        await audit_service.log_workflow_stage_update(stage_id, updated_by, stage_update.dict(exclude_none=True))
        
        return {
            "message": "Workflow stage updated successfully",
            "stage_id": stage_id,
            "updated_by": updated_by,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow stage: {str(e)}")

@router.post("/stages/{stage_id}/start")
async def start_workflow_stage(
    stage_id: UUID,
    started_by: str = Query(..., description="User starting the stage"),
    workflow_service: WorkflowService = Depends(),
    audit_service: AuditService = Depends()
):
    """Start a workflow stage"""
    try:
        # Verify stage exists and can be started
        stage = await workflow_service.get_workflow_stage_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Workflow stage not found")
        
        if stage.status not in ["pending", "planned"]:
            raise HTTPException(status_code=400, detail=f"Cannot start stage with status: {stage.status}")
        
        # Start the stage
        started_stage = await workflow_service.start_workflow_stage(stage_id, started_by)
        
        # Log audit trail
        await audit_service.log_workflow_stage_start(stage_id, started_by)
        
        return {
            "message": "Workflow stage started successfully",
            "stage_id": stage_id,
            "stage": started_stage.stage,
            "started_at": started_stage.actual_start_time,
            "started_by": started_by
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow stage: {str(e)}")

@router.post("/stages/{stage_id}/complete")
async def complete_workflow_stage(
    stage_id: UUID,
    completed_by: str = Query(..., description="User completing the stage"),
    stage_yield: Optional[float] = Query(None, ge=0, le=100, description="Stage yield percentage"),
    workflow_service: WorkflowService = Depends(),
    audit_service: AuditService = Depends()
):
    """Complete a workflow stage"""
    try:
        # Verify stage exists and can be completed
        stage = await workflow_service.get_workflow_stage_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Workflow stage not found")
        
        if stage.status != "in_progress":
            raise HTTPException(status_code=400, detail=f"Cannot complete stage with status: {stage.status}")
        
        # Complete the stage
        completed_stage = await workflow_service.complete_workflow_stage(stage_id, completed_by, stage_yield)
        
        # Log audit trail
        await audit_service.log_workflow_stage_completion(stage_id, completed_by)
        
        return {
            "message": "Workflow stage completed successfully",
            "stage_id": stage_id,
            "stage": completed_stage.stage,
            "completed_at": completed_stage.actual_end_time,
            "stage_yield": completed_stage.stage_yield,
            "completed_by": completed_by
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete workflow stage: {str(e)}")

@router.post("/stages/{stage_id}/deviations")
async def record_stage_deviation(
    stage_id: UUID,
    deviation: WorkflowStageDeviation,
    workflow_service: WorkflowService = Depends(),
    audit_service: AuditService = Depends()
):
    """Record a deviation for a workflow stage"""
    try:
        # Verify stage exists
        stage = await workflow_service.get_workflow_stage_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Workflow stage not found")
        
        # Record the deviation
        deviation_record = await workflow_service.record_stage_deviation(stage_id, deviation)
        
        # Log audit trail
        await audit_service.log_workflow_stage_deviation(stage_id, deviation.reported_by, deviation.dict())
        
        return {
            "message": "Stage deviation recorded successfully",
            "stage_id": stage_id,
            "deviation_id": deviation_record["deviation_id"],
            "reported_by": deviation.reported_by,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record stage deviation: {str(e)}")

@router.put("/stages/{stage_id}/parameters")
async def update_process_parameters(
    stage_id: UUID,
    parameters_update: ProcessParametersUpdate,
    workflow_service: WorkflowService = Depends(),
    audit_service: AuditService = Depends()
):
    """Update process parameters for a workflow stage"""
    try:
        # Verify stage exists
        stage = await workflow_service.get_workflow_stage_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Workflow stage not found")
        
        # Update process parameters
        updated_stage = await workflow_service.update_process_parameters(
            stage_id, 
            parameters_update.parameters,
            parameters_update.recorded_by
        )
        
        # Log audit trail
        await audit_service.log_process_parameters_update(
            stage_id, 
            parameters_update.recorded_by, 
            parameters_update.parameters
        )
        
        return {
            "message": "Process parameters updated successfully",
            "stage_id": stage_id,
            "parameters": parameters_update.parameters,
            "recorded_by": parameters_update.recorded_by,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update process parameters: {str(e)}")

@router.get("/batch/{batch_id}/workflow", response_model=List[BatchWorkflowStageResponse])
async def get_batch_workflow(
    batch_id: UUID,
    workflow_service: WorkflowService = Depends()
):
    """Get complete workflow for a batch"""
    try:
        workflow_stages = await workflow_service.get_batch_workflow(batch_id)
        return workflow_stages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch workflow: {str(e)}")

@router.get("/batch/{batch_id}/workflow/progress")
async def get_batch_workflow_progress(
    batch_id: UUID,
    workflow_service: WorkflowService = Depends()
):
    """Get workflow progress for a batch"""
    try:
        progress = await workflow_service.get_batch_workflow_progress(batch_id)
        
        return {
            "batch_id": batch_id,
            "progress": progress,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow progress: {str(e)}")

@router.get("/stage-types/{stage}/summary")
async def get_stage_type_summary(
    stage: WorkflowStage,
    days: int = Query(30, description="Number of days to analyze"),
    workflow_service: WorkflowService = Depends()
):
    """Get summary for a specific workflow stage type"""
    try:
        summary = await workflow_service.get_stage_type_summary(stage, days)
        
        return {
            "stage": stage,
            "analysis_period_days": days,
            "summary": summary,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stage summary: {str(e)}")

@router.get("/equipment/{equipment_id}/workflow-history")
async def get_equipment_workflow_history(
    equipment_id: UUID,
    days: int = Query(30, description="Number of days of history"),
    workflow_service: WorkflowService = Depends()
):
    """Get workflow history for specific equipment"""
    try:
        history = await workflow_service.get_equipment_workflow_history(equipment_id, days)
        
        return {
            "equipment_id": equipment_id,
            "history_period_days": days,
            "workflow_history": history,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve equipment workflow history: {str(e)}")

@router.get("/operators/{operator}/workload")
async def get_operator_workload(
    operator: str,
    days: int = Query(7, description="Number of days to analyze"),
    workflow_service: WorkflowService = Depends()
):
    """Get workload summary for an operator"""
    try:
        workload = await workflow_service.get_operator_workload(operator, days)
        
        return {
            "operator": operator,
            "analysis_period_days": days,
            "workload": workload,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve operator workload: {str(e)}")

@router.get("/reports/workflow-efficiency")
async def get_workflow_efficiency_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    stage: Optional[WorkflowStage] = Query(None, description="Filter by stage"),
    workflow_service: WorkflowService = Depends()
):
    """Get workflow efficiency report"""
    try:
        efficiency_report = await workflow_service.get_workflow_efficiency_report(
            start_date=start_date,
            end_date=end_date,
            stage=stage
        )
        
        return {
            "report_type": "workflow_efficiency",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "stage_filter": stage,
            "report": efficiency_report,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate workflow efficiency report: {str(e)}")

@router.get("/health/manufacturing-workflow")
async def manufacturing_workflow_health_check(
    workflow_service: WorkflowService = Depends()
):
    """Health check endpoint for manufacturing workflow system"""
    try:
        health_status = await workflow_service.perform_health_check()
        
        return {
            "service": "manufacturing_workflow",
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "details": health_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "service": "manufacturing_workflow",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }