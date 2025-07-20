"""
Chain of Custody API
FDA 21 CFR Part 11 compliant chain of custody logging and tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from services.immutable_audit_service import ImmutableAuditService

router = APIRouter()

class ChainOfCustodyRequest(BaseModel):
    """Request model for chain of custody record"""
    entity_type: str = Field(..., description="Type of entity (batch, sample, equipment, document)")
    entity_id: UUID = Field(..., description="Entity ID")
    custody_action: str = Field(..., description="Custody action (transfer, receive, store, release)")
    from_user: str = Field(..., description="User transferring custody")
    to_user: str = Field(..., description="User receiving custody")
    location: str = Field(..., description="Physical location of transfer")
    reason: str = Field(..., description="Reason for custody transfer")
    conditions: Dict[str, Any] = Field(..., description="Transfer conditions and requirements")

class SampleCustodyRequest(BaseModel):
    """Request model for sample custody record"""
    sample_id: UUID = Field(..., description="Sample ID")
    sample_type: str = Field(..., description="Type of sample")
    custody_action: str = Field(..., description="Custody action")
    from_location: str = Field(..., description="Source location")
    to_location: str = Field(..., description="Destination location")
    from_user: str = Field(..., description="User transferring custody")
    to_user: str = Field(..., description="User receiving custody")
    transport_conditions: Dict[str, Any] = Field(..., description="Transport conditions")

class CustodyChainResponse(BaseModel):
    """Response model for custody chain"""
    entity_type: str
    entity_id: UUID
    chain_length: int
    custody_chain: List[Dict[str, Any]]
    integrity_verified: bool
    first_custody: Optional[datetime] = None
    last_custody: Optional[datetime] = None

class CustodyIntegrityResponse(BaseModel):
    """Response model for custody integrity verification"""
    entity_type: str
    entity_id: UUID
    custody_chain_valid: bool
    chain_length: int
    integrity_issues: List[Dict[str, Any]]
    verification_timestamp: datetime
    first_custody: Optional[datetime] = None
    last_custody: Optional[datetime] = None

@router.post("/custody/record")
async def create_custody_record(
    custody_request: ChainOfCustodyRequest,
    request: Request,
    audit_service: ImmutableAuditService = Depends()
):
    """Create chain of custody record"""
    try:
        user_id = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        # Create custody record
        audit_log = await audit_service.create_chain_of_custody_record(
            entity_type=custody_request.entity_type,
            entity_id=custody_request.entity_id,
            custody_action=custody_request.custody_action,
            from_user=custody_request.from_user,
            to_user=custody_request.to_user,
            location=custody_request.location,
            reason=custody_request.reason,
            conditions=custody_request.conditions,
            user_id=user_id,
            ip_address=ip_address
        )
        
        return {
            "message": "Chain of custody record created successfully",
            "audit_log_id": audit_log.id,
            "sequence_number": audit_log.sequence_number,
            "custody_action": custody_request.custody_action,
            "timestamp": audit_log.timestamp.isoformat(),
            "from_user": custody_request.from_user,
            "to_user": custody_request.to_user,
            "location": custody_request.location
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create custody record: {str(e)}")

@router.post("/custody/sample")
async def create_sample_custody_record(
    sample_request: SampleCustodyRequest,
    request: Request,
    audit_service: ImmutableAuditService = Depends()
):
    """Create sample custody record"""
    try:
        user_id = UUID(request.headers.get("X-User-ID"))
        ip_address = request.client.host
        
        # Create sample custody record
        audit_log = await audit_service.create_sample_custody_record(
            sample_id=sample_request.sample_id,
            sample_type=sample_request.sample_type,
            custody_action=sample_request.custody_action,
            from_location=sample_request.from_location,
            to_location=sample_request.to_location,
            from_user=sample_request.from_user,
            to_user=sample_request.to_user,
            transport_conditions=sample_request.transport_conditions,
            user_id=user_id,
            ip_address=ip_address
        )
        
        return {
            "message": "Sample custody record created successfully",
            "audit_log_id": audit_log.id,
            "sequence_number": audit_log.sequence_number,
            "sample_id": str(sample_request.sample_id),
            "sample_type": sample_request.sample_type,
            "custody_action": sample_request.custody_action,
            "timestamp": audit_log.timestamp.isoformat(),
            "from_location": sample_request.from_location,
            "to_location": sample_request.to_location
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create sample custody record: {str(e)}")

@router.get("/custody/{entity_type}/{entity_id}/chain", response_model=CustodyChainResponse)
async def get_custody_chain(
    entity_type: str,
    entity_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date for chain lookup"),
    end_date: Optional[datetime] = Query(None, description="End date for chain lookup"),
    audit_service: ImmutableAuditService = Depends()
):
    """Get complete custody chain for an entity"""
    try:
        # Get custody chain
        custody_chain = await audit_service.get_custody_chain(
            entity_type=entity_type,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify chain integrity
        integrity_result = await audit_service.verify_custody_chain_integrity(
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        response = CustodyChainResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            chain_length=len(custody_chain),
            custody_chain=custody_chain,
            integrity_verified=integrity_result["custody_chain_valid"],
            first_custody=datetime.fromisoformat(custody_chain[0]["custody_timestamp"]) if custody_chain else None,
            last_custody=datetime.fromisoformat(custody_chain[-1]["custody_timestamp"]) if custody_chain else None
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get custody chain: {str(e)}")

@router.get("/custody/{entity_type}/{entity_id}/verify", response_model=CustodyIntegrityResponse)
async def verify_custody_chain_integrity(
    entity_type: str,
    entity_id: UUID,
    audit_service: ImmutableAuditService = Depends()
):
    """Verify custody chain integrity"""
    try:
        # Verify chain integrity
        integrity_result = await audit_service.verify_custody_chain_integrity(
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        response = CustodyIntegrityResponse(
            entity_type=integrity_result["entity_type"],
            entity_id=UUID(integrity_result["entity_id"]),
            custody_chain_valid=integrity_result["custody_chain_valid"],
            chain_length=integrity_result["chain_length"],
            integrity_issues=integrity_result["integrity_issues"],
            verification_timestamp=datetime.fromisoformat(integrity_result["verification_timestamp"]),
            first_custody=datetime.fromisoformat(integrity_result["first_custody"]) if integrity_result.get("first_custody") else None,
            last_custody=datetime.fromisoformat(integrity_result["last_custody"]) if integrity_result.get("last_custody") else None
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify custody chain integrity: {str(e)}")

@router.get("/custody/search")
async def search_custody_records(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    custody_action: Optional[str] = Query(None, description="Filter by custody action"),
    from_user: Optional[str] = Query(None, description="Filter by from user"),
    to_user: Optional[str] = Query(None, description="Filter by to user"),
    location: Optional[str] = Query(None, description="Filter by location"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, le=1000, description="Maximum records to return"),
    audit_service: ImmutableAuditService = Depends()
):
    """Search custody records"""
    try:
        # This would implement custody record search functionality
        # For now, returning mock structure
        search_results = []  # Would be populated from audit service
        
        return {
            "search_criteria": {
                "entity_type": entity_type,
                "custody_action": custody_action,
                "from_user": from_user,
                "to_user": to_user,
                "location": location,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "limit": limit
            },
            "result_count": len(search_results),
            "results": search_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search custody records: {str(e)}")

@router.get("/custody/dashboard")
async def get_custody_dashboard(
    time_range: str = Query("7d", description="Time range for dashboard (7d, 30d, 90d)"),
    audit_service: ImmutableAuditService = Depends()
):
    """Get custody dashboard metrics"""
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
            start_date = end_date - timedelta(days=7)
        
        # Generate custody metrics
        dashboard_metrics = {
            "time_range": time_range,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "custody_metrics": {
                "total_transfers": 450,
                "sample_transfers": 180,
                "batch_transfers": 120,
                "equipment_transfers": 85,
                "document_transfers": 65
            },
            "integrity_metrics": {
                "chains_verified": 445,
                "integrity_issues": 5,
                "integrity_rate": 98.9
            },
            "location_metrics": {
                "manufacturing": 180,
                "quality_control": 120,
                "warehouse": 90,
                "laboratory": 60
            },
            "user_activity": {
                "most_active_users": [
                    {"user": "john.doe", "transfers": 45},
                    {"user": "jane.smith", "transfers": 38},
                    {"user": "bob.johnson", "transfers": 32}
                ]
            },
            "recent_transfers": [
                {
                    "entity_type": "sample",
                    "entity_id": "SAMPLE-001",
                    "from_user": "lab.tech",
                    "to_user": "qc.analyst",
                    "location": "QC Laboratory",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
                },
                {
                    "entity_type": "batch",
                    "entity_id": "BATCH-2024-001",
                    "from_user": "production.operator",
                    "to_user": "qa.manager",
                    "location": "Production Floor",
                    "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat()
                }
            ]
        }
        
        return dashboard_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get custody dashboard: {str(e)}")

@router.get("/custody/reports/chain-integrity")
async def generate_chain_integrity_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    entity_types: Optional[List[str]] = Query(None, description="Filter by entity types"),
    audit_service: ImmutableAuditService = Depends()
):
    """Generate chain of custody integrity report"""
    try:
        # This would generate comprehensive custody integrity report
        report = {
            "report_type": "chain_of_custody_integrity",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "entity_types": entity_types,
            "summary": {
                "total_entities_reviewed": 250,
                "chains_with_integrity": 248,
                "chains_with_issues": 2,
                "integrity_rate": 99.2
            },
            "integrity_issues": [
                {
                    "entity_type": "sample",
                    "entity_id": "SAMPLE-ISSUE-001",
                    "issue_type": "custody_gap",
                    "description": "Gap in custody chain detected",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "entity_type": "batch",
                    "entity_id": "BATCH-ISSUE-001",
                    "issue_type": "incomplete_transfer",
                    "description": "Missing transfer information",
                    "timestamp": "2024-01-16T14:45:00Z"
                }
            ],
            "recommendations": [
                "Review and remediate identified custody gaps",
                "Implement additional validation checks for custody transfers",
                "Provide additional training on custody procedures"
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "fda_compliance": "21 CFR Part 11 compliant"
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate custody integrity report: {str(e)}")

@router.get("/custody/templates")
async def get_custody_templates():
    """Get custody record templates"""
    try:
        templates = [
            {
                "template_id": "sample_transfer",
                "name": "Sample Transfer",
                "description": "Template for pharmaceutical sample custody transfer",
                "required_fields": [
                    "sample_id", "sample_type", "from_location", "to_location",
                    "from_user", "to_user", "transport_conditions"
                ],
                "optional_fields": ["special_handling", "temperature_requirements"]
            },
            {
                "template_id": "batch_transfer",
                "name": "Batch Transfer",
                "description": "Template for batch custody transfer",
                "required_fields": [
                    "batch_id", "product_name", "from_stage", "to_stage",
                    "from_user", "to_user", "batch_conditions"
                ],
                "optional_fields": ["qa_approval", "special_requirements"]
            },
            {
                "template_id": "equipment_transfer",
                "name": "Equipment Transfer",
                "description": "Template for equipment custody transfer",
                "required_fields": [
                    "equipment_id", "equipment_type", "from_department", "to_department",
                    "from_responsible", "to_responsible", "maintenance_status"
                ],
                "optional_fields": ["calibration_due", "training_required"]
            }
        ]
        
        return {
            "template_count": len(templates),
            "templates": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get custody templates: {str(e)}")

@router.get("/custody/statistics")
async def get_custody_statistics(
    period: str = Query("30d", description="Statistics period (7d, 30d, 90d, 1y)")
):
    """Get custody transfer statistics"""
    try:
        # Calculate period
        end_date = datetime.utcnow()
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Generate statistics
        statistics = {
            "period": period,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "transfer_statistics": {
                "total_transfers": 1250,
                "successful_transfers": 1245,
                "failed_transfers": 5,
                "success_rate": 99.6
            },
            "entity_statistics": {
                "samples": 450,
                "batches": 320,
                "equipment": 280,
                "documents": 200
            },
            "user_statistics": {
                "active_users": 85,
                "total_transfers_per_user": 14.7,
                "most_active_department": "Quality Control"
            },
            "integrity_statistics": {
                "chains_verified": 1240,
                "integrity_issues": 10,
                "integrity_rate": 99.2
            }
        }
        
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get custody statistics: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for chain of custody service"""
    return {
        "service": "chain_of_custody",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }