"""
Environmental Monitoring Service
Monitors pharmaceutical manufacturing environment conditions
"""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EnvironmentStatus(Enum):
    """Environmental status"""
    OPTIMAL = "optimal"
    ACCEPTABLE = "acceptable"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class EnvironmentalReading:
    """Environmental sensor reading"""
    sensor_id: str
    location: str
    temperature: float
    humidity: float
    pressure: float
    particle_count: int
    timestamp: datetime
    status: EnvironmentStatus

class EnvironmentalService:
    """Service for environmental monitoring"""
    
    def __init__(self):
        self.sensors: Dict[str, Dict[str, Any]] = {}
        self.readings: List[EnvironmentalReading] = []
        self._initialize_sensors()
        logger.info("Environmental Service initialized")
    
    def _initialize_sensors(self):
        """Initialize environmental sensors"""
        self.sensors = {
            "ENV-001": {
                "location": "Clean Room 1",
                "type": "Temperature/Humidity",
                "status": "active"
            },
            "ENV-002": {
                "location": "Clean Room 2",
                "type": "Particle Counter",
                "status": "active"
            },
            "ENV-003": {
                "location": "Storage Area",
                "type": "Temperature/Humidity",
                "status": "active"
            },
            "ENV-004": {
                "location": "Production Floor",
                "type": "Environmental Monitor",
                "status": "active"
            }
        }
    
    async def get_current_readings(self) -> List[Dict[str, Any]]:
        """Get current environmental readings"""
        readings = []
        for sensor_id, sensor_info in self.sensors.items():
            reading = self._generate_reading(sensor_id, sensor_info["location"])
            readings.append({
                "sensor_id": sensor_id,
                "location": sensor_info["location"],
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "pressure": reading.pressure,
                "particle_count": reading.particle_count,
                "status": reading.status.value,
                "timestamp": reading.timestamp.isoformat()
            })
            self.readings.append(reading)
        
        return readings
    
    def _generate_reading(self, sensor_id: str, location: str) -> EnvironmentalReading:
        """Generate simulated environmental reading"""
        # Simulate environmental conditions
        if "Clean Room" in location:
            temp = 20.0 + random.uniform(-0.5, 0.5)
            humidity = 45.0 + random.uniform(-2, 2)
            pressure = 101.3 + random.uniform(-0.2, 0.2)
            particles = random.randint(100, 1000)
        else:
            temp = 22.0 + random.uniform(-2, 2)
            humidity = 50.0 + random.uniform(-5, 5)
            pressure = 101.3 + random.uniform(-0.5, 0.5)
            particles = random.randint(1000, 5000)
        
        # Determine status
        if temp < 18 or temp > 25 or humidity < 30 or humidity > 70:
            status = EnvironmentStatus.WARNING
        elif temp < 15 or temp > 30 or humidity < 20 or humidity > 80:
            status = EnvironmentStatus.CRITICAL
        elif 19 <= temp <= 23 and 40 <= humidity <= 60:
            status = EnvironmentStatus.OPTIMAL
        else:
            status = EnvironmentStatus.ACCEPTABLE
        
        return EnvironmentalReading(
            sensor_id=sensor_id,
            location=location,
            temperature=round(temp, 2),
            humidity=round(humidity, 2),
            pressure=round(pressure, 2),
            particle_count=particles,
            timestamp=datetime.now(timezone.utc),
            status=status
        )
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get environmental alerts"""
        alerts = []
        current_readings = await self.get_current_readings()
        
        for reading in current_readings:
            if reading["status"] in ["warning", "critical"]:
                alerts.append({
                    "sensor_id": reading["sensor_id"],
                    "location": reading["location"],
                    "alert_type": reading["status"],
                    "message": f"Environmental conditions outside acceptable range at {reading['location']}",
                    "temperature": reading["temperature"],
                    "humidity": reading["humidity"],
                    "timestamp": reading["timestamp"]
                })
        
        return alerts
    
    async def get_historical_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical environmental data"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        historical = [
            {
                "sensor_id": r.sensor_id,
                "location": r.location,
                "temperature": r.temperature,
                "humidity": r.humidity,
                "pressure": r.pressure,
                "particle_count": r.particle_count,
                "status": r.status.value,
                "timestamp": r.timestamp.isoformat()
            }
            for r in self.readings
            if r.timestamp >= cutoff_time
        ]
        
        return historical[-100:]  # Return last 100 readings
    
    async def get_compliance_status(self) -> Dict[str, Any]:
        """Get environmental compliance status"""
        current_readings = await self.get_current_readings()
        
        total_sensors = len(current_readings)
        optimal = sum(1 for r in current_readings if r["status"] == "optimal")
        acceptable = sum(1 for r in current_readings if r["status"] == "acceptable")
        warning = sum(1 for r in current_readings if r["status"] == "warning")
        critical = sum(1 for r in current_readings if r["status"] == "critical")
        
        return {
            "overall_status": "compliant" if critical == 0 and warning == 0 else "non_compliant",
            "total_sensors": total_sensors,
            "optimal_count": optimal,
            "acceptable_count": acceptable,
            "warning_count": warning,
            "critical_count": critical,
            "compliance_percentage": ((optimal + acceptable) / total_sensors * 100) if total_sensors > 0 else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }