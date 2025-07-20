"""
Quality Control API
GMP-compliant quality control checkpoints and testing results
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

from models.manufacturing import QualityTest, QualityTestStatus
from services.quality_service import QualityService
from services.audit_service import AuditService
from services.alert_manager import AlertManager

router = APIRouter()

# Pydantic models for API
class QualityTestResponse(BaseModel):
    id: UUID
    batch_id: UUID
    test_type: str
    test_method: str
    specification: str
    result_value: Optional[str]
    result_units: Optional[str]
    pass_fail: Optional[bool]
    status: str
    lower_limit: Optional[float]
    upper_limit: Optional[float]
    target_value: Optional[float]
    tested_by: str
    reviewed_by: Optional[str]
    approved_by: Optional[str]
    test_date: datetime
    reviewed_date: Optional[datetime]
    approved_date: Optional[datetime]
    test_notes: Optional[str]
    deviation_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class QualityTestCreate(BaseModel):
    batch_id: UUID = Field(..., description="Batch ID being tested")
    test_type: str = Field(..., description="Type of quality test")
    test_method: str = Field(..., description="Test method/procedure")
    specification: str = Field(..., description="Test specification/requirements")
    lower_limit: Optional[float] = Field(None, description="Lower specification limit")
    upper_limit: Optional[float] = Field(None, description="Upper specification limit")
    target_value: Optional[float] = Field(None, description="Target value")
    tested_by: str = Field(..., description="Person performing the test")
    test_notes: Optional[str] = Field(None, description="Test notes or observations")

class QualityTestResult(BaseModel):
    result_value: str = Field(..., description="Test result value")
    result_units: Optional[str] = Field(None, description="Result units")
    pass_fail: bool = Field(..., description="Pass/fail determination")
    test_notes: Optional[str] = Field(None, description="Additional test notes")
    deviation_reason: Optional[str] = Field(None, description="Reason for deviation if failed")

class QualityTestReview(BaseModel):
    reviewed_by: str = Field(..., description="Person reviewing the test")
    review_notes: Optional[str] = Field(None, description="Review notes")
    approved: bool = Field(..., description="Test approved/rejected")

class QualityTestApproval(BaseModel):
    approved_by: str = Field(..., description="Person approving the test")
    approval_notes: Optional[str] = Field(None, description="Approval notes")

class QualitySpecification(BaseModel):
    test_type: str = Field(..., description="Type of quality test")
    test_method: str = Field(..., description="Test method/procedure")
    specification: str = Field(..., description="Test specification")
    lower_limit: Optional[float] = Field(None, description="Lower limit")
    upper_limit: Optional[float] = Field(None, description="Upper limit")
    target_value: Optional[float] = Field(None, description="Target value")
    units: str = Field(..., description="Measurement units")
    frequency: str = Field(..., description="Testing frequency")
    criticality: str = Field(..., description="Critical/non-critical classification")

@router.get("/tests", response_model=List[QualityTestResponse])
async def get_all_quality_tests(
    batch_id: Optional[UUID] = Query(None, description="Filter by batch ID"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    status: Optional[QualityTestStatus] = Query(None, description="Filter by test status"),
    start_date: Optional[datetime] = Query(None, description="Filter tests after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter tests before this date"),
    limit: int = Query(100, le=1000, description="Maximum number of tests to return"),
    quality_service: QualityService = Depends()
):
    """Get list of quality tests with optional filtering"""
    try:
        tests = await quality_service.get_quality_tests(
            batch_id=batch_id,
            test_type=test_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return tests
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quality tests: {str(e)}")

@router.get("/tests/{test_id}", response_model=QualityTestResponse)
async def get_quality_test_details(
    test_id: UUID,
    quality_service: QualityService = Depends()
):
    """Get detailed information about a specific quality test"""
    try:
        test = await quality_service.get_quality_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Quality test not found")
        return test
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quality test: {str(e)}")

@router.post("/tests", response_model=QualityTestResponse)
async def create_quality_test(
    test_data: QualityTestCreate,
    quality_service: QualityService = Depends(),
    audit_service: AuditService = Depends()
):
    """Create a new quality test for a batch"""
    try:
        # Create the quality test
        new_test = await quality_service.create_quality_test(test_data)
        
        # Log audit trail
        await audit_service.log_quality_test_creation(new_test.id, test_data.tested_by)
        
        return new_test
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create quality test: {str(e)}")

@router.put("/tests/{test_id}/results")
async def submit_test_results(
    test_id: UUID,
    test_result: QualityTestResult,
    quality_service: QualityService = Depends(),
    audit_service: AuditService = Depends(),
    alert_manager: AlertManager = Depends()
):
    """Submit results for a quality test"""
    try:
        # Verify test exists and is in progress
        test = await quality_service.get_quality_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Quality test not found")
        
        if test.status not in [QualityTestStatus.PENDING, QualityTestStatus.IN_PROGRESS]:
            raise HTTPException(status_code=400, detail=f"Cannot submit results for test with status: {test.status}")
        
        # Submit the results
        updated_test = await quality_service.submit_test_results(test_id, test_result)
        
        # Create alert if test failed
        if not test_result.pass_fail:
            await alert_manager.create_quality_test_failure_alert(
                test_id=test_id,
                batch_id=test.batch_id,
                test_type=test.test_type,
                deviation_reason=test_result.deviation_reason
            )
        
        # Log audit trail
        await audit_service.log_quality_test_results(test_id, updated_test.tested_by, test_result.dict())
        
        return {
            "message": "Test results submitted successfully",
            "test_id": test_id,
            "result": test_result.result_value,
            "pass_fail": test_result.pass_fail,
            "submitted_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit test results: {str(e)}")

@router.put("/tests/{test_id}/review")
async def review_quality_test(
    test_id: UUID,
    review_data: QualityTestReview,
    quality_service: QualityService = Depends(),
    audit_service: AuditService = Depends()
):
    """Review a completed quality test"""
    try:
        # Verify test exists and has results
        test = await quality_service.get_quality_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Quality test not found")
        
        if test.status != QualityTestStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail=f"Cannot review test with status: {test.status}")
        
        if test.result_value is None:
            raise HTTPException(status_code=400, detail="Test results must be submitted before review")
        
        # Submit the review
        reviewed_test = await quality_service.review_quality_test(test_id, review_data)
        
        # Log audit trail
        await audit_service.log_quality_test_review(test_id, review_data.reviewed_by, review_data.approved)
        
        return {
            "message": "Quality test reviewed successfully",
            "test_id": test_id,
            "reviewed_by": review_data.reviewed_by,
            "approved": review_data.approved,
            "reviewed_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to review quality test: {str(e)}")

@router.put("/tests/{test_id}/approve")
async def approve_quality_test(
    test_id: UUID,
    approval_data: QualityTestApproval,
    quality_service: QualityService = Depends(),
    audit_service: AuditService = Depends()
):
    """Approve a reviewed quality test"""
    try:
        # Verify test exists and is reviewed
        test = await quality_service.get_quality_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Quality test not found")
        
        if test.status not in [QualityTestStatus.PASSED, QualityTestStatus.FAILED]:
            raise HTTPException(status_code=400, detail=f"Cannot approve test with status: {test.status}")
        
        if test.reviewed_by is None:
            raise HTTPException(status_code=400, detail="Test must be reviewed before approval")
        
        # Approve the test
        approved_test = await quality_service.approve_quality_test(test_id, approval_data)
        
        # Log audit trail
        await audit_service.log_quality_test_approval(test_id, approval_data.approved_by)
        
        return {
            "message": "Quality test approved successfully",
            "test_id": test_id,
            "approved_by": approval_data.approved_by,
            "approved_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve quality test: {str(e)}")

@router.get("/tests/batch/{batch_id}", response_model=List[QualityTestResponse])
async def get_batch_quality_tests(
    batch_id: UUID,
    quality_service: QualityService = Depends()
):
    """Get all quality tests for a specific batch"""
    try:
        tests = await quality_service.get_batch_quality_tests(batch_id)
        return tests
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch quality tests: {str(e)}")

@router.get("/tests/batch/{batch_id}/summary")
async def get_batch_quality_summary(
    batch_id: UUID,
    quality_service: QualityService = Depends()
):
    """Get quality test summary for a batch"""
    try:
        summary = await quality_service.get_batch_quality_summary(batch_id)
        
        return {
            "batch_id": batch_id,
            "summary": summary,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch quality summary: {str(e)}")

@router.get("/specifications", response_model=List[QualitySpecification])
async def get_quality_specifications(
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    quality_service: QualityService = Depends()
):
    """Get quality specifications/standards"""
    try:
        specifications = await quality_service.get_quality_specifications(
            test_type=test_type,
            criticality=criticality
        )
        return specifications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quality specifications: {str(e)}")

@router.post("/specifications")
async def create_quality_specification(
    specification: QualitySpecification,
    created_by: str = Query(..., description="User creating the specification"),
    quality_service: QualityService = Depends(),
    audit_service: AuditService = Depends()
):
    """Create a new quality specification"""
    try:
        new_spec = await quality_service.create_quality_specification(specification)
        
        # Log audit trail
        await audit_service.log_specification_creation(new_spec.id, created_by)
        
        return {
            "message": "Quality specification created successfully",
            "specification_id": new_spec.id,
            "test_type": specification.test_type,
            "created_by": created_by,
            "created_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create quality specification: {str(e)}")

@router.get("/reports/test-results")
async def get_test_results_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    pass_fail: Optional[bool] = Query(None, description="Filter by pass/fail"),
    quality_service: QualityService = Depends()
):
    """Get quality test results report"""
    try:
        report = await quality_service.get_test_results_report(
            start_date=start_date,
            end_date=end_date,
            test_type=test_type,
            pass_fail=pass_fail
        )
        
        return {
            "report_type": "test_results",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "filters": {
                "test_type": test_type,
                "pass_fail": pass_fail
            },
            "report": report,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate test results report: {str(e)}")

@router.get("/reports/failure-analysis")
async def get_failure_analysis_report(
    days: int = Query(30, description="Number of days to analyze"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    quality_service: QualityService = Depends()
):
    """Get failure analysis report"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        failure_analysis = await quality_service.get_failure_analysis_report(
            start_date=start_date,
            test_type=test_type
        )
        
        return {
            "report_type": "failure_analysis",
            "analysis_period_days": days,
            "test_type_filter": test_type,
            "analysis": failure_analysis,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate failure analysis report: {str(e)}")

@router.get("/dashboard/quality-metrics")
async def get_quality_dashboard_metrics(
    days: int = Query(7, description="Number of days for metrics"),
    quality_service: QualityService = Depends()
):
    """Get quality metrics for dashboard"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        metrics = await quality_service.get_quality_dashboard_metrics(start_date)
        
        return {
            "period_days": days,
            "metrics": metrics,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quality metrics: {str(e)}")

@router.get("/health/quality-control")
async def quality_control_health_check(
    quality_service: QualityService = Depends()
):
    """Health check endpoint for quality control system"""
    try:
        health_status = await quality_service.perform_health_check()
        
        return {
            "service": "quality_control",
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "details": health_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "service": "quality_control",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }