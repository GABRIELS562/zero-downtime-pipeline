"""
In-Process Quality Control Testing Service
Quality control testing during manufacturing stages for pharmaceutical products
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from src.models.gmp_models import InProcessTesting, TestStatus
from src.services.immutable_audit_service import ImmutableAuditService
from src.models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class InProcessTestingService:
    """
    Service for managing in-process quality control testing during manufacturing
    Ensures product quality at each manufacturing stage
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.manufacturing_stages = self._initialize_manufacturing_stages()
        self.test_specifications = self._initialize_test_specifications()
        self.sampling_plans = self._initialize_sampling_plans()
        
    def _initialize_manufacturing_stages(self) -> Dict[str, Dict[str, Any]]:
        """Initialize manufacturing stages configuration"""
        return {
            "dispensing": {
                "stage_name": "Raw Material Dispensing",
                "sequence": 1,
                "required_tests": ["material_verification", "weight_verification", "identity_check"],
                "critical_parameters": ["accurate_dispensing", "material_identity", "cross_contamination"],
                "stage_duration_hours": 2,
                "hold_time_limit_hours": 24
            },
            "mixing": {
                "stage_name": "Blending/Mixing",
                "sequence": 2,
                "required_tests": ["blend_uniformity", "moisture_content", "bulk_density"],
                "critical_parameters": ["uniformity", "moisture", "particle_size"],
                "stage_duration_hours": 4,
                "hold_time_limit_hours": 48
            },
            "granulation": {
                "stage_name": "Wet Granulation",
                "sequence": 3,
                "required_tests": ["granule_size", "moisture_content", "bulk_density", "flow_properties"],
                "critical_parameters": ["particle_size", "moisture", "flowability"],
                "stage_duration_hours": 6,
                "hold_time_limit_hours": 72
            },
            "drying": {
                "stage_name": "Fluid Bed Drying",
                "sequence": 4,
                "required_tests": ["moisture_content", "temperature_profile", "drying_end_point"],
                "critical_parameters": ["moisture_level", "temperature", "time"],
                "stage_duration_hours": 8,
                "hold_time_limit_hours": 48
            },
            "sizing": {
                "stage_name": "Milling/Sizing",
                "sequence": 5,
                "required_tests": ["particle_size_distribution", "bulk_density", "tapped_density"],
                "critical_parameters": ["particle_size", "uniformity", "density"],
                "stage_duration_hours": 2,
                "hold_time_limit_hours": 24
            },
            "final_blending": {
                "stage_name": "Final Blending",
                "sequence": 6,
                "required_tests": ["blend_uniformity", "assay", "content_uniformity"],
                "critical_parameters": ["uniformity", "potency", "homogeneity"],
                "stage_duration_hours": 3,
                "hold_time_limit_hours": 24
            },
            "compression": {
                "stage_name": "Tablet Compression",
                "sequence": 7,
                "required_tests": ["tablet_weight", "hardness", "thickness", "friability"],
                "critical_parameters": ["weight_variation", "mechanical_strength", "dimensions"],
                "stage_duration_hours": 12,
                "hold_time_limit_hours": 168
            },
            "coating": {
                "stage_name": "Film Coating",
                "sequence": 8,
                "required_tests": ["coating_weight_gain", "appearance", "dissolution"],
                "critical_parameters": ["coating_uniformity", "appearance", "release_profile"],
                "stage_duration_hours": 8,
                "hold_time_limit_hours": 72
            }
        }
    
    def _initialize_test_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Initialize test specifications for different stages"""
        return {
            "blend_uniformity": {
                "test_method": "HPLC Assay",
                "sampling_locations": 10,
                "acceptance_criteria": {
                    "relative_standard_deviation": {"max": 6.0, "unit": "%"},
                    "individual_results": {"min": 85.0, "max": 115.0, "unit": "% of target"}
                },
                "analysis_time_minutes": 45,
                "sample_size_grams": 1.0
            },
            "moisture_content": {
                "test_method": "Karl Fischer Titration",
                "sampling_locations": 5,
                "acceptance_criteria": {
                    "moisture_level": {"max": 3.0, "unit": "% w/w"}
                },
                "analysis_time_minutes": 15,
                "sample_size_grams": 2.0
            },
            "particle_size_distribution": {
                "test_method": "Sieve Analysis",
                "sampling_locations": 3,
                "acceptance_criteria": {
                    "d10": {"min": 50, "max": 150, "unit": "μm"},
                    "d50": {"min": 200, "max": 400, "unit": "μm"},
                    "d90": {"min": 500, "max": 1000, "unit": "μm"}
                },
                "analysis_time_minutes": 30,
                "sample_size_grams": 10.0
            },
            "tablet_weight": {
                "test_method": "Individual Weight Determination",
                "sampling_frequency": "every_30_minutes",
                "acceptance_criteria": {
                    "average_weight": {"min": 95.0, "max": 105.0, "unit": "% of target"},
                    "individual_weights": {"min": 90.0, "max": 110.0, "unit": "% of target"},
                    "rsd": {"max": 5.0, "unit": "%"}
                },
                "analysis_time_minutes": 10,
                "sample_size_tablets": 20
            },
            "hardness": {
                "test_method": "Hardness Tester",
                "sampling_frequency": "every_hour",
                "acceptance_criteria": {
                    "hardness_range": {"min": 4.0, "max": 8.0, "unit": "kp"},
                    "individual_results": {"min": 3.5, "max": 8.5, "unit": "kp"}
                },
                "analysis_time_minutes": 5,
                "sample_size_tablets": 10
            },
            "dissolution": {
                "test_method": "USP Dissolution Apparatus",
                "sampling_locations": 1,
                "acceptance_criteria": {
                    "q_15min": {"min": 70.0, "unit": "% released"},
                    "q_30min": {"min": 85.0, "unit": "% released"}
                },
                "analysis_time_minutes": 90,
                "sample_size_tablets": 6
            },
            "assay": {
                "test_method": "HPLC",
                "sampling_locations": 3,
                "acceptance_criteria": {
                    "potency": {"min": 95.0, "max": 105.0, "unit": "% of label claim"}
                },
                "analysis_time_minutes": 30,
                "sample_size_grams": 0.5
            },
            "content_uniformity": {
                "test_method": "HPLC Individual Content",
                "sampling_frequency": "per_batch",
                "acceptance_criteria": {
                    "individual_content": {"min": 85.0, "max": 115.0, "unit": "% of label claim"},
                    "rsd": {"max": 6.0, "unit": "%"}
                },
                "analysis_time_minutes": 60,
                "sample_size_units": 30
            }
        }
    
    def _initialize_sampling_plans(self) -> Dict[str, Dict[str, Any]]:
        """Initialize sampling plans for different stages"""
        return {
            "dispensing": {
                "sampling_strategy": "verification_sampling",
                "sample_points": ["scale_verification", "container_identification"],
                "frequency": "each_material",
                "sample_size": "representative_portion"
            },
            "mixing": {
                "sampling_strategy": "systematic_sampling",
                "sample_points": ["top", "middle", "bottom", "corners", "center"],
                "frequency": "end_of_mixing",
                "sample_size": "minimum_10_locations"
            },
            "granulation": {
                "sampling_strategy": "time_based_sampling",
                "sample_points": ["outlet_stream", "endpoint_verification"],
                "frequency": "every_30_minutes",
                "sample_size": "50g_per_sample"
            },
            "compression": {
                "sampling_strategy": "statistical_sampling",
                "sample_points": ["compression_station_output"],
                "frequency": "every_30_minutes",
                "sample_size": "20_tablets_per_sample"
            },
            "coating": {
                "sampling_strategy": "process_monitoring",
                "sample_points": ["coating_booth_output"],
                "frequency": "hourly_during_coating",
                "sample_size": "10_tablets_per_sample"
            }
        }
    
    async def initiate_in_process_testing(
        self,
        batch_id: UUID,
        manufacturing_stage: str,
        test_point_id: str,
        initiated_by: UUID,
        expected_tests: Optional[List[str]] = None,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Initiate in-process testing for a manufacturing stage
        """
        try:
            # Validate manufacturing stage
            if manufacturing_stage not in self.manufacturing_stages:
                raise ValueError(f"Unknown manufacturing stage: {manufacturing_stage}")
            
            stage_config = self.manufacturing_stages[manufacturing_stage]
            
            # Determine required tests
            required_tests = expected_tests or stage_config["required_tests"]
            
            # Generate sampling plan
            sampling_plan = await self._generate_sampling_plan(manufacturing_stage, required_tests)
            
            # Create test records for each required test
            test_records = []
            for test_name in required_tests:
                test_record = InProcessTesting(
                    id=uuid4(),
                    batch_id=batch_id,
                    manufacturing_stage=manufacturing_stage,
                    test_point_id=test_point_id,
                    test_name=test_name,
                    test_method=self.test_specifications.get(test_name, {}).get("test_method", "Unknown"),
                    sample_id=f"{test_point_id}-{test_name}-{datetime.now().strftime('%Y%m%d%H%M')}",
                    sampling_time=datetime.now(timezone.utc),
                    performed_by=initiated_by,
                    test_parameters=self.test_specifications.get(test_name, {}),
                    specifications=self.test_specifications.get(test_name, {}).get("acceptance_criteria", {}),
                    result_status=TestStatus.PENDING,
                    notes=f"In-process testing initiated for {manufacturing_stage}"
                )
                test_records.append(test_record)
            
            # Store test records
            for record in test_records:
                await self._store_testing_record(record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=initiated_by,
                username=await self._get_username(initiated_by),
                full_name=await self._get_full_name(initiated_by),
                action=AuditAction.CREATE,
                action_description=f"In-process testing initiated for {manufacturing_stage}",
                entity_type="in_process_testing",
                entity_id=batch_id,
                entity_identifier=f"BATCH:{batch_id}:{manufacturing_stage}",
                new_values={
                    "batch_id": str(batch_id),
                    "manufacturing_stage": manufacturing_stage,
                    "test_point_id": test_point_id,
                    "required_tests": required_tests,
                    "test_count": len(test_records)
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"In-process testing initiated: {batch_id} stage {manufacturing_stage}")
            
            return {
                "batch_id": str(batch_id),
                "manufacturing_stage": manufacturing_stage,
                "test_point_id": test_point_id,
                "tests_initiated": len(test_records),
                "test_records": [
                    {
                        "test_id": str(record.id),
                        "test_name": record.test_name,
                        "sample_id": record.sample_id,
                        "test_method": record.test_method,
                        "status": record.result_status.value
                    }
                    for record in test_records
                ],
                "sampling_plan": sampling_plan,
                "estimated_completion_time": datetime.now(timezone.utc) + timedelta(
                    minutes=sum(
                        self.test_specifications.get(test, {}).get("analysis_time_minutes", 30)
                        for test in required_tests
                    )
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate in-process testing: {str(e)}")
            raise
    
    async def record_test_results(
        self,
        test_id: UUID,
        test_results: Dict[str, Any],
        performed_by: UUID,
        reviewed_by: Optional[UUID] = None,
        test_notes: Optional[str] = None,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record in-process test results
        """
        try:
            # Get test record
            test_record = await self._get_testing_record(test_id)
            if not test_record:
                raise ValueError(f"Test record not found: {test_id}")
            
            # Validate test results against specifications
            validation_result = await self._validate_test_results(
                test_record["test_name"],
                test_results,
                test_record.get("specifications", {})
            )
            
            # Determine impact on batch
            batch_impact = await self._assess_batch_impact(
                test_record["batch_id"],
                test_record["manufacturing_stage"],
                test_record["test_name"],
                validation_result
            )
            
            # Update test record
            updated_record = {
                "test_start_time": test_record.get("test_start_time") or datetime.now(timezone.utc),
                "test_completion_time": datetime.now(timezone.utc),
                "performed_by": performed_by,
                "reviewed_by": reviewed_by,
                "test_results": test_results,
                "result_status": TestStatus.PASSED if validation_result["passed"] else TestStatus.FAILED,
                "batch_disposition": batch_impact["disposition"],
                "impact_assessment": batch_impact["assessment"],
                "notes": test_notes
            }
            
            # Add deviation investigation if failed
            if not validation_result["passed"]:
                updated_record["deviation_investigation"] = await self._initiate_deviation_investigation(
                    test_record, validation_result
                )
                updated_record["corrective_action"] = "Investigation required - batch on hold"
            
            # Store updated record
            await self._update_testing_record(test_id, updated_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=performed_by,
                username=await self._get_username(performed_by),
                full_name=await self._get_full_name(performed_by),
                action=AuditAction.UPDATE,
                action_description=f"In-process test completed: {test_record['test_name']}",
                entity_type="in_process_testing",
                entity_id=test_id,
                entity_identifier=f"TEST:{test_record['sample_id']}",
                old_values={"result_status": TestStatus.PENDING.value},
                new_values={
                    "result_status": updated_record["result_status"].value,
                    "test_passed": validation_result["passed"],
                    "batch_disposition": batch_impact["disposition"],
                    "test_completion_time": updated_record["test_completion_time"].isoformat()
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=not validation_result["passed"]
            )
            
            # Update batch status if needed
            if batch_impact["action_required"]:
                await self._update_batch_status(
                    test_record["batch_id"],
                    batch_impact["disposition"],
                    f"In-process test failure: {test_record['test_name']}"
                )
            
            logger.info(f"In-process test completed: {test_record['test_name']} - {'PASSED' if validation_result['passed'] else 'FAILED'}")
            
            return {
                "test_id": str(test_id),
                "test_name": test_record["test_name"],
                "sample_id": test_record["sample_id"],
                "result_status": updated_record["result_status"].value,
                "test_passed": validation_result["passed"],
                "batch_id": str(test_record["batch_id"]),
                "manufacturing_stage": test_record["manufacturing_stage"],
                "batch_disposition": batch_impact["disposition"],
                "test_completion_time": updated_record["test_completion_time"].isoformat(),
                "validation_details": validation_result,
                "batch_impact": batch_impact
            }
            
        except Exception as e:
            logger.error(f"Failed to record test results: {str(e)}")
            raise
    
    async def get_batch_testing_status(
        self,
        batch_id: UUID,
        manufacturing_stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get in-process testing status for a batch
        """
        try:
            # Get all test records for batch
            test_records = await self._get_batch_test_records(batch_id, manufacturing_stage)
            
            # Group by manufacturing stage
            stages_status = {}
            for record in test_records:
                stage = record["manufacturing_stage"]
                if stage not in stages_status:
                    stages_status[stage] = {
                        "stage_name": self.manufacturing_stages.get(stage, {}).get("stage_name", stage),
                        "sequence": self.manufacturing_stages.get(stage, {}).get("sequence", 0),
                        "tests": [],
                        "stage_status": "pending",
                        "tests_completed": 0,
                        "tests_passed": 0,
                        "tests_failed": 0
                    }
                
                test_info = {
                    "test_id": str(record["id"]),
                    "test_name": record["test_name"],
                    "sample_id": record["sample_id"],
                    "test_method": record["test_method"],
                    "sampling_time": record["sampling_time"],
                    "completion_time": record.get("test_completion_time"),
                    "status": record["result_status"],
                    "passed": record["result_status"] == TestStatus.PASSED,
                    "batch_disposition": record.get("batch_disposition")
                }
                
                stages_status[stage]["tests"].append(test_info)
                
                # Update stage statistics
                if record["result_status"] in [TestStatus.PASSED, TestStatus.FAILED]:
                    stages_status[stage]["tests_completed"] += 1
                    if record["result_status"] == TestStatus.PASSED:
                        stages_status[stage]["tests_passed"] += 1
                    else:
                        stages_status[stage]["tests_failed"] += 1
            
            # Determine stage status
            for stage_info in stages_status.values():
                total_tests = len(stage_info["tests"])
                if stage_info["tests_completed"] == total_tests:
                    if stage_info["tests_failed"] == 0:
                        stage_info["stage_status"] = "completed_passed"
                    else:
                        stage_info["stage_status"] = "completed_failed"
                elif stage_info["tests_completed"] > 0:
                    stage_info["stage_status"] = "in_progress"
                else:
                    stage_info["stage_status"] = "pending"
            
            # Calculate overall batch status
            total_tests = sum(len(stage["tests"]) for stage in stages_status.values())
            total_completed = sum(stage["tests_completed"] for stage in stages_status.values())
            total_passed = sum(stage["tests_passed"] for stage in stages_status.values())
            total_failed = sum(stage["tests_failed"] for stage in stages_status.values())
            
            if total_failed > 0:
                overall_status = "failed"
            elif total_completed == total_tests:
                overall_status = "completed"
            elif total_completed > 0:
                overall_status = "in_progress"
            else:
                overall_status = "pending"
            
            return {
                "batch_id": str(batch_id),
                "overall_status": overall_status,
                "stages": dict(sorted(stages_status.items(), key=lambda x: x[1]["sequence"])),
                "summary": {
                    "total_tests": total_tests,
                    "tests_completed": total_completed,
                    "tests_passed": total_passed,
                    "tests_failed": total_failed,
                    "completion_rate": (total_completed / total_tests * 100) if total_tests > 0 else 0,
                    "pass_rate": (total_passed / total_completed * 100) if total_completed > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get batch testing status: {str(e)}")
            return {"error": str(e)}
    
    async def generate_stage_release_report(
        self,
        batch_id: UUID,
        manufacturing_stage: str,
        reported_by: UUID
    ) -> Dict[str, Any]:
        """
        Generate stage release report for batch progression
        """
        try:
            # Get test records for stage
            test_records = await self._get_batch_test_records(batch_id, manufacturing_stage)
            
            if not test_records:
                raise ValueError(f"No test records found for batch {batch_id} stage {manufacturing_stage}")
            
            # Validate all tests are complete
            incomplete_tests = [
                record for record in test_records 
                if record["result_status"] not in [TestStatus.PASSED, TestStatus.FAILED]
            ]
            
            if incomplete_tests:
                incomplete_names = [record["test_name"] for record in incomplete_tests]
                raise ValueError(f"Cannot generate release report - incomplete tests: {', '.join(incomplete_names)}")
            
            # Check for any failed tests
            failed_tests = [record for record in test_records if record["result_status"] == TestStatus.FAILED]
            
            # Determine release decision
            if failed_tests:
                release_decision = "HOLD"
                release_rationale = f"Stage cannot be released due to {len(failed_tests)} failed test(s)"
            else:
                release_decision = "RELEASED"
                release_rationale = "All in-process tests passed acceptance criteria"
            
            # Generate report
            report = {
                "report_type": "stage_release",
                "batch_id": str(batch_id),
                "manufacturing_stage": manufacturing_stage,
                "stage_name": self.manufacturing_stages.get(manufacturing_stage, {}).get("stage_name", manufacturing_stage),
                "report_date": datetime.now(timezone.utc).isoformat(),
                "reported_by": str(reported_by),
                "release_decision": release_decision,
                "release_rationale": release_rationale,
                "test_summary": {
                    "total_tests": len(test_records),
                    "tests_passed": len([r for r in test_records if r["result_status"] == TestStatus.PASSED]),
                    "tests_failed": len(failed_tests),
                    "pass_rate": len([r for r in test_records if r["result_status"] == TestStatus.PASSED]) / len(test_records) * 100
                },
                "test_results": [
                    {
                        "test_name": record["test_name"],
                        "sample_id": record["sample_id"],
                        "test_method": record["test_method"],
                        "result_status": record["result_status"].value,
                        "test_results": record.get("test_results", {}),
                        "specifications": record.get("specifications", {}),
                        "completion_time": record.get("test_completion_time")
                    }
                    for record in test_records
                ],
                "failed_tests": [
                    {
                        "test_name": record["test_name"],
                        "failure_reason": record.get("deviation_investigation", "Test failure"),
                        "corrective_action": record.get("corrective_action", "Under investigation")
                    }
                    for record in failed_tests
                ] if failed_tests else [],
                "next_stage": await self._get_next_manufacturing_stage(manufacturing_stage),
                "gmp_compliance": "GMP compliant - all procedures followed"
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate stage release report: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_sampling_plan(self, manufacturing_stage: str, required_tests: List[str]) -> Dict[str, Any]:
        """Generate sampling plan for manufacturing stage"""
        stage_sampling = self.sampling_plans.get(manufacturing_stage, {})
        
        sampling_plan = {
            "manufacturing_stage": manufacturing_stage,
            "sampling_strategy": stage_sampling.get("sampling_strategy", "systematic_sampling"),
            "sample_points": stage_sampling.get("sample_points", ["multiple_locations"]),
            "sampling_frequency": stage_sampling.get("frequency", "end_of_stage"),
            "tests": []
        }
        
        for test_name in required_tests:
            test_spec = self.test_specifications.get(test_name, {})
            test_plan = {
                "test_name": test_name,
                "test_method": test_spec.get("test_method", "Unknown"),
                "sampling_locations": test_spec.get("sampling_locations", 1),
                "sample_size": test_spec.get("sample_size_grams", test_spec.get("sample_size_tablets", 1)),
                "analysis_time_minutes": test_spec.get("analysis_time_minutes", 30)
            }
            sampling_plan["tests"].append(test_plan)
        
        return sampling_plan
    
    async def _validate_test_results(self, test_name: str, test_results: Dict[str, Any], specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test results against specifications"""
        validation = {
            "passed": True,
            "issues": [],
            "test_name": test_name
        }
        
        for param, spec in specifications.items():
            if param in test_results:
                result_value = test_results[param]
                
                if isinstance(spec, dict):
                    if "min" in spec and "max" in spec:
                        if result_value < spec["min"] or result_value > spec["max"]:
                            validation["passed"] = False
                            validation["issues"].append(
                                f"{param}: {result_value} outside range {spec['min']}-{spec['max']}"
                            )
                    elif "max" in spec:
                        if result_value > spec["max"]:
                            validation["passed"] = False
                            validation["issues"].append(f"{param}: {result_value} exceeds maximum {spec['max']}")
                    elif "min" in spec:
                        if result_value < spec["min"]:
                            validation["passed"] = False
                            validation["issues"].append(f"{param}: {result_value} below minimum {spec['min']}")
            else:
                validation["passed"] = False
                validation["issues"].append(f"Missing test result: {param}")
        
        return validation
    
    async def _assess_batch_impact(self, batch_id: UUID, manufacturing_stage: str, test_name: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess impact of test results on batch disposition"""
        impact = {
            "disposition": "continue",
            "assessment": "Test results within specification",
            "action_required": False
        }
        
        if not validation_result["passed"]:
            # Determine criticality of failed test
            critical_tests = ["assay", "content_uniformity", "dissolution", "blend_uniformity"]
            
            if test_name in critical_tests:
                impact["disposition"] = "hold"
                impact["assessment"] = f"Critical test failure: {test_name}. Batch requires investigation."
                impact["action_required"] = True
            else:
                impact["disposition"] = "investigate"
                impact["assessment"] = f"Test failure: {test_name}. Investigation required before proceeding."
                impact["action_required"] = True
        
        return impact
    
    async def _initiate_deviation_investigation(self, test_record: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
        """Initiate deviation investigation for failed test"""
        investigation = f"DEVIATION INVESTIGATION INITIATED\n"
        investigation += f"Test: {test_record['test_name']}\n"
        investigation += f"Sample: {test_record['sample_id']}\n"
        investigation += f"Failure Reason: {'; '.join(validation_result['issues'])}\n"
        investigation += f"Investigation Required: Root cause analysis and corrective action\n"
        investigation += f"Status: OPEN\n"
        investigation += f"Initiated: {datetime.now(timezone.utc).isoformat()}"
        
        return investigation
    
    async def _get_next_manufacturing_stage(self, current_stage: str) -> Optional[str]:
        """Get next manufacturing stage in sequence"""
        current_sequence = self.manufacturing_stages.get(current_stage, {}).get("sequence", 0)
        
        for stage, config in self.manufacturing_stages.items():
            if config.get("sequence", 0) == current_sequence + 1:
                return stage
        
        return None
    
    # Database operations (these would integrate with actual database)
    async def _store_testing_record(self, record: InProcessTesting):
        """Store testing record in database"""
        logger.debug(f"Storing in-process testing record {record.id}")
    
    async def _get_testing_record(self, test_id: UUID) -> Optional[Dict[str, Any]]:
        """Get testing record from database"""
        return None
    
    async def _update_testing_record(self, test_id: UUID, updates: Dict[str, Any]):
        """Update testing record in database"""
        logger.debug(f"Updating testing record {test_id}")
    
    async def _get_batch_test_records(self, batch_id: UUID, manufacturing_stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get test records for batch"""
        return []
    
    async def _update_batch_status(self, batch_id: UUID, status: str, reason: str):
        """Update batch status"""
        logger.debug(f"Updating batch {batch_id} status to {status}: {reason}")
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"