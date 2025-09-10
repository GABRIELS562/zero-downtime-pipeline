"""
Alert Management API
Real-time alerting system for parameter violations in pharmaceutical manufacturing
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.manufacturing import Alert, AlertSeverity
from src.services.alert_manager import AlertManager
from src.services.alert_manager import AlertManager

router = APIRouter()

# Pydantic models for API
class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    severity: str
    title: str
    message: str
    source_type: str
    source_id: Optional[str]
    status: str
    acknowledged: bool
    resolved: bool
    acknowledged_by: Optional[str]
    resolved_by: Optional[str]
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    metadata: Optional[dict]
    
    class Config:
        from_attributes = True

class AlertCreate(BaseModel):
    alert_type: str = Field(..., description="Type of alert (equipment, environmental, quality, etc.)")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    title: str = Field(..., max_length=200, description="Alert title")
    message: str = Field(..., description="Detailed alert message")
    source_type: str = Field(..., description="Source type (equipment, room, batch, etc.)")
    source_id: Optional[str] = Field(None, description="Source identifier")
    metadata: Optional[dict] = Field(None, description="Additional alert metadata")

class AlertAcknowledge(BaseModel):
    acknowledged_by: str = Field(..., description="Person acknowledging the alert")
    notes: Optional[str] = Field(None, description="Acknowledgment notes")

class AlertResolve(BaseModel):
    resolved_by: str = Field(..., description="Person resolving the alert")
    resolution_notes: str = Field(..., description="Resolution notes and actions taken")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")

class AlertEscalation(BaseModel):
    escalated_to: str = Field(..., description="Person or team to escalate to")
    escalation_reason: str = Field(..., description="Reason for escalation")
    escalated_by: str = Field(..., description="Person performing the escalation")

class AlertFilters(BaseModel):
    severity: Optional[AlertSeverity] = None
    alert_type: Optional[str] = None
    source_type: Optional[str] = None
    status: Optional[str] = None
    acknowledged: Optional[bool] = None
    resolved: Optional[bool] = None

@router.get("/", response_model=List[AlertResponse])
async def get_all_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    hours: int = Query(24, description="Number of hours of alerts to retrieve"),
    limit: int = Query(100, le=1000, description="Maximum number of alerts to return"),
    alert_service: AlertService = Depends()
):
    """Get list of alerts with optional filtering"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        alerts = await alert_service.get_alerts(
            severity=severity,
            alert_type=alert_type,
            source_type=source_type,
            status=status,
            acknowledged=acknowledged,
            resolved=resolved,
            start_time=start_time,
            limit=limit
        )
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_details(
    alert_id: UUID,
    alert_service: AlertService = Depends()
):
    """Get detailed information about a specific alert"""
    try:
        alert = await alert_service.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alert: {str(e)}")

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    created_by: str = Query(..., description="User creating the alert"),
    alert_service: AlertService = Depends(),
    notification_service: NotificationService = Depends()
):
    """Create a new alert"""
    try:
        # Create the alert
        new_alert = await alert_service.create_alert(alert_data, created_by)
        
        # Send notifications based on severity
        await notification_service.send_alert_notifications(new_alert)
        
        return new_alert
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")

