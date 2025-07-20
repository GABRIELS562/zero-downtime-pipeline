"""
Equipment Monitoring API
Real-time monitoring of pharmaceutical manufacturing equipment
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

from models.manufacturing import Equipment, SensorReading, EquipmentStatus
from services.equipment_service import EquipmentService
from services.alert_manager import AlertManager

router = APIRouter()

# Pydantic models for API
class SensorReadingResponse(BaseModel):
    id: UUID
    equipment_id: UUID
    sensor_type: str
    value: float
    unit: str
    lower_limit: Optional[float]
    upper_limit: Optional[float]
    target_value: Optional[float]
    in_specification: bool
    deviation_magnitude: Optional[float]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class EquipmentResponse(BaseModel):
    id: UUID
    equipment_id: str
    name: str
    equipment_type: str
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    status: str
    location: str
    last_maintenance_date: Optional[datetime]
    next_maintenance_date: Optional[datetime]
    last_calibration_date: Optional[datetime]
    next_calibration_date: Optional[datetime]
    operating_parameters: Optional[dict]
    
    class Config:
        from_attributes = True

class SensorReadingCreate(BaseModel):
    equipment_id: UUID
    sensor_type: str = Field(..., description="Type of sensor (temperature, pressure, humidity, etc.)")
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., description="Unit of measurement")
    lower_limit: Optional[float] = Field(None, description="Lower specification limit")
    upper_limit: Optional[float] = Field(None, description="Upper specification limit")
    target_value: Optional[float] = Field(None, description="Target value")
    measurement_method: Optional[str] = Field(None, description="Method used for measurement")

class EquipmentStatusUpdate(BaseModel):
    status: EquipmentStatus
    notes: Optional[str] = Field(None, description="Notes about status change")

class EquipmentParametersUpdate(BaseModel):
    operating_parameters: dict = Field(..., description="Operating parameters as key-value pairs")

@router.get("/", response_model=List[EquipmentResponse])
async def get_all_equipment(
    status: Optional[EquipmentStatus] = Query(None, description="Filter by equipment status"),
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    equipment_service: EquipmentService = Depends()
):
    """Get list of all manufacturing equipment with optional filtering"""
    try:
        equipment_list = await equipment_service.get_equipment_list(
            status=status,
            equipment_type=equipment_type,
            location=location
        )
        return equipment_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve equipment: {str(e)}")

@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment_details(
    equipment_id: UUID,
    equipment_service: EquipmentService = Depends()
):
    """Get detailed information about specific equipment"""
    try:
        equipment = await equipment_service.get_equipment_by_id(equipment_id)
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        return equipment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve equipment: {str(e)}")

@router.get("/{equipment_id}/status")
async def get_equipment_status(
    equipment_id: UUID,
    equipment_service: EquipmentService = Depends()
):
    """Get current operational status of equipment"""
    try:
        status_info = await equipment_service.get_equipment_status(equipment_id)
        if not status_info:
            raise HTTPException(status_code=404, detail="Equipment not found")
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve equipment status: {str(e)}")

@router.put("/{equipment_id}/status")
async def update_equipment_status(
    equipment_id: UUID,
    status_update: EquipmentStatusUpdate,
    equipment_service: EquipmentService = Depends()
):
    """Update equipment operational status"""
    try:
        updated_equipment = await equipment_service.update_equipment_status(
            equipment_id, 
            status_update.status, 
            status_update.notes
        )
        if not updated_equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        return {
            "message": "Equipment status updated successfully",
            "equipment_id": equipment_id,
            "new_status": status_update.status,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update equipment status: {str(e)}")

@router.get("/{equipment_id}/sensors", response_model=List[SensorReadingResponse])
async def get_equipment_sensor_readings(
    equipment_id: UUID,
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    hours: int = Query(24, description="Number of hours of data to retrieve"),
    limit: int = Query(1000, description="Maximum number of readings to return"),
    equipment_service: EquipmentService = Depends()
):
    """Get sensor readings for specific equipment"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        sensor_readings = await equipment_service.get_sensor_readings(
            equipment_id=equipment_id,
            sensor_type=sensor_type,
            start_time=start_time,
            limit=limit
        )
        return sensor_readings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sensor readings: {str(e)}")

@router.post("/{equipment_id}/sensors", response_model=SensorReadingResponse)
async def create_sensor_reading(
    equipment_id: UUID,
    sensor_reading: SensorReadingCreate,
    equipment_service: EquipmentService = Depends(),
    alert_manager: AlertManager = Depends()
):
    """Record new sensor reading for equipment"""
    try:
        # Verify equipment exists
        equipment = await equipment_service.get_equipment_by_id(equipment_id)
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        # Create sensor reading
        new_reading = await equipment_service.create_sensor_reading(sensor_reading)
        
        # Check for out-of-specification conditions and generate alerts
        if not new_reading.in_specification:
            await alert_manager.create_equipment_alert(
                equipment_id=equipment_id,
                sensor_type=sensor_reading.sensor_type,
                current_value=sensor_reading.value,
                lower_limit=sensor_reading.lower_limit,
                upper_limit=sensor_reading.upper_limit
            )
        
        return new_reading
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sensor reading: {str(e)}")

@router.get("/{equipment_id}/sensors/latest")
async def get_latest_sensor_readings(
    equipment_id: UUID,
    equipment_service: EquipmentService = Depends()
):
    """Get latest sensor reading for each sensor type on equipment"""
    try:
        latest_readings = await equipment_service.get_latest_sensor_readings(equipment_id)
        return {
            "equipment_id": equipment_id,
            "readings": latest_readings,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest sensor readings: {str(e)}")

@router.get("/{equipment_id}/parameters")
async def get_equipment_parameters(
    equipment_id: UUID,
    equipment_service: EquipmentService = Depends()
):
    """Get current operating parameters for equipment"""
    try:
        parameters = await equipment_service.get_equipment_parameters(equipment_id)
        if parameters is None:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        return {
            "equipment_id": equipment_id,
            "operating_parameters": parameters,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve equipment parameters: {str(e)}")

@router.put("/{equipment_id}/parameters")
async def update_equipment_parameters(
    equipment_id: UUID,
    parameters_update: EquipmentParametersUpdate,
    equipment_service: EquipmentService = Depends()
):
    """Update operating parameters for equipment"""
    try:
        updated_equipment = await equipment_service.update_equipment_parameters(
            equipment_id, 
            parameters_update.operating_parameters
        )
        if not updated_equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        return {
            "message": "Equipment parameters updated successfully",
            "equipment_id": equipment_id,
            "parameters": parameters_update.operating_parameters,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update equipment parameters: {str(e)}")

@router.get("/{equipment_id}/maintenance")
async def get_equipment_maintenance_info(
    equipment_id: UUID,
    equipment_service: EquipmentService = Depends()
):
    """Get maintenance and calibration information for equipment"""
    try:
        maintenance_info = await equipment_service.get_maintenance_info(equipment_id)
        if not maintenance_info:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        return maintenance_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve maintenance info: {str(e)}")

@router.get("/types/{equipment_type}/summary")
async def get_equipment_type_summary(
    equipment_type: str,
    equipment_service: EquipmentService = Depends()
):
    """Get summary information for all equipment of a specific type"""
    try:
        summary = await equipment_service.get_equipment_type_summary(equipment_type)
        return {
            "equipment_type": equipment_type,
            "summary": summary,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve equipment type summary: {str(e)}")

@router.get("/sensors/out-of-spec")
async def get_out_of_spec_sensors(
    hours: int = Query(24, description="Number of hours to check"),
    equipment_service: EquipmentService = Depends()
):
    """Get all sensor readings that are out of specification"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        out_of_spec_readings = await equipment_service.get_out_of_spec_readings(start_time)
        
        return {
            "period_hours": hours,
            "out_of_spec_count": len(out_of_spec_readings),
            "readings": out_of_spec_readings,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve out-of-spec readings: {str(e)}")

@router.get("/health/equipment-monitoring")
async def equipment_monitoring_health_check(
    equipment_service: EquipmentService = Depends()
):
    """Health check endpoint for equipment monitoring system"""
    try:
        health_status = await equipment_service.perform_health_check()
        
        return {
            "service": "equipment_monitoring",
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "details": health_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "service": "equipment_monitoring",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }