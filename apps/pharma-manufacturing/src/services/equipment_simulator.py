"""
Equipment Simulator Service
Simulates pharmaceutical manufacturing equipment for demonstration purposes
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)

class EquipmentType(Enum):
    """Types of pharmaceutical manufacturing equipment"""
    REACTOR = "reactor"
    MIXER = "mixer"
    DRYER = "dryer"
    TABLET_PRESS = "tablet_press"
    COATING_PAN = "coating_pan"
    PACKAGING_LINE = "packaging_line"

class EquipmentStatus(Enum):
    """Equipment operational status"""
    RUNNING = "running"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    OFFLINE = "offline"

class Equipment:
    """Simulated equipment instance"""
    def __init__(self, equipment_id: str, equipment_type: EquipmentType, location: str):
        self.equipment_id = equipment_id
        self.equipment_type = equipment_type
        self.location = location
        self.status = EquipmentStatus.OFFLINE
        self.temperature = 20.0
        self.pressure = 1.0
        self.speed = 0.0
        self.efficiency = 100.0
        self.last_maintenance = datetime.now(timezone.utc)
        self.operating_hours = 0.0
        self.error_count = 0
        self.current_batch = None
        
    def get_metrics(self) -> dict:
        """Get current equipment metrics"""
        return {
            "equipment_id": self.equipment_id,
            "type": self.equipment_type.value,
            "location": self.location,
            "status": self.status.value,
            "temperature": round(self.temperature, 2),
            "pressure": round(self.pressure, 2),
            "speed": round(self.speed, 2),
            "efficiency": round(self.efficiency, 2),
            "operating_hours": round(self.operating_hours, 2),
            "error_count": self.error_count,
            "current_batch": self.current_batch,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

class EquipmentSimulator:
    """Simulates pharmaceutical manufacturing equipment"""
    
    def __init__(self):
        self.equipment: Dict[str, Equipment] = {}
        self.running = False
        self.simulation_task = None
        self.update_interval = 5.0  # seconds
        
    async def start(self):
        """Start equipment simulation"""
        try:
            logger.info("Starting Equipment Simulator")
            
            # Create simulated equipment
            self._create_equipment()
            
            # Start simulation loop
            self.running = True
            self.simulation_task = asyncio.create_task(self._simulation_loop())
            
            logger.info(f"Equipment Simulator started with {len(self.equipment)} equipment units")
            
        except Exception as e:
            logger.error(f"Failed to start Equipment Simulator: {e}")
            self.running = False
    
    def _create_equipment(self):
        """Create simulated equipment instances"""
        equipment_configs = [
            ("REACTOR-001", EquipmentType.REACTOR, "Building-A Floor-2"),
            ("REACTOR-002", EquipmentType.REACTOR, "Building-A Floor-2"),
            ("MIXER-001", EquipmentType.MIXER, "Building-A Floor-1"),
            ("MIXER-002", EquipmentType.MIXER, "Building-A Floor-1"),
            ("DRYER-001", EquipmentType.DRYER, "Building-B Floor-1"),
            ("TABLET-PRESS-001", EquipmentType.TABLET_PRESS, "Building-B Floor-3"),
            ("TABLET-PRESS-002", EquipmentType.TABLET_PRESS, "Building-B Floor-3"),
            ("COATING-PAN-001", EquipmentType.COATING_PAN, "Building-B Floor-2"),
            ("PACKAGING-001", EquipmentType.PACKAGING_LINE, "Building-C Floor-1"),
            ("PACKAGING-002", EquipmentType.PACKAGING_LINE, "Building-C Floor-1"),
        ]
        
        for eq_id, eq_type, location in equipment_configs:
            equipment = Equipment(eq_id, eq_type, location)
            equipment.status = EquipmentStatus.IDLE
            self.equipment[eq_id] = equipment
    
    async def _simulation_loop(self):
        """Main simulation loop"""
        while self.running:
            try:
                # Update each equipment
                for equipment in self.equipment.values():
                    await self._update_equipment(equipment)
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
                await asyncio.sleep(1)
    
    async def _update_equipment(self, equipment: Equipment):
        """Update individual equipment metrics"""
        try:
            # Simulate status changes
            if equipment.status == EquipmentStatus.IDLE and random.random() < 0.1:
                equipment.status = EquipmentStatus.RUNNING
                equipment.current_batch = f"BATCH-{random.randint(1000, 9999)}"
            
            elif equipment.status == EquipmentStatus.RUNNING:
                # Small chance of going to maintenance or error
                if random.random() < 0.005:
                    equipment.status = EquipmentStatus.MAINTENANCE
                    equipment.current_batch = None
                elif random.random() < 0.002:
                    equipment.status = EquipmentStatus.ERROR
                    equipment.error_count += 1
                    equipment.current_batch = None
                elif random.random() < 0.05:
                    equipment.status = EquipmentStatus.IDLE
                    equipment.current_batch = None
            
            elif equipment.status in [EquipmentStatus.MAINTENANCE, EquipmentStatus.ERROR]:
                # Chance to return to idle
                if random.random() < 0.2:
                    equipment.status = EquipmentStatus.IDLE
            
            # Update metrics based on status
            if equipment.status == EquipmentStatus.RUNNING:
                # Running equipment parameters
                equipment.temperature = self._simulate_temperature(equipment)
                equipment.pressure = self._simulate_pressure(equipment)
                equipment.speed = self._simulate_speed(equipment)
                equipment.efficiency = max(80.0, equipment.efficiency + random.uniform(-2, 1))
                equipment.operating_hours += self.update_interval / 3600
                
            elif equipment.status == EquipmentStatus.IDLE:
                # Idle equipment
                equipment.temperature = min(25.0, equipment.temperature + random.uniform(-0.5, 0.5))
                equipment.pressure = 1.0 + random.uniform(-0.05, 0.05)
                equipment.speed = 0.0
                
            elif equipment.status == EquipmentStatus.ERROR:
                # Equipment in error state
                equipment.temperature += random.uniform(-5, 5)
                equipment.efficiency = max(0.0, equipment.efficiency - random.uniform(5, 10))
                equipment.speed = random.uniform(0, 10)  # Erratic speed
                
            else:  # MAINTENANCE or OFFLINE
                equipment.temperature = 20.0 + random.uniform(-2, 2)
                equipment.pressure = 1.0
                equipment.speed = 0.0
                
        except Exception as e:
            logger.error(f"Error updating equipment {equipment.equipment_id}: {e}")
    
    def _simulate_temperature(self, equipment: Equipment) -> float:
        """Simulate equipment temperature"""
        base_temps = {
            EquipmentType.REACTOR: 85.0,
            EquipmentType.MIXER: 45.0,
            EquipmentType.DRYER: 120.0,
            EquipmentType.TABLET_PRESS: 35.0,
            EquipmentType.COATING_PAN: 65.0,
            EquipmentType.PACKAGING_LINE: 25.0
        }
        
        base_temp = base_temps.get(equipment.equipment_type, 25.0)
        return base_temp + random.uniform(-5, 5)
    
    def _simulate_pressure(self, equipment: Equipment) -> float:
        """Simulate equipment pressure"""
        base_pressures = {
            EquipmentType.REACTOR: 2.5,
            EquipmentType.MIXER: 1.2,
            EquipmentType.DRYER: 0.8,
            EquipmentType.TABLET_PRESS: 15.0,
            EquipmentType.COATING_PAN: 1.1,
            EquipmentType.PACKAGING_LINE: 1.0
        }
        
        base_pressure = base_pressures.get(equipment.equipment_type, 1.0)
        return base_pressure + random.uniform(-0.1, 0.1)
    
    def _simulate_speed(self, equipment: Equipment) -> float:
        """Simulate equipment speed/RPM"""
        base_speeds = {
            EquipmentType.REACTOR: 150.0,
            EquipmentType.MIXER: 300.0,
            EquipmentType.DRYER: 50.0,
            EquipmentType.TABLET_PRESS: 1200.0,
            EquipmentType.COATING_PAN: 80.0,
            EquipmentType.PACKAGING_LINE: 500.0
        }
        
        base_speed = base_speeds.get(equipment.equipment_type, 100.0)
        return base_speed + random.uniform(-10, 10)
    
    async def get_equipment_status(self, equipment_id: str = None) -> dict:
        """Get status of specific equipment or all equipment"""
        if equipment_id:
            if equipment_id in self.equipment:
                return self.equipment[equipment_id].get_metrics()
            else:
                return {"error": f"Equipment {equipment_id} not found"}
        
        return {
            "equipment_count": len(self.equipment),
            "equipment": {eq_id: eq.get_metrics() for eq_id, eq in self.equipment.items()},
            "summary": self._get_summary()
        }
    
    def _get_summary(self) -> dict:
        """Get equipment summary statistics"""
        status_counts = {}
        for status in EquipmentStatus:
            status_counts[status.value] = sum(1 for eq in self.equipment.values() if eq.status == status)
        
        return {
            "status_counts": status_counts,
            "total_operating_hours": sum(eq.operating_hours for eq in self.equipment.values()),
            "total_errors": sum(eq.error_count for eq in self.equipment.values()),
            "average_efficiency": sum(eq.efficiency for eq in self.equipment.values()) / len(self.equipment)
        }
    
    async def set_equipment_status(self, equipment_id: str, status: str) -> bool:
        """Manually set equipment status (for testing)"""
        if equipment_id not in self.equipment:
            return False
        
        try:
            new_status = EquipmentStatus(status)
            self.equipment[equipment_id].status = new_status
            logger.info(f"Equipment {equipment_id} status changed to {status}")
            return True
        except ValueError:
            logger.error(f"Invalid status: {status}")
            return False
    
    async def stop(self):
        """Stop equipment simulation"""
        logger.info("Stopping Equipment Simulator")
        self.running = False
        
        if self.simulation_task:
            self.simulation_task.cancel()
            try:
                await self.simulation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Equipment Simulator stopped")
    
    async def health_check(self) -> dict:
        """Check simulator health"""
        return {
            "status": "healthy" if self.running else "stopped",
            "equipment_count": len(self.equipment),
            "running_equipment": len([eq for eq in self.equipment.values() if eq.status == EquipmentStatus.RUNNING]),
            "error_equipment": len([eq for eq in self.equipment.values() if eq.status == EquipmentStatus.ERROR])
        }