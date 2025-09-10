"""
Environmental Monitoring API
Clean room environmental condition monitoring for pharmaceutical manufacturing
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.manufacturing import EnvironmentalReading
from src.services.environmental_service import EnvironmentalService
from src.services.alert_manager import AlertManager

router = APIRouter()

# Pydantic models for API
class EnvironmentalReadingResponse(BaseModel):
    id: UUID
    room_id: str
    room_name: str
    room_classification: str
    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    particle_count: Optional[int]
    air_changes_per_hour: Optional[float]
    temperature_spec_min: Optional[float]
    temperature_spec_max: Optional[float]
    humidity_spec_min: Optional[float]
    humidity_spec_max: Optional[float]
    in_specification: bool
    alert_generated: bool
    timestamp: datetime
    
    class Config:
        from_attributes = True

class EnvironmentalReadingCreate(BaseModel):
    room_id: str = Field(..., description="Unique room identifier")
    room_name: str = Field(..., description="Room name")
    room_classification: str = Field(..., description="Clean room classification (ISO 5, ISO 7, etc.)")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Relative humidity percentage")
    pressure: Optional[float] = Field(None, description="Pressure in Pascals")
    particle_count: Optional[int] = Field(None, ge=0, description="Particle count per cubic meter")
    air_changes_per_hour: Optional[float] = Field(None, ge=0, description="Air changes per hour")
    temperature_spec_min: Optional[float] = Field(None, description="Minimum temperature specification")
    temperature_spec_max: Optional[float] = Field(None, description="Maximum temperature specification")
    humidity_spec_min: Optional[float] = Field(None, description="Minimum humidity specification")
    humidity_spec_max: Optional[float] = Field(None, description="Maximum humidity specification")

class RoomSpecifications(BaseModel):
    room_id: str = Field(..., description="Room identifier")
    temperature_min: float = Field(..., description="Minimum temperature")
    temperature_max: float = Field(..., description="Maximum temperature")
    humidity_min: float = Field(..., description="Minimum humidity")
    humidity_max: float = Field(..., description="Maximum humidity")
    pressure_min: Optional[float] = Field(None, description="Minimum pressure")
    pressure_max: Optional[float] = Field(None, description="Maximum pressure")
    max_particle_count: Optional[int] = Field(None, description="Maximum particle count")
    min_air_changes: Optional[float] = Field(None, description="Minimum air changes per hour")

class EnvironmentalAlert(BaseModel):
    room_id: str
    parameter: str
    current_value: float
    specification_min: Optional[float]
    specification_max: Optional[float]
    deviation_percentage: float
    severity: str
    message: str

@router.get("/readings", response_model=List[EnvironmentalReadingResponse])
async def get_environmental_readings(
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    room_classification: Optional[str] = Query(None, description="Filter by room classification"),
    hours: int = Query(24, description="Number of hours of data to retrieve"),
    out_of_spec_only: bool = Query(False, description="Show only out-of-specification readings"),
    limit: int = Query(1000, le=10000, description="Maximum number of readings to return"),
    environmental_service: EnvironmentalService = Depends()
):
    """Get environmental readings with optional filtering"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        readings = await environmental_service.get_environmental_readings(
            room_id=room_id,
            room_classification=room_classification,
            start_time=start_time,
            out_of_spec_only=out_of_spec_only,
            limit=limit
        )
        return readings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve environmental readings: {str(e)}")

@router.get("/readings/{reading_id}", response_model=EnvironmentalReadingResponse)
async def get_environmental_reading_details(
    reading_id: UUID,
    environmental_service: EnvironmentalService = Depends()
):
    """Get detailed information about a specific environmental reading"""
    try:
        reading = await environmental_service.get_environmental_reading_by_id(reading_id)
        if not reading:
            raise HTTPException(status_code=404, detail="Environmental reading not found")
        return reading
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve environmental reading: {str(e)}")

@router.post("/readings", response_model=EnvironmentalReadingResponse)
async def create_environmental_reading(
    reading_data: EnvironmentalReadingCreate,
    environmental_service: EnvironmentalService = Depends(),
    alert_manager: AlertManager = Depends()
):
    """Record new environmental reading"""
    try:
        # Create the environmental reading
        new_reading = await environmental_service.create_environmental_reading(reading_data)
        
        # Check for out-of-specification conditions and generate alerts if needed
        if not new_reading.in_specification:
            await alert_manager.create_environmental_alert(
                room_id=reading_data.room_id,
                reading_data=reading_data,
                current_reading=new_reading
            )
        
        return new_reading
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create environmental reading: {str(e)}")

