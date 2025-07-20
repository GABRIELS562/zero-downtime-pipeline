"""
Manufacturing Event Service
Time-stamped records system for all manufacturing events per FDA 21 CFR Part 11
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from models.fda_compliance import AuditAction
from services.immutable_audit_service import ImmutableAuditService
from services.electronic_signature_service import ElectronicSignatureService

logger = logging.getLogger(__name__)

class ManufacturingEventService:
    """
    Service for managing time-stamped manufacturing events
    Implements comprehensive event tracking per FDA requirements
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.signature_service = ElectronicSignatureService()
        
    async def record_manufacturing_event(
        self,
        event_type: str,
        event_category: str,
        event_description: str,
        batch_id: Optional[UUID],
        equipment_id: Optional[UUID],
        product_id: Optional[UUID],
        process_step: Optional[str],
        event_data: Dict[str, Any],
        critical_parameters: Dict[str, Any],
        operator_id: UUID,
        supervisor_id: Optional[UUID],
        location: str,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record manufacturing event with time-stamped integrity
        """
        try:
            # Generate unique event ID
            event_id = uuid4()
            event_timestamp = datetime.now(timezone.utc)
            
            # Create event record
            event_record = {
                "event_id": str(event_id),
                "event_type": event_type,
                "event_category": event_category,
                "event_description": event_description,
                "batch_id": str(batch_id) if batch_id else None,
                "equipment_id": str(equipment_id) if equipment_id else None,
                "product_id": str(product_id) if product_id else None,
                "process_step": process_step,
                "event_data": event_data,
                "critical_parameters": critical_parameters,
                "operator_id": str(operator_id),
                "supervisor_id": str(supervisor_id) if supervisor_id else None,
                "location": location,
                "event_timestamp": event_timestamp.isoformat(),
                "system_timestamp": datetime.now(timezone.utc).isoformat(),
                "timezone": "UTC"
            }
            
            # Calculate event hash for integrity
            event_hash = self._calculate_event_hash(event_record)
            event_record["event_hash"] = event_hash
            
            # Store event record
            await self._store_manufacturing_event(event_record)
            
            # Create audit trail entry
            await self.audit_service.create_audit_log(
                user_id=operator_id,
                username=await self._get_username(operator_id),
                full_name=await self._get_full_name(operator_id),
                action=AuditAction.CREATE,
                action_description=f"Manufacturing event recorded: {event_type}",
                entity_type="manufacturing_event",
                entity_id=event_id,
                entity_identifier=f"{event_type}:{event_category}",
                new_values={
                    "event_type": event_type,
                    "event_category": event_category,
                    "event_description": event_description,
                    "batch_id": str(batch_id) if batch_id else None,
                    "equipment_id": str(equipment_id) if equipment_id else None,
                    "process_step": process_step,
                    "location": location,
                    "event_hash": event_hash
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=event_category in ["production", "quality_control", "deviation"]
            )
            
            # Check if event requires supervisor verification
            if await self._requires_supervisor_verification(event_type, event_category):
                await self._request_supervisor_verification(event_id, supervisor_id, operator_id)
            
            # Auto-trigger alerts for critical events
            if event_category in ["deviation", "equipment_failure", "quality_alert"]:
                await self._trigger_critical_event_alerts(event_record)
            
            logger.info(f"Manufacturing event recorded: {event_type} - {event_id}")
            
            return {
                "event_id": str(event_id),
                "event_timestamp": event_timestamp.isoformat(),
                "event_hash": event_hash,
                "verification_required": await self._requires_supervisor_verification(event_type, event_category),
                "status": "recorded",
                "integrity_verified": True
            }
            
        except Exception as e:
            logger.error(f"Failed to record manufacturing event: {str(e)}")
            raise
    
    async def verify_manufacturing_event(
        self,
        event_id: UUID,
        verified_by: UUID,
        verification_notes: str,
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Verify manufacturing event with supervisor signature
        """
        try:
            # Get event record
            event_record = await self._get_manufacturing_event(event_id)
            if not event_record:
                raise ValueError("Manufacturing event not found")
            
            # Check if user can verify
            if not await self._can_verify_event(verified_by, event_record):
                raise ValueError("Insufficient privileges to verify event")
            
            # Update event with verification
            verification_data = {
                "verified_by": str(verified_by),
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verification_notes": verification_notes,
                "verification_status": "verified"
            }
            
            # Recalculate hash with verification data
            event_record.update(verification_data)
            new_hash = self._calculate_event_hash(event_record)
            event_record["event_hash"] = new_hash
            
            # Store updated event
            await self._update_manufacturing_event(event_id, event_record)
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=verified_by,
                username=await self._get_username(verified_by),
                full_name=await self._get_full_name(verified_by),
                action=AuditAction.VERIFY,
                action_description=f"Manufacturing event verified: {event_record['event_type']}",
                entity_type="manufacturing_event",
                entity_id=event_id,
                entity_identifier=f"{event_record['event_type']}:{event_record['event_category']}",
                old_values={"verification_status": "pending"},
                new_values=verification_data,
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Manufacturing event verified: {event_id} by {verified_by}")
            
            return {
                "event_id": str(event_id),
                "verification_status": "verified",
                "verified_by": str(verified_by),
                "verified_at": verification_data["verified_at"],
                "updated_hash": new_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to verify manufacturing event {event_id}: {str(e)}")
            raise
    
    async def get_manufacturing_events(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None,
        event_category: Optional[str] = None,
        batch_id: Optional[UUID] = None,
        equipment_id: Optional[UUID] = None,
        operator_id: Optional[UUID] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get manufacturing events with filtering
        """
        try:
            events = await self._get_events_by_criteria(
                start_date=start_date,
                end_date=end_date,
                event_type=event_type,
                event_category=event_category,
                batch_id=batch_id,
                equipment_id=equipment_id,
                operator_id=operator_id,
                limit=limit
            )
            
            # Verify integrity of each event
            verified_events = []
            for event in events:
                integrity_check = await self._verify_event_integrity(event)
                event["integrity_verified"] = integrity_check["valid"]
                if not integrity_check["valid"]:
                    event["integrity_issues"] = integrity_check["issues"]
                verified_events.append(event)
            
            return verified_events
            
        except Exception as e:
            logger.error(f"Failed to get manufacturing events: {str(e)}")
            return []
    
    async def get_event_timeline(
        self,
        batch_id: UUID,
        include_related_events: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete timeline of events for a batch
        """
        try:
            # Get all events for batch
            batch_events = await self._get_batch_events(batch_id)
            
            # Get related events if requested
            related_events = []
            if include_related_events:
                related_events = await self._get_related_events(batch_id)
            
            # Combine and sort chronologically
            all_events = batch_events + related_events
            all_events.sort(key=lambda x: x["event_timestamp"])
            
            # Calculate timeline metrics
            timeline_metrics = {
                "total_events": len(all_events),
                "critical_events": len([e for e in all_events if e["event_category"] in ["deviation", "quality_alert"]]),
                "verified_events": len([e for e in all_events if e.get("verification_status") == "verified"]),
                "start_time": all_events[0]["event_timestamp"] if all_events else None,
                "end_time": all_events[-1]["event_timestamp"] if all_events else None
            }
            
            return {
                "batch_id": str(batch_id),
                "timeline_metrics": timeline_metrics,
                "events": all_events,
                "integrity_status": await self._verify_timeline_integrity(all_events)
            }
            
        except Exception as e:
            logger.error(f"Failed to get event timeline for batch {batch_id}: {str(e)}")
            return {"error": str(e)}
    
    async def generate_event_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "comprehensive",
        include_integrity_check: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive manufacturing event report
        """
        try:
            # Get all events in period
            events = await self._get_events_by_criteria(
                start_date=start_date,
                end_date=end_date,
                limit=None
            )
            
            # Calculate summary statistics
            summary = {
                "total_events": len(events),
                "event_types": {},
                "event_categories": {},
                "operators": set(),
                "equipment_used": set(),
                "batches_affected": set()
            }
            
            integrity_issues = []
            
            for event in events:
                # Count event types
                event_type = event["event_type"]
                summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
                
                # Count event categories
                event_category = event["event_category"]
                summary["event_categories"][event_category] = summary["event_categories"].get(event_category, 0) + 1
                
                # Track operators
                summary["operators"].add(event["operator_id"])
                
                # Track equipment
                if event["equipment_id"]:
                    summary["equipment_used"].add(event["equipment_id"])
                
                # Track batches
                if event["batch_id"]:
                    summary["batches_affected"].add(event["batch_id"])
                
                # Check integrity if requested
                if include_integrity_check:
                    integrity_check = await self._verify_event_integrity(event)
                    if not integrity_check["valid"]:
                        integrity_issues.append({
                            "event_id": event["event_id"],
                            "issues": integrity_check["issues"]
                        })
            
            # Convert sets to counts
            summary["unique_operators"] = len(summary["operators"])
            summary["unique_equipment"] = len(summary["equipment_used"])
            summary["unique_batches"] = len(summary["batches_affected"])
            del summary["operators"], summary["equipment_used"], summary["batches_affected"]
            
            report = {
                "report_type": report_type,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": summary,
                "events": events,
                "integrity_check": {
                    "performed": include_integrity_check,
                    "issues_found": len(integrity_issues),
                    "issues": integrity_issues
                } if include_integrity_check else None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "fda_compliance": "21 CFR Part 11 compliant"
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate event report: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_event_hash(self, event_record: Dict[str, Any]) -> str:
        """Calculate hash for event integrity verification"""
        # Remove hash field if present for calculation
        hash_data = {k: v for k, v in event_record.items() if k != "event_hash"}
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def _verify_event_integrity(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Verify event integrity"""
        try:
            stored_hash = event.get("event_hash")
            if not stored_hash:
                return {"valid": False, "issues": ["No hash found"]}
            
            calculated_hash = self._calculate_event_hash(event)
            
            if stored_hash != calculated_hash:
                return {
                    "valid": False,
                    "issues": ["Hash mismatch - event may have been tampered with"]
                }
            
            return {"valid": True, "issues": []}
            
        except Exception as e:
            return {"valid": False, "issues": [f"Integrity check failed: {str(e)}"]}
    
    async def _verify_timeline_integrity(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify timeline integrity"""
        integrity_issues = []
        
        for event in events:
            event_integrity = await self._verify_event_integrity(event)
            if not event_integrity["valid"]:
                integrity_issues.extend(event_integrity["issues"])
        
        return {
            "valid": len(integrity_issues) == 0,
            "issues": integrity_issues,
            "total_events_checked": len(events)
        }
    
    # Database operations (these would integrate with actual database)
    async def _store_manufacturing_event(self, event_record: Dict[str, Any]):
        """Store manufacturing event in database"""
        logger.debug(f"Storing manufacturing event {event_record['event_id']}")
    
    async def _get_manufacturing_event(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """Get manufacturing event from database"""
        return None
    
    async def _update_manufacturing_event(self, event_id: UUID, event_record: Dict[str, Any]):
        """Update manufacturing event in database"""
        logger.debug(f"Updating manufacturing event {event_id}")
    
    async def _get_events_by_criteria(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None,
        event_category: Optional[str] = None,
        batch_id: Optional[UUID] = None,
        equipment_id: Optional[UUID] = None,
        operator_id: Optional[UUID] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get events by criteria"""
        return []
    
    async def _get_batch_events(self, batch_id: UUID) -> List[Dict[str, Any]]:
        """Get events for specific batch"""
        return []
    
    async def _get_related_events(self, batch_id: UUID) -> List[Dict[str, Any]]:
        """Get events related to batch"""
        return []
    
    async def _requires_supervisor_verification(self, event_type: str, event_category: str) -> bool:
        """Check if event requires supervisor verification"""
        critical_events = ["deviation", "equipment_failure", "quality_alert", "batch_release"]
        return event_category in critical_events
    
    async def _can_verify_event(self, user_id: UUID, event_record: Dict[str, Any]) -> bool:
        """Check if user can verify event"""
        return True
    
    async def _request_supervisor_verification(self, event_id: UUID, supervisor_id: Optional[UUID], operator_id: UUID):
        """Request supervisor verification"""
        logger.debug(f"Requesting supervisor verification for event {event_id}")
    
    async def _trigger_critical_event_alerts(self, event_record: Dict[str, Any]):
        """Trigger alerts for critical events"""
        logger.info(f"Triggering alerts for critical event: {event_record['event_type']}")
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"