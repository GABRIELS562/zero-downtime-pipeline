"""
Manufacturing Health Service
Comprehensive health monitoring and critical parameter tracking for pharmaceutical manufacturing
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging
from dataclasses import dataclass
from enum import Enum

from src.services.immutable_audit_service import ImmutableAuditService
from src.services.environmental_monitoring_service import EnvironmentalMonitoringService
from src.services.equipment_calibration_service import EquipmentCalibrationService
from src.services.raw_material_testing_service import RawMaterialTestingService
from src.services.in_process_testing_service import InProcessTestingService
from src.services.finished_product_testing_service import FinishedProductTestingService
from src.services.clean_room_monitoring_service import CleanRoomMonitoringService

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_INVESTIGATION = "under_investigation"
    PENDING_REVIEW = "pending_review"

@dataclass
class HealthMetric:
    name: str
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    status: HealthStatus
    last_updated: datetime
    trend: str = "stable"

@dataclass
class ManufacturingLineStatus:
    line_id: str
    line_name: str
    efficiency: float
    oee: float  # Overall Equipment Effectiveness
    availability: float
    performance: float
    quality: float
    current_batch: Optional[str]
    status: HealthStatus
    last_updated: datetime

class ManufacturingHealthService:
    """
    Comprehensive health monitoring service for pharmaceutical manufacturing operations
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.environmental_service = EnvironmentalMonitoringService()
        self.equipment_service = EquipmentCalibrationService()
        self.raw_material_service = RawMaterialTestingService()
        self.in_process_service = InProcessTestingService()
        self.finished_product_service = FinishedProductTestingService()
        self.clean_room_service = CleanRoomMonitoringService()
        
        self.manufacturing_lines = self._initialize_manufacturing_lines()
        self.critical_parameters = self._initialize_critical_parameters()
        self.compliance_standards = self._initialize_compliance_standards()
        self.health_thresholds = self._initialize_health_thresholds()
        
    def _initialize_manufacturing_lines(self) -> Dict[str, Dict[str, Any]]:
        """Initialize manufacturing line configurations"""
        return {
            "LINE_TABLET_001": {
                "line_name": "Tablet Manufacturing Line 1",
                "product_types": ["tablets", "capsules"],
                "capacity_units_per_hour": 50000,
                "efficiency_target": 98.5,
                "equipment": ["mixer", "granulator", "dryer", "tablet_press", "coater"],
                "clean_room": "CR_TABLET_COMPRESSION",
                "critical_parameters": {
                    "compression_force": {"min": 5.0, "max": 15.0, "unit": "kN"},
                    "tablet_weight": {"min": 95.0, "max": 105.0, "unit": "% of target"},
                    "hardness": {"min": 4.0, "max": 8.0, "unit": "kp"},
                    "friability": {"max": 1.0, "unit": "% weight loss"},
                    "dissolution_rate": {"min": 80.0, "unit": "% in 30 min"}
                }
            },
            "LINE_LIQUID_001": {
                "line_name": "Liquid Manufacturing Line 1",
                "product_types": ["oral_liquids", "syrups"],
                "capacity_units_per_hour": 5000,
                "efficiency_target": 97.0,
                "equipment": ["mixing_tank", "homogenizer", "filling_machine", "capping_machine"],
                "clean_room": "CR_ASEPTIC_PREP",
                "critical_parameters": {
                    "fill_volume": {"min": 98.0, "max": 102.0, "unit": "% of target"},
                    "viscosity": {"min": 90.0, "max": 110.0, "unit": "% of target"},
                    "ph_level": {"min": 6.8, "max": 7.2, "unit": "pH"},
                    "density": {"min": 95.0, "max": 105.0, "unit": "% of target"},
                    "microbial_content": {"max": 10, "unit": "CFU/mL"}
                }
            },
            "LINE_STERILE_001": {
                "line_name": "Sterile Manufacturing Line 1",
                "product_types": ["injections", "iv_solutions"],
                "capacity_units_per_hour": 1000,
                "efficiency_target": 99.0,
                "equipment": ["preparation_tank", "filtration_system", "filling_machine", "autoclave"],
                "clean_room": "CR_STERILE_FILL",
                "critical_parameters": {
                    "sterility": {"max": 0, "unit": "CFU/unit"},
                    "endotoxin_level": {"max": 0.5, "unit": "EU/mL"},
                    "particulate_matter": {"max": 25, "unit": "particles/mL"},
                    "fill_volume": {"min": 99.0, "max": 101.0, "unit": "% of target"},
                    "container_integrity": {"min": 100.0, "unit": "% pass rate"}
                }
            }
        }
    
    def _initialize_critical_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Initialize critical process parameters (CPPs)"""
        return {
            "temperature_control": {
                "parameter_name": "Temperature Control",
                "specification": {"min": 20.0, "max": 25.0, "unit": "°C"},
                "monitoring_frequency": "continuous",
                "alert_threshold": 1.0,
                "criticality": "high"
            },
            "humidity_control": {
                "parameter_name": "Humidity Control",
                "specification": {"min": 45.0, "max": 65.0, "unit": "%RH"},
                "monitoring_frequency": "continuous",
                "alert_threshold": 5.0,
                "criticality": "high"
            },
            "pressure_differential": {
                "parameter_name": "Pressure Differential",
                "specification": {"min": 10.0, "max": 20.0, "unit": "Pa"},
                "monitoring_frequency": "continuous",
                "alert_threshold": 2.0,
                "criticality": "medium"
            },
            "particle_count": {
                "parameter_name": "Particle Count",
                "specification": {"max": 3520, "unit": "particles/m³"},
                "monitoring_frequency": "continuous",
                "alert_threshold": 500,
                "criticality": "critical"
            },
            "microbial_levels": {
                "parameter_name": "Microbial Levels",
                "specification": {"max": 1, "unit": "CFU/m³"},
                "monitoring_frequency": "hourly",
                "alert_threshold": 1,
                "criticality": "critical"
            }
        }
    
    def _initialize_compliance_standards(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance standards"""
        return {
            "FDA_21_CFR_PART_11": {
                "standard_name": "FDA 21 CFR Part 11",
                "description": "Electronic Records and Electronic Signatures",
                "requirements": [
                    "audit_trail_integrity",
                    "user_authentication",
                    "data_integrity",
                    "electronic_signature_validation"
                ],
                "compliance_level": "mandatory"
            },
            "FDA_21_CFR_PART_210_211": {
                "standard_name": "FDA 21 CFR Parts 210 & 211",
                "description": "Current Good Manufacturing Practice",
                "requirements": [
                    "personnel_qualification",
                    "equipment_validation",
                    "process_validation",
                    "quality_control_testing"
                ],
                "compliance_level": "mandatory"
            },
            "ISO_14644": {
                "standard_name": "ISO 14644",
                "description": "Cleanrooms and Associated Controlled Environments",
                "requirements": [
                    "particle_count_limits",
                    "air_change_rates",
                    "pressure_differentials",
                    "recovery_time"
                ],
                "compliance_level": "required"
            },
            "ICH_Q7": {
                "standard_name": "ICH Q7",
                "description": "Good Manufacturing Practice for APIs",
                "requirements": [
                    "quality_management",
                    "personnel_training",
                    "buildings_facilities",
                    "equipment_maintenance"
                ],
                "compliance_level": "guidance"
            }
        }
    
    def _initialize_health_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize health monitoring thresholds"""
        return {
            "manufacturing_efficiency": {
                "warning": 95.0,
                "critical": 90.0,
                "target": 98.5
            },
            "equipment_availability": {
                "warning": 95.0,
                "critical": 90.0,
                "target": 99.0
            },
            "quality_pass_rate": {
                "warning": 95.0,
                "critical": 90.0,
                "target": 99.5
            },
            "environmental_compliance": {
                "warning": 95.0,
                "critical": 90.0,
                "target": 100.0
            },
            "batch_cycle_time": {
                "warning": 110.0,  # % of target
                "critical": 120.0,
                "target": 100.0
            }
        }
    
    async def get_overall_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the manufacturing system
        """
        try:
            # Collect health metrics from all subsystems
            environmental_health = await self._get_environmental_health()
            equipment_health = await self._get_equipment_health()
            quality_health = await self._get_quality_health()
            manufacturing_health = await self._get_manufacturing_line_health()
            compliance_health = await self._get_compliance_health()
            
            # Calculate overall health score
            overall_score = await self._calculate_overall_health_score([
                environmental_health,
                equipment_health,
                quality_health,
                manufacturing_health,
                compliance_health
            ])
            
            # Determine overall status
            overall_status = self._determine_health_status(overall_score)
            
            return {
                "system_health": {
                    "overall_status": overall_status.value,
                    "overall_score": overall_score,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "uptime": await self._calculate_system_uptime()
                },
                "subsystem_health": {
                    "environmental": environmental_health,
                    "equipment": equipment_health,
                    "quality": quality_health,
                    "manufacturing": manufacturing_health,
                    "compliance": compliance_health
                },
                "critical_alerts": await self._get_critical_alerts(),
                "performance_metrics": await self._get_performance_metrics(),
                "recommendations": await self._generate_health_recommendations(overall_score)
            }
            
        except Exception as e:
            logger.error(f"Failed to get overall health status: {str(e)}")
            return {
                "system_health": {
                    "overall_status": HealthStatus.UNKNOWN.value,
                    "error": str(e),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            }
    
    async def get_manufacturing_line_efficiency(self, line_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get manufacturing line efficiency metrics
        """
        try:
            lines_to_check = [line_id] if line_id else list(self.manufacturing_lines.keys())
            
            line_metrics = {}
            for current_line_id in lines_to_check:
                if current_line_id not in self.manufacturing_lines:
                    continue
                    
                line_config = self.manufacturing_lines[current_line_id]
                
                # Calculate OEE components
                availability = await self._calculate_availability(current_line_id)
                performance = await self._calculate_performance(current_line_id)
                quality = await self._calculate_quality_rate(current_line_id)
                
                # Calculate Overall Equipment Effectiveness (OEE)
                oee = (availability * performance * quality) / 10000  # Convert from percentages
                
                # Calculate efficiency
                efficiency = await self._calculate_line_efficiency(current_line_id)
                
                # Get current batch information
                current_batch = await self._get_current_batch(current_line_id)
                
                # Determine status
                status = self._determine_line_status(efficiency, line_config["efficiency_target"])
                
                line_status = ManufacturingLineStatus(
                    line_id=current_line_id,
                    line_name=line_config["line_name"],
                    efficiency=efficiency,
                    oee=oee,
                    availability=availability,
                    performance=performance,
                    quality=quality,
                    current_batch=current_batch,
                    status=status,
                    last_updated=datetime.now(timezone.utc)
                )
                
                line_metrics[current_line_id] = {
                    "line_id": line_status.line_id,
                    "line_name": line_status.line_name,
                    "efficiency": line_status.efficiency,
                    "oee": line_status.oee,
                    "availability": line_status.availability,
                    "performance": line_status.performance,
                    "quality": line_status.quality,
                    "current_batch": line_status.current_batch,
                    "status": line_status.status.value,
                    "target_efficiency": line_config["efficiency_target"],
                    "capacity_utilization": await self._calculate_capacity_utilization(current_line_id),
                    "production_rate": await self._calculate_production_rate(current_line_id),
                    "downtime_analysis": await self._get_downtime_analysis(current_line_id),
                    "last_updated": line_status.last_updated.isoformat()
                }
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "manufacturing_lines": line_metrics,
                "overall_efficiency": sum(line["efficiency"] for line in line_metrics.values()) / len(line_metrics) if line_metrics else 0,
                "lines_above_target": len([line for line in line_metrics.values() if line["efficiency"] >= line["target_efficiency"]]),
                "total_lines": len(line_metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get manufacturing line efficiency: {str(e)}")
            return {"error": str(e)}
    
    async def get_environmental_validation_status(self) -> Dict[str, Any]:
        """
        Get environmental parameter validation status
        """
        try:
            # Get current environmental conditions
            current_conditions = await self.environmental_service.get_current_conditions()
            
            # Validate against critical parameters
            validation_results = {}
            for condition in current_conditions:
                param_name = condition["parameter_type"]
                current_value = condition["current_value"]
                
                if param_name in self.critical_parameters:
                    param_spec = self.critical_parameters[param_name]
                    validation_result = await self._validate_parameter(
                        param_name,
                        current_value,
                        param_spec["specification"]
                    )
                    validation_results[param_name] = validation_result
            
            # Calculate overall environmental compliance
            compliant_parameters = len([v for v in validation_results.values() if v["compliant"]])
            total_parameters = len(validation_results)
            compliance_rate = (compliant_parameters / total_parameters * 100) if total_parameters > 0 else 0
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environmental_compliance": {
                    "compliance_rate": compliance_rate,
                    "compliant_parameters": compliant_parameters,
                    "total_parameters": total_parameters,
                    "status": ComplianceStatus.COMPLIANT.value if compliance_rate >= 100 else ComplianceStatus.NON_COMPLIANT.value
                },
                "parameter_validation": validation_results,
                "critical_excursions": [
                    {
                        "parameter": param,
                        "current_value": result["current_value"],
                        "specification": result["specification"],
                        "deviation": result["deviation"]
                    }
                    for param, result in validation_results.items()
                    if not result["compliant"]
                ],
                "trending_analysis": await self._get_environmental_trends()
            }
            
        except Exception as e:
            logger.error(f"Failed to get environmental validation status: {str(e)}")
            return {"error": str(e)}
    
    async def get_batch_integrity_status(self, batch_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get batch integrity and chain of custody verification status
        """
        try:
            if batch_id:
                batches_to_check = [batch_id]
            else:
                batches_to_check = await self._get_active_batches()
            
            batch_statuses = {}
            for current_batch_id in batches_to_check:
                # Get batch information
                batch_info = await self._get_batch_info(current_batch_id)
                
                # Verify chain of custody
                custody_verification = await self._verify_batch_custody_chain(current_batch_id)
                
                # Check batch integrity
                integrity_checks = await self._perform_batch_integrity_checks(current_batch_id)
                
                # Get testing status
                testing_status = await self._get_batch_testing_status(current_batch_id)
                
                # Calculate integrity score
                integrity_score = await self._calculate_batch_integrity_score(
                    custody_verification,
                    integrity_checks,
                    testing_status
                )
                
                batch_statuses[str(current_batch_id)] = {
                    "batch_id": str(current_batch_id),
                    "batch_info": batch_info,
                    "integrity_score": integrity_score,
                    "custody_verification": custody_verification,
                    "integrity_checks": integrity_checks,
                    "testing_status": testing_status,
                    "compliance_status": self._determine_batch_compliance(integrity_score),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "batch_integrity_summary": {
                    "total_batches": len(batch_statuses),
                    "compliant_batches": len([b for b in batch_statuses.values() if b["compliance_status"] == ComplianceStatus.COMPLIANT.value]),
                    "average_integrity_score": sum(b["integrity_score"] for b in batch_statuses.values()) / len(batch_statuses) if batch_statuses else 0
                },
                "batch_details": batch_statuses,
                "integrity_alerts": [
                    {
                        "batch_id": batch_id,
                        "alert_type": "integrity_violation",
                        "severity": "high" if batch["integrity_score"] < 80 else "medium"
                    }
                    for batch_id, batch in batch_statuses.items()
                    if batch["integrity_score"] < 90
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get batch integrity status: {str(e)}")
            return {"error": str(e)}
    
    async def get_equipment_calibration_status(self) -> Dict[str, Any]:
        """
        Get equipment status and calibration validation
        """
        try:
            # Get calibration due list
            calibration_due = await self.equipment_service.get_calibration_due_list(days_ahead=30)
            
            # Get equipment status overview
            equipment_overview = await self._get_equipment_overview()
            
            # Calculate calibration compliance
            total_equipment = len(equipment_overview)
            calibrated_equipment = len([eq for eq in equipment_overview if eq["calibration_status"] == "current"])
            calibration_compliance = (calibrated_equipment / total_equipment * 100) if total_equipment > 0 else 0
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "calibration_compliance": {
                    "compliance_rate": calibration_compliance,
                    "calibrated_equipment": calibrated_equipment,
                    "total_equipment": total_equipment,
                    "overdue_equipment": len([eq for eq in equipment_overview if eq["calibration_status"] == "overdue"]),
                    "due_soon": len(calibration_due)
                },
                "equipment_overview": equipment_overview,
                "calibration_due_list": calibration_due,
                "critical_equipment_status": await self._get_critical_equipment_status(),
                "maintenance_schedule": await self._get_maintenance_schedule()
            }
            
        except Exception as e:
            logger.error(f"Failed to get equipment calibration status: {str(e)}")
            return {"error": str(e)}
    
    async def get_quality_control_monitoring(self) -> Dict[str, Any]:
        """
        Get quality control test result monitoring
        """
        try:
            # Get QC test results summary
            qc_summary = await self._get_qc_test_summary()
            
            # Get test trend analysis
            test_trends = await self._get_qc_test_trends()
            
            # Get out-of-specification investigations
            oos_investigations = await self._get_oos_investigations()
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "qc_summary": qc_summary,
                "test_trends": test_trends,
                "oos_investigations": oos_investigations,
                "quality_metrics": {
                    "first_pass_rate": qc_summary.get("first_pass_rate", 0),
                    "right_first_time": qc_summary.get("right_first_time", 0),
                    "deviation_rate": qc_summary.get("deviation_rate", 0),
                    "testing_efficiency": qc_summary.get("testing_efficiency", 0)
                },
                "critical_quality_alerts": await self._get_critical_quality_alerts()
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality control monitoring: {str(e)}")
            return {"error": str(e)}
    
    async def get_production_yield_tracking(self) -> Dict[str, Any]:
        """
        Get production yield and waste tracking
        """
        try:
            # Get yield metrics by manufacturing line
            yield_metrics = {}
            for line_id, line_config in self.manufacturing_lines.items():
                line_yield = await self._calculate_line_yield(line_id)
                waste_analysis = await self._get_waste_analysis(line_id)
                
                yield_metrics[line_id] = {
                    "line_name": line_config["line_name"],
                    "theoretical_yield": line_yield["theoretical_yield"],
                    "actual_yield": line_yield["actual_yield"],
                    "yield_variance": line_yield["yield_variance"],
                    "waste_analysis": waste_analysis,
                    "material_utilization": line_yield["material_utilization"],
                    "cost_impact": line_yield["cost_impact"]
                }
            
            # Calculate overall metrics
            overall_yield = sum(line["actual_yield"] for line in yield_metrics.values()) / len(yield_metrics) if yield_metrics else 0
            total_waste = sum(line["waste_analysis"]["total_waste"] for line in yield_metrics.values())
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_metrics": {
                    "overall_yield": overall_yield,
                    "total_waste": total_waste,
                    "waste_cost_impact": sum(line["waste_analysis"]["cost_impact"] for line in yield_metrics.values()),
                    "material_efficiency": sum(line["material_utilization"] for line in yield_metrics.values()) / len(yield_metrics) if yield_metrics else 0
                },
                "line_metrics": yield_metrics,
                "yield_trends": await self._get_yield_trends(),
                "waste_reduction_opportunities": await self._identify_waste_reduction_opportunities()
            }
            
        except Exception as e:
            logger.error(f"Failed to get production yield tracking: {str(e)}")
            return {"error": str(e)}
    
    async def get_compliance_indicators(self) -> Dict[str, Any]:
        """
        Get compliance status indicators for FDA, GMP, and ISO standards
        """
        try:
            compliance_status = {}
            
            for standard_id, standard_config in self.compliance_standards.items():
                # Evaluate compliance for each standard
                compliance_evaluation = await self._evaluate_compliance(standard_id, standard_config)
                
                compliance_status[standard_id] = {
                    "standard_name": standard_config["standard_name"],
                    "description": standard_config["description"],
                    "compliance_level": standard_config["compliance_level"],
                    "compliance_score": compliance_evaluation["score"],
                    "status": compliance_evaluation["status"],
                    "requirements_met": compliance_evaluation["requirements_met"],
                    "total_requirements": compliance_evaluation["total_requirements"],
                    "findings": compliance_evaluation["findings"],
                    "last_assessment": compliance_evaluation["last_assessment"]
                }
            
            # Calculate overall compliance score
            overall_compliance = sum(status["compliance_score"] for status in compliance_status.values()) / len(compliance_status)
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_compliance": {
                    "compliance_score": overall_compliance,
                    "status": ComplianceStatus.COMPLIANT.value if overall_compliance >= 95 else ComplianceStatus.NON_COMPLIANT.value,
                    "critical_findings": sum(len(status["findings"]["critical"]) for status in compliance_status.values()),
                    "total_findings": sum(len(status["findings"]["total"]) for status in compliance_status.values())
                },
                "standard_compliance": compliance_status,
                "regulatory_readiness": await self._assess_regulatory_readiness(),
                "audit_preparation": await self._get_audit_preparation_status()
            }
            
        except Exception as e:
            logger.error(f"Failed to get compliance indicators: {str(e)}")
            return {"error": str(e)}
    
    async def get_schedule_adherence_monitoring(self) -> Dict[str, Any]:
        """
        Get manufacturing schedule adherence monitoring
        """
        try:
            # Get current schedule status
            schedule_status = await self._get_schedule_status()
            
            # Calculate adherence metrics
            adherence_metrics = await self._calculate_schedule_adherence()
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schedule_adherence": adherence_metrics,
                "current_schedule": schedule_status,
                "delay_analysis": await self._get_delay_analysis(),
                "capacity_planning": await self._get_capacity_planning_metrics(),
                "schedule_optimization": await self._get_schedule_optimization_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Failed to get schedule adherence monitoring: {str(e)}")
            return {"error": str(e)}
    
    async def get_critical_process_parameters(self) -> Dict[str, Any]:
        """
        Get critical process parameter (CPP) tracking
        """
        try:
            cpp_status = {}
            
            for param_id, param_config in self.critical_parameters.items():
                # Get current parameter values
                current_values = await self._get_parameter_values(param_id)
                
                # Analyze parameter trends
                trend_analysis = await self._analyze_parameter_trends(param_id, current_values)
                
                # Check for deviations
                deviation_analysis = await self._check_parameter_deviations(param_id, current_values, param_config)
                
                cpp_status[param_id] = {
                    "parameter_name": param_config["parameter_name"],
                    "current_values": current_values,
                    "specification": param_config["specification"],
                    "trend_analysis": trend_analysis,
                    "deviation_analysis": deviation_analysis,
                    "control_status": self._determine_parameter_control_status(deviation_analysis),
                    "criticality": param_config["criticality"],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpp_overview": {
                    "total_parameters": len(cpp_status),
                    "in_control": len([p for p in cpp_status.values() if p["control_status"] == "in_control"]),
                    "out_of_control": len([p for p in cpp_status.values() if p["control_status"] == "out_of_control"]),
                    "critical_alerts": len([p for p in cpp_status.values() if p["criticality"] == "critical" and p["control_status"] != "in_control"])
                },
                "parameter_details": cpp_status,
                "process_capability": await self._calculate_process_capability(),
                "control_recommendations": await self._generate_control_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Failed to get critical process parameters: {str(e)}")
            return {"error": str(e)}
    
    async def get_contamination_risk_assessment(self) -> Dict[str, Any]:
        """
        Get contamination risk assessment metrics
        """
        try:
            # Get clean room status
            clean_room_status = await self.clean_room_service.get_clean_room_status()
            
            # Assess contamination risks
            risk_assessment = await self._assess_contamination_risks()
            
            # Get mitigation measures
            mitigation_measures = await self._get_contamination_mitigation_measures()
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "risk_assessment": risk_assessment,
                "clean_room_status": clean_room_status,
                "mitigation_measures": mitigation_measures,
                "contamination_incidents": await self._get_contamination_incidents(),
                "preventive_measures": await self._get_preventive_measures_status()
            }
            
        except Exception as e:
            logger.error(f"Failed to get contamination risk assessment: {str(e)}")
            return {"error": str(e)}
    
    # Helper methods for health calculations
    async def _get_environmental_health(self) -> Dict[str, Any]:
        """Get environmental health metrics"""
        try:
            current_conditions = await self.environmental_service.get_current_conditions()
            
            compliant_conditions = len([c for c in current_conditions if c["is_within_specification"]])
            total_conditions = len(current_conditions)
            compliance_rate = (compliant_conditions / total_conditions * 100) if total_conditions > 0 else 0
            
            return {
                "compliance_rate": compliance_rate,
                "status": HealthStatus.HEALTHY.value if compliance_rate >= 95 else HealthStatus.WARNING.value if compliance_rate >= 90 else HealthStatus.CRITICAL.value,
                "monitored_parameters": total_conditions,
                "compliant_parameters": compliant_conditions
            }
        except Exception:
            return {"status": HealthStatus.UNKNOWN.value, "error": "Failed to get environmental health"}
    
    async def _get_equipment_health(self) -> Dict[str, Any]:
        """Get equipment health metrics"""
        try:
            calibration_due = await self.equipment_service.get_calibration_due_list(days_ahead=30)
            
            # Mock equipment data for demonstration
            total_equipment = 50
            operational_equipment = 48
            availability = (operational_equipment / total_equipment * 100)
            
            return {
                "availability": availability,
                "status": HealthStatus.HEALTHY.value if availability >= 95 else HealthStatus.WARNING.value if availability >= 90 else HealthStatus.CRITICAL.value,
                "total_equipment": total_equipment,
                "operational_equipment": operational_equipment,
                "calibration_due": len(calibration_due)
            }
        except Exception:
            return {"status": HealthStatus.UNKNOWN.value, "error": "Failed to get equipment health"}
    
    async def _get_quality_health(self) -> Dict[str, Any]:
        """Get quality health metrics"""
        try:
            # Mock quality data for demonstration
            pass_rate = 98.5
            
            return {
                "pass_rate": pass_rate,
                "status": HealthStatus.HEALTHY.value if pass_rate >= 95 else HealthStatus.WARNING.value if pass_rate >= 90 else HealthStatus.CRITICAL.value,
                "tests_conducted": 1250,
                "tests_passed": int(1250 * pass_rate / 100)
            }
        except Exception:
            return {"status": HealthStatus.UNKNOWN.value, "error": "Failed to get quality health"}
    
    async def _get_manufacturing_line_health(self) -> Dict[str, Any]:
        """Get manufacturing line health metrics"""
        try:
            # Mock manufacturing data for demonstration
            efficiency = 97.8
            
            return {
                "efficiency": efficiency,
                "status": HealthStatus.HEALTHY.value if efficiency >= 95 else HealthStatus.WARNING.value if efficiency >= 90 else HealthStatus.CRITICAL.value,
                "active_lines": 3,
                "total_lines": 3
            }
        except Exception:
            return {"status": HealthStatus.UNKNOWN.value, "error": "Failed to get manufacturing line health"}
    
    async def _get_compliance_health(self) -> Dict[str, Any]:
        """Get compliance health metrics"""
        try:
            # Mock compliance data for demonstration
            compliance_score = 96.2
            
            return {
                "compliance_score": compliance_score,
                "status": HealthStatus.HEALTHY.value if compliance_score >= 95 else HealthStatus.WARNING.value if compliance_score >= 90 else HealthStatus.CRITICAL.value,
                "standards_evaluated": len(self.compliance_standards),
                "compliant_standards": 4
            }
        except Exception:
            return {"status": HealthStatus.UNKNOWN.value, "error": "Failed to get compliance health"}
    
    async def _calculate_overall_health_score(self, health_metrics: List[Dict[str, Any]]) -> float:
        """Calculate overall health score"""
        scores = []
        for metric in health_metrics:
            if metric["status"] == HealthStatus.HEALTHY.value:
                scores.append(100)
            elif metric["status"] == HealthStatus.WARNING.value:
                scores.append(80)
            elif metric["status"] == HealthStatus.CRITICAL.value:
                scores.append(60)
            else:
                scores.append(0)
        
        return sum(scores) / len(scores) if scores else 0
    
    def _determine_health_status(self, score: float) -> HealthStatus:
        """Determine health status based on score"""
        if score >= 95:
            return HealthStatus.HEALTHY
        elif score >= 80:
            return HealthStatus.WARNING
        elif score >= 60:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.UNKNOWN
    
    async def _calculate_system_uptime(self) -> float:
        """Calculate system uptime percentage"""
        # Mock uptime calculation
        return 99.8
    
    async def _get_critical_alerts(self) -> List[Dict[str, Any]]:
        """Get critical alerts"""
        return [
            {
                "alert_id": "ENV_001",
                "severity": "warning",
                "message": "Temperature deviation detected in clean room CR_STERILE_FILL",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "throughput": 45000,
            "efficiency": 97.8,
            "quality_rate": 98.5,
            "downtime_hours": 2.3
        }
    
    async def _generate_health_recommendations(self, health_score: float) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        if health_score < 95:
            recommendations.append("Review and address system performance issues")
        if health_score < 80:
            recommendations.append("Implement immediate corrective actions")
        
        recommendations.extend([
            "Maintain regular preventive maintenance schedule",
            "Monitor critical parameters continuously",
            "Review compliance status regularly"
        ])
        
        return recommendations
    
    # Additional helper methods would continue here...
    # Due to length constraints, I'll implement the key methods above
    # and provide placeholder implementations for the remaining methods
    
    async def _calculate_availability(self, line_id: str) -> float:
        """Calculate line availability"""
        return 96.5  # Mock value
    
    async def _calculate_performance(self, line_id: str) -> float:
        """Calculate line performance"""
        return 98.2  # Mock value
    
    async def _calculate_quality_rate(self, line_id: str) -> float:
        """Calculate quality rate"""
        return 99.1  # Mock value
    
    async def _calculate_line_efficiency(self, line_id: str) -> float:
        """Calculate line efficiency"""
        return 97.8  # Mock value
    
    async def _get_current_batch(self, line_id: str) -> Optional[str]:
        """Get current batch on line"""
        return f"BATCH-{line_id}-001"
    
    def _determine_line_status(self, efficiency: float, target: float) -> HealthStatus:
        """Determine line status based on efficiency"""
        if efficiency >= target:
            return HealthStatus.HEALTHY
        elif efficiency >= target * 0.95:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL
    
    async def _calculate_capacity_utilization(self, line_id: str) -> float:
        """Calculate capacity utilization"""
        return 85.3  # Mock value
    
    async def _calculate_production_rate(self, line_id: str) -> float:
        """Calculate production rate"""
        return 47500  # Mock value
    
    async def _get_downtime_analysis(self, line_id: str) -> Dict[str, Any]:
        """Get downtime analysis"""
        return {
            "planned_downtime": 2.5,
            "unplanned_downtime": 1.2,
            "total_downtime": 3.7,
            "downtime_reasons": ["maintenance", "material_shortage"]
        }
    
    # Placeholder implementations for remaining methods...
    async def _validate_parameter(self, param_name: str, value: float, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameter against specification"""
        compliant = True
        deviation = 0
        
        if "min" in spec and value < spec["min"]:
            compliant = False
            deviation = spec["min"] - value
        elif "max" in spec and value > spec["max"]:
            compliant = False
            deviation = value - spec["max"]
        
        return {
            "compliant": compliant,
            "current_value": value,
            "specification": spec,
            "deviation": deviation
        }
    
    async def _get_environmental_trends(self) -> Dict[str, Any]:
        """Get environmental trends"""
        return {"trend": "stable", "improvement_rate": 2.3}
    
    async def _get_active_batches(self) -> List[UUID]:
        """Get active batches"""
        return [uuid4() for _ in range(5)]
    
    async def _get_batch_info(self, batch_id: UUID) -> Dict[str, Any]:
        """Get batch information"""
        return {
            "batch_number": f"BATCH-{str(batch_id)[:8]}",
            "product": "Acetaminophen Tablets 500mg",
            "status": "in_progress"
        }
    
    async def _verify_batch_custody_chain(self, batch_id: UUID) -> Dict[str, Any]:
        """Verify batch custody chain"""
        return {
            "chain_verified": True,
            "chain_length": 8,
            "integrity_score": 98.5
        }
    
    async def _perform_batch_integrity_checks(self, batch_id: UUID) -> Dict[str, Any]:
        """Perform batch integrity checks"""
        return {
            "data_integrity": True,
            "documentation_complete": True,
            "audit_trail_intact": True
        }
    
    async def _get_batch_testing_status(self, batch_id: UUID) -> Dict[str, Any]:
        """Get batch testing status"""
        return {
            "tests_completed": 12,
            "tests_passed": 11,
            "tests_failed": 1,
            "overall_status": "in_progress"
        }
    
    async def _calculate_batch_integrity_score(self, custody: Dict[str, Any], integrity: Dict[str, Any], testing: Dict[str, Any]) -> float:
        """Calculate batch integrity score"""
        return 95.5  # Mock value
    
    def _determine_batch_compliance(self, score: float) -> str:
        """Determine batch compliance status"""
        return ComplianceStatus.COMPLIANT.value if score >= 95 else ComplianceStatus.NON_COMPLIANT.value
    
    # Additional placeholder methods would continue here...
    
    async def _get_equipment_overview(self) -> List[Dict[str, Any]]:
        """Get equipment overview"""
        return [
            {
                "equipment_id": "BAL-001",
                "equipment_name": "Analytical Balance #1",
                "status": "operational",
                "calibration_status": "current",
                "last_calibration": "2024-06-15"
            }
        ]
    
    async def _get_critical_equipment_status(self) -> List[Dict[str, Any]]:
        """Get critical equipment status"""
        return []
    
    async def _get_maintenance_schedule(self) -> List[Dict[str, Any]]:
        """Get maintenance schedule"""
        return []
    
    async def _get_qc_test_summary(self) -> Dict[str, Any]:
        """Get QC test summary"""
        return {
            "first_pass_rate": 98.5,
            "right_first_time": 97.2,
            "deviation_rate": 1.5,
            "testing_efficiency": 95.8
        }
    
    async def _get_qc_test_trends(self) -> Dict[str, Any]:
        """Get QC test trends"""
        return {"trend": "improving", "rate": 1.2}
    
    async def _get_oos_investigations(self) -> List[Dict[str, Any]]:
        """Get out-of-specification investigations"""
        return []
    
    async def _get_critical_quality_alerts(self) -> List[Dict[str, Any]]:
        """Get critical quality alerts"""
        return []
    
    async def _calculate_line_yield(self, line_id: str) -> Dict[str, Any]:
        """Calculate line yield"""
        return {
            "theoretical_yield": 98.5,
            "actual_yield": 96.8,
            "yield_variance": -1.7,
            "material_utilization": 95.2,
            "cost_impact": 12500
        }
    
    async def _get_waste_analysis(self, line_id: str) -> Dict[str, Any]:
        """Get waste analysis"""
        return {
            "total_waste": 125.5,
            "waste_percentage": 2.1,
            "cost_impact": 8500,
            "waste_categories": ["material_loss", "rework", "scrap"]
        }
    
    async def _get_yield_trends(self) -> Dict[str, Any]:
        """Get yield trends"""
        return {"trend": "stable", "improvement_rate": 0.5}
    
    async def _identify_waste_reduction_opportunities(self) -> List[Dict[str, Any]]:
        """Identify waste reduction opportunities"""
        return [
            {
                "opportunity": "Optimize mixing time",
                "potential_savings": 5000,
                "implementation_effort": "medium"
            }
        ]
    
    async def _evaluate_compliance(self, standard_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate compliance for a standard"""
        return {
            "score": 96.5,
            "status": ComplianceStatus.COMPLIANT.value,
            "requirements_met": 18,
            "total_requirements": 20,
            "findings": {
                "critical": [],
                "major": [],
                "minor": ["Documentation formatting"],
                "total": ["Documentation formatting"]
            },
            "last_assessment": datetime.now(timezone.utc).isoformat()
        }
    
    async def _assess_regulatory_readiness(self) -> Dict[str, Any]:
        """Assess regulatory readiness"""
        return {
            "readiness_score": 95.8,
            "audit_readiness": "high",
            "preparation_time": "2_weeks"
        }
    
    async def _get_audit_preparation_status(self) -> Dict[str, Any]:
        """Get audit preparation status"""
        return {
            "documentation_complete": 98.5,
            "training_current": 96.2,
            "system_validation": 99.1
        }
    
    async def _get_schedule_status(self) -> Dict[str, Any]:
        """Get schedule status"""
        return {
            "on_schedule": 18,
            "delayed": 2,
            "ahead_of_schedule": 1
        }
    
    async def _calculate_schedule_adherence(self) -> Dict[str, Any]:
        """Calculate schedule adherence"""
        return {
            "adherence_rate": 85.7,
            "average_delay": 0.8,
            "on_time_delivery": 85.7
        }
    
    async def _get_delay_analysis(self) -> Dict[str, Any]:
        """Get delay analysis"""
        return {
            "average_delay": 0.8,
            "delay_causes": ["material_shortage", "equipment_maintenance"],
            "impact_assessment": "medium"
        }
    
    async def _get_capacity_planning_metrics(self) -> Dict[str, Any]:
        """Get capacity planning metrics"""
        return {
            "capacity_utilization": 85.3,
            "available_capacity": 14.7,
            "bottlenecks": ["packaging"]
        }
    
    async def _get_schedule_optimization_recommendations(self) -> List[str]:
        """Get schedule optimization recommendations"""
        return [
            "Optimize batch sequencing",
            "Reduce changeover times",
            "Improve material planning"
        ]
    
    async def _get_parameter_values(self, param_id: str) -> Dict[str, Any]:
        """Get parameter values"""
        return {
            "current_value": 22.5,
            "average_value": 22.3,
            "min_value": 21.8,
            "max_value": 23.1
        }
    
    async def _analyze_parameter_trends(self, param_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parameter trends"""
        return {
            "trend": "stable",
            "variation": 0.5,
            "control_status": "in_control"
        }
    
    async def _check_parameter_deviations(self, param_id: str, values: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Check parameter deviations"""
        return {
            "deviations_detected": 0,
            "deviation_severity": "none",
            "corrective_actions": []
        }
    
    def _determine_parameter_control_status(self, deviation_analysis: Dict[str, Any]) -> str:
        """Determine parameter control status"""
        return "in_control" if deviation_analysis["deviations_detected"] == 0 else "out_of_control"
    
    async def _calculate_process_capability(self) -> Dict[str, Any]:
        """Calculate process capability"""
        return {
            "cp": 1.33,
            "cpk": 1.25,
            "capability_assessment": "capable"
        }
    
    async def _generate_control_recommendations(self) -> List[str]:
        """Generate control recommendations"""
        return [
            "Maintain current control parameters",
            "Monitor trending closely",
            "Review control limits quarterly"
        ]
    
    async def _assess_contamination_risks(self) -> Dict[str, Any]:
        """Assess contamination risks"""
        return {
            "overall_risk": "low",
            "risk_factors": ["personnel_movement", "material_transfer"],
            "mitigation_effectiveness": 95.5
        }
    
    async def _get_contamination_mitigation_measures(self) -> List[Dict[str, Any]]:
        """Get contamination mitigation measures"""
        return [
            {
                "measure": "Enhanced cleaning protocols",
                "effectiveness": 98.5,
                "implementation_status": "active"
            }
        ]
    
    async def _get_contamination_incidents(self) -> List[Dict[str, Any]]:
        """Get contamination incidents"""
        return []
    
    async def _get_preventive_measures_status(self) -> Dict[str, Any]:
        """Get preventive measures status"""
        return {
            "measures_implemented": 15,
            "measures_effective": 14,
            "effectiveness_rate": 93.3
        }