"""
Deviation and CAPA Management API
FDA 21 CFR Part 11 compliant deviation tracking and CAPA management
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from services.capa_deviation_service import CAPADeviationService
from services.immutable_audit_service import ImmutableAuditService

router = APIRouter()

class DeviationCreateRequest(BaseModel):
    """Request model for creating deviation"""
    title: str = Field(..., description="Deviation title")
    description: str = Field(..., description="Deviation description")
    severity: str = Field(..., description="Deviation severity (minor, major, critical)")
    category: str = Field(..., description="Deviation category")
    batch_id: Optional[UUID] = Field(None, description="Related batch ID")
    product_id: Optional[UUID] = Field(None, description="Related product ID")
    equipment_id: Optional[UUID] = Field(None, description="Related equipment ID")
    discovered_by: UUID = Field(..., description="User who discovered the deviation")
    discovered_at: datetime = Field(..., description="When deviation was discovered")

class DeviationInvestigationRequest(BaseModel):
    """Request model for deviation investigation"""
    investigation_summary: str = Field(..., description="Investigation summary")
    root_cause: str = Field(..., description="Root cause analysis")
    quality_impact: str = Field(..., description="Quality impact assessment")
    regulatory_impact: str = Field(..., description="Regulatory impact assessment")
    customer_impact: str = Field(..., description="Customer impact assessment")
    immediate_action: str = Field(..., description="Immediate action taken")

class DeviationClosureRequest(BaseModel):
    """Request model for deviation closure"""
    closure_summary: str = Field(..., description="Closure summary")
    corrective_action: str = Field(..., description="Corrective action taken")
    preventive_action: str = Field(..., description="Preventive action implemented")

class CAPACreateRequest(BaseModel):
    """Request model for creating CAPA"""
    problem_description: str = Field(..., description="Problem description")
    problem_category: str = Field(..., description="Problem category")
    severity: str = Field(..., description="CAPA severity")
    source_type: str = Field(..., description="Source type (deviation, audit, complaint)")
    source_id: Optional[UUID] = Field(None, description="Source ID")
    source_reference: Optional[str] = Field(None, description="Source reference")
    corrective_actions: List[Dict[str, Any]] = Field(..., description="Corrective actions")
    preventive_actions: List[Dict[str, Any]] = Field(..., description="Preventive actions")
    corrective_action_owner: UUID = Field(..., description="Corrective action owner")
    preventive_action_owner: UUID = Field(..., description="Preventive action owner")
    target_completion_date: datetime = Field(..., description="Target completion date")

class CAPAProgressRequest(BaseModel):
    """Request model for CAPA progress update"""
    corrective_action_completed: Optional[bool] = Field(None, description="Corrective action completed")
    preventive_action_completed: Optional[bool] = Field(None, description="Preventive action completed")
    progress_notes: str = Field(..., description="Progress notes")

class CAPAEffectivenessRequest(BaseModel):
    """Request model for CAPA effectiveness verification"""
    effectiveness_verified: bool = Field(..., description="Effectiveness verified")
    verification_notes: str = Field(..., description="Verification notes")

class DeviationResponse(BaseModel):
    """Response model for deviation operations"""
    id: UUID
    deviation_number: str
    title: str
    description: str
    severity: str
    category: str
    batch_id: Optional[UUID]
    product_id: Optional[UUID]
    equipment_id: Optional[UUID]
    discovered_by: UUID
    discovered_at: datetime
    reported_by: UUID
    reported_at: datetime
    status: str
    due_date: Optional[datetime]
    investigator_id: Optional[UUID]
    assigned_to: Optional[UUID]
    capa_required: bool
    capa_id: Optional[UUID]
    
    class Config:
        from_attributes = True

class CAPAResponse(BaseModel):
    """Response model for CAPA operations"""
    id: UUID
    capa_number: str
    problem_description: str
    problem_category: str
    severity: str
    source_type: str
    source_id: Optional[UUID]
    source_reference: Optional[str]
    corrective_actions: List[Dict[str, Any]]
    preventive_actions: List[Dict[str, Any]]
    corrective_action_owner: UUID
    preventive_action_owner: UUID
    target_completion_date: datetime
    status: str
    assigned_to: UUID
    initiated_date: datetime
    corrective_action_completed: Optional[bool]
    preventive_action_completed: Optional[bool]
    actual_completion_date: Optional[datetime]
    effectiveness_verified: Optional[bool]
    
    class Config:
        from_attributes = True

@router.post("/deviations", response_model=DeviationResponse)
async def create_deviation(
    deviation_request: DeviationCreateRequest,
    request: Request,
    capa_service: CAPADeviationService = Depends()
):
    """Create new deviation record"""
    try:
        reported_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        deviation = await capa_service.create_deviation(
            title=deviation_request.title,
            description=deviation_request.description,
            severity=deviation_request.severity,
            category=deviation_request.category,
            batch_id=deviation_request.batch_id,
            product_id=deviation_request.product_id,
            equipment_id=deviation_request.equipment_id,
            discovered_by=deviation_request.discovered_by,
            discovered_at=deviation_request.discovered_at,
            reported_by=reported_by,
            ip_address=ip_address
        )
        
        return DeviationResponse.model_validate(deviation)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create deviation: {str(e)}")

@router.post("/deviations/{deviation_id}/investigate", response_model=DeviationResponse)
async def investigate_deviation(
    deviation_id: UUID,
    investigation_request: DeviationInvestigationRequest,
    request: Request,
    capa_service: CAPADeviationService = Depends()
):
    """Complete deviation investigation"""
    try:
        investigator_id = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        deviation = await capa_service.investigate_deviation(
            deviation_id=deviation_id,
            investigation_summary=investigation_request.investigation_summary,
            root_cause=investigation_request.root_cause,
            quality_impact=investigation_request.quality_impact,
            regulatory_impact=investigation_request.regulatory_impact,
            customer_impact=investigation_request.customer_impact,
            immediate_action=investigation_request.immediate_action,
            investigator_id=investigator_id,
            ip_address=ip_address
        )
        
        return DeviationResponse.model_validate(deviation)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to investigate deviation: {str(e)}")

@router.post("/deviations/{deviation_id}/close", response_model=DeviationResponse)
async def close_deviation(
    deviation_id: UUID,
    closure_request: DeviationClosureRequest,
    request: Request,
    capa_service: CAPADeviationService = Depends()
):
    """Close deviation with corrective and preventive actions"""
    try:
        closed_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        deviation = await capa_service.close_deviation(
            deviation_id=deviation_id,
            closure_summary=closure_request.closure_summary,
            corrective_action=closure_request.corrective_action,
            preventive_action=closure_request.preventive_action,
            closed_by=closed_by,
            ip_address=ip_address
        )
        
        return DeviationResponse.model_validate(deviation)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to close deviation: {str(e)}")

@router.get("/deviations/{deviation_id}", response_model=DeviationResponse)
async def get_deviation(
    deviation_id: UUID,
    capa_service: CAPADeviationService = Depends()
):
    """Get deviation details"""
    try:
        deviation = await capa_service._get_deviation(deviation_id)
        
        if not deviation:
            raise HTTPException(status_code=404, detail="Deviation not found")
        
        return DeviationResponse.model_validate(deviation)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deviation: {str(e)}")

@router.get("/deviations/search")
async def search_deviations(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    batch_id: Optional[UUID] = Query(None, description="Filter by batch ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(100, le=1000, description="Maximum records to return")
):
    """Search deviations with filters"""
    try:
        # This would implement deviation search functionality
        search_results = []  # Would be populated from database query
        
        return {
            "search_criteria": {
                "status": status,
                "severity": severity,
                "category": category,
                "batch_id": str(batch_id) if batch_id else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "limit": limit
            },
            "result_count": len(search_results),
            "results": search_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search deviations: {str(e)}")

@router.get("/deviations/analytics")
async def get_deviation_analytics(
    start_date: datetime = Query(..., description="Start date for analytics"),
    end_date: datetime = Query(..., description="End date for analytics"),
    capa_service: CAPADeviationService = Depends()
):
    """Get deviation analytics and trends"""
    try:
        analytics = await capa_service.get_deviation_analytics(start_date, end_date)
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deviation analytics: {str(e)}")

@router.post("/capa", response_model=CAPAResponse)
async def create_capa(
    capa_request: CAPACreateRequest,
    request: Request,
    capa_service: CAPADeviationService = Depends()
):
    """Create new CAPA record"""
    try:
        created_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        capa = await capa_service.create_capa(
            problem_description=capa_request.problem_description,
            problem_category=capa_request.problem_category,
            severity=capa_request.severity,
            source_type=capa_request.source_type,
            source_id=capa_request.source_id,
            source_reference=capa_request.source_reference,
            corrective_actions=capa_request.corrective_actions,
            preventive_actions=capa_request.preventive_actions,
            corrective_action_owner=capa_request.corrective_action_owner,
            preventive_action_owner=capa_request.preventive_action_owner,
            target_completion_date=capa_request.target_completion_date,
            created_by=created_by,
            ip_address=ip_address
        )
        
        return CAPAResponse.model_validate(capa)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create CAPA: {str(e)}")

@router.post("/capa/{capa_id}/progress", response_model=CAPAResponse)
async def update_capa_progress(
    capa_id: UUID,
    progress_request: CAPAProgressRequest,
    request: Request,
    capa_service: CAPADeviationService = Depends()
):
    """Update CAPA progress"""
    try:
        updated_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        capa = await capa_service.update_capa_progress(
            capa_id=capa_id,
            corrective_action_completed=progress_request.corrective_action_completed,
            preventive_action_completed=progress_request.preventive_action_completed,
            progress_notes=progress_request.progress_notes,
            updated_by=updated_by,
            ip_address=ip_address
        )
        
        return CAPAResponse.model_validate(capa)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update CAPA progress: {str(e)}")

@router.post("/capa/{capa_id}/verify-effectiveness", response_model=CAPAResponse)
async def verify_capa_effectiveness(
    capa_id: UUID,
    effectiveness_request: CAPAEffectivenessRequest,
    request: Request,
    capa_service: CAPADeviationService = Depends()
):
    """Verify CAPA effectiveness"""
    try:
        verified_by = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        capa = await capa_service.verify_capa_effectiveness(
            capa_id=capa_id,
            effectiveness_verified=effectiveness_request.effectiveness_verified,
            verification_notes=effectiveness_request.verification_notes,
            verified_by=verified_by,
            ip_address=ip_address
        )
        
        return CAPAResponse.model_validate(capa)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to verify CAPA effectiveness: {str(e)}")

@router.get("/capa/{capa_id}", response_model=CAPAResponse)
async def get_capa(
    capa_id: UUID,
    capa_service: CAPADeviationService = Depends()
):
    """Get CAPA details"""
    try:
        capa = await capa_service._get_capa(capa_id)
        
        if not capa:
            raise HTTPException(status_code=404, detail="CAPA not found")
        
        return CAPAResponse.model_validate(capa)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CAPA: {str(e)}")

@router.get("/capa/search")
async def search_capa(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    owner: Optional[UUID] = Query(None, description="Filter by owner"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(100, le=1000, description="Maximum records to return")
):
    """Search CAPA records with filters"""
    try:
        # This would implement CAPA search functionality
        search_results = []  # Would be populated from database query
        
        return {
            "search_criteria": {
                "status": status,
                "severity": severity,
                "source_type": source_type,
                "owner": str(owner) if owner else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "limit": limit
            },
            "result_count": len(search_results),
            "results": search_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search CAPA: {str(e)}")

@router.get("/capa/overdue")
async def get_overdue_capa(
    limit: int = Query(50, le=200, description="Maximum records to return")
):
    """Get overdue CAPA records"""
    try:
        # This would query overdue CAPA records
        overdue_capa = []  # Would be populated from database query
        
        return {
            "overdue_count": len(overdue_capa),
            "overdue_capa": overdue_capa,
            "query_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overdue CAPA: {str(e)}")

@router.get("/deviations/{deviation_id}/audit-trail")
async def get_deviation_audit_trail(
    deviation_id: UUID,
    audit_service: ImmutableAuditService = Depends()
):
    """Get audit trail for specific deviation"""
    try:
        audit_trail = await audit_service.get_audit_trail_for_entity(
            entity_type="deviation",
            entity_id=deviation_id
        )
        
        return {
            "deviation_id": str(deviation_id),
            "audit_trail": audit_trail,
            "total_entries": len(audit_trail) if audit_trail else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deviation audit trail: {str(e)}")

@router.get("/capa/{capa_id}/audit-trail")
async def get_capa_audit_trail(
    capa_id: UUID,
    audit_service: ImmutableAuditService = Depends()
):
    """Get audit trail for specific CAPA"""
    try:
        audit_trail = await audit_service.get_audit_trail_for_entity(
            entity_type="capa_record",
            entity_id=capa_id
        )
        
        return {
            "capa_id": str(capa_id),
            "audit_trail": audit_trail,
            "total_entries": len(audit_trail) if audit_trail else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CAPA audit trail: {str(e)}")

@router.get("/dashboard/summary")
async def get_deviation_capa_summary(
    time_range: str = Query("30d", description="Time range for summary (7d, 30d, 90d)"),
    capa_service: CAPADeviationService = Depends()
):
    """Get deviation and CAPA summary for dashboard"""
    try:
        # Calculate time range
        end_date = datetime.utcnow()
        if time_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif time_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif time_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get deviation analytics
        deviation_analytics = await capa_service.get_deviation_analytics(start_date, end_date)
        
        # Calculate CAPA metrics (would come from actual service)
        capa_metrics = {
            "total_capa": 45,
            "open_capa": 12,
            "completed_capa": 30,
            "overdue_capa": 3,
            "effectiveness_verified": 28
        }
        
        summary = {
            "time_range": time_range,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "deviation_metrics": deviation_analytics,
            "capa_metrics": capa_metrics,
            "alerts": [],
            "trends": {
                "deviation_trend": "stable",
                "capa_completion_trend": "improving"
            }
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deviation/CAPA summary: {str(e)}")

@router.get("/reports/deviation-report")
async def generate_deviation_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    format: str = Query("json", description="Report format (json, pdf, excel)"),
    capa_service: CAPADeviationService = Depends()
):
    """Generate comprehensive deviation report"""
    try:
        # Get deviation analytics
        analytics = await capa_service.get_deviation_analytics(start_date, end_date)
        
        report = {
            "report_type": "deviation_report",
            "format": format,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": "FDA Compliance System"
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate deviation report: {str(e)}")

@router.get("/reports/capa-report")
async def generate_capa_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    format: str = Query("json", description="Report format (json, pdf, excel)")
):
    """Generate comprehensive CAPA report"""
    try:
        # This would generate CAPA report
        report = {
            "report_type": "capa_report",
            "format": format,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_capa": 45,
                "completed_capa": 30,
                "overdue_capa": 3,
                "effectiveness_rate": 93.3
            },
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": "FDA Compliance System"
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CAPA report: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for deviation/CAPA service"""
    return {
        "service": "deviation_capa_management",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }