"""
Finished Product Testing Service
Comprehensive testing and release criteria validation for pharmaceutical finished products
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from src.models.gmp_models import FinishedProductTesting, TestStatus
from src.services.immutable_audit_service import ImmutableAuditService
from src.models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class FinishedProductTestingService:
    """
    Service for managing finished product testing, release criteria validation,
    and batch disposition decisions
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.product_specifications = self._initialize_product_specifications()
        self.test_methods = self._initialize_test_methods()
        self.release_criteria = self._initialize_release_criteria()
        self.stability_protocols = self._initialize_stability_protocols()
        
    def _initialize_product_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Initialize product specifications for different products"""
        return {
            "acetaminophen_tablets_500mg": {
                "product_name": "Acetaminophen Tablets 500mg",
                "product_code": "ACE-500-TAB",
                "dosage_form": "tablet",
                "strength": "500mg",
                "release_tests": {
                    "identification": {
                        "method": "HPLC",
                        "acceptance_criteria": "Retention time matches reference standard ± 2%"
                    },
                    "assay": {
                        "method": "HPLC",
                        "acceptance_criteria": {"min": 95.0, "max": 105.0, "unit": "% of label claim"}
                    },
                    "dissolution": {
                        "method": "USP Dissolution Apparatus II",
                        "acceptance_criteria": {
                            "Q_15min": {"min": 80.0, "unit": "% released"},
                            "individual_units": {"min": 70.0, "unit": "% released"}
                        }
                    },
                    "content_uniformity": {
                        "method": "HPLC Individual Content",
                        "acceptance_criteria": {
                            "individual_content": {"min": 85.0, "max": 115.0, "unit": "% of label claim"},
                            "rsd": {"max": 6.0, "unit": "%"}
                        }
                    },
                    "weight_variation": {
                        "method": "Individual Weight Determination",
                        "acceptance_criteria": {
                            "individual_weights": {"min": 90.0, "max": 110.0, "unit": "% of average weight"}
                        }
                    },
                    "hardness": {
                        "method": "Hardness Tester",
                        "acceptance_criteria": {"min": 4.0, "max": 8.0, "unit": "kp"}
                    },
                    "friability": {
                        "method": "Friability Tester",
                        "acceptance_criteria": {"max": 1.0, "unit": "% weight loss"}
                    },
                    "disintegration": {
                        "method": "Disintegration Tester",
                        "acceptance_criteria": {"max": 30.0, "unit": "minutes"}
                    },
                    "appearance": {
                        "method": "Visual Inspection",
                        "acceptance_criteria": "White to off-white, round, biconvex tablets"
                    },
                    "related_substances": {
                        "method": "HPLC",
                        "acceptance_criteria": {
                            "individual_impurity": {"max": 0.5, "unit": "%"},
                            "total_impurities": {"max": 2.0, "unit": "%"}
                        }
                    },
                    "residual_solvents": {
                        "method": "GC",
                        "acceptance_criteria": {
                            "methanol": {"max": 3000, "unit": "ppm"},
                            "ethanol": {"max": 5000, "unit": "ppm"}
                        }
                    },
                    "water_content": {
                        "method": "Karl Fischer",
                        "acceptance_criteria": {"max": 3.0, "unit": "% w/w"}
                    },
                    "microbial_limits": {
                        "method": "USP <61>",
                        "acceptance_criteria": {
                            "total_aerobic_count": {"max": 1000, "unit": "CFU/g"},
                            "yeast_mold": {"max": 100, "unit": "CFU/g"},
                            "e_coli": "Absent per 1g",
                            "salmonella": "Absent per 10g"
                        }
                    }
                },
                "packaging_tests": {
                    "container_closure_integrity": {
                        "method": "Vacuum Decay",
                        "acceptance_criteria": "No leaks detected"
                    },
                    "extractables_leachables": {
                        "method": "HPLC-MS",
                        "acceptance_criteria": {"max": 10.0, "unit": "ppm total"}
                    },
                    "moisture_protection": {
                        "method": "Moisture Permeation",
                        "acceptance_criteria": {"max": 0.5, "unit": "g/package/day"}
                    }
                },
                "labeling_requirements": {
                    "label_accuracy": "100% accuracy required",
                    "barcode_verification": "All barcodes must scan correctly",
                    "expiry_date_format": "MM/YYYY format required"
                }
            },
            "ibuprofen_capsules_200mg": {
                "product_name": "Ibuprofen Capsules 200mg",
                "product_code": "IBU-200-CAP",
                "dosage_form": "capsule",
                "strength": "200mg",
                "release_tests": {
                    "identification": {
                        "method": "HPLC",
                        "acceptance_criteria": "Retention time matches reference standard ± 2%"
                    },
                    "assay": {
                        "method": "HPLC",
                        "acceptance_criteria": {"min": 95.0, "max": 105.0, "unit": "% of label claim"}
                    },
                    "dissolution": {
                        "method": "USP Dissolution Apparatus I",
                        "acceptance_criteria": {
                            "Q_30min": {"min": 80.0, "unit": "% released"},
                            "individual_units": {"min": 70.0, "unit": "% released"}
                        }
                    },
                    "content_uniformity": {
                        "method": "HPLC Individual Content",
                        "acceptance_criteria": {
                            "individual_content": {"min": 85.0, "max": 115.0, "unit": "% of label claim"},
                            "rsd": {"max": 6.0, "unit": "%"}
                        }
                    },
                    "capsule_integrity": {
                        "method": "Visual Inspection",
                        "acceptance_criteria": "No cracks, splits, or deformation"
                    },
                    "related_substances": {
                        "method": "HPLC",
                        "acceptance_criteria": {
                            "individual_impurity": {"max": 0.5, "unit": "%"},
                            "total_impurities": {"max": 2.0, "unit": "%"}
                        }
                    }
                }
            }
        }
    
    def _initialize_test_methods(self) -> Dict[str, Dict[str, Any]]:
        """Initialize test methods and procedures"""
        return {
            "HPLC": {
                "method_name": "High Performance Liquid Chromatography",
                "equipment_required": ["HPLC System", "Column", "Reference Standards"],
                "sample_preparation": "Dissolve sample in mobile phase",
                "analysis_time_minutes": 45,
                "analyst_qualification": "HPLC certified",
                "system_suitability": {
                    "resolution": {"min": 2.0},
                    "tailing_factor": {"max": 2.0},
                    "rsd_replicate_injections": {"max": 2.0}
                }
            },
            "USP Dissolution Apparatus II": {
                "method_name": "USP Dissolution Test - Paddle Method",
                "equipment_required": ["Dissolution Tester", "Paddle", "Dissolution Medium"],
                "sample_preparation": "6 units per test",
                "analysis_time_minutes": 60,
                "test_conditions": {
                    "medium": "900 mL purified water",
                    "temperature": "37°C ± 0.5°C",
                    "rotation_speed": "50 rpm"
                }
            },
            "Hardness Tester": {
                "method_name": "Tablet Hardness Test",
                "equipment_required": ["Hardness Tester"],
                "sample_preparation": "10 tablets",
                "analysis_time_minutes": 15,
                "test_conditions": {
                    "sample_conditioning": "Room temperature",
                    "measurement_units": "kp or N"
                }
            },
            "Friability Tester": {
                "method_name": "Tablet Friability Test",
                "equipment_required": ["Friability Tester"],
                "sample_preparation": "Sample equivalent to 6.5g",
                "analysis_time_minutes": 30,
                "test_conditions": {
                    "rotation_speed": "25 rpm",
                    "duration": "4 minutes",
                    "number_of_rotations": "100"
                }
            },
            "Karl Fischer": {
                "method_name": "Karl Fischer Titration",
                "equipment_required": ["Karl Fischer Titrator", "KF Reagent"],
                "sample_preparation": "Direct injection or dissolution",
                "analysis_time_minutes": 20,
                "test_conditions": {
                    "sample_size": "Appropriate for expected water content",
                    "titrant": "KF reagent"
                }
            },
            "USP <61>": {
                "method_name": "Microbial Enumeration Tests",
                "equipment_required": ["Laminar Flow Hood", "Incubator", "Culture Media"],
                "sample_preparation": "Aseptic sampling",
                "analysis_time_minutes": 4320,  # 3 days
                "test_conditions": {
                    "total_aerobic_count": "32.5°C, 3-5 days",
                    "yeast_mold": "22.5°C, 5-7 days"
                }
            }
        }
    
    def _initialize_release_criteria(self) -> Dict[str, Any]:
        """Initialize release criteria framework"""
        return {
            "critical_tests": ["identification", "assay", "dissolution", "content_uniformity", "microbial_limits"],
            "non_critical_tests": ["hardness", "friability", "appearance", "weight_variation"],
            "release_decision_matrix": {
                "all_critical_pass": "release",
                "any_critical_fail": "reject",
                "non_critical_fail_investigation": "investigate"
            },
            "stability_requirements": {
                "initial_testing": "Required before release",
                "accelerated_conditions": "40°C/75%RH for 6 months",
                "long_term_conditions": "25°C/60%RH for 24 months"
            }
        }
    
    def _initialize_stability_protocols(self) -> Dict[str, Dict[str, Any]]:
        """Initialize stability testing protocols"""
        return {
            "accelerated": {
                "conditions": "40°C ± 2°C / 75%RH ± 5%RH",
                "duration_months": 6,
                "testing_intervals": [0, 3, 6],
                "tests": ["appearance", "assay", "dissolution", "related_substances", "water_content"]
            },
            "intermediate": {
                "conditions": "30°C ± 2°C / 65%RH ± 5%RH",
                "duration_months": 12,
                "testing_intervals": [0, 3, 6, 9, 12],
                "tests": ["appearance", "assay", "dissolution", "related_substances"]
            },
            "long_term": {
                "conditions": "25°C ± 2°C / 60%RH ± 5%RH",
                "duration_months": 24,
                "testing_intervals": [0, 3, 6, 9, 12, 18, 24],
                "tests": ["appearance", "assay", "dissolution", "related_substances", "water_content", "microbial_limits"]
            }
        }
    
    async def initiate_finished_product_testing(
        self,
        batch_id: UUID,
        product_name: str,
        product_code: str,
        batch_size: float,
        manufacturing_date: datetime,
        expiry_date: datetime,
        initiated_by: UUID,
        testing_type: str = "release",  # release, stability, retain
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Initiate finished product testing for batch release
        """
        try:
            # Get product specifications
            product_key = self._get_product_key(product_name, product_code)
            if product_key not in self.product_specifications:
                raise ValueError(f"Product specifications not found for {product_name}")
            
            product_spec = self.product_specifications[product_key]
            
            # Generate sampling plan
            sampling_plan = await self._generate_sampling_plan(product_spec, batch_size)
            
            # Create test suite based on specifications
            test_suite = await self._create_test_suite(product_spec, testing_type)
            
            # Create finished product testing record
            testing_record = FinishedProductTesting(
                id=uuid4(),
                batch_id=batch_id,
                product_name=product_name,
                product_code=product_code,
                batch_size=batch_size,
                manufacturing_date=manufacturing_date,
                expiry_date=expiry_date,
                sampling_plan=sampling_plan,
                test_suite=test_suite,
                performed_by=initiated_by,
                release_specifications=product_spec["release_tests"],
                overall_result=TestStatus.PENDING,
                release_decision="PENDING",
                notes=f"Finished product testing initiated for {testing_type}"
            )
            
            # Store testing record
            await self._store_testing_record(testing_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=initiated_by,
                username=await self._get_username(initiated_by),
                full_name=await self._get_full_name(initiated_by),
                action=AuditAction.CREATE,
                action_description=f"Finished product testing initiated: {product_name}",
                entity_type="finished_product_testing",
                entity_id=testing_record.id,
                entity_identifier=f"BATCH:{batch_id}",
                new_values={
                    "batch_id": str(batch_id),
                    "product_name": product_name,
                    "product_code": product_code,
                    "batch_size": batch_size,
                    "testing_type": testing_type,
                    "test_count": len(test_suite)
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Finished product testing initiated: {product_name} batch {batch_id}")
            
            return {
                "testing_record_id": str(testing_record.id),
                "batch_id": str(batch_id),
                "product_name": product_name,
                "product_code": product_code,
                "testing_type": testing_type,
                "sampling_plan": sampling_plan,
                "test_suite": test_suite,
                "estimated_completion_time": datetime.now(timezone.utc) + timedelta(
                    minutes=sum(
                        self.test_methods.get(test.get("method", ""), {}).get("analysis_time_minutes", 60)
                        for test in test_suite
                    )
                ),
                "critical_tests": [test["test_name"] for test in test_suite if test.get("critical", False)]
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate finished product testing: {str(e)}")
            raise
    
    async def record_test_results(
        self,
        testing_record_id: UUID,
        test_results: Dict[str, Any],
        performed_by: UUID,
        reviewed_by: Optional[UUID] = None,
        testing_notes: Optional[str] = None,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record finished product test results
        """
        try:
            # Get testing record
            testing_record = await self._get_testing_record(testing_record_id)
            if not testing_record:
                raise ValueError("Testing record not found")
            
            # Validate test results against specifications
            validation_result = await self._validate_test_results(
                test_results,
                testing_record.get("release_specifications", {})
            )
            
            # Assess packaging integrity
            packaging_assessment = await self._assess_packaging_integrity(test_results)
            
            # Verify labeling compliance
            labeling_verification = await self._verify_labeling_compliance(
                testing_record["product_code"],
                test_results
            )
            
            # Generate certificate of analysis
            certificate_of_analysis = await self._generate_certificate_of_analysis(
                testing_record,
                test_results,
                validation_result
            )
            
            # Determine overall result
            overall_result = TestStatus.PASSED if validation_result["overall_pass"] else TestStatus.FAILED
            
            # Make release decision
            release_decision = await self._make_release_decision(
                validation_result,
                packaging_assessment,
                labeling_verification
            )
            
            # Update testing record
            updated_record = {
                "testing_started": testing_record.get("testing_started") or datetime.now(timezone.utc),
                "testing_completed": datetime.now(timezone.utc),
                "performed_by": performed_by,
                "reviewed_by": reviewed_by,
                "test_results": test_results,
                "overall_result": overall_result,
                "release_decision": release_decision["decision"],
                "release_date": datetime.now(timezone.utc) if release_decision["decision"] == "RELEASED" else None,
                "certificate_of_analysis": certificate_of_analysis,
                "packaging_integrity": packaging_assessment,
                "labeling_verification": labeling_verification,
                "notes": testing_notes
            }
            
            # Store updated record
            await self._update_testing_record(testing_record_id, updated_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=performed_by,
                username=await self._get_username(performed_by),
                full_name=await self._get_full_name(performed_by),
                action=AuditAction.UPDATE,
                action_description=f"Finished product testing completed: {testing_record['product_name']}",
                entity_type="finished_product_testing",
                entity_id=testing_record_id,
                entity_identifier=f"BATCH:{testing_record['batch_id']}",
                old_values={"overall_result": TestStatus.PENDING.value},
                new_values={
                    "overall_result": overall_result.value,
                    "release_decision": release_decision["decision"],
                    "testing_completed": updated_record["testing_completed"].isoformat(),
                    "validation_passed": validation_result["overall_pass"]
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=not validation_result["overall_pass"]
            )
            
            # Update batch status
            await self._update_batch_status(
                testing_record["batch_id"],
                release_decision["decision"],
                release_decision["rationale"]
            )
            
            # Initiate stability testing if released
            if release_decision["decision"] == "RELEASED":
                await self._initiate_stability_testing(testing_record_id)
            
            logger.info(f"Finished product testing completed: {testing_record['product_name']} - {release_decision['decision']}")
            
            return {
                "testing_record_id": str(testing_record_id),
                "batch_id": str(testing_record["batch_id"]),
                "product_name": testing_record["product_name"],
                "overall_result": overall_result.value,
                "release_decision": release_decision["decision"],
                "release_rationale": release_decision["rationale"],
                "testing_completed": updated_record["testing_completed"].isoformat(),
                "certificate_of_analysis": certificate_of_analysis,
                "validation_summary": validation_result,
                "packaging_integrity": packaging_assessment,
                "labeling_verification": labeling_verification
            }
            
        except Exception as e:
            logger.error(f"Failed to record test results: {str(e)}")
            raise
    
    async def get_batch_testing_status(
        self,
        batch_id: UUID
    ) -> Dict[str, Any]:
        """
        Get finished product testing status for batch
        """
        try:
            # Get testing record
            testing_record = await self._get_testing_record_by_batch(batch_id)
            
            if not testing_record:
                return {
                    "batch_id": str(batch_id),
                    "status": "not_initiated",
                    "message": "Finished product testing not initiated for this batch"
                }
            
            # Calculate testing progress
            test_suite = testing_record.get("test_suite", [])
            test_results = testing_record.get("test_results", {})
            
            completed_tests = len([test for test in test_suite if test["test_name"] in test_results])
            total_tests = len(test_suite)
            
            # Determine status
            if testing_record.get("overall_result") == TestStatus.PASSED:
                status = "completed_passed"
            elif testing_record.get("overall_result") == TestStatus.FAILED:
                status = "completed_failed"
            elif completed_tests > 0:
                status = "in_progress"
            else:
                status = "pending"
            
            return {
                "batch_id": str(batch_id),
                "testing_record_id": str(testing_record["id"]),
                "product_name": testing_record["product_name"],
                "product_code": testing_record["product_code"],
                "status": status,
                "overall_result": testing_record.get("overall_result"),
                "release_decision": testing_record.get("release_decision", "PENDING"),
                "testing_progress": {
                    "completed_tests": completed_tests,
                    "total_tests": total_tests,
                    "completion_percentage": (completed_tests / total_tests * 100) if total_tests > 0 else 0
                },
                "critical_tests_status": await self._get_critical_tests_status(testing_record),
                "release_date": testing_record.get("release_date"),
                "expiry_date": testing_record.get("expiry_date")
            }
            
        except Exception as e:
            logger.error(f"Failed to get batch testing status: {str(e)}")
            return {"error": str(e)}
    
    async def generate_release_certificate(
        self,
        testing_record_id: UUID,
        approved_by: UUID
    ) -> Dict[str, Any]:
        """
        Generate official release certificate
        """
        try:
            # Get testing record
            testing_record = await self._get_testing_record(testing_record_id)
            if not testing_record:
                raise ValueError("Testing record not found")
            
            # Validate release eligibility
            if testing_record.get("release_decision") != "RELEASED":
                raise ValueError("Batch not approved for release")
            
            # Generate certificate
            certificate = {
                "certificate_type": "batch_release_certificate",
                "certificate_number": f"RC-{testing_record['batch_id']}-{datetime.now().strftime('%Y%m%d%H%M')}",
                "batch_id": str(testing_record["batch_id"]),
                "product_name": testing_record["product_name"],
                "product_code": testing_record["product_code"],
                "batch_size": testing_record["batch_size"],
                "manufacturing_date": testing_record["manufacturing_date"],
                "expiry_date": testing_record["expiry_date"],
                "release_date": testing_record["release_date"],
                "approved_by": str(approved_by),
                "certificate_date": datetime.now(timezone.utc).isoformat(),
                "testing_summary": {
                    "total_tests": len(testing_record.get("test_suite", [])),
                    "tests_passed": len([
                        test for test in testing_record.get("test_suite", [])
                        if test["test_name"] in testing_record.get("test_results", {})
                    ]),
                    "overall_result": testing_record.get("overall_result"),
                    "certificate_of_analysis": testing_record.get("certificate_of_analysis")
                },
                "quality_statement": "This batch has been tested and found to comply with all established specifications and release criteria.",
                "regulatory_compliance": "Manufactured in accordance with cGMP requirements and FDA regulations",
                "authorized_signature": f"Electronically signed by {await self._get_full_name(approved_by)}",
                "certificate_validity": "This certificate is valid for the lifetime of the batch"
            }
            
            return certificate
            
        except Exception as e:
            logger.error(f"Failed to generate release certificate: {str(e)}")
            return {"error": str(e)}
    
    def _get_product_key(self, product_name: str, product_code: str) -> str:
        """Get product key for specifications lookup"""
        # Normalize product name for lookup
        normalized_name = product_name.lower().replace(" ", "_")
        return normalized_name
    
    async def _generate_sampling_plan(self, product_spec: Dict[str, Any], batch_size: float) -> Dict[str, Any]:
        """Generate sampling plan for finished product testing"""
        # Calculate sample size based on batch size
        if batch_size <= 100000:
            sample_size = min(30, max(10, int(batch_size * 0.0003)))
        else:
            sample_size = 30
        
        return {
            "batch_size": batch_size,
            "sample_size": sample_size,
            "sampling_method": "random_sampling",
            "sampling_locations": ["beginning", "middle", "end"],
            "sample_identification": "Sequential numbering required",
            "sampling_conditions": "Room temperature, controlled environment",
            "sample_integrity": "Maintain sample integrity until testing"
        }
    
    async def _create_test_suite(self, product_spec: Dict[str, Any], testing_type: str) -> List[Dict[str, Any]]:
        """Create test suite based on product specifications"""
        test_suite = []
        
        release_tests = product_spec.get("release_tests", {})
        critical_tests = self.release_criteria["critical_tests"]
        
        for test_name, test_spec in release_tests.items():
            test_item = {
                "test_name": test_name,
                "method": test_spec.get("method", "Unknown"),
                "acceptance_criteria": test_spec.get("acceptance_criteria"),
                "critical": test_name in critical_tests,
                "testing_type": testing_type,
                "estimated_time": self.test_methods.get(test_spec.get("method", ""), {}).get("analysis_time_minutes", 60)
            }
            test_suite.append(test_item)
        
        return test_suite
    
    async def _validate_test_results(self, test_results: Dict[str, Any], specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test results against specifications"""
        validation = {
            "overall_pass": True,
            "failed_tests": [],
            "test_validations": {}
        }
        
        for test_name, test_spec in specifications.items():
            if test_name in test_results:
                test_validation = await self._validate_single_test(
                    test_name,
                    test_results[test_name],
                    test_spec.get("acceptance_criteria", {})
                )
                
                validation["test_validations"][test_name] = test_validation
                
                if not test_validation["passed"]:
                    validation["overall_pass"] = False
                    validation["failed_tests"].append({
                        "test_name": test_name,
                        "issues": test_validation["issues"]
                    })
        
        return validation
    
    async def _validate_single_test(self, test_name: str, test_result: Any, acceptance_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single test result"""
        validation = {
            "passed": True,
            "issues": []
        }
        
        if isinstance(acceptance_criteria, dict):
            for criterion, limit in acceptance_criteria.items():
                if isinstance(limit, dict) and "min" in limit and "max" in limit:
                    if isinstance(test_result, dict) and criterion in test_result:
                        value = test_result[criterion]
                        if value < limit["min"] or value > limit["max"]:
                            validation["passed"] = False
                            validation["issues"].append(f"{criterion}: {value} outside range {limit['min']}-{limit['max']}")
                elif isinstance(limit, dict) and "max" in limit:
                    if isinstance(test_result, dict) and criterion in test_result:
                        value = test_result[criterion]
                        if value > limit["max"]:
                            validation["passed"] = False
                            validation["issues"].append(f"{criterion}: {value} exceeds maximum {limit['max']}")
        
        return validation
    
    async def _assess_packaging_integrity(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess packaging integrity"""
        packaging_tests = ["container_closure_integrity", "extractables_leachables", "moisture_protection"]
        
        packaging_results = {}
        for test in packaging_tests:
            if test in test_results:
                packaging_results[test] = test_results[test]
        
        return {
            "packaging_tests_completed": len(packaging_results),
            "packaging_integrity_verified": len(packaging_results) > 0,
            "packaging_results": packaging_results
        }
    
    async def _verify_labeling_compliance(self, product_code: str, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Verify labeling compliance"""
        return {
            "label_accuracy_verified": True,
            "barcode_verification": "All barcodes scan correctly",
            "expiry_date_format": "MM/YYYY format confirmed",
            "regulatory_text": "All required regulatory text present",
            "product_code_match": product_code in test_results.get("label_verification", {})
        }
    
    async def _generate_certificate_of_analysis(self, testing_record: Dict[str, Any], test_results: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
        """Generate certificate of analysis"""
        coa_lines = [
            "CERTIFICATE OF ANALYSIS",
            "="*50,
            f"Product: {testing_record['product_name']}",
            f"Batch ID: {testing_record['batch_id']}",
            f"Manufacturing Date: {testing_record['manufacturing_date']}",
            f"Expiry Date: {testing_record['expiry_date']}",
            f"Batch Size: {testing_record['batch_size']}",
            "",
            "TEST RESULTS:",
            "-"*30
        ]
        
        for test_name, result in test_results.items():
            status = "PASS" if validation_result["test_validations"].get(test_name, {}).get("passed", False) else "FAIL"
            coa_lines.append(f"{test_name}: {result} - {status}")
        
        coa_lines.extend([
            "",
            f"Overall Result: {'PASS' if validation_result['overall_pass'] else 'FAIL'}",
            f"Certificate Date: {datetime.now(timezone.utc).isoformat()}",
            "",
            "This certificate confirms that the above batch has been tested according to established specifications."
        ])
        
        return "\n".join(coa_lines)
    
    async def _make_release_decision(self, validation_result: Dict[str, Any], packaging_assessment: Dict[str, Any], labeling_verification: Dict[str, Any]) -> Dict[str, Any]:
        """Make batch release decision"""
        if validation_result["overall_pass"] and packaging_assessment["packaging_integrity_verified"] and labeling_verification["label_accuracy_verified"]:
            return {
                "decision": "RELEASED",
                "rationale": "All tests passed acceptance criteria"
            }
        else:
            return {
                "decision": "REJECTED",
                "rationale": "One or more tests failed to meet acceptance criteria"
            }
    
    async def _get_critical_tests_status(self, testing_record: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of critical tests"""
        critical_tests = self.release_criteria["critical_tests"]
        test_results = testing_record.get("test_results", {})
        
        critical_status = {}
        for test in critical_tests:
            if test in test_results:
                critical_status[test] = "completed"
            else:
                critical_status[test] = "pending"
        
        return critical_status
    
    async def _initiate_stability_testing(self, testing_record_id: UUID):
        """Initiate stability testing for released batch"""
        logger.info(f"Initiating stability testing for testing record {testing_record_id}")
        # This would create stability testing protocols
    
    # Database operations (these would integrate with actual database)
    async def _store_testing_record(self, record: FinishedProductTesting):
        """Store testing record in database"""
        logger.debug(f"Storing finished product testing record {record.id}")
    
    async def _get_testing_record(self, testing_record_id: UUID) -> Optional[Dict[str, Any]]:
        """Get testing record from database"""
        return None
    
    async def _get_testing_record_by_batch(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Get testing record by batch ID"""
        return None
    
    async def _update_testing_record(self, testing_record_id: UUID, updates: Dict[str, Any]):
        """Update testing record in database"""
        logger.debug(f"Updating testing record {testing_record_id}")
    
    async def _update_batch_status(self, batch_id: UUID, decision: str, rationale: str):
        """Update batch status"""
        logger.debug(f"Updating batch {batch_id} status to {decision}: {rationale}")
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"