"""
CAPA and Deviation Management Service
Corrective and Preventive Actions (CAPA) and deviation tracking per FDA requirements
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from src.models.fda_compliance import (
    CAPARecord, Deviation, AuditAction
)
from src.services.immutable_audit_service import ImmutableAuditService
from src.services.electronic_signature_service import ElectronicSignatureService

logger = logging.getLogger(__name__)

class CAPADeviationService:
    """
    Service for managing CAPA and deviation tracking
    Implements FDA requirements for corrective and preventive actions
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.signature_service = ElectronicSignatureService()
        
    async def create_deviation(
        self,
        title: str,
        description: str,
        severity: str,
        category: str,
        batch_id: Optional[UUID],
        product_id: Optional[UUID],
        equipment_id: Optional[UUID],
        discovered_by: UUID,
        discovered_at: datetime,
        reported_by: UUID,
        ip_address: str = "unknown"
    ) -> Deviation:
        """
        Create new deviation record
        """
        try:
            # Generate unique deviation number
            deviation_number = await self._generate_deviation_number()
            
            # Create deviation record
            deviation = Deviation(
                id=uuid4(),
                deviation_number=deviation_number,
                title=title,
                description=description,
                severity=severity,
                category=category,
                batch_id=batch_id,
                product_id=product_id,
                equipment_id=equipment_id,
                discovered_by=discovered_by,
                discovered_at=discovered_at,
                reported_by=reported_by,
                reported_at=datetime.now(timezone.utc),
                investigation_required=True,
                status="open",
                capa_required=severity in ["major", "critical"]
            )
            
            # Set due date based on severity
            deviation.due_date = self._calculate_deviation_due_date(severity)
            
            # Store deviation
            await self._store_deviation(deviation)
            
            # Auto-assign investigator based on category
            investigator_id = await self._assign_investigator(category, severity)
            if investigator_id:
                deviation.investigator_id = investigator_id
                deviation.assigned_to = investigator_id
                await self._update_deviation(deviation)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=reported_by,
                username=await self._get_username(reported_by),
                full_name=await self._get_full_name(reported_by),
                action=AuditAction.CREATE,
                action_description=f"Created deviation: {title}",
                entity_type="deviation",
                entity_id=deviation.id,
                entity_identifier=deviation_number,
                new_values={
                    "deviation_number": deviation_number,
                    "title": title,
                    "severity": severity,
                    "category": category,
                    "discovered_by": str(discovered_by),
                    "discovered_at": discovered_at.isoformat(),
                    "batch_id": str(batch_id) if batch_id else None,
                    "product_id": str(product_id) if product_id else None,
                    "equipment_id": str(equipment_id) if equipment_id else None
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=severity in ["major", "critical"]
            )
            
            # Send notifications
            await self._send_deviation_notifications(deviation)
            
            logger.info(f"Deviation created: {deviation_number}")
            return deviation
            
        except Exception as e:
            logger.error(f"Failed to create deviation: {str(e)}")
            raise
    
    async def investigate_deviation(
        self,
        deviation_id: UUID,
        investigation_summary: str,
        root_cause: str,
        quality_impact: str,
        regulatory_impact: str,
        customer_impact: str,
        immediate_action: str,
        investigator_id: UUID,
        ip_address: str = "unknown"
    ) -> Deviation:
        """
        Complete deviation investigation
        """
        try:
            # Get deviation
            deviation = await self._get_deviation(deviation_id)
            if not deviation:
                raise ValueError("Deviation not found")
            
            # Check if user can investigate
            if not await self._can_investigate_deviation(investigator_id, deviation):
                raise ValueError("Insufficient privileges to investigate deviation")
            
            # Update deviation with investigation results
            old_values = {
                "status": deviation.status,
                "investigation_summary": deviation.investigation_summary,
                "root_cause": deviation.root_cause
            }
            
            deviation.investigation_summary = investigation_summary
            deviation.root_cause = root_cause
            deviation.quality_impact = quality_impact
            deviation.regulatory_impact = regulatory_impact
            deviation.customer_impact = customer_impact
            deviation.immediate_action = immediate_action
            deviation.investigator_id = investigator_id
            deviation.status = "investigated"
            
            # Store updated deviation
            await self._update_deviation(deviation)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=investigator_id,
                username=await self._get_username(investigator_id),
                full_name=await self._get_full_name(investigator_id),
                action=AuditAction.UPDATE,
                action_description=f"Completed deviation investigation: {deviation.deviation_number}",
                entity_type="deviation",
                entity_id=deviation_id,
                entity_identifier=deviation.deviation_number,
                old_values=old_values,
                new_values={
                    "status": "investigated",
                    "investigation_summary": investigation_summary,
                    "root_cause": root_cause,
                    "quality_impact": quality_impact,
                    "regulatory_impact": regulatory_impact,
                    "customer_impact": customer_impact,
                    "immediate_action": immediate_action
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            # Auto-create CAPA if required
            if deviation.capa_required:
                await self._auto_create_capa_from_deviation(deviation, investigator_id, ip_address)
            
            logger.info(f"Deviation investigated: {deviation.deviation_number}")
            return deviation
            
        except Exception as e:
            logger.error(f"Failed to investigate deviation {deviation_id}: {str(e)}")
            raise
    
    async def close_deviation(
        self,
        deviation_id: UUID,
        closure_summary: str,
        corrective_action: str,
        preventive_action: str,
        closed_by: UUID,
        ip_address: str = "unknown"
    ) -> Deviation:
        """
        Close deviation with corrective and preventive actions
        """
        try:
            # Get deviation
            deviation = await self._get_deviation(deviation_id)
            if not deviation:
                raise ValueError("Deviation not found")
            
            # Check if user can close deviation
            if not await self._can_close_deviation(closed_by, deviation):
                raise ValueError("Insufficient privileges to close deviation")
            
            # Check if investigation is complete
            if deviation.status != "investigated":
                raise ValueError("Deviation must be investigated before closure")
            
            # Update deviation
            deviation.corrective_action = corrective_action
            deviation.preventive_action = preventive_action
            deviation.closure_summary = closure_summary
            deviation.closed_by = closed_by
            deviation.closed_at = datetime.now(timezone.utc)
            deviation.status = "closed"
            
            # Store updated deviation
            await self._update_deviation(deviation)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=closed_by,
                username=await self._get_username(closed_by),
                full_name=await self._get_full_name(closed_by),
                action=AuditAction.UPDATE,
                action_description=f"Closed deviation: {deviation.deviation_number}",
                entity_type="deviation",
                entity_id=deviation_id,
                entity_identifier=deviation.deviation_number,
                old_values={"status": "investigated"},
                new_values={
                    "status": "closed",
                    "corrective_action": corrective_action,
                    "preventive_action": preventive_action,
                    "closure_summary": closure_summary,
                    "closed_by": str(closed_by),
                    "closed_at": deviation.closed_at.isoformat()
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Deviation closed: {deviation.deviation_number}")
            return deviation
            
        except Exception as e:
            logger.error(f"Failed to close deviation {deviation_id}: {str(e)}")
            raise
    
    async def create_capa(
        self,
        problem_description: str,
        problem_category: str,
        severity: str,
        source_type: str,
        source_id: Optional[UUID],
        source_reference: Optional[str],
        corrective_actions: List[Dict[str, Any]],
        preventive_actions: List[Dict[str, Any]],
        corrective_action_owner: UUID,
        preventive_action_owner: UUID,
        target_completion_date: datetime,
        created_by: UUID,
        ip_address: str = "unknown"
    ) -> CAPARecord:
        """
        Create new CAPA record
        """
        try:
            # Generate unique CAPA number
            capa_number = await self._generate_capa_number()
            
            # Create CAPA record
            capa = CAPARecord(
                id=uuid4(),
                capa_number=capa_number,
                problem_description=problem_description,
                problem_category=problem_category,
                severity=severity,
                source_type=source_type,
                source_id=source_id,
                source_reference=source_reference,
                corrective_actions=corrective_actions,
                preventive_actions=preventive_actions,
                corrective_action_owner=corrective_action_owner,
                preventive_action_owner=preventive_action_owner,
                target_completion_date=target_completion_date,
                status="open",
                assigned_to=corrective_action_owner,
                initiated_date=datetime.now(timezone.utc)
            )
            
            # Calculate due dates
            capa.corrective_action_due_date = self._calculate_corrective_action_due_date(severity)
            capa.preventive_action_due_date = self._calculate_preventive_action_due_date(severity)
            capa.effectiveness_check_due = target_completion_date + timedelta(days=30)
            
            # Store CAPA
            await self._store_capa(capa)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=created_by,
                username=await self._get_username(created_by),
                full_name=await self._get_full_name(created_by),
                action=AuditAction.CREATE,
                action_description=f"Created CAPA: {problem_description[:50]}...",
                entity_type="capa_record",
                entity_id=capa.id,
                entity_identifier=capa_number,
                new_values={
                    "capa_number": capa_number,
                    "problem_description": problem_description,
                    "problem_category": problem_category,
                    "severity": severity,
                    "source_type": source_type,
                    "corrective_action_owner": str(corrective_action_owner),
                    "preventive_action_owner": str(preventive_action_owner),
                    "target_completion_date": target_completion_date.isoformat()
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=severity in ["high", "critical"]
            )
            
            # Send notifications to action owners
            await self._send_capa_notifications(capa)
            
            logger.info(f"CAPA created: {capa_number}")
            return capa
            
        except Exception as e:
            logger.error(f"Failed to create CAPA: {str(e)}")
            raise
    
    async def update_capa_progress(
        self,
        capa_id: UUID,
        corrective_action_completed: Optional[bool],
        preventive_action_completed: Optional[bool],
        progress_notes: str,
        updated_by: UUID,
        ip_address: str = "unknown"
    ) -> CAPARecord:
        """
        Update CAPA progress
        """
        try:
            # Get CAPA
            capa = await self._get_capa(capa_id)
            if not capa:
                raise ValueError("CAPA not found")
            
            # Check if user can update CAPA
            if not await self._can_update_capa(updated_by, capa):
                raise ValueError("Insufficient privileges to update CAPA")
            
            # Store old values
            old_values = {
                "corrective_action_completed": capa.corrective_action_completed,
                "preventive_action_completed": capa.preventive_action_completed,
                "status": capa.status
            }
            
            # Update CAPA
            if corrective_action_completed is not None:
                capa.corrective_action_completed = corrective_action_completed
            
            if preventive_action_completed is not None:
                capa.preventive_action_completed = preventive_action_completed
            
            # Update status based on completion
            if capa.corrective_action_completed and capa.preventive_action_completed:
                capa.status = "completed"
                capa.actual_completion_date = datetime.now(timezone.utc)
            elif capa.corrective_action_completed or capa.preventive_action_completed:
                capa.status = "in_progress"
            
            # Store updated CAPA
            await self._update_capa(capa)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=updated_by,
                username=await self._get_username(updated_by),
                full_name=await self._get_full_name(updated_by),
                action=AuditAction.UPDATE,
                action_description=f"Updated CAPA progress: {capa.capa_number}",
                entity_type="capa_record",
                entity_id=capa_id,
                entity_identifier=capa.capa_number,
                old_values=old_values,
                new_values={
                    "corrective_action_completed": capa.corrective_action_completed,
                    "preventive_action_completed": capa.preventive_action_completed,
                    "status": capa.status,
                    "progress_notes": progress_notes
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"CAPA progress updated: {capa.capa_number}")
            return capa
            
        except Exception as e:
            logger.error(f"Failed to update CAPA progress {capa_id}: {str(e)}")
            raise
    
    async def verify_capa_effectiveness(
        self,
        capa_id: UUID,
        effectiveness_verified: bool,
        verification_notes: str,
        verified_by: UUID,
        ip_address: str = "unknown"
    ) -> CAPARecord:
        """
        Verify CAPA effectiveness
        """
        try:
            # Get CAPA
            capa = await self._get_capa(capa_id)
            if not capa:
                raise ValueError("CAPA not found")
            
            # Check if CAPA is completed
            if capa.status != "completed":
                raise ValueError("CAPA must be completed before effectiveness verification")
            
            # Check if user can verify effectiveness
            if not await self._can_verify_capa_effectiveness(verified_by, capa):
                raise ValueError("Insufficient privileges to verify CAPA effectiveness")
            
            # Update CAPA
            capa.effectiveness_verified = effectiveness_verified
            capa.effectiveness_verification_notes = verification_notes
            
            if effectiveness_verified:
                capa.status = "closed"
            else:
                # If effectiveness is not verified, may need additional actions
                capa.status = "effectiveness_review"
            
            # Store updated CAPA
            await self._update_capa(capa)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=verified_by,
                username=await self._get_username(verified_by),
                full_name=await self._get_full_name(verified_by),
                action=AuditAction.UPDATE,
                action_description=f"Verified CAPA effectiveness: {capa.capa_number}",
                entity_type="capa_record",
                entity_id=capa_id,
                entity_identifier=capa.capa_number,
                old_values={"effectiveness_verified": False},
                new_values={
                    "effectiveness_verified": effectiveness_verified,
                    "effectiveness_verification_notes": verification_notes,
                    "status": capa.status
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"CAPA effectiveness verified: {capa.capa_number}")
            return capa
            
        except Exception as e:
            logger.error(f"Failed to verify CAPA effectiveness {capa_id}: {str(e)}")
            raise
    
    async def get_deviation_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get deviation analytics and trends
        """
        try:
            # Get deviations in date range
            deviations = await self._get_deviations_by_date_range(start_date, end_date)
            
            # Calculate analytics
            total_deviations = len(deviations)
            
            # By severity
            severity_breakdown = {}
            for deviation in deviations:
                severity = deviation.severity
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
            
            # By category
            category_breakdown = {}
            for deviation in deviations:
                category = deviation.category
                category_breakdown[category] = category_breakdown.get(category, 0) + 1
            
            # By status
            status_breakdown = {}
            for deviation in deviations:
                status = deviation.status
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            # Calculate average resolution time
            closed_deviations = [d for d in deviations if d.status == "closed" and d.closed_at]
            avg_resolution_time = 0
            if closed_deviations:
                total_resolution_time = sum(
                    (d.closed_at - d.reported_at).total_seconds() / 86400  # days
                    for d in closed_deviations
                )
                avg_resolution_time = total_resolution_time / len(closed_deviations)
            
            # Overdue deviations
            overdue_deviations = [
                d for d in deviations 
                if d.status not in ["closed"] and d.due_date and d.due_date < datetime.now(timezone.utc)
            ]
            
            analytics = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_deviations": total_deviations,
                    "open_deviations": len([d for d in deviations if d.status == "open"]),
                    "closed_deviations": len([d for d in deviations if d.status == "closed"]),
                    "overdue_deviations": len(overdue_deviations),
                    "avg_resolution_time_days": round(avg_resolution_time, 2)
                },
                "breakdowns": {
                    "by_severity": severity_breakdown,
                    "by_category": category_breakdown,
                    "by_status": status_breakdown
                },
                "trends": {
                    "monthly_trend": await self._calculate_monthly_deviation_trend(start_date, end_date),
                    "severity_trend": await self._calculate_severity_trend(start_date, end_date)
                },
                "overdue_items": [
                    {
                        "deviation_number": d.deviation_number,
                        "title": d.title,
                        "severity": d.severity,
                        "due_date": d.due_date.isoformat(),
                        "days_overdue": (datetime.now(timezone.utc) - d.due_date).days
                    }
                    for d in overdue_deviations
                ]
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get deviation analytics: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_deviation_due_date(self, severity: str) -> datetime:
        """Calculate deviation due date based on severity"""
        days_map = {
            "critical": 3,
            "major": 7,
            "minor": 14,
            "low": 30
        }
        days = days_map.get(severity.lower(), 14)
        return datetime.now(timezone.utc) + timedelta(days=days)
    
    def _calculate_corrective_action_due_date(self, severity: str) -> datetime:
        """Calculate corrective action due date"""
        days_map = {
            "critical": 7,
            "high": 14,
            "medium": 30,
            "low": 60
        }
        days = days_map.get(severity.lower(), 30)
        return datetime.now(timezone.utc) + timedelta(days=days)
    
    def _calculate_preventive_action_due_date(self, severity: str) -> datetime:
        """Calculate preventive action due date"""
        days_map = {
            "critical": 14,
            "high": 30,
            "medium": 60,
            "low": 90
        }
        days = days_map.get(severity.lower(), 60)
        return datetime.now(timezone.utc) + timedelta(days=days)
    
    async def _auto_create_capa_from_deviation(
        self,
        deviation: Deviation,
        created_by: UUID,
        ip_address: str
    ):
        """Auto-create CAPA from deviation"""
        try:
            capa = await self.create_capa(
                problem_description=f"Deviation: {deviation.title}",
                problem_category=deviation.category,
                severity=deviation.severity,
                source_type="deviation",
                source_id=deviation.id,
                source_reference=deviation.deviation_number,
                corrective_actions=[{
                    "description": deviation.corrective_action or "To be determined",
                    "owner": str(created_by),
                    "due_date": self._calculate_corrective_action_due_date(deviation.severity).isoformat()
                }],
                preventive_actions=[{
                    "description": deviation.preventive_action or "To be determined",
                    "owner": str(created_by),
                    "due_date": self._calculate_preventive_action_due_date(deviation.severity).isoformat()
                }],
                corrective_action_owner=created_by,
                preventive_action_owner=created_by,
                target_completion_date=self._calculate_preventive_action_due_date(deviation.severity),
                created_by=created_by,
                ip_address=ip_address
            )
            
            # Link CAPA to deviation
            deviation.capa_id = capa.id
            await self._update_deviation(deviation)
            
            logger.info(f"Auto-created CAPA {capa.capa_number} from deviation {deviation.deviation_number}")
            
        except Exception as e:
            logger.error(f"Failed to auto-create CAPA from deviation: {str(e)}")
    
    # Database operations (these would integrate with actual database)
    async def _generate_deviation_number(self) -> str:
        """Generate unique deviation number"""
        return f"DEV-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
    
    async def _generate_capa_number(self) -> str:
        """Generate unique CAPA number"""
        return f"CAPA-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
    
    async def _store_deviation(self, deviation: Deviation):
        """Store deviation in database"""
        logger.debug(f"Storing deviation {deviation.deviation_number}")
    
    async def _get_deviation(self, deviation_id: UUID) -> Optional[Deviation]:
        """Get deviation from database"""
        return None
    
    async def _update_deviation(self, deviation: Deviation):
        """Update deviation in database"""
        logger.debug(f"Updating deviation {deviation.id}")
    
    async def _store_capa(self, capa: CAPARecord):
        """Store CAPA in database"""
        logger.debug(f"Storing CAPA {capa.capa_number}")
    
    async def _get_capa(self, capa_id: UUID) -> Optional[CAPARecord]:
        """Get CAPA from database"""
        return None
    
    async def _update_capa(self, capa: CAPARecord):
        """Update CAPA in database"""
        logger.debug(f"Updating CAPA {capa.id}")
    
    async def _get_deviations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Deviation]:
        """Get deviations by date range"""
        return []
    
    async def _assign_investigator(self, category: str, severity: str) -> Optional[UUID]:
        """Auto-assign investigator based on category and severity"""
        return None
    
    async def _send_deviation_notifications(self, deviation: Deviation):
        """Send deviation notifications"""
        logger.debug(f"Sending notifications for deviation {deviation.deviation_number}")
    
    async def _send_capa_notifications(self, capa: CAPARecord):
        """Send CAPA notifications"""
        logger.debug(f"Sending notifications for CAPA {capa.capa_number}")
    
    async def _calculate_monthly_deviation_trend(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Calculate monthly deviation trend"""
        return []
    
    async def _calculate_severity_trend(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Calculate severity trend"""
        return []
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"
    
    async def _can_investigate_deviation(self, user_id: UUID, deviation: Deviation) -> bool:
        """Check if user can investigate deviation"""
        return True
    
    async def _can_close_deviation(self, user_id: UUID, deviation: Deviation) -> bool:
        """Check if user can close deviation"""
        return True
    
    async def _can_update_capa(self, user_id: UUID, capa: CAPARecord) -> bool:
        """Check if user can update CAPA"""
        return True
    
    async def _can_verify_capa_effectiveness(self, user_id: UUID, capa: CAPARecord) -> bool:
        """Check if user can verify CAPA effectiveness"""
        return True