@router.get("/rooms")
async def get_monitored_rooms(
    classification: Optional[str] = Query(None, description="Filter by room classification"),
    environmental_service: EnvironmentalService = Depends()
):
    """Get list of all monitored rooms"""
    try:
        rooms = await environmental_service.get_monitored_rooms(classification)
        return {
            "rooms": rooms,
            "total_count": len(rooms),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve monitored rooms: {str(e)}")

@router.get("/rooms/{room_id}/latest")
async def get_latest_room_conditions(
    room_id: str,
    environmental_service: EnvironmentalService = Depends()
):
    """Get latest environmental conditions for a specific room"""
    try:
        latest_conditions = await environmental_service.get_latest_room_conditions(room_id)
        if not latest_conditions:
            raise HTTPException(status_code=404, detail="No environmental data found for room")
        
        return {
            "room_id": room_id,
            "latest_conditions": latest_conditions,
            "retrieved_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest room conditions: {str(e)}")

@router.get("/rooms/{room_id}/history")
async def get_room_environmental_history(
    room_id: str,
    hours: int = Query(24, description="Number of hours of history"),
    parameter: Optional[str] = Query(None, description="Specific parameter (temperature, humidity, etc.)"),
    environmental_service: EnvironmentalService = Depends()
):
    """Get environmental history for a specific room"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        history = await environmental_service.get_room_environmental_history(
            room_id=room_id,
            start_time=start_time,
            parameter=parameter
        )
        
        return {
            "room_id": room_id,
            "period_hours": hours,
            "parameter_filter": parameter,
            "history": history,
            "data_points": len(history),
            "retrieved_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve room environmental history: {str(e)}")

@router.put("/rooms/{room_id}/specifications")
async def update_room_specifications(
    room_id: str,
    specifications: RoomSpecifications,
    updated_by: str = Query(..., description="User updating the specifications"),
    environmental_service: EnvironmentalService = Depends()
):
    """Update environmental specifications for a room"""
    try:
        updated_specs = await environmental_service.update_room_specifications(room_id, specifications)
        
        return {
            "message": "Room specifications updated successfully",
            "room_id": room_id,
            "specifications": specifications.dict(),
            "updated_by": updated_by,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update room specifications: {str(e)}")

@router.get("/rooms/{room_id}/specifications")
async def get_room_specifications(
    room_id: str,
    environmental_service: EnvironmentalService = Depends()
):
    """Get environmental specifications for a room"""
    try:
        specifications = await environmental_service.get_room_specifications(room_id)
        if not specifications:
            raise HTTPException(status_code=404, detail="Room specifications not found")
        
        return {
            "room_id": room_id,
            "specifications": specifications,
            "retrieved_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve room specifications: {str(e)}")

@router.get("/alerts/out-of-spec")
async def get_out_of_spec_alerts(
    hours: int = Query(24, description="Number of hours to check"),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    environmental_service: EnvironmentalService = Depends()
):
    """Get environmental alerts for out-of-specification conditions"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        alerts = await environmental_service.get_out_of_spec_alerts(
            start_time=start_time,
            room_id=room_id,
            severity=severity
        )
        
        return {
            "period_hours": hours,
            "room_filter": room_id,
            "severity_filter": severity,
            "alerts": alerts,
            "alert_count": len(alerts),
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve out-of-spec alerts: {str(e)}")

@router.get("/reports/compliance-summary")
async def get_environmental_compliance_summary(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    environmental_service: EnvironmentalService = Depends()
):
    """Get environmental compliance summary report"""
    try:
        compliance_summary = await environmental_service.get_compliance_summary_report(
            start_date=start_date,
            end_date=end_date,
            room_id=room_id
        )
        
        return {
            "report_type": "environmental_compliance_summary",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "room_filter": room_id,
            "summary": compliance_summary,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate compliance summary: {str(e)}")

@router.get("/reports/trend-analysis")
async def get_environmental_trend_analysis(
    room_id: str = Query(..., description="Room ID for analysis"),
    parameter: str = Query(..., description="Parameter to analyze (temperature, humidity, etc.)"),
    days: int = Query(30, description="Number of days to analyze"),
    environmental_service: EnvironmentalService = Depends()
):
    """Get environmental trend analysis for a specific parameter"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        trend_analysis = await environmental_service.get_trend_analysis(
            room_id=room_id,
            parameter=parameter,
            start_date=start_date
        )
        
        return {
            "report_type": "environmental_trend_analysis",
            "room_id": room_id,
            "parameter": parameter,
            "analysis_period_days": days,
            "trend_analysis": trend_analysis,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate trend analysis: {str(e)}")

@router.get("/dashboard/environmental-overview")
async def get_environmental_dashboard_overview(
    environmental_service: EnvironmentalService = Depends()
):
    """Get environmental monitoring dashboard overview"""
    try:
        dashboard_data = await environmental_service.get_dashboard_overview()
        
        return {
            "dashboard_type": "environmental_overview",
            "overview": dashboard_data,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve environmental dashboard: {str(e)}")

@router.get("/rooms/{room_id}/batch-correlation")
async def get_room_batch_correlation(
    room_id: str,
    batch_id: Optional[UUID] = Query(None, description="Specific batch ID"),
    hours: int = Query(24, description="Number of hours to analyze"),
    environmental_service: EnvironmentalService = Depends()
):
    """Get correlation between environmental conditions and batch production"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        correlation_data = await environmental_service.get_room_batch_correlation(
            room_id=room_id,
            batch_id=batch_id,
            start_time=start_time
        )
        
        return {
            "room_id": room_id,
            "batch_id": batch_id,
            "analysis_period_hours": hours,
            "correlation_data": correlation_data,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch correlation data: {str(e)}")

@router.get("/health/environmental-monitoring")
async def environmental_monitoring_health_check(
    environmental_service: EnvironmentalService = Depends()
):
    """Health check endpoint for environmental monitoring system"""
    try:
        health_status = await environmental_service.perform_health_check()
        
        return {
            "service": "environmental_monitoring",
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "details": health_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "service": "environmental_monitoring",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }