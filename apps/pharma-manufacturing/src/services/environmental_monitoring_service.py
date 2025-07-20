"""
Environmental Monitoring Service
Real-time environmental monitoring for pharmaceutical manufacturing areas
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from models.gmp_models import EnvironmentalMonitoring, EnvironmentalParameterType
from services.immutable_audit_service import ImmutableAuditService
from models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class EnvironmentalMonitoringService:
    """
    Service for real-time environmental monitoring in pharmaceutical facilities
    Monitors temperature, humidity, pressure, particle counts, and other critical parameters
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.monitoring_active = False
        self.alert_thresholds = self._initialize_alert_thresholds()
        self.monitoring_points = self._initialize_monitoring_points()
        
    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize alert thresholds for different parameters"""
        return {
            "temperature": {
                "min_warning": 18.0,
                "min_critical": 15.0,
                "max_warning": 27.0,
                "max_critical": 30.0
            },
            "humidity": {
                "min_warning": 40.0,
                "min_critical": 35.0,
                "max_warning": 70.0,
                "max_critical": 75.0
            },
            "pressure": {
                "min_warning": -5.0,
                "min_critical": -10.0,
                "max_warning": 25.0,
                "max_critical": 30.0
            },
            "particle_count": {
                "iso5_0_5um": 3520,
                "iso5_5_0um": 29,
                "iso7_0_5um": 352000,
                "iso7_5_0um": 2930,
                "iso8_0_5um": 3520000,
                "iso8_5_0um": 29300
            }
        }
    
    def _initialize_monitoring_points(self) -> Dict[str, Dict[str, Any]]:
        """Initialize monitoring points configuration"""
        return {
            "PROD_ROOM_A": {
                "location": "Production Room A",
                "area_classification": "ISO 7",
                "parameters": ["temperature", "humidity", "pressure", "particle_count"],
                "specifications": {
                    "temperature": {"min": 20.0, "max": 25.0, "unit": "°C"},
                    "humidity": {"min": 45.0, "max": 65.0, "unit": "%RH"},
                    "pressure": {"min": 5.0, "max": 15.0, "unit": "Pa"},
                    "particle_count": {"classification": "ISO 7"}
                }
            },
            "CLEAN_ROOM_B": {
                "location": "Clean Room B",
                "area_classification": "ISO 5",
                "parameters": ["temperature", "humidity", "pressure", "particle_count", "airflow"],
                "specifications": {
                    "temperature": {"min": 20.0, "max": 25.0, "unit": "°C"},
                    "humidity": {"min": 45.0, "max": 65.0, "unit": "%RH"},
                    "pressure": {"min": 10.0, "max": 20.0, "unit": "Pa"},
                    "particle_count": {"classification": "ISO 5"},
                    "airflow": {"min": 0.35, "max": 0.55, "unit": "m/s"}
                }
            },
            "WAREHOUSE": {
                "location": "Raw Material Warehouse",
                "area_classification": "General",
                "parameters": ["temperature", "humidity"],
                "specifications": {
                    "temperature": {"min": 15.0, "max": 30.0, "unit": "°C"},
                    "humidity": {"min": 35.0, "max": 75.0, "unit": "%RH"}
                }
            },
            "QC_LAB": {
                "location": "Quality Control Laboratory",
                "area_classification": "ISO 8",
                "parameters": ["temperature", "humidity", "pressure"],
                "specifications": {
                    "temperature": {"min": 20.0, "max": 25.0, "unit": "°C"},
                    "humidity": {"min": 45.0, "max": 65.0, "unit": "%RH"},
                    "pressure": {"min": 2.0, "max": 8.0, "unit": "Pa"}
                }
            }
        }
    
    async def record_environmental_reading(
        self,
        monitoring_point_id: str,
        parameter_type: EnvironmentalParameterType,
        measured_value: float,
        equipment_id: Optional[UUID] = None,
        operator_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record environmental monitoring reading
        """
        try:
            # Get monitoring point configuration
            if monitoring_point_id not in self.monitoring_points:
                raise ValueError(f"Unknown monitoring point: {monitoring_point_id}")
            
            point_config = self.monitoring_points[monitoring_point_id]
            parameter_specs = point_config["specifications"].get(parameter_type.value, {})
            
            # Check if parameter is within specification
            is_within_spec = True
            deviation_percentage = 0.0
            
            if "min" in parameter_specs and "max" in parameter_specs:
                min_val = parameter_specs["min"]
                max_val = parameter_specs["max"]
                
                if measured_value < min_val or measured_value > max_val:
                    is_within_spec = False
                    
                    # Calculate deviation percentage
                    target_range = max_val - min_val
                    if measured_value < min_val:
                        deviation_percentage = ((min_val - measured_value) / target_range) * 100
                    else:
                        deviation_percentage = ((measured_value - max_val) / target_range) * 100
            
            # Check for alert conditions
            alert_triggered = await self._check_alert_conditions(parameter_type, measured_value)
            corrective_action_required = not is_within_spec or alert_triggered
            
            # Create environmental monitoring record
            monitoring_record = EnvironmentalMonitoring(
                id=uuid4(),
                monitoring_point_id=monitoring_point_id,
                location=point_config["location"],
                area_classification=point_config["area_classification"],
                parameter_type=parameter_type,
                measured_value=measured_value,
                unit_of_measure=parameter_specs.get("unit", ""),
                specification_min=parameter_specs.get("min"),
                specification_max=parameter_specs.get("max"),
                is_within_specification=is_within_spec,
                deviation_percentage=deviation_percentage,
                measurement_timestamp=datetime.now(timezone.utc),
                equipment_id=equipment_id,
                operator_id=operator_id,
                alert_triggered=alert_triggered,
                corrective_action_required=corrective_action_required,
                notes=notes
            )
            
            # Store monitoring record
            await self._store_monitoring_record(monitoring_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=operator_id or uuid4(),
                username=await self._get_username(operator_id) if operator_id else "system",
                full_name=await self._get_full_name(operator_id) if operator_id else "System",
                action=AuditAction.CREATE,
                action_description=f"Environmental reading recorded: {parameter_type.value}",
                entity_type="environmental_monitoring",
                entity_id=monitoring_record.id,
                entity_identifier=f"{monitoring_point_id}:{parameter_type.value}",
                new_values={
                    "monitoring_point": monitoring_point_id,
                    "parameter_type": parameter_type.value,
                    "measured_value": measured_value,
                    "is_within_specification": is_within_spec,
                    "alert_triggered": alert_triggered
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=not is_within_spec
            )
            
            # Trigger alerts if necessary
            if alert_triggered or not is_within_spec:
                await self._trigger_environmental_alert(monitoring_record)
            
            logger.info(f"Environmental reading recorded: {monitoring_point_id} {parameter_type.value}={measured_value}")
            
            return {
                "reading_id": str(monitoring_record.id),
                "monitoring_point": monitoring_point_id,
                "parameter_type": parameter_type.value,
                "measured_value": measured_value,
                "is_within_specification": is_within_spec,
                "deviation_percentage": deviation_percentage,
                "alert_triggered": alert_triggered,
                "corrective_action_required": corrective_action_required,
                "timestamp": monitoring_record.measurement_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to record environmental reading: {str(e)}")
            raise
    
    async def start_continuous_monitoring(
        self,
        monitoring_interval_seconds: int = 60,
        user_id: Optional[UUID] = None
    ):
        """
        Start continuous environmental monitoring
        """
        try:
            self.monitoring_active = True
            logger.info(f"Starting continuous environmental monitoring (interval: {monitoring_interval_seconds}s)")
            
            while self.monitoring_active:
                # Simulate sensor readings for all monitoring points
                for point_id, point_config in self.monitoring_points.items():
                    for parameter in point_config["parameters"]:
                        # Generate simulated sensor reading
                        reading = await self._simulate_sensor_reading(point_id, parameter)
                        
                        # Record the reading
                        await self.record_environmental_reading(
                            monitoring_point_id=point_id,
                            parameter_type=EnvironmentalParameterType(parameter),
                            measured_value=reading["value"],
                            equipment_id=reading.get("equipment_id"),
                            operator_id=user_id,
                            notes="Continuous monitoring"
                        )
                
                # Wait for next monitoring cycle
                await asyncio.sleep(monitoring_interval_seconds)
                
        except Exception as e:
            logger.error(f"Continuous monitoring error: {str(e)}")
            self.monitoring_active = False
            raise
    
    async def stop_continuous_monitoring(self):
        """Stop continuous environmental monitoring"""
        self.monitoring_active = False
        logger.info("Continuous environmental monitoring stopped")
    
    async def get_current_conditions(
        self,
        monitoring_point_id: Optional[str] = None,
        parameter_type: Optional[EnvironmentalParameterType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get current environmental conditions
        """
        try:
            # Get recent readings (last 5 minutes)
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            readings = await self._get_recent_readings(cutoff_time, monitoring_point_id, parameter_type)
            
            current_conditions = []
            for reading in readings:
                condition = {
                    "monitoring_point": reading["monitoring_point_id"],
                    "location": reading["location"],
                    "parameter_type": reading["parameter_type"],
                    "current_value": reading["measured_value"],
                    "unit": reading["unit_of_measure"],
                    "specification_range": {
                        "min": reading["specification_min"],
                        "max": reading["specification_max"]
                    },
                    "is_within_specification": reading["is_within_specification"],
                    "alert_status": reading["alert_triggered"],
                    "last_reading": reading["measurement_timestamp"],
                    "trend": await self._calculate_trend(reading["monitoring_point_id"], reading["parameter_type"])
                }
                current_conditions.append(condition)
            
            return current_conditions
            
        except Exception as e:
            logger.error(f"Failed to get current conditions: {str(e)}")
            return []
    
    async def get_environmental_trends(
        self,
        monitoring_point_id: str,
        parameter_type: EnvironmentalParameterType,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get environmental trends and analysis
        """
        try:
            # Get historical readings
            readings = await self._get_historical_readings(
                monitoring_point_id, parameter_type, start_date, end_date
            )
            
            if not readings:
                return {
                    "monitoring_point": monitoring_point_id,
                    "parameter_type": parameter_type.value,
                    "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                    "data_points": 0,
                    "trend_analysis": "No data available"
                }
            
            # Calculate statistics
            values = [r["measured_value"] for r in readings]
            statistics = {
                "count": len(values),
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values)
            }
            
            # Calculate standard deviation
            mean = statistics["mean"]
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            statistics["std_dev"] = variance ** 0.5
            
            # Calculate compliance rate
            within_spec_count = sum(1 for r in readings if r["is_within_specification"])
            compliance_rate = (within_spec_count / len(readings)) * 100
            
            # Detect trends
            trend_analysis = await self._analyze_trends(readings)
            
            return {
                "monitoring_point": monitoring_point_id,
                "parameter_type": parameter_type.value,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "data_points": len(readings),
                "statistics": statistics,
                "compliance_rate": compliance_rate,
                "trend_analysis": trend_analysis,
                "readings": readings
            }
            
        except Exception as e:
            logger.error(f"Failed to get environmental trends: {str(e)}")
            return {"error": str(e)}
    
    async def generate_environmental_report(
        self,
        start_date: datetime,
        end_date: datetime,
        monitoring_points: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive environmental monitoring report
        """
        try:
            report = {
                "report_type": "environmental_monitoring",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "monitoring_points": {},
                "summary": {},
                "alerts": [],
                "recommendations": []
            }
            
            # Get data for each monitoring point
            points_to_analyze = monitoring_points or list(self.monitoring_points.keys())
            
            total_readings = 0
            total_excursions = 0
            
            for point_id in points_to_analyze:
                point_data = {
                    "location": self.monitoring_points[point_id]["location"],
                    "area_classification": self.monitoring_points[point_id]["area_classification"],
                    "parameters": {}
                }
                
                for parameter in self.monitoring_points[point_id]["parameters"]:
                    param_type = EnvironmentalParameterType(parameter)
                    trends = await self.get_environmental_trends(point_id, param_type, start_date, end_date)
                    
                    point_data["parameters"][parameter] = trends
                    total_readings += trends.get("data_points", 0)
                    
                    # Count excursions
                    if "readings" in trends:
                        excursions = sum(1 for r in trends["readings"] if not r["is_within_specification"])
                        total_excursions += excursions
                
                report["monitoring_points"][point_id] = point_data
            
            # Calculate summary statistics
            report["summary"] = {
                "total_readings": total_readings,
                "total_excursions": total_excursions,
                "compliance_rate": ((total_readings - total_excursions) / total_readings * 100) if total_readings > 0 else 0,
                "monitoring_points_analyzed": len(points_to_analyze)
            }
            
            # Get alerts during period
            report["alerts"] = await self._get_environmental_alerts(start_date, end_date)
            
            # Generate recommendations
            report["recommendations"] = await self._generate_environmental_recommendations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate environmental report: {str(e)}")
            return {"error": str(e)}
    
    async def _check_alert_conditions(
        self,
        parameter_type: EnvironmentalParameterType,
        measured_value: float
    ) -> bool:
        """Check if alert conditions are met"""
        param_name = parameter_type.value
        
        if param_name not in self.alert_thresholds:
            return False
        
        thresholds = self.alert_thresholds[param_name]
        
        # Check critical thresholds
        if "min_critical" in thresholds and measured_value <= thresholds["min_critical"]:
            return True
        if "max_critical" in thresholds and measured_value >= thresholds["max_critical"]:
            return True
        
        return False
    
    async def _simulate_sensor_reading(self, point_id: str, parameter: str) -> Dict[str, Any]:
        """Simulate sensor readings for demonstration"""
        import random
        
        point_config = self.monitoring_points[point_id]
        specs = point_config["specifications"].get(parameter, {})
        
        if parameter == "temperature":
            # Generate temperature reading within normal range with occasional variations
            base_value = (specs.get("min", 20) + specs.get("max", 25)) / 2
            variation = random.normalvariate(0, 0.5)
            value = base_value + variation
        elif parameter == "humidity":
            # Generate humidity reading
            base_value = (specs.get("min", 45) + specs.get("max", 65)) / 2
            variation = random.normalvariate(0, 2.0)
            value = base_value + variation
        elif parameter == "pressure":
            # Generate pressure reading
            base_value = (specs.get("min", 5) + specs.get("max", 15)) / 2
            variation = random.normalvariate(0, 1.0)
            value = base_value + variation
        elif parameter == "particle_count":
            # Generate particle count based on ISO classification
            classification = specs.get("classification", "ISO 8")
            if classification == "ISO 5":
                value = random.randint(1000, 3000)
            elif classification == "ISO 7":
                value = random.randint(100000, 300000)
            else:
                value = random.randint(1000000, 3000000)
        else:
            value = random.normalvariate(50, 5)
        
        return {
            "value": round(value, 2),
            "equipment_id": uuid4()  # Simulated equipment ID
        }
    
    async def _trigger_environmental_alert(self, monitoring_record: EnvironmentalMonitoring):
        """Trigger environmental alert"""
        alert_message = f"Environmental excursion detected at {monitoring_record.location}: "
        alert_message += f"{monitoring_record.parameter_type.value} = {monitoring_record.measured_value} "
        alert_message += f"{monitoring_record.unit_of_measure}"
        
        logger.warning(alert_message)
        
        # In a real system, this would send notifications, emails, SMS, etc.
        # For now, we'll just log the alert
    
    async def _calculate_trend(self, monitoring_point_id: str, parameter_type: str) -> str:
        """Calculate parameter trend"""
        # This would analyze recent data to determine if the parameter is trending up, down, or stable
        # For now, return a simple trend indicator
        return "stable"
    
    async def _analyze_trends(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in environmental data"""
        if len(readings) < 2:
            return {"trend": "insufficient_data"}
        
        # Simple trend analysis based on first and last values
        first_value = readings[0]["measured_value"]
        last_value = readings[-1]["measured_value"]
        
        change_percentage = ((last_value - first_value) / first_value) * 100
        
        if abs(change_percentage) < 2:
            trend = "stable"
        elif change_percentage > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        return {
            "trend": trend,
            "change_percentage": round(change_percentage, 2),
            "analysis_period": f"{len(readings)} readings"
        }
    
    async def _generate_environmental_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on environmental data"""
        recommendations = []
        
        if report["summary"]["compliance_rate"] < 95:
            recommendations.append("Review and improve environmental control systems")
        
        if report["summary"]["total_excursions"] > 0:
            recommendations.append("Investigate root causes of environmental excursions")
        
        recommendations.append("Continue regular calibration of monitoring equipment")
        recommendations.append("Review environmental control procedures quarterly")
        
        return recommendations
    
    # Database operations (these would integrate with actual database)
    async def _store_monitoring_record(self, record: EnvironmentalMonitoring):
        """Store monitoring record in database"""
        logger.debug(f"Storing environmental monitoring record {record.id}")
    
    async def _get_recent_readings(
        self,
        cutoff_time: datetime,
        monitoring_point_id: Optional[str] = None,
        parameter_type: Optional[EnvironmentalParameterType] = None
    ) -> List[Dict[str, Any]]:
        """Get recent environmental readings"""
        # This would query the database for recent readings
        return []
    
    async def _get_historical_readings(
        self,
        monitoring_point_id: str,
        parameter_type: EnvironmentalParameterType,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get historical environmental readings"""
        # This would query the database for historical readings
        return []
    
    async def _get_environmental_alerts(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get environmental alerts during period"""
        return []
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"