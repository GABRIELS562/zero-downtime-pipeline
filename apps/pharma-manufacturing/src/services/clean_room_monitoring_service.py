"""
Clean Room Monitoring Service
Comprehensive clean room monitoring and contamination control for pharmaceutical manufacturing
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from models.gmp_models import CleanRoomMonitoring
from services.immutable_audit_service import ImmutableAuditService
from models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class CleanRoomMonitoringService:
    """
    Service for monitoring clean room environments, contamination control,
    and compliance with ISO classifications
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.clean_room_configurations = self._initialize_clean_room_configurations()
        self.iso_classifications = self._initialize_iso_classifications()
        self.contamination_procedures = self._initialize_contamination_procedures()
        self.monitoring_active = False
        
    def _initialize_clean_room_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize clean room configurations"""
        return {
            "CR_STERILE_FILL": {
                "room_name": "Sterile Filling Clean Room",
                "iso_classification": "ISO 5",
                "area_m2": 50.0,
                "volume_m3": 150.0,
                "air_changes_per_hour": 600,
                "personnel_capacity": 4,
                "activities": ["sterile_filling", "aseptic_assembly", "sterile_inspection"],
                "critical_parameters": {
                    "particle_count_0_5um": {"max": 3520, "unit": "particles/m³"},
                    "particle_count_5_0um": {"max": 29, "unit": "particles/m³"},
                    "temperature": {"min": 20, "max": 24, "unit": "°C"},
                    "humidity": {"min": 45, "max": 60, "unit": "%RH"},
                    "pressure_differential": {"min": 12, "max": 15, "unit": "Pa"},
                    "air_velocity": {"min": 0.36, "max": 0.54, "unit": "m/s"}
                },
                "microbial_limits": {
                    "settle_plates": {"max": 1, "unit": "CFU/plate/4h"},
                    "air_samples": {"max": 1, "unit": "CFU/m³"},
                    "contact_plates": {"max": 1, "unit": "CFU/plate"},
                    "glove_prints": {"max": 1, "unit": "CFU/glove"}
                }
            },
            "CR_ASEPTIC_PREP": {
                "room_name": "Aseptic Preparation Clean Room",
                "iso_classification": "ISO 7",
                "area_m2": 80.0,
                "volume_m3": 240.0,
                "air_changes_per_hour": 60,
                "personnel_capacity": 6,
                "activities": ["material_preparation", "equipment_setup", "component_assembly"],
                "critical_parameters": {
                    "particle_count_0_5um": {"max": 352000, "unit": "particles/m³"},
                    "particle_count_5_0um": {"max": 2930, "unit": "particles/m³"},
                    "temperature": {"min": 20, "max": 25, "unit": "°C"},
                    "humidity": {"min": 45, "max": 65, "unit": "%RH"},
                    "pressure_differential": {"min": 10, "max": 15, "unit": "Pa"}
                },
                "microbial_limits": {
                    "settle_plates": {"max": 50, "unit": "CFU/plate/4h"},
                    "air_samples": {"max": 10, "unit": "CFU/m³"},
                    "contact_plates": {"max": 25, "unit": "CFU/plate"},
                    "glove_prints": {"max": 10, "unit": "CFU/glove"}
                }
            },
            "CR_TABLET_COMPRESSION": {
                "room_name": "Tablet Compression Clean Room",
                "iso_classification": "ISO 8",
                "area_m2": 120.0,
                "volume_m3": 360.0,
                "air_changes_per_hour": 20,
                "personnel_capacity": 8,
                "activities": ["tablet_compression", "coating", "packaging"],
                "critical_parameters": {
                    "particle_count_0_5um": {"max": 3520000, "unit": "particles/m³"},
                    "particle_count_5_0um": {"max": 29300, "unit": "particles/m³"},
                    "temperature": {"min": 18, "max": 26, "unit": "°C"},
                    "humidity": {"min": 40, "max": 70, "unit": "%RH"},
                    "pressure_differential": {"min": 5, "max": 10, "unit": "Pa"}
                },
                "microbial_limits": {
                    "settle_plates": {"max": 200, "unit": "CFU/plate/4h"},
                    "air_samples": {"max": 100, "unit": "CFU/m³"},
                    "contact_plates": {"max": 50, "unit": "CFU/plate"}
                }
            },
            "CR_MATERIAL_DISPENSING": {
                "room_name": "Material Dispensing Clean Room",
                "iso_classification": "ISO 8",
                "area_m2": 60.0,
                "volume_m3": 180.0,
                "air_changes_per_hour": 15,
                "personnel_capacity": 4,
                "activities": ["raw_material_dispensing", "weighing", "pre_blending"],
                "critical_parameters": {
                    "particle_count_0_5um": {"max": 3520000, "unit": "particles/m³"},
                    "particle_count_5_0um": {"max": 29300, "unit": "particles/m³"},
                    "temperature": {"min": 18, "max": 26, "unit": "°C"},
                    "humidity": {"min": 40, "max": 70, "unit": "%RH"},
                    "pressure_differential": {"min": 5, "max": 10, "unit": "Pa"}
                },
                "microbial_limits": {
                    "settle_plates": {"max": 200, "unit": "CFU/plate/4h"},
                    "air_samples": {"max": 100, "unit": "CFU/m³"},
                    "contact_plates": {"max": 50, "unit": "CFU/plate"}
                }
            }
        }
    
    def _initialize_iso_classifications(self) -> Dict[str, Dict[str, Any]]:
        """Initialize ISO 14644 clean room classifications"""
        return {
            "ISO 5": {
                "class_name": "ISO Class 5",
                "description": "Sterile manufacturing areas",
                "particle_limits": {
                    "0.1um": {"max": 100000, "unit": "particles/m³"},
                    "0.2um": {"max": 23700, "unit": "particles/m³"},
                    "0.3um": {"max": 10200, "unit": "particles/m³"},
                    "0.5um": {"max": 3520, "unit": "particles/m³"},
                    "1.0um": {"max": 832, "unit": "particles/m³"},
                    "5.0um": {"max": 29, "unit": "particles/m³"}
                },
                "air_changes_per_hour": {"min": 500, "max": 650},
                "recovery_time_minutes": {"max": 15}
            },
            "ISO 7": {
                "class_name": "ISO Class 7",
                "description": "Aseptic processing areas",
                "particle_limits": {
                    "0.1um": {"max": 10000000, "unit": "particles/m³"},
                    "0.2um": {"max": 2370000, "unit": "particles/m³"},
                    "0.3um": {"max": 1020000, "unit": "particles/m³"},
                    "0.5um": {"max": 352000, "unit": "particles/m³"},
                    "1.0um": {"max": 83200, "unit": "particles/m³"},
                    "5.0um": {"max": 2930, "unit": "particles/m³"}
                },
                "air_changes_per_hour": {"min": 50, "max": 80},
                "recovery_time_minutes": {"max": 30}
            },
            "ISO 8": {
                "class_name": "ISO Class 8",
                "description": "Non-sterile manufacturing areas",
                "particle_limits": {
                    "0.1um": {"max": 100000000, "unit": "particles/m³"},
                    "0.2um": {"max": 23700000, "unit": "particles/m³"},
                    "0.3um": {"max": 10200000, "unit": "particles/m³"},
                    "0.5um": {"max": 3520000, "unit": "particles/m³"},
                    "1.0um": {"max": 832000, "unit": "particles/m³"},
                    "5.0um": {"max": 29300, "unit": "particles/m³"}
                },
                "air_changes_per_hour": {"min": 15, "max": 25},
                "recovery_time_minutes": {"max": 60}
            }
        }
    
    def _initialize_contamination_procedures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize contamination control procedures"""
        return {
            "cleaning_procedures": {
                "routine_cleaning": {
                    "frequency": "daily",
                    "agents": ["70% isopropyl alcohol", "quaternary ammonium compounds"],
                    "contact_time_minutes": 10,
                    "procedure": "Spray and wipe method with lint-free cloths"
                },
                "deep_cleaning": {
                    "frequency": "weekly",
                    "agents": ["sporicidal agents", "hydrogen peroxide"],
                    "contact_time_minutes": 30,
                    "procedure": "Fogging or spray application with extended contact time"
                },
                "validation_cleaning": {
                    "frequency": "monthly",
                    "agents": ["validated cleaning agents"],
                    "contact_time_minutes": 60,
                    "procedure": "Complete room decontamination with validation sampling"
                }
            },
            "disinfection_procedures": {
                "surface_disinfection": {
                    "frequency": "between_batches",
                    "agents": ["quaternary ammonium", "phenolic compounds"],
                    "rotation_schedule": "weekly_rotation",
                    "efficacy_testing": "quarterly"
                },
                "air_disinfection": {
                    "frequency": "continuous",
                    "methods": ["HEPA filtration", "UV irradiation"],
                    "monitoring": "continuous_particle_monitoring",
                    "validation": "annual_validation"
                },
                "equipment_disinfection": {
                    "frequency": "pre_use",
                    "agents": ["sterile_70%_alcohol", "sterile_water"],
                    "procedure": "spray_and_wipe",
                    "documentation": "disinfection_logs"
                }
            },
            "personnel_procedures": {
                "gowning_requirements": {
                    "sterile_areas": ["sterile_coveralls", "sterile_gloves", "sterile_boots", "sterile_mask"],
                    "aseptic_areas": ["cleanroom_garments", "sterile_gloves", "shoe_covers", "hair_covers"],
                    "non_sterile_areas": ["lab_coats", "safety_glasses", "shoe_covers"]
                },
                "entry_procedures": {
                    "hand_washing": "antimicrobial_soap_minimum_30_seconds",
                    "airlock_timing": "minimum_15_seconds_per_stage",
                    "gowning_validation": "annual_qualification_required"
                },
                "monitoring_requirements": {
                    "glove_testing": "each_exit_from_sterile_area",
                    "gown_testing": "weekly_contact_plates",
                    "air_sampling": "breathing_zone_monitoring"
                }
            }
        }
    
    async def record_clean_room_monitoring(
        self,
        clean_room_id: str,
        monitoring_data: Dict[str, Any],
        performed_by: UUID,
        cleaning_performed: bool = False,
        disinfection_performed: bool = False,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record clean room monitoring data
        """
        try:
            # Validate clean room configuration
            if clean_room_id not in self.clean_room_configurations:
                raise ValueError(f"Unknown clean room: {clean_room_id}")
            
            room_config = self.clean_room_configurations[clean_room_id]
            
            # Extract monitoring parameters
            particle_counts = monitoring_data.get("particle_counts", {})
            viable_counts = monitoring_data.get("viable_counts", {})
            environmental_conditions = monitoring_data.get("environmental_conditions", {})
            hvac_status = monitoring_data.get("hvac_status", {})
            
            # Validate against ISO classification
            classification_validation = await self._validate_iso_classification(
                clean_room_id,
                particle_counts,
                viable_counts,
                environmental_conditions
            )
            
            # Check for alert conditions
            alert_triggered = not classification_validation["compliant"]
            
            # Determine corrective actions if needed
            corrective_actions = []
            if alert_triggered:
                corrective_actions = await self._determine_corrective_actions(
                    clean_room_id,
                    classification_validation["violations"]
                )
            
            # Create monitoring record
            monitoring_record = CleanRoomMonitoring(
                id=uuid4(),
                clean_room_id=clean_room_id,
                room_classification=room_config["iso_classification"],
                monitoring_date=datetime.now(timezone.utc),
                particle_counts=particle_counts,
                viable_counts=viable_counts,
                environmental_conditions=environmental_conditions,
                personnel_count=monitoring_data.get("personnel_count", 0),
                activity_level=monitoring_data.get("activity_level", "normal"),
                hvac_status=hvac_status,
                cleaning_performed=cleaning_performed,
                cleaning_agent=monitoring_data.get("cleaning_agent"),
                disinfection_performed=disinfection_performed,
                disinfectant_used=monitoring_data.get("disinfectant_used"),
                monitoring_frequency=monitoring_data.get("monitoring_frequency", "routine"),
                alert_levels_exceeded=alert_triggered,
                corrective_actions=corrective_actions,
                performed_by=performed_by,
                notes=monitoring_data.get("notes")
            )
            
            # Store monitoring record
            await self._store_monitoring_record(monitoring_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=performed_by,
                username=await self._get_username(performed_by),
                full_name=await self._get_full_name(performed_by),
                action=AuditAction.CREATE,
                action_description=f"Clean room monitoring recorded: {clean_room_id}",
                entity_type="clean_room_monitoring",
                entity_id=monitoring_record.id,
                entity_identifier=f"ROOM:{clean_room_id}",
                new_values={
                    "clean_room_id": clean_room_id,
                    "iso_classification": room_config["iso_classification"],
                    "monitoring_date": monitoring_record.monitoring_date.isoformat(),
                    "compliant": classification_validation["compliant"],
                    "alert_triggered": alert_triggered,
                    "cleaning_performed": cleaning_performed,
                    "disinfection_performed": disinfection_performed
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=alert_triggered
            )
            
            # Trigger alerts if necessary
            if alert_triggered:
                await self._trigger_contamination_alert(monitoring_record, classification_validation)
            
            logger.info(f"Clean room monitoring recorded: {clean_room_id} - {'COMPLIANT' if classification_validation['compliant'] else 'NON-COMPLIANT'}")
            
            return {
                "monitoring_record_id": str(monitoring_record.id),
                "clean_room_id": clean_room_id,
                "room_classification": room_config["iso_classification"],
                "monitoring_date": monitoring_record.monitoring_date.isoformat(),
                "classification_validation": classification_validation,
                "alert_triggered": alert_triggered,
                "corrective_actions": corrective_actions,
                "compliance_status": "compliant" if classification_validation["compliant"] else "non_compliant"
            }
            
        except Exception as e:
            logger.error(f"Failed to record clean room monitoring: {str(e)}")
            raise
    
    async def start_continuous_monitoring(
        self,
        clean_room_id: str,
        monitoring_interval_minutes: int = 15,
        user_id: Optional[UUID] = None
    ):
        """
        Start continuous clean room monitoring
        """
        try:
            self.monitoring_active = True
            logger.info(f"Starting continuous monitoring for {clean_room_id} (interval: {monitoring_interval_minutes} minutes)")
            
            while self.monitoring_active:
                # Generate simulated monitoring data
                monitoring_data = await self._simulate_monitoring_data(clean_room_id)
                
                # Record monitoring data
                await self.record_clean_room_monitoring(
                    clean_room_id=clean_room_id,
                    monitoring_data=monitoring_data,
                    performed_by=user_id or uuid4(),
                    cleaning_performed=False,
                    disinfection_performed=False
                )
                
                # Wait for next monitoring cycle
                await asyncio.sleep(monitoring_interval_minutes * 60)
                
        except Exception as e:
            logger.error(f"Continuous monitoring error: {str(e)}")
            self.monitoring_active = False
            raise
    
    async def stop_continuous_monitoring(self):
        """Stop continuous clean room monitoring"""
        self.monitoring_active = False
        logger.info("Continuous clean room monitoring stopped")
    
    async def perform_contamination_investigation(
        self,
        clean_room_id: str,
        contamination_type: str,
        investigation_data: Dict[str, Any],
        investigated_by: UUID,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Perform contamination investigation
        """
        try:
            investigation_id = uuid4()
            
            # Determine investigation scope
            investigation_scope = await self._determine_investigation_scope(
                clean_room_id,
                contamination_type,
                investigation_data
            )
            
            # Perform root cause analysis
            root_cause_analysis = await self._perform_root_cause_analysis(
                contamination_type,
                investigation_data,
                investigation_scope
            )
            
            # Develop corrective and preventive actions
            capa_plan = await self._develop_capa_plan(
                clean_room_id,
                contamination_type,
                root_cause_analysis
            )
            
            # Create investigation record
            investigation_record = {
                "investigation_id": str(investigation_id),
                "clean_room_id": clean_room_id,
                "contamination_type": contamination_type,
                "investigation_date": datetime.now(timezone.utc).isoformat(),
                "investigated_by": str(investigated_by),
                "investigation_scope": investigation_scope,
                "root_cause_analysis": root_cause_analysis,
                "capa_plan": capa_plan,
                "investigation_data": investigation_data,
                "status": "in_progress"
            }
            
            # Store investigation record
            await self._store_investigation_record(investigation_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=investigated_by,
                username=await self._get_username(investigated_by),
                full_name=await self._get_full_name(investigated_by),
                action=AuditAction.CREATE,
                action_description=f"Contamination investigation initiated: {clean_room_id}",
                entity_type="contamination_investigation",
                entity_id=investigation_id,
                entity_identifier=f"INVEST:{clean_room_id}:{contamination_type}",
                new_values={
                    "clean_room_id": clean_room_id,
                    "contamination_type": contamination_type,
                    "investigation_scope": investigation_scope,
                    "capa_actions": len(capa_plan["actions"])
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Contamination investigation initiated: {clean_room_id} - {contamination_type}")
            
            return investigation_record
            
        except Exception as e:
            logger.error(f"Failed to perform contamination investigation: {str(e)}")
            raise
    
    async def get_clean_room_status(
        self,
        clean_room_id: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get current clean room status
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            
            if clean_room_id:
                rooms_to_check = [clean_room_id]
            else:
                rooms_to_check = list(self.clean_room_configurations.keys())
            
            room_statuses = {}
            for room_id in rooms_to_check:
                # Get recent monitoring data
                recent_monitoring = await self._get_recent_monitoring_data(room_id, cutoff_time)
                
                if recent_monitoring:
                    latest_record = recent_monitoring[0]  # Most recent
                    
                    room_status = {
                        "room_id": room_id,
                        "room_name": self.clean_room_configurations[room_id]["room_name"],
                        "iso_classification": self.clean_room_configurations[room_id]["iso_classification"],
                        "current_status": "compliant" if not latest_record.get("alert_levels_exceeded", False) else "non_compliant",
                        "last_monitoring": latest_record.get("monitoring_date"),
                        "particle_counts": latest_record.get("particle_counts", {}),
                        "viable_counts": latest_record.get("viable_counts", {}),
                        "environmental_conditions": latest_record.get("environmental_conditions", {}),
                        "personnel_count": latest_record.get("personnel_count", 0),
                        "activity_level": latest_record.get("activity_level", "normal"),
                        "alerts_last_24h": len([r for r in recent_monitoring if r.get("alert_levels_exceeded", False)]),
                        "cleaning_status": {
                            "last_cleaning": self._get_last_cleaning_date(recent_monitoring),
                            "last_disinfection": self._get_last_disinfection_date(recent_monitoring)
                        }
                    }
                else:
                    room_status = {
                        "room_id": room_id,
                        "room_name": self.clean_room_configurations[room_id]["room_name"],
                        "iso_classification": self.clean_room_configurations[room_id]["iso_classification"],
                        "current_status": "no_data",
                        "last_monitoring": None,
                        "message": "No monitoring data available"
                    }
                
                room_statuses[room_id] = room_status
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "time_range_hours": time_range_hours,
                "rooms_monitored": len(room_statuses),
                "room_statuses": room_statuses,
                "overall_summary": {
                    "compliant_rooms": len([r for r in room_statuses.values() if r.get("current_status") == "compliant"]),
                    "non_compliant_rooms": len([r for r in room_statuses.values() if r.get("current_status") == "non_compliant"]),
                    "total_alerts": sum(r.get("alerts_last_24h", 0) for r in room_statuses.values())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get clean room status: {str(e)}")
            return {"error": str(e)}
    
    async def generate_contamination_report(
        self,
        start_date: datetime,
        end_date: datetime,
        clean_room_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive contamination control report
        """
        try:
            report = {
                "report_type": "contamination_control",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "clean_rooms": {},
                "summary": {},
                "contamination_events": [],
                "recommendations": []
            }
            
            # Get data for specified clean rooms
            rooms_to_analyze = clean_room_ids or list(self.clean_room_configurations.keys())
            
            total_monitoring_records = 0
            total_violations = 0
            
            for room_id in rooms_to_analyze:
                room_data = await self._get_monitoring_data_for_period(room_id, start_date, end_date)
                
                # Calculate room statistics
                room_violations = len([r for r in room_data if r.get("alert_levels_exceeded", False)])
                compliance_rate = ((len(room_data) - room_violations) / len(room_data) * 100) if room_data else 0
                
                room_analysis = {
                    "room_name": self.clean_room_configurations[room_id]["room_name"],
                    "iso_classification": self.clean_room_configurations[room_id]["iso_classification"],
                    "monitoring_records": len(room_data),
                    "violations": room_violations,
                    "compliance_rate": compliance_rate,
                    "contamination_events": await self._analyze_contamination_events(room_data),
                    "cleaning_frequency": await self._analyze_cleaning_frequency(room_data),
                    "trending_analysis": await self._analyze_trending_data(room_data)
                }
                
                report["clean_rooms"][room_id] = room_analysis
                total_monitoring_records += len(room_data)
                total_violations += room_violations
            
            # Calculate overall summary
            report["summary"] = {
                "total_monitoring_records": total_monitoring_records,
                "total_violations": total_violations,
                "overall_compliance_rate": ((total_monitoring_records - total_violations) / total_monitoring_records * 100) if total_monitoring_records > 0 else 0,
                "rooms_analyzed": len(rooms_to_analyze)
            }
            
            # Get contamination events
            report["contamination_events"] = await self._get_contamination_events(start_date, end_date)
            
            # Generate recommendations
            report["recommendations"] = await self._generate_contamination_recommendations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate contamination report: {str(e)}")
            return {"error": str(e)}
    
    async def _validate_iso_classification(
        self,
        clean_room_id: str,
        particle_counts: Dict[str, Any],
        viable_counts: Dict[str, Any],
        environmental_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate against ISO classification requirements"""
        room_config = self.clean_room_configurations[clean_room_id]
        iso_class = room_config["iso_classification"]
        iso_limits = self.iso_classifications[iso_class]
        
        violations = []
        compliant = True
        
        # Check particle counts
        for size, count in particle_counts.items():
            if size in iso_limits["particle_limits"]:
                limit = iso_limits["particle_limits"][size]["max"]
                if count > limit:
                    violations.append({
                        "parameter": f"particle_count_{size}",
                        "measured": count,
                        "limit": limit,
                        "violation_type": "particle_count_exceeded"
                    })
                    compliant = False
        
        # Check environmental conditions
        for param, value in environmental_conditions.items():
            if param in room_config["critical_parameters"]:
                limits = room_config["critical_parameters"][param]
                if "min" in limits and value < limits["min"]:
                    violations.append({
                        "parameter": param,
                        "measured": value,
                        "limit": limits["min"],
                        "violation_type": "below_minimum"
                    })
                    compliant = False
                elif "max" in limits and value > limits["max"]:
                    violations.append({
                        "parameter": param,
                        "measured": value,
                        "limit": limits["max"],
                        "violation_type": "above_maximum"
                    })
                    compliant = False
        
        # Check microbial limits
        for test, count in viable_counts.items():
            if test in room_config["microbial_limits"]:
                limit = room_config["microbial_limits"][test]["max"]
                if count > limit:
                    violations.append({
                        "parameter": f"microbial_{test}",
                        "measured": count,
                        "limit": limit,
                        "violation_type": "microbial_limit_exceeded"
                    })
                    compliant = False
        
        return {
            "compliant": compliant,
            "violations": violations,
            "iso_classification": iso_class,
            "validation_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _determine_corrective_actions(self, clean_room_id: str, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Determine corrective actions based on violations"""
        corrective_actions = []
        
        for violation in violations:
            if violation["violation_type"] == "particle_count_exceeded":
                corrective_actions.append({
                    "action": "increase_cleaning_frequency",
                    "description": "Increase cleaning frequency and check HVAC system",
                    "priority": "high",
                    "responsible": "facilities_maintenance",
                    "timeline": "immediate"
                })
            elif violation["violation_type"] == "microbial_limit_exceeded":
                corrective_actions.append({
                    "action": "enhanced_disinfection",
                    "description": "Perform enhanced disinfection and investigate contamination source",
                    "priority": "critical",
                    "responsible": "quality_assurance",
                    "timeline": "immediate"
                })
            elif violation["violation_type"] in ["below_minimum", "above_maximum"]:
                corrective_actions.append({
                    "action": "adjust_environmental_controls",
                    "description": f"Adjust environmental controls for {violation['parameter']}",
                    "priority": "medium",
                    "responsible": "facilities_maintenance",
                    "timeline": "within_4_hours"
                })
        
        return corrective_actions
    
    async def _simulate_monitoring_data(self, clean_room_id: str) -> Dict[str, Any]:
        """Simulate monitoring data for demonstration"""
        import random
        
        room_config = self.clean_room_configurations[clean_room_id]
        iso_class = room_config["iso_classification"]
        
        # Generate particle counts based on ISO classification
        if iso_class == "ISO 5":
            particle_counts = {
                "0.5um": random.randint(2000, 3500),
                "5.0um": random.randint(10, 25)
            }
        elif iso_class == "ISO 7":
            particle_counts = {
                "0.5um": random.randint(200000, 350000),
                "5.0um": random.randint(1000, 2500)
            }
        else:  # ISO 8
            particle_counts = {
                "0.5um": random.randint(2000000, 3500000),
                "5.0um": random.randint(15000, 25000)
            }
        
        # Generate viable counts
        if iso_class == "ISO 5":
            viable_counts = {
                "settle_plates": random.randint(0, 1),
                "air_samples": random.randint(0, 1),
                "contact_plates": random.randint(0, 1)
            }
        elif iso_class == "ISO 7":
            viable_counts = {
                "settle_plates": random.randint(5, 45),
                "air_samples": random.randint(1, 8),
                "contact_plates": random.randint(3, 20)
            }
        else:  # ISO 8
            viable_counts = {
                "settle_plates": random.randint(50, 180),
                "air_samples": random.randint(10, 80),
                "contact_plates": random.randint(10, 45)
            }
        
        # Generate environmental conditions
        environmental_conditions = {
            "temperature": random.uniform(20, 24),
            "humidity": random.uniform(45, 60),
            "pressure_differential": random.uniform(5, 15)
        }
        
        return {
            "particle_counts": particle_counts,
            "viable_counts": viable_counts,
            "environmental_conditions": environmental_conditions,
            "personnel_count": random.randint(1, room_config["personnel_capacity"]),
            "activity_level": random.choice(["low", "normal", "high"]),
            "hvac_status": {
                "air_changes_per_hour": room_config["air_changes_per_hour"],
                "hepa_filter_status": "operational",
                "pressure_status": "normal"
            }
        }
    
    async def _trigger_contamination_alert(self, monitoring_record: CleanRoomMonitoring, validation_result: Dict[str, Any]):
        """Trigger contamination alert"""
        alert_message = f"Clean room contamination alert: {monitoring_record.clean_room_id} - "
        alert_message += f"ISO {monitoring_record.room_classification} limits exceeded"
        
        logger.warning(alert_message)
        
        # In a real system, this would send notifications, emails, SMS, etc.
        # For now, we'll just log the alert
    
    def _get_last_cleaning_date(self, monitoring_data: List[Dict[str, Any]]) -> Optional[str]:
        """Get last cleaning date from monitoring data"""
        for record in monitoring_data:
            if record.get("cleaning_performed"):
                return record.get("monitoring_date")
        return None
    
    def _get_last_disinfection_date(self, monitoring_data: List[Dict[str, Any]]) -> Optional[str]:
        """Get last disinfection date from monitoring data"""
        for record in monitoring_data:
            if record.get("disinfection_performed"):
                return record.get("monitoring_date")
        return None
    
    async def _determine_investigation_scope(self, clean_room_id: str, contamination_type: str, investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine investigation scope"""
        return {
            "scope_type": "comprehensive",
            "areas_to_investigate": [clean_room_id, "adjacent_areas", "personnel_practices"],
            "investigation_duration": "7_days",
            "required_samples": 20,
            "testing_required": ["environmental_monitoring", "personnel_monitoring", "equipment_swabs"]
        }
    
    async def _perform_root_cause_analysis(self, contamination_type: str, investigation_data: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
        """Perform root cause analysis"""
        return {
            "analysis_method": "fishbone_analysis",
            "potential_causes": [
                "inadequate_cleaning_procedures",
                "personnel_gowning_issues",
                "hvac_system_malfunction",
                "raw_material_contamination"
            ],
            "most_likely_cause": "inadequate_cleaning_procedures",
            "evidence": ["cleaning_logs_gaps", "increased_particle_counts"],
            "confidence_level": "high"
        }
    
    async def _develop_capa_plan(self, clean_room_id: str, contamination_type: str, root_cause: Dict[str, Any]) -> Dict[str, Any]:
        """Develop corrective and preventive action plan"""
        return {
            "corrective_actions": [
                {
                    "action": "immediate_deep_cleaning",
                    "responsible": "facilities_team",
                    "timeline": "24_hours",
                    "verification": "environmental_monitoring"
                }
            ],
            "preventive_actions": [
                {
                    "action": "revise_cleaning_procedures",
                    "responsible": "quality_assurance",
                    "timeline": "30_days",
                    "verification": "procedure_review"
                }
            ],
            "monitoring_plan": {
                "increased_frequency": "daily_for_2_weeks",
                "additional_parameters": ["surface_sampling", "air_sampling"],
                "effectiveness_review": "monthly"
            }
        }
    
    async def _generate_contamination_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate contamination control recommendations"""
        recommendations = []
        
        overall_compliance = report["summary"]["overall_compliance_rate"]
        
        if overall_compliance < 95:
            recommendations.append("Review and enhance contamination control procedures")
        
        if report["summary"]["total_violations"] > 0:
            recommendations.append("Investigate root causes of contamination events")
        
        recommendations.extend([
            "Maintain regular cleaning and disinfection schedules",
            "Ensure proper personnel training on contamination control",
            "Review HVAC system performance regularly",
            "Implement risk-based monitoring approach"
        ])
        
        return recommendations
    
    # Database operations (these would integrate with actual database)
    async def _store_monitoring_record(self, record: CleanRoomMonitoring):
        """Store monitoring record in database"""
        logger.debug(f"Storing clean room monitoring record {record.id}")
    
    async def _store_investigation_record(self, record: Dict[str, Any]):
        """Store investigation record in database"""
        logger.debug(f"Storing investigation record {record['investigation_id']}")
    
    async def _get_recent_monitoring_data(self, clean_room_id: str, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get recent monitoring data"""
        return []
    
    async def _get_monitoring_data_for_period(self, clean_room_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get monitoring data for period"""
        return []
    
    async def _get_contamination_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get contamination events"""
        return []
    
    async def _analyze_contamination_events(self, room_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contamination events"""
        return {"events": 0, "severity": "low"}
    
    async def _analyze_cleaning_frequency(self, room_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cleaning frequency"""
        return {"frequency": "daily", "compliance": 100}
    
    async def _analyze_trending_data(self, room_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trending data"""
        return {"trend": "stable", "improvement": "none_required"}
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"