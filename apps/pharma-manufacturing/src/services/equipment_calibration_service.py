"""
Equipment Calibration Service
Comprehensive equipment calibration tracking and validation for pharmaceutical manufacturing
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from src.models.gmp_models import EquipmentCalibration, EquipmentStatus
from src.services.immutable_audit_service import ImmutableAuditService
from src.models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class EquipmentCalibrationService:
    """
    Service for managing equipment calibration, validation, and qualification
    Ensures equipment meets GMP requirements and maintains accuracy
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.calibration_procedures = self._initialize_calibration_procedures()
        self.equipment_registry = self._initialize_equipment_registry()
        
    def _initialize_calibration_procedures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize calibration procedures for different equipment types"""
        return {
            "analytical_balance": {
                "procedure_id": "CAL-BAL-001",
                "frequency_months": 6,
                "calibration_points": [0, 50, 100, 150, 200],  # grams
                "acceptance_criteria": {"accuracy": 0.1, "repeatability": 0.05},
                "calibration_standards": ["NIST_Class_1_Weights"],
                "environmental_requirements": {
                    "temperature": {"min": 18, "max": 25},
                    "humidity": {"min": 45, "max": 65}
                }
            },
            "ph_meter": {
                "procedure_id": "CAL-PH-001",
                "frequency_months": 3,
                "calibration_points": [4.01, 7.00, 10.01],  # pH units
                "acceptance_criteria": {"accuracy": 0.02, "slope": {"min": 95, "max": 105}},
                "calibration_standards": ["pH_4.01_Buffer", "pH_7.00_Buffer", "pH_10.01_Buffer"],
                "environmental_requirements": {
                    "temperature": {"min": 20, "max": 25}
                }
            },
            "hplc_system": {
                "procedure_id": "CAL-HPLC-001",
                "frequency_months": 12,
                "calibration_points": ["retention_time", "peak_area", "peak_height"],
                "acceptance_criteria": {
                    "retention_time_rsd": 2.0,
                    "peak_area_rsd": 2.0,
                    "resolution": 2.0
                },
                "calibration_standards": ["USP_Reference_Standards"],
                "environmental_requirements": {
                    "temperature": {"min": 15, "max": 30}
                }
            },
            "temperature_probe": {
                "procedure_id": "CAL-TEMP-001",
                "frequency_months": 12,
                "calibration_points": [0, 25, 50, 75, 100],  # °C
                "acceptance_criteria": {"accuracy": 0.1, "stability": 0.05},
                "calibration_standards": ["NIST_Traceable_Thermometer"],
                "environmental_requirements": {
                    "temperature": {"min": 15, "max": 35}
                }
            },
            "humidity_sensor": {
                "procedure_id": "CAL-HUM-001",
                "frequency_months": 12,
                "calibration_points": [33, 50, 75, 90],  # %RH
                "acceptance_criteria": {"accuracy": 2.0, "repeatability": 1.0},
                "calibration_standards": ["Saturated_Salt_Solutions"],
                "environmental_requirements": {
                    "temperature": {"min": 20, "max": 25}
                }
            },
            "pressure_transducer": {
                "procedure_id": "CAL-PRESS-001",
                "frequency_months": 12,
                "calibration_points": [0, 25, 50, 75, 100],  # % of range
                "acceptance_criteria": {"accuracy": 0.25, "linearity": 0.1},
                "calibration_standards": ["NIST_Traceable_Pressure_Standard"],
                "environmental_requirements": {
                    "temperature": {"min": 15, "max": 35}
                }
            }
        }
    
    def _initialize_equipment_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize equipment registry with sample equipment"""
        return {
            "BAL-001": {
                "equipment_name": "Analytical Balance #1",
                "equipment_type": "analytical_balance",
                "manufacturer": "Mettler Toledo",
                "model_number": "XPE205",
                "serial_number": "B123456789",
                "location": "QC Laboratory",
                "installation_date": "2023-01-15",
                "last_calibration": "2024-06-15",
                "next_calibration": "2024-12-15"
            },
            "PH-001": {
                "equipment_name": "pH Meter #1",
                "equipment_type": "ph_meter",
                "manufacturer": "Hanna Instruments",
                "model_number": "HI-2020",
                "serial_number": "PH987654321",
                "location": "QC Laboratory",
                "installation_date": "2023-02-01",
                "last_calibration": "2024-09-01",
                "next_calibration": "2024-12-01"
            },
            "HPLC-001": {
                "equipment_name": "HPLC System #1",
                "equipment_type": "hplc_system",
                "manufacturer": "Agilent",
                "model_number": "1260 Infinity II",
                "serial_number": "HPLC001234",
                "location": "Analytical Laboratory",
                "installation_date": "2023-03-01",
                "last_calibration": "2024-03-01",
                "next_calibration": "2025-03-01"
            }
        }
    
    async def perform_equipment_calibration(
        self,
        equipment_id: UUID,
        calibration_procedure: str,
        performed_by: UUID,
        calibration_data: Dict[str, Any],
        calibration_standards: List[str],
        environmental_conditions: Dict[str, float],
        notes: Optional[str] = None,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Perform equipment calibration and record results
        """
        try:
            # Get equipment information
            equipment_info = await self._get_equipment_info(equipment_id)
            if not equipment_info:
                raise ValueError(f"Equipment {equipment_id} not found")
            
            equipment_type = equipment_info["equipment_type"]
            
            # Get calibration procedure
            if equipment_type not in self.calibration_procedures:
                raise ValueError(f"No calibration procedure for equipment type: {equipment_type}")
            
            procedure = self.calibration_procedures[equipment_type]
            
            # Validate environmental conditions
            env_check = await self._validate_environmental_conditions(
                procedure["environmental_requirements"], 
                environmental_conditions
            )
            
            if not env_check["valid"]:
                raise ValueError(f"Environmental conditions not suitable: {env_check['issues']}")
            
            # Analyze calibration results
            calibration_analysis = await self._analyze_calibration_results(
                equipment_type, 
                calibration_data, 
                procedure["acceptance_criteria"]
            )
            
            # Calculate next calibration date
            next_calibration_date = datetime.now(timezone.utc) + timedelta(
                days=procedure["frequency_months"] * 30
            )
            
            # Determine equipment status
            status = EquipmentStatus.OPERATIONAL if calibration_analysis["passed"] else EquipmentStatus.OUT_OF_SERVICE
            
            # Create calibration record
            calibration_record = EquipmentCalibration(
                id=uuid4(),
                equipment_id=equipment_id,
                equipment_name=equipment_info["equipment_name"],
                equipment_type=equipment_type,
                manufacturer=equipment_info.get("manufacturer"),
                model_number=equipment_info.get("model_number"),
                serial_number=equipment_info.get("serial_number"),
                location=equipment_info.get("location"),
                calibration_procedure=calibration_procedure,
                calibration_date=datetime.now(timezone.utc),
                next_calibration_date=next_calibration_date,
                calibration_frequency_months=procedure["frequency_months"],
                performed_by=performed_by,
                calibration_standard=", ".join(calibration_standards),
                calibration_results=calibration_data,
                accuracy_achieved=calibration_analysis.get("accuracy_achieved"),
                status=status,
                is_qualified=calibration_analysis["passed"],
                qualification_date=datetime.now(timezone.utc) if calibration_analysis["passed"] else None,
                notes=notes
            )
            
            # Store calibration record
            await self._store_calibration_record(calibration_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=performed_by,
                username=await self._get_username(performed_by),
                full_name=await self._get_full_name(performed_by),
                action=AuditAction.UPDATE,
                action_description=f"Equipment calibration performed: {equipment_info['equipment_name']}",
                entity_type="equipment_calibration",
                entity_id=calibration_record.id,
                entity_identifier=f"CAL:{equipment_id}",
                new_values={
                    "equipment_id": str(equipment_id),
                    "calibration_procedure": calibration_procedure,
                    "calibration_passed": calibration_analysis["passed"],
                    "next_calibration_date": next_calibration_date.isoformat(),
                    "status": status.value
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            # Update equipment status
            await self._update_equipment_status(equipment_id, status, next_calibration_date)
            
            # Generate calibration certificate if passed
            certificate = None
            if calibration_analysis["passed"]:
                certificate = await self._generate_calibration_certificate(calibration_record)
            
            logger.info(f"Equipment calibration completed: {equipment_id} - {'PASSED' if calibration_analysis['passed'] else 'FAILED'}")
            
            return {
                "calibration_id": str(calibration_record.id),
                "equipment_id": str(equipment_id),
                "equipment_name": equipment_info["equipment_name"],
                "calibration_date": calibration_record.calibration_date.isoformat(),
                "next_calibration_date": next_calibration_date.isoformat(),
                "calibration_passed": calibration_analysis["passed"],
                "status": status.value,
                "accuracy_achieved": calibration_analysis.get("accuracy_achieved"),
                "certificate_number": certificate.get("certificate_number") if certificate else None,
                "analysis_details": calibration_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to perform equipment calibration: {str(e)}")
            raise
    
    async def get_calibration_due_list(
        self,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get list of equipment requiring calibration
        """
        try:
            cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
            
            # Get equipment with calibration due
            due_equipment = await self._get_calibration_due_equipment(cutoff_date)
            
            due_list = []
            for equipment in due_equipment:
                days_until_due = (equipment["next_calibration_date"] - datetime.now(timezone.utc)).days
                
                due_item = {
                    "equipment_id": str(equipment["equipment_id"]),
                    "equipment_name": equipment["equipment_name"],
                    "equipment_type": equipment["equipment_type"],
                    "location": equipment["location"],
                    "last_calibration_date": equipment["last_calibration_date"],
                    "next_calibration_date": equipment["next_calibration_date"],
                    "days_until_due": days_until_due,
                    "status": equipment["status"],
                    "priority": self._calculate_priority(days_until_due),
                    "calibration_procedure": self.calibration_procedures.get(
                        equipment["equipment_type"], {}
                    ).get("procedure_id", "Unknown")
                }
                due_list.append(due_item)
            
            # Sort by priority and days until due
            due_list.sort(key=lambda x: (x["priority"], x["days_until_due"]))
            
            return due_list
            
        except Exception as e:
            logger.error(f"Failed to get calibration due list: {str(e)}")
            return []
    
    async def validate_equipment_qualification(
        self,
        equipment_id: UUID,
        validation_type: str,  # IQ, OQ, PQ
        performed_by: UUID,
        validation_data: Dict[str, Any],
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Perform equipment qualification validation (IQ/OQ/PQ)
        """
        try:
            equipment_info = await self._get_equipment_info(equipment_id)
            if not equipment_info:
                raise ValueError(f"Equipment {equipment_id} not found")
            
            # Validate qualification data
            validation_result = await self._validate_qualification_data(
                equipment_info["equipment_type"], 
                validation_type, 
                validation_data
            )
            
            # Create qualification record
            qualification_record = {
                "qualification_id": str(uuid4()),
                "equipment_id": str(equipment_id),
                "validation_type": validation_type,
                "validation_date": datetime.now(timezone.utc).isoformat(),
                "performed_by": str(performed_by),
                "validation_data": validation_data,
                "validation_result": validation_result,
                "qualification_passed": validation_result["passed"]
            }
            
            # Store qualification record
            await self._store_qualification_record(qualification_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=performed_by,
                username=await self._get_username(performed_by),
                full_name=await self._get_full_name(performed_by),
                action=AuditAction.UPDATE,
                action_description=f"Equipment {validation_type} qualification: {equipment_info['equipment_name']}",
                entity_type="equipment_qualification",
                entity_id=UUID(qualification_record["qualification_id"]),
                entity_identifier=f"{validation_type}:{equipment_id}",
                new_values={
                    "equipment_id": str(equipment_id),
                    "validation_type": validation_type,
                    "qualification_passed": validation_result["passed"]
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Equipment {validation_type} qualification completed: {equipment_id}")
            
            return qualification_record
            
        except Exception as e:
            logger.error(f"Failed to validate equipment qualification: {str(e)}")
            raise
    
    async def get_equipment_calibration_history(
        self,
        equipment_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get calibration history for equipment
        """
        try:
            # Get calibration records
            calibration_history = await self._get_calibration_history(
                equipment_id, start_date, end_date
            )
            
            # Calculate statistics
            if calibration_history:
                total_calibrations = len(calibration_history)
                passed_calibrations = sum(1 for cal in calibration_history if cal.get("calibration_passed", False))
                success_rate = (passed_calibrations / total_calibrations) * 100
                
                # Calculate average time between calibrations
                if len(calibration_history) > 1:
                    time_diffs = []
                    for i in range(1, len(calibration_history)):
                        prev_date = datetime.fromisoformat(calibration_history[i-1]["calibration_date"])
                        curr_date = datetime.fromisoformat(calibration_history[i]["calibration_date"])
                        time_diffs.append((curr_date - prev_date).days)
                    avg_interval_days = sum(time_diffs) / len(time_diffs)
                else:
                    avg_interval_days = None
            else:
                total_calibrations = 0
                passed_calibrations = 0
                success_rate = 0
                avg_interval_days = None
            
            return {
                "equipment_id": str(equipment_id),
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "statistics": {
                    "total_calibrations": total_calibrations,
                    "passed_calibrations": passed_calibrations,
                    "failed_calibrations": total_calibrations - passed_calibrations,
                    "success_rate": success_rate,
                    "average_interval_days": avg_interval_days
                },
                "calibration_history": calibration_history
            }
            
        except Exception as e:
            logger.error(f"Failed to get calibration history: {str(e)}")
            return {"error": str(e)}
    
    async def generate_calibration_report(
        self,
        start_date: datetime,
        end_date: datetime,
        equipment_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive calibration report
        """
        try:
            report = {
                "report_type": "equipment_calibration",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {},
                "equipment_analysis": {},
                "compliance_metrics": {},
                "recommendations": []
            }
            
            # Get calibration data for period
            calibration_data = await self._get_calibration_data_for_period(
                start_date, end_date, equipment_types
            )
            
            # Calculate summary statistics
            total_calibrations = len(calibration_data)
            passed_calibrations = sum(1 for cal in calibration_data if cal.get("calibration_passed", False))
            overdue_equipment = await self._get_overdue_equipment_count()
            
            report["summary"] = {
                "total_calibrations_performed": total_calibrations,
                "calibrations_passed": passed_calibrations,
                "calibrations_failed": total_calibrations - passed_calibrations,
                "success_rate": (passed_calibrations / total_calibrations * 100) if total_calibrations > 0 else 0,
                "overdue_equipment_count": overdue_equipment
            }
            
            # Analyze by equipment type
            equipment_analysis = {}
            for equipment_type in self.calibration_procedures.keys():
                type_calibrations = [cal for cal in calibration_data if cal.get("equipment_type") == equipment_type]
                if type_calibrations:
                    equipment_analysis[equipment_type] = {
                        "total_calibrations": len(type_calibrations),
                        "passed_calibrations": sum(1 for cal in type_calibrations if cal.get("calibration_passed", False)),
                        "success_rate": (sum(1 for cal in type_calibrations if cal.get("calibration_passed", False)) / len(type_calibrations)) * 100
                    }
            
            report["equipment_analysis"] = equipment_analysis
            
            # Calculate compliance metrics
            report["compliance_metrics"] = {
                "calibration_compliance_rate": (passed_calibrations / total_calibrations * 100) if total_calibrations > 0 else 100,
                "overdue_equipment_percentage": (overdue_equipment / await self._get_total_equipment_count() * 100) if await self._get_total_equipment_count() > 0 else 0,
                "gmp_compliance_status": "compliant" if overdue_equipment == 0 and (passed_calibrations / total_calibrations * 100) >= 95 else "non_compliant"
            }
            
            # Generate recommendations
            report["recommendations"] = await self._generate_calibration_recommendations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate calibration report: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_priority(self, days_until_due: int) -> int:
        """Calculate calibration priority based on days until due"""
        if days_until_due < 0:
            return 1  # Overdue - highest priority
        elif days_until_due <= 7:
            return 2  # Due within a week
        elif days_until_due <= 30:
            return 3  # Due within a month
        else:
            return 4  # Future due date
    
    async def _validate_environmental_conditions(
        self,
        requirements: Dict[str, Dict[str, float]],
        actual_conditions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Validate environmental conditions for calibration"""
        issues = []
        
        for param, limits in requirements.items():
            if param in actual_conditions:
                value = actual_conditions[param]
                if "min" in limits and value < limits["min"]:
                    issues.append(f"{param} too low: {value} < {limits['min']}")
                if "max" in limits and value > limits["max"]:
                    issues.append(f"{param} too high: {value} > {limits['max']}")
            else:
                issues.append(f"Missing {param} measurement")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    async def _analyze_calibration_results(
        self,
        equipment_type: str,
        calibration_data: Dict[str, Any],
        acceptance_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze calibration results against acceptance criteria"""
        analysis = {
            "passed": True,
            "issues": [],
            "accuracy_achieved": None
        }
        
        # Equipment-specific analysis
        if equipment_type == "analytical_balance":
            if "accuracy" in calibration_data and "accuracy" in acceptance_criteria:
                accuracy = calibration_data["accuracy"]
                required_accuracy = acceptance_criteria["accuracy"]
                analysis["accuracy_achieved"] = accuracy
                
                if accuracy > required_accuracy:
                    analysis["passed"] = False
                    analysis["issues"].append(f"Accuracy {accuracy} exceeds limit {required_accuracy}")
        
        elif equipment_type == "ph_meter":
            if "slope" in calibration_data and "slope" in acceptance_criteria:
                slope = calibration_data["slope"]
                slope_limits = acceptance_criteria["slope"]
                
                if slope < slope_limits["min"] or slope > slope_limits["max"]:
                    analysis["passed"] = False
                    analysis["issues"].append(f"Slope {slope}% outside limits {slope_limits['min']}-{slope_limits['max']}%")
        
        # Add more equipment-specific analyses as needed
        
        return analysis
    
    async def _validate_qualification_data(
        self,
        equipment_type: str,
        validation_type: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate equipment qualification data"""
        result = {
            "passed": True,
            "issues": [],
            "validation_type": validation_type
        }
        
        # Validation logic based on equipment type and validation type
        required_tests = {
            "IQ": ["documentation_review", "installation_verification", "utility_connections"],
            "OQ": ["operational_range_testing", "alarm_testing", "safety_function_testing"],
            "PQ": ["performance_testing", "process_simulation", "batch_consistency"]
        }
        
        if validation_type in required_tests:
            for test in required_tests[validation_type]:
                if test not in validation_data or not validation_data[test].get("passed", False):
                    result["passed"] = False
                    result["issues"].append(f"Test failed or missing: {test}")
        
        return result
    
    async def _generate_calibration_certificate(
        self,
        calibration_record: EquipmentCalibration
    ) -> Dict[str, Any]:
        """Generate calibration certificate"""
        certificate_number = f"CAL-{datetime.now().strftime('%Y%m%d')}-{str(calibration_record.id)[:8].upper()}"
        
        certificate = {
            "certificate_number": certificate_number,
            "equipment_id": str(calibration_record.equipment_id),
            "equipment_name": calibration_record.equipment_name,
            "calibration_date": calibration_record.calibration_date.isoformat(),
            "next_calibration_date": calibration_record.next_calibration_date.isoformat(),
            "performed_by": str(calibration_record.performed_by),
            "accuracy_achieved": calibration_record.accuracy_achieved,
            "certificate_valid_until": calibration_record.next_calibration_date.isoformat(),
            "traceability": "NIST traceable standards used",
            "certificate_issued": datetime.now(timezone.utc).isoformat()
        }
        
        return certificate
    
    async def _generate_calibration_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on calibration report"""
        recommendations = []
        
        success_rate = report["summary"]["success_rate"]
        overdue_count = report["summary"]["overdue_equipment_count"]
        
        if success_rate < 95:
            recommendations.append("Investigate causes of calibration failures and improve procedures")
        
        if overdue_count > 0:
            recommendations.append(f"Schedule immediate calibration for {overdue_count} overdue equipment")
        
        recommendations.append("Maintain regular calibration schedule to ensure GMP compliance")
        recommendations.append("Review calibration procedures annually for continuous improvement")
        
        return recommendations
    
    # Database operations (these would integrate with actual database)
    async def _store_calibration_record(self, record: EquipmentCalibration):
        """Store calibration record in database"""
        logger.debug(f"Storing calibration record {record.id}")
    
    async def _store_qualification_record(self, record: Dict[str, Any]):
        """Store qualification record in database"""
        logger.debug(f"Storing qualification record {record['qualification_id']}")
    
    async def _get_equipment_info(self, equipment_id: UUID) -> Optional[Dict[str, Any]]:
        """Get equipment information"""
        # This would query the equipment database
        # For now, return sample data
        equipment_key = str(equipment_id)[:7]  # Use first 7 chars as key
        return self.equipment_registry.get(equipment_key)
    
    async def _update_equipment_status(self, equipment_id: UUID, status: EquipmentStatus, next_calibration: datetime):
        """Update equipment status"""
        logger.debug(f"Updating equipment {equipment_id} status to {status.value}")
    
    async def _get_calibration_due_equipment(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Get equipment with calibration due"""
        return []
    
    async def _get_calibration_history(self, equipment_id: UUID, start_date: Optional[datetime], end_date: Optional[datetime]) -> List[Dict[str, Any]]:
        """Get calibration history for equipment"""
        return []
    
    async def _get_calibration_data_for_period(self, start_date: datetime, end_date: datetime, equipment_types: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Get calibration data for period"""
        return []
    
    async def _get_overdue_equipment_count(self) -> int:
        """Get count of overdue equipment"""
        return 0
    
    async def _get_total_equipment_count(self) -> int:
        """Get total equipment count"""
        return len(self.equipment_registry)
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"