@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    acknowledge_data: AlertAcknowledge,
    alert_service: AlertService = Depends(),
    notification_service: NotificationService = Depends()
):
    """Acknowledge an alert"""
    try:
        # Verify alert exists and can be acknowledged
        alert = await alert_service.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        if alert.acknowledged:
            raise HTTPException(status_code=400, detail="Alert is already acknowledged")
        
        # Acknowledge the alert
        acknowledged_alert = await alert_service.acknowledge_alert(alert_id, acknowledge_data)
        
        # Send acknowledgment notifications
        await notification_service.send_acknowledgment_notification(acknowledged_alert, acknowledge_data)
        
        return {
            "message": "Alert acknowledged successfully",
            "alert_id": alert_id,
            "acknowledged_by": acknowledge_data.acknowledged_by,
            "acknowledged_at": acknowledged_alert.acknowledged_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolve_data: AlertResolve,
    alert_service: AlertService = Depends(),
    notification_service: NotificationService = Depends()
):
    """Resolve an alert"""
    try:
        # Verify alert exists and can be resolved
        alert = await alert_service.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        if alert.resolved:
            raise HTTPException(status_code=400, detail="Alert is already resolved")
        
        # Resolve the alert
        resolved_alert = await alert_service.resolve_alert(alert_id, resolve_data)
        
        # Send resolution notifications
        await notification_service.send_resolution_notification(resolved_alert, resolve_data)
        
        return {
            "message": "Alert resolved successfully",
            "alert_id": alert_id,
            "resolved_by": resolve_data.resolved_by,
            "resolved_at": resolved_alert.resolved_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@router.put("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: UUID,
    escalation_data: AlertEscalation,
    alert_service: AlertService = Depends(),
    notification_service: NotificationService = Depends()
):
    """Escalate an alert to higher authority"""
    try:
        # Verify alert exists
        alert = await alert_service.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        if alert.resolved:
            raise HTTPException(status_code=400, detail="Cannot escalate resolved alert")
        
        # Escalate the alert
        escalated_alert = await alert_service.escalate_alert(alert_id, escalation_data)
        
        # Send escalation notifications
        await notification_service.send_escalation_notification(escalated_alert, escalation_data)
        
        return {
            "message": "Alert escalated successfully",
            "alert_id": alert_id,
            "escalated_to": escalation_data.escalated_to,
            "escalated_by": escalation_data.escalated_by,
            "escalation_time": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to escalate alert: {str(e)}")

@router.get("/active/summary")
async def get_active_alerts_summary(
    alert_service: AlertService = Depends()
):
    """Get summary of active alerts by severity and type"""
    try:
        summary = await alert_service.get_active_alerts_summary()
        
        return {
            "summary": summary,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active alerts summary: {str(e)}")

@router.get("/critical/unacknowledged")
async def get_critical_unacknowledged_alerts(
    hours: int = Query(24, description="Number of hours to check"),
    alert_service: AlertService = Depends()
):
    """Get critical alerts that haven't been acknowledged"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        critical_alerts = await alert_service.get_critical_unacknowledged_alerts(start_time)
        
        return {
            "period_hours": hours,
            "critical_unacknowledged_count": len(critical_alerts),
            "alerts": critical_alerts,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve critical unacknowledged alerts: {str(e)}")

@router.get("/source/{source_type}/{source_id}")
async def get_alerts_by_source(
    source_type: str,
    source_id: str,
    hours: int = Query(24, description="Number of hours of alerts"),
    alert_service: AlertService = Depends()
):
    """Get all alerts for a specific source"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        source_alerts = await alert_service.get_alerts_by_source(
            source_type=source_type,
            source_id=source_id,
            start_time=start_time
        )
        
        return {
            "source_type": source_type,
            "source_id": source_id,
            "period_hours": hours,
            "alerts_count": len(source_alerts),
            "alerts": source_alerts,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts by source: {str(e)}")

@router.get("/reports/alert-trends")
async def get_alert_trends_report(
    days: int = Query(30, description="Number of days to analyze"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    alert_service: AlertService = Depends()
):
    """Get alert trends analysis report"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        trends_report = await alert_service.get_alert_trends_report(
            start_date=start_date,
            alert_type=alert_type,
            source_type=source_type
        )
        
        return {
            "report_type": "alert_trends",
            "analysis_period_days": days,
            "filters": {
                "alert_type": alert_type,
                "source_type": source_type
            },
            "trends": trends_report,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate alert trends report: {str(e)}")

@router.get("/reports/response-times")
async def get_alert_response_times_report(
    days: int = Query(30, description="Number of days to analyze"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    alert_service: AlertService = Depends()
):
    """Get alert response times analysis report"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        response_times_report = await alert_service.get_response_times_report(
            start_date=start_date,
            severity=severity
        )
        
        return {
            "report_type": "alert_response_times",
            "analysis_period_days": days,
            "severity_filter": severity,
            "response_times": response_times_report,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response times report: {str(e)}")

@router.get("/dashboard/alert-metrics")
async def get_alert_dashboard_metrics(
    hours: int = Query(24, description="Number of hours for metrics"),
    alert_service: AlertService = Depends()
):
    """Get alert metrics for dashboard display"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        dashboard_metrics = await alert_service.get_dashboard_metrics(start_time)
        
        return {
            "period_hours": hours,
            "metrics": dashboard_metrics,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alert dashboard metrics: {str(e)}")

@router.post("/test")
async def create_test_alert(
    alert_type: str = Query("test", description="Test alert type"),
    severity: AlertSeverity = Query(AlertSeverity.LOW, description="Test alert severity"),
    created_by: str = Query("system", description="User creating test alert"),
    alert_service: AlertService = Depends()
):
    """Create a test alert for system validation"""
    try:
        test_alert_data = AlertCreate(
            alert_type=alert_type,
            severity=severity,
            title="Test Alert",
            message="This is a test alert for system validation",
            source_type="system",
            source_id="test",
            metadata={"test": True, "created_for": "system_validation"}
        )
        
        test_alert = await alert_service.create_alert(test_alert_data, created_by)
        
        return {
            "message": "Test alert created successfully",
            "alert_id": test_alert.id,
            "alert_type": alert_type,
            "severity": severity,
            "created_by": created_by,
            "created_at": test_alert.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test alert: {str(e)}")

@router.get("/health/alert-system")
async def alert_system_health_check(
    alert_service: AlertService = Depends()
):
    """Health check endpoint for alert system"""
    try:
        health_status = await alert_service.perform_health_check()
        
        return {
            "service": "alert_system",
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "details": health_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "service": "alert_system",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }