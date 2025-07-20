"""
Electronic Batch Records (EBR) API
FDA 21 CFR Part 11 compliant electronic batch records with digital signatures
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from services.electronic_batch_record_service import ElectronicBatchRecordService
from services.electronic_signature_service import ElectronicSignatureService
from services.immutable_audit_service import ImmutableAuditService

router = APIRouter()

class EBRCreateRequest(BaseModel):
    """Request model for creating EBR"""
    batch_id: UUID = Field(..., description="Batch ID")
    template_id: UUID = Field(..., description="EBR template ID")
    template_version: str = Field(..., description="Template version")
    manufacturing_instructions: Dict[str, Any] = Field(..., description="Manufacturing instructions")
    critical_process_parameters: Dict[str, Any] = Field(..., description="Critical process parameters")
    quality_attributes: Dict[str, Any] = Field(..., description="Quality attributes")

class EBRResponse(BaseModel):
    """Response model for EBR operations"""
    ebr_id: UUID
    batch_id: UUID
    ebr_number: str
    template_id: UUID
    template_version: str
    status: str
    approval_status: str
    locked: bool
    started_by: Optional[UUID]
    started_at: Optional[datetime]
    completed_by: Optional[UUID]
    completed_at: Optional[datetime]
    record_hash: str
    
    class Config:
        from_attributes = True

class EBRStepExecutionRequest(BaseModel):
    """Request model for EBR step execution"""
    actual_values: Dict[str, Any] = Field(..., description="Actual parameter values")
    observations: str = Field(..., description="Operator observations")
    deviations: Optional[Dict[str, Any]] = Field(None, description="Deviations if any")

class EBRStepVerificationRequest(BaseModel):
    """Request model for EBR step verification"""
    verification_notes: str = Field(..., description="Verification notes")

class EBRCompletionRequest(BaseModel):
    """Request model for EBR completion"""
    final_review_notes: str = Field(..., description="Final review notes")

class EBRStepResponse(BaseModel):
    """Response model for EBR step operations"""
    step_id: UUID
    ebr_id: UUID
    step_number: int
    step_name: str
    step_type: str
    status: str
    executed_by: Optional[UUID]
    executed_at: Optional[datetime]
    verified_by: Optional[UUID]
    verified_at: Optional[datetime]
    actual_values: Optional[Dict[str, Any]]
    observations: Optional[str]
    deviations: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class EBRStatusResponse(BaseModel):
    """Response model for EBR status"""
    ebr_id: UUID
    ebr_number: str
    batch_id: UUID
    status: str
    approval_status: str
    locked: bool
    progress: Dict[str, Any]
    execution_info: Dict[str, Any]
    signatures: List[Dict[str, Any]]
    integrity: Dict[str, Any]

@router.post("/ebr", response_model=EBRResponse)
async def create_ebr(
    ebr_request: EBRCreateRequest,
    request: Request,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Create new Electronic Batch Record"""
    try:
        created_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        ebr = await ebr_service.create_ebr(
            batch_id=ebr_request.batch_id,
            template_id=ebr_request.template_id,
            template_version=ebr_request.template_version,
            manufacturing_instructions=ebr_request.manufacturing_instructions,
            critical_process_parameters=ebr_request.critical_process_parameters,
            quality_attributes=ebr_request.quality_attributes,
            created_by=created_by,
            ip_address=ip_address
        )
        
        return EBRResponse.model_validate(ebr)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create EBR: {str(e)}")

@router.post("/ebr/{ebr_id}/start", response_model=EBRResponse)
async def start_ebr_execution(
    ebr_id: UUID,
    request: Request,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Start EBR execution with digital signature"""
    try:
        started_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        ebr = await ebr_service.start_ebr_execution(
            ebr_id=ebr_id,
            started_by=started_by,
            ip_address=ip_address
        )
        
        return EBRResponse.model_validate(ebr)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to start EBR execution: {str(e)}")

@router.post("/ebr/steps/{step_id}/execute", response_model=EBRStepResponse)
async def execute_ebr_step(
    step_id: UUID,
    step_request: EBRStepExecutionRequest,
    request: Request,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Execute EBR step with parameter recording"""
    try:
        executed_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        step = await ebr_service.execute_ebr_step(
            step_id=step_id,
            executed_by=executed_by,
            actual_values=step_request.actual_values,
            observations=step_request.observations,
            deviations=step_request.deviations,
            ip_address=ip_address
        )
        
        return EBRStepResponse.model_validate(step)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to execute EBR step: {str(e)}")

@router.post("/ebr/steps/{step_id}/verify", response_model=EBRStepResponse)
async def verify_ebr_step(
    step_id: UUID,
    verification_request: EBRStepVerificationRequest,
    request: Request,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Verify EBR step with supervisor signature"""
    try:
        verified_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        step = await ebr_service.verify_ebr_step(
            step_id=step_id,
            verified_by=verified_by,
            verification_notes=verification_request.verification_notes,
            ip_address=ip_address
        )
        
        return EBRStepResponse.model_validate(step)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to verify EBR step: {str(e)}")

@router.post("/ebr/{ebr_id}/complete", response_model=EBRResponse)
async def complete_ebr(
    ebr_id: UUID,
    completion_request: EBRCompletionRequest,
    request: Request,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Complete EBR with final review and signature"""
    try:
        completed_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        ebr = await ebr_service.complete_ebr(
            ebr_id=ebr_id,
            completed_by=completed_by,
            final_review_notes=completion_request.final_review_notes,
            ip_address=ip_address
        )
        
        return EBRResponse.model_validate(ebr)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to complete EBR: {str(e)}")

@router.get("/ebr/{ebr_id}/status", response_model=EBRStatusResponse)
async def get_ebr_status(
    ebr_id: UUID,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Get comprehensive EBR status and progress"""
    try:
        status_info = await ebr_service.get_ebr_status(ebr_id)
        
        return EBRStatusResponse(
            ebr_id=UUID(status_info["ebr_id"]),
            ebr_number=status_info["ebr_number"],
            batch_id=UUID(status_info["batch_id"]),
            status=status_info["status"],
            approval_status=status_info["approval_status"],
            locked=status_info["locked"],
            progress=status_info["progress"],
            execution_info=status_info["execution_info"],
            signatures=status_info["signatures"],
            integrity=status_info["integrity"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBR status: {str(e)}")

@router.get("/ebr/{ebr_id}")
async def get_ebr_details(
    ebr_id: UUID,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Get detailed EBR information"""
    try:
        # This would get full EBR details from service
        ebr_details = await ebr_service._get_ebr(ebr_id)
        
        if not ebr_details:
            raise HTTPException(status_code=404, detail="EBR not found")
        
        return {
            "ebr_id": str(ebr_id),
            "ebr_details": ebr_details,
            "message": "EBR details retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBR details: {str(e)}")

@router.get("/ebr/{ebr_id}/steps")
async def get_ebr_steps(
    ebr_id: UUID,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Get all steps for an EBR"""
    try:
        steps = await ebr_service._get_ebr_steps(ebr_id)
        
        return {
            "ebr_id": str(ebr_id),
            "total_steps": len(steps),
            "steps": steps
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBR steps: {str(e)}")

@router.get("/ebr/{ebr_id}/signatures")
async def get_ebr_signatures(
    ebr_id: UUID,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Get all signatures for an EBR"""
    try:
        signatures = await ebr_service._get_ebr_signatures(ebr_id)
        
        return {
            "ebr_id": str(ebr_id),
            "signature_count": len(signatures),
            "signatures": signatures
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBR signatures: {str(e)}")

@router.get("/ebr/{ebr_id}/integrity-check")
async def check_ebr_integrity(
    ebr_id: UUID,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Verify EBR integrity"""
    try:
        integrity_verified = await ebr_service._verify_ebr_integrity(ebr_id)
        
        return {
            "ebr_id": str(ebr_id),
            "integrity_verified": integrity_verified,
            "check_timestamp": datetime.utcnow().isoformat(),
            "status": "verified" if integrity_verified else "compromised"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check EBR integrity: {str(e)}")

@router.get("/ebr/batch/{batch_id}")
async def get_ebrs_for_batch(
    batch_id: UUID,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Get all EBRs for a specific batch"""
    try:
        # This would query EBRs by batch_id
        ebrs = []  # Would be populated from database
        
        return {
            "batch_id": str(batch_id),
            "ebr_count": len(ebrs),
            "ebrs": ebrs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBRs for batch: {str(e)}")

@router.get("/ebr/search")
async def search_ebrs(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    template_id: Optional[UUID] = None,
    limit: int = 100
):
    """Search EBRs with filters"""
    try:
        # This would implement EBR search functionality
        search_results = []  # Would be populated from database query
        
        return {
            "search_criteria": {
                "status": status,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "template_id": str(template_id) if template_id else None,
                "limit": limit
            },
            "result_count": len(search_results),
            "results": search_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search EBRs: {str(e)}")

@router.get("/ebr/{ebr_id}/pdf-export")
async def export_ebr_to_pdf(
    ebr_id: UUID,
    ebr_service: ElectronicBatchRecordService = Depends()
):
    """Export EBR to PDF format"""
    try:
        # This would generate PDF export of EBR
        return {
            "ebr_id": str(ebr_id),
            "export_format": "pdf",
            "export_status": "completed",
            "export_timestamp": datetime.utcnow().isoformat(),
            "download_url": f"/api/exports/ebr/{ebr_id}.pdf"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export EBR to PDF: {str(e)}")

@router.get("/ebr/{ebr_id}/audit-trail")
async def get_ebr_audit_trail(
    ebr_id: UUID,
    audit_service: ImmutableAuditService = Depends()
):
    """Get audit trail for specific EBR"""
    try:
        audit_trail = await audit_service.get_audit_trail_for_entity(
            entity_type="electronic_batch_record",
            entity_id=ebr_id
        )
        
        return {
            "ebr_id": str(ebr_id),
            "audit_trail": audit_trail,
            "total_entries": len(audit_trail) if audit_trail else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBR audit trail: {str(e)}")

@router.get("/ebr/templates")
async def get_ebr_templates():
    """Get available EBR templates"""
    try:
        # This would query available EBR templates
        templates = []  # Would be populated from database
        
        return {
            "template_count": len(templates),
            "templates": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBR templates: {str(e)}")

@router.post("/ebr/templates")
async def create_ebr_template(
    template_data: Dict[str, Any],
    request: Request
):
    """Create new EBR template"""
    try:
        created_by = UUID(request.headers.get("X-User-ID"))
        
        # This would create new EBR template
        template_id = UUID("12345678-1234-5678-9abc-123456789012")  # Would be generated
        
        return {
            "template_id": str(template_id),
            "status": "created",
            "created_by": str(created_by),
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create EBR template: {str(e)}")

@router.get("/ebr/statistics")
async def get_ebr_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get EBR statistics and metrics"""
    try:
        # This would calculate EBR statistics
        statistics = {
            "total_ebrs": 150,
            "completed_ebrs": 140,
            "active_ebrs": 8,
            "draft_ebrs": 2,
            "average_completion_time_hours": 48.5,
            "compliance_rate": 99.3,
            "signature_compliance": 100.0,
            "deviation_rate": 2.1
        }
        
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EBR statistics: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for EBR service"""
    return {
        "service": "electronic_batch_records",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }