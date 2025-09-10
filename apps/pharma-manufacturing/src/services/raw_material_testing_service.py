"""
Raw Material Testing and COA Management Service
Comprehensive testing and certificate of analysis management for pharmaceutical raw materials
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from src.models.gmp_models import RawMaterialTesting, TestStatus
from src.services.immutable_audit_service import ImmutableAuditService
from src.models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class RawMaterialTestingService:
    """
    Service for managing raw material testing, certificate of analysis (COA),
    and material release/quarantine decisions
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.material_specifications = self._initialize_material_specifications()
        self.test_methods = self._initialize_test_methods()
        
    def _initialize_material_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Initialize specifications for different raw materials"""
        return {
            "active_pharmaceutical_ingredient": {
                "api_001": {
                    "material_name": "Acetaminophen USP",
                    "specification_version": "1.2",
                    "tests": {
                        "identity": {
                            "method": "HPLC",
                            "acceptance_criteria": "Retention time matches reference standard ± 2%"
                        },
                        "assay": {
                            "method": "HPLC",
                            "acceptance_criteria": {"min": 98.0, "max": 102.0, "unit": "% w/w"}
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
                            "acceptance_criteria": {"max": 0.5, "unit": "% w/w"}
                        },
                        "particle_size": {
                            "method": "Laser Diffraction",
                            "acceptance_criteria": {
                                "d10": {"min": 5, "max": 15, "unit": "μm"},
                                "d50": {"min": 20, "max": 40, "unit": "μm"},
                                "d90": {"min": 60, "max": 100, "unit": "μm"}
                            }
                        },
                        "heavy_metals": {
                            "method": "ICP-MS",
                            "acceptance_criteria": {"max": 20, "unit": "ppm"}
                        }
                    },
                    "storage_conditions": {
                        "temperature": {"min": 15, "max": 30, "unit": "°C"},
                        "humidity": {"max": 65, "unit": "%RH"},
                        "light": "Protected from light"
                    }
                }
            },
            "excipient": {
                "exc_001": {
                    "material_name": "Microcrystalline Cellulose NF",
                    "specification_version": "1.1",
                    "tests": {
                        "identity": {
                            "method": "FTIR",
                            "acceptance_criteria": "Spectrum matches reference standard"
                        },
                        "ph": {
                            "method": "pH Meter",
                            "acceptance_criteria": {"min": 5.0, "max": 7.5}
                        },
                        "loss_on_drying": {
                            "method": "Gravimetric",
                            "acceptance_criteria": {"max": 7.0, "unit": "% w/w"}
                        },
                        "bulk_density": {
                            "method": "USP Method",
                            "acceptance_criteria": {"min": 0.25, "max": 0.35, "unit": "g/mL"}
                        },
                        "particle_size_distribution": {
                            "method": "Sieve Analysis",
                            "acceptance_criteria": {
                                "retained_on_150μm": {"max": 15, "unit": "%"},
                                "passing_through_45μm": {"min": 85, "unit": "%"}
                            }
                        },
                        "microbial_limits": {
                            "method": "USP <61>",
                            "acceptance_criteria": {
                                "total_aerobic_count": {"max": 1000, "unit": "CFU/g"},
                                "yeast_mold": {"max": 100, "unit": "CFU/g"},
                                "e_coli": "Absent in 1g",
                                "salmonella": "Absent in 10g"
                            }
                        }
                    },
                    "storage_conditions": {
                        "temperature": {"min": 15, "max": 30, "unit": "°C"},
                        "humidity": {"max": 65, "unit": "%RH"}
                    }
                }
            },
            "packaging_material": {
                "pkg_001": {
                    "material_name": "HDPE Bottles",
                    "specification_version": "1.0",
                    "tests": {
                        "visual_inspection": {
                            "method": "Visual",
                            "acceptance_criteria": "No cracks, deformation, or foreign matter"
                        },
                        "dimensions": {
                            "method": "Caliper Measurement",
                            "acceptance_criteria": {
                                "height": {"min": 98, "max": 102, "unit": "mm"},
                                "diameter": {"min": 48, "max": 52, "unit": "mm"}
                            }
                        },
                        "extractables": {
                            "method": "HPLC-MS",
                            "acceptance_criteria": {"max": 10, "unit": "ppm total"}
                        },
                        "barrier_properties": {
                            "method": "Permeation Testing",
                            "acceptance_criteria": {
                                "oxygen_transmission": {"max": 0.1, "unit": "cc/package/day"}
                            }
                        }
                    },
                    "storage_conditions": {
                        "temperature": {"min": 15, "max": 30, "unit": "°C"},
                        "humidity": {"max": 65, "unit": "%RH"}
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
                "analysis_time": 30,  # minutes
                "precision_requirement": {"rsd": 2.0}  # %RSD
            },
            "GC": {
                "method_name": "Gas Chromatography",
                "equipment_required": ["GC System", "Column", "Standards"],
                "sample_preparation": "Extract with suitable solvent",
                "analysis_time": 45,
                "precision_requirement": {"rsd": 5.0}
            },
            "Karl Fischer": {
                "method_name": "Karl Fischer Titration",
                "equipment_required": ["Karl Fischer Titrator", "KF Reagent"],
                "sample_preparation": "Direct injection or dissolution",
                "analysis_time": 15,
                "precision_requirement": {"rsd": 3.0}
            },
            "FTIR": {
                "method_name": "Fourier Transform Infrared Spectroscopy",
                "equipment_required": ["FTIR Spectrometer", "Reference Standards"],
                "sample_preparation": "KBr pellet or ATR",
                "analysis_time": 10,
                "precision_requirement": {"correlation": 0.95}
            },
            "ICP-MS": {
                "method_name": "Inductively Coupled Plasma Mass Spectrometry",
                "equipment_required": ["ICP-MS System", "Certified Standards"],
                "sample_preparation": "Acid digestion",
                "analysis_time": 60,
                "precision_requirement": {"rsd": 10.0}
            }
        }
    
    async def receive_raw_material(
        self,
        material_id: UUID,
        material_name: str,
        material_category: str,
        supplier: str,
        lot_number: str,
        quantity_received: float,
        unit_of_measure: str,
        receipt_date: datetime,
        expiry_date: Optional[datetime] = None,
        coa_received: bool = False,
        coa_data: Optional[Dict[str, Any]] = None,
        received_by: UUID,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record receipt of raw material and initiate testing process
        """
        try:
            # Create raw material testing record
            testing_record = RawMaterialTesting(
                id=uuid4(),
                material_id=material_id,
                material_name=material_name,
                supplier=supplier,
                lot_number=lot_number,
                receipt_date=receipt_date,
                expiry_date=expiry_date,
                quantity_received=quantity_received,
                unit_of_measure=unit_of_measure,
                coa_received=coa_received,
                testing_required=True,
                testing_status=TestStatus.PENDING,
                quarantine_status=True,  # All materials start in quarantine
                notes=f"Material received from {supplier}"
            )
            
            # Generate COA number if not provided
            if coa_received and not testing_record.coa_number:
                testing_record.coa_number = f"COA-{lot_number}-{datetime.now().strftime('%Y%m%d')}"
            
            # Get material specifications
            specifications = await self._get_material_specifications(material_name, material_category)
            testing_record.specifications = specifications
            
            # Store COA data if provided
            if coa_data:
                await self._validate_coa_data(coa_data, specifications)
                testing_record.test_results = coa_data
            
            # Store testing record
            await self._store_testing_record(testing_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=received_by,
                username=await self._get_username(received_by),
                full_name=await self._get_full_name(received_by),
                action=AuditAction.CREATE,
                action_description=f"Raw material received: {material_name}",
                entity_type="raw_material_testing",
                entity_id=testing_record.id,
                entity_identifier=f"{lot_number}:{material_name}",
                new_values={
                    "material_name": material_name,
                    "supplier": supplier,
                    "lot_number": lot_number,
                    "quantity_received": quantity_received,
                    "quarantine_status": True,
                    "coa_received": coa_received
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            # Generate testing plan
            testing_plan = await self._generate_testing_plan(specifications)
            
            logger.info(f"Raw material received: {material_name} lot {lot_number}")
            
            return {
                "testing_record_id": str(testing_record.id),
                "material_id": str(material_id),
                "material_name": material_name,
                "lot_number": lot_number,
                "receipt_date": receipt_date.isoformat(),
                "quarantine_status": True,
                "testing_status": TestStatus.PENDING.value,
                "coa_received": coa_received,
                "testing_plan": testing_plan,
                "estimated_testing_duration": sum(
                    self.test_methods.get(test.get("method", ""), {}).get("analysis_time", 30)
                    for test in testing_plan
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to receive raw material: {str(e)}")
            raise
    
    async def perform_raw_material_testing(
        self,
        testing_record_id: UUID,
        test_results: Dict[str, Any],
        tested_by: UUID,
        reviewed_by: Optional[UUID] = None,
        testing_notes: Optional[str] = None,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record raw material testing results
        """
        try:
            # Get testing record
            testing_record = await self._get_testing_record(testing_record_id)
            if not testing_record:
                raise ValueError("Testing record not found")
            
            # Validate test results against specifications
            validation_result = await self._validate_test_results(
                test_results, 
                testing_record.get("specifications", {})
            )
            
            # Update testing record
            updated_record = {
                "test_results": test_results,
                "testing_status": TestStatus.PASSED if validation_result["overall_pass"] else TestStatus.FAILED,
                "test_started_date": testing_record.get("test_started_date") or datetime.now(timezone.utc),
                "test_completed_date": datetime.now(timezone.utc),
                "tested_by": tested_by,
                "reviewed_by": reviewed_by,
                "overall_result": TestStatus.PASSED if validation_result["overall_pass"] else TestStatus.FAILED,
                "notes": testing_notes
            }
            
            # Store updated record
            await self._update_testing_record(testing_record_id, updated_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=tested_by,
                username=await self._get_username(tested_by),
                full_name=await self._get_full_name(tested_by),
                action=AuditAction.UPDATE,
                action_description=f"Raw material testing completed: {testing_record['material_name']}",
                entity_type="raw_material_testing",
                entity_id=testing_record_id,
                entity_identifier=f"{testing_record['lot_number']}:{testing_record['material_name']}",
                old_values={"testing_status": TestStatus.PENDING.value},
                new_values={
                    "testing_status": updated_record["testing_status"].value,
                    "overall_result": updated_record["overall_result"].value,
                    "test_completed_date": updated_record["test_completed_date"].isoformat(),
                    "validation_passed": validation_result["overall_pass"]
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=not validation_result["overall_pass"]
            )
            
            # Generate certificate of analysis
            if validation_result["overall_pass"]:
                coa = await self._generate_certificate_of_analysis(testing_record_id, test_results, validation_result)
            else:
                coa = None
            
            logger.info(f"Raw material testing completed: {testing_record['material_name']} - {'PASSED' if validation_result['overall_pass'] else 'FAILED'}")
            
            return {
                "testing_record_id": str(testing_record_id),
                "material_name": testing_record["material_name"],
                "lot_number": testing_record["lot_number"],
                "testing_status": updated_record["testing_status"].value,
                "overall_result": updated_record["overall_result"].value,
                "validation_passed": validation_result["overall_pass"],
                "failed_tests": validation_result["failed_tests"],
                "test_completion_date": updated_record["test_completed_date"].isoformat(),
                "certificate_of_analysis": coa,
                "quarantine_status": True  # Remains in quarantine until approved for release
            }
            
        except Exception as e:
            logger.error(f"Failed to perform raw material testing: {str(e)}")
            raise
    
    async def release_or_reject_material(
        self,
        testing_record_id: UUID,
        decision: str,  # "release" or "reject"
        approved_by: UUID,
        approval_notes: str,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Release or reject raw material based on testing results
        """
        try:
            # Get testing record
            testing_record = await self._get_testing_record(testing_record_id)
            if not testing_record:
                raise ValueError("Testing record not found")
            
            # Validate decision
            if decision not in ["release", "reject"]:
                raise ValueError("Decision must be 'release' or 'reject'")
            
            # Check if testing is complete
            if testing_record.get("testing_status") not in [TestStatus.PASSED, TestStatus.FAILED]:
                raise ValueError("Testing must be completed before release/reject decision")
            
            # Update material status
            release_date = datetime.now(timezone.utc) if decision == "release" else None
            quarantine_status = decision != "release"
            
            updated_record = {
                "approved_by": approved_by,
                "release_date": release_date,
                "quarantine_status": quarantine_status,
                "notes": f"{testing_record.get('notes', '')}\\n\\nApproval Decision: {decision.upper()} - {approval_notes}"
            }
            
            # Store updated record
            await self._update_testing_record(testing_record_id, updated_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=approved_by,
                username=await self._get_username(approved_by),
                full_name=await self._get_full_name(approved_by),
                action=AuditAction.APPROVE if decision == "release" else AuditAction.REJECT,
                action_description=f"Raw material {decision}: {testing_record['material_name']}",
                entity_type="raw_material_testing",
                entity_id=testing_record_id,
                entity_identifier=f"{testing_record['lot_number']}:{testing_record['material_name']}",
                old_values={"quarantine_status": True},
                new_values={
                    "quarantine_status": quarantine_status,
                    "release_decision": decision,
                    "approved_by": str(approved_by),
                    "release_date": release_date.isoformat() if release_date else None
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=decision == "reject"
            )
            
            # Update inventory status if released
            if decision == "release":
                await self._update_inventory_status(testing_record["material_id"], "available")
            else:
                await self._update_inventory_status(testing_record["material_id"], "rejected")
            
            logger.info(f"Raw material {decision}: {testing_record['material_name']} lot {testing_record['lot_number']}")
            
            return {
                "testing_record_id": str(testing_record_id),
                "material_name": testing_record["material_name"],
                "lot_number": testing_record["lot_number"],
                "decision": decision,
                "approved_by": str(approved_by),
                "decision_date": datetime.now(timezone.utc).isoformat(),
                "quarantine_status": quarantine_status,
                "release_date": release_date.isoformat() if release_date else None,
                "inventory_status": "available" if decision == "release" else "rejected"
            }
            
        except Exception as e:
            logger.error(f"Failed to release/reject material: {str(e)}")
            raise
    
    async def get_material_testing_status(
        self,
        material_id: Optional[UUID] = None,
        lot_number: Optional[str] = None,
        supplier: Optional[str] = None,
        status: Optional[TestStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get material testing status with filtering options
        """
        try:
            # Get testing records based on filters
            testing_records = await self._get_testing_records_filtered(
                material_id, lot_number, supplier, status
            )
            
            status_list = []
            for record in testing_records:
                status_item = {
                    "testing_record_id": str(record["id"]),
                    "material_id": str(record["material_id"]),
                    "material_name": record["material_name"],
                    "supplier": record["supplier"],
                    "lot_number": record["lot_number"],
                    "receipt_date": record["receipt_date"],
                    "testing_status": record["testing_status"],
                    "quarantine_status": record["quarantine_status"],
                    "coa_received": record["coa_received"],
                    "days_in_quarantine": (datetime.now(timezone.utc) - record["receipt_date"]).days if record["quarantine_status"] else 0,
                    "release_date": record.get("release_date"),
                    "expiry_date": record.get("expiry_date")
                }
                
                # Add testing progress
                if record.get("test_results"):
                    total_tests = len(record.get("specifications", {}).get("tests", {}))
                    completed_tests = len(record.get("test_results", {}))
                    status_item["testing_progress"] = {
                        "completed_tests": completed_tests,
                        "total_tests": total_tests,
                        "progress_percentage": (completed_tests / total_tests * 100) if total_tests > 0 else 0
                    }
                
                status_list.append(status_item)
            
            return status_list
            
        except Exception as e:
            logger.error(f"Failed to get material testing status: {str(e)}")
            return []
    
    async def generate_raw_material_report(
        self,
        start_date: datetime,
        end_date: datetime,
        suppliers: Optional[List[str]] = None,
        material_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive raw material testing report
        """
        try:
            report = {
                "report_type": "raw_material_testing",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {},
                "supplier_analysis": {},
                "material_analysis": {},
                "quality_metrics": {},
                "recommendations": []
            }
            
            # Get raw material data for period
            testing_data = await self._get_testing_data_for_period(
                start_date, end_date, suppliers, material_types
            )
            
            # Calculate summary statistics
            total_lots = len(testing_data)
            passed_lots = sum(1 for test in testing_data if test.get("overall_result") == TestStatus.PASSED)
            rejected_lots = sum(1 for test in testing_data if test.get("overall_result") == TestStatus.FAILED)
            quarantined_lots = sum(1 for test in testing_data if test.get("quarantine_status"))
            
            report["summary"] = {
                "total_lots_received": total_lots,
                "lots_passed": passed_lots,
                "lots_rejected": rejected_lots,
                "lots_in_quarantine": quarantined_lots,
                "acceptance_rate": (passed_lots / total_lots * 100) if total_lots > 0 else 0,
                "rejection_rate": (rejected_lots / total_lots * 100) if total_lots > 0 else 0
            }
            
            # Analyze by supplier
            supplier_analysis = {}
            for supplier in set(test.get("supplier", "Unknown") for test in testing_data):
                supplier_lots = [test for test in testing_data if test.get("supplier") == supplier]
                supplier_passed = sum(1 for test in supplier_lots if test.get("overall_result") == TestStatus.PASSED)
                
                supplier_analysis[supplier] = {
                    "total_lots": len(supplier_lots),
                    "passed_lots": supplier_passed,
                    "acceptance_rate": (supplier_passed / len(supplier_lots) * 100) if supplier_lots else 0
                }
            
            report["supplier_analysis"] = supplier_analysis
            
            # Calculate quality metrics
            avg_testing_time = await self._calculate_average_testing_time(testing_data)
            
            report["quality_metrics"] = {
                "average_testing_time_days": avg_testing_time,
                "coa_availability_rate": sum(1 for test in testing_data if test.get("coa_received")) / total_lots * 100 if total_lots > 0 else 0,
                "on_time_testing_rate": 95,  # Would calculate based on actual data
                "supplier_performance": supplier_analysis
            }
            
            # Generate recommendations
            report["recommendations"] = await self._generate_raw_material_recommendations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate raw material report: {str(e)}")
            return {"error": str(e)}
    
    async def _get_material_specifications(self, material_name: str, material_category: str) -> Dict[str, Any]:
        """Get material specifications"""
        category_specs = self.material_specifications.get(material_category, {})
        
        # Find matching material specification
        for spec_key, spec_data in category_specs.items():
            if material_name.lower() in spec_data["material_name"].lower():
                return spec_data
        
        # Return default specification if not found
        return {
            "material_name": material_name,
            "specification_version": "1.0",
            "tests": {},
            "storage_conditions": {}
        }
    
    async def _validate_coa_data(self, coa_data: Dict[str, Any], specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Validate COA data against specifications"""
        validation_result = {
            "valid": True,
            "issues": []
        }
        
        spec_tests = specifications.get("tests", {})
        
        for test_name, test_spec in spec_tests.items():
            if test_name in coa_data:
                # Validate test result against acceptance criteria
                result = await self._validate_single_test(
                    test_name, coa_data[test_name], test_spec.get("acceptance_criteria", {})
                )
                if not result["passed"]:
                    validation_result["valid"] = False
                    validation_result["issues"].extend(result["issues"])
            else:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing test result: {test_name}")
        
        return validation_result
    
    async def _generate_testing_plan(self, specifications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate testing plan based on specifications"""
        testing_plan = []
        
        for test_name, test_spec in specifications.get("tests", {}).items():
            method = test_spec.get("method", "Unknown")
            plan_item = {
                "test_name": test_name,
                "method": method,
                "acceptance_criteria": test_spec.get("acceptance_criteria"),
                "estimated_time": self.test_methods.get(method, {}).get("analysis_time", 30),
                "equipment_required": self.test_methods.get(method, {}).get("equipment_required", []),
                "sample_preparation": self.test_methods.get(method, {}).get("sample_preparation", "Standard preparation")
            }
            testing_plan.append(plan_item)
        
        return testing_plan
    
    async def _validate_test_results(self, test_results: Dict[str, Any], specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test results against specifications"""
        validation_result = {
            "overall_pass": True,
            "failed_tests": [],
            "test_validations": {}
        }
        
        spec_tests = specifications.get("tests", {})
        
        for test_name, test_result in test_results.items():
            if test_name in spec_tests:
                test_validation = await self._validate_single_test(
                    test_name, test_result, spec_tests[test_name].get("acceptance_criteria", {})
                )
                
                validation_result["test_validations"][test_name] = test_validation
                
                if not test_validation["passed"]:
                    validation_result["overall_pass"] = False
                    validation_result["failed_tests"].append({
                        "test_name": test_name,
                        "issues": test_validation["issues"]
                    })
        
        return validation_result
    
    async def _validate_single_test(self, test_name: str, test_result: Any, acceptance_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single test result"""
        validation = {
            "passed": True,
            "issues": []
        }
        
        if isinstance(acceptance_criteria, dict):
            if "min" in acceptance_criteria and "max" in acceptance_criteria:
                # Range validation
                if isinstance(test_result, (int, float)):
                    if test_result < acceptance_criteria["min"] or test_result > acceptance_criteria["max"]:
                        validation["passed"] = False
                        validation["issues"].append(f"Value {test_result} outside range {acceptance_criteria['min']}-{acceptance_criteria['max']}")
            elif "max" in acceptance_criteria:
                # Maximum value validation
                if isinstance(test_result, (int, float)):
                    if test_result > acceptance_criteria["max"]:
                        validation["passed"] = False
                        validation["issues"].append(f"Value {test_result} exceeds maximum {acceptance_criteria['max']}")
        
        return validation
    
    async def _generate_certificate_of_analysis(self, testing_record_id: UUID, test_results: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate certificate of analysis"""
        testing_record = await self._get_testing_record(testing_record_id)
        
        coa = {
            "coa_number": f"COA-{testing_record['lot_number']}-{datetime.now().strftime('%Y%m%d%H%M')}",
            "material_name": testing_record["material_name"],
            "lot_number": testing_record["lot_number"],
            "supplier": testing_record["supplier"],
            "test_results": test_results,
            "overall_conclusion": "PASS" if validation_result["overall_pass"] else "FAIL",
            "tested_by": str(testing_record["tested_by"]),
            "test_date": testing_record["test_completed_date"],
            "certificate_date": datetime.now(timezone.utc).isoformat(),
            "expiry_date": testing_record.get("expiry_date"),
            "storage_conditions": testing_record.get("specifications", {}).get("storage_conditions", {})
        }
        
        return coa
    
    async def _calculate_average_testing_time(self, testing_data: List[Dict[str, Any]]) -> float:
        """Calculate average testing time"""
        completed_tests = [
            test for test in testing_data 
            if test.get("test_started_date") and test.get("test_completed_date")
        ]
        
        if not completed_tests:
            return 0.0
        
        total_time = 0
        for test in completed_tests:
            start_date = test["test_started_date"]
            end_date = test["test_completed_date"]
            time_diff = (end_date - start_date).total_seconds() / 86400  # Convert to days
            total_time += time_diff
        
        return total_time / len(completed_tests)
    
    async def _generate_raw_material_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on raw material report"""
        recommendations = []
        
        acceptance_rate = report["summary"]["acceptance_rate"]
        rejection_rate = report["summary"]["rejection_rate"]
        
        if acceptance_rate < 95:
            recommendations.append("Review supplier qualification and incoming material quality")
        
        if rejection_rate > 5:
            recommendations.append("Investigate root causes of material failures")
        
        # Analyze supplier performance
        poor_suppliers = [
            supplier for supplier, data in report["supplier_analysis"].items()
            if data["acceptance_rate"] < 90
        ]
        
        if poor_suppliers:
            recommendations.append(f"Review and potentially re-qualify suppliers: {', '.join(poor_suppliers)}")
        
        recommendations.append("Maintain regular communication with suppliers on quality requirements")
        recommendations.append("Consider additional supplier audits for critical materials")
        
        return recommendations
    
    # Database operations (these would integrate with actual database)
    async def _store_testing_record(self, record: RawMaterialTesting):
        """Store testing record in database"""
        logger.debug(f"Storing raw material testing record {record.id}")
    
    async def _get_testing_record(self, testing_record_id: UUID) -> Optional[Dict[str, Any]]:
        """Get testing record from database"""
        return None
    
    async def _update_testing_record(self, testing_record_id: UUID, updates: Dict[str, Any]):
        """Update testing record in database"""
        logger.debug(f"Updating testing record {testing_record_id}")
    
    async def _get_testing_records_filtered(self, material_id: Optional[UUID], lot_number: Optional[str], supplier: Optional[str], status: Optional[TestStatus]) -> List[Dict[str, Any]]:
        """Get filtered testing records"""
        return []
    
    async def _get_testing_data_for_period(self, start_date: datetime, end_date: datetime, suppliers: Optional[List[str]], material_types: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Get testing data for period"""
        return []
    
    async def _update_inventory_status(self, material_id: UUID, status: str):
        """Update inventory status"""
        logger.debug(f"Updating inventory status for {material_id} to {status}")
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"