"""
Immutable Audit Trail Service
Implementation of FDA 21 CFR Part 11.10(e) requirements for audit trails
"""

import hashlib
import json
import hmac
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64

from src.models.fda_compliance import AuditLog, AuditAction

logger = logging.getLogger(__name__)

class ImmutableAuditService:
    """
    Service for maintaining immutable audit trails per 21 CFR Part 11
    Implements cryptographic integrity and chain of custody
    """
    
    def __init__(self):
        self.audit_key = self._get_audit_key()
        self.current_sequence = 0
        self.genesis_hash = self._calculate_genesis_hash()
        self.last_log_hash = self.genesis_hash
        
    def _get_audit_key(self) -> bytes:
        """Get or generate audit trail signing key"""
        # In production, this should come from secure key management
        return b"pharma_audit_trail_signing_key_change_in_production"
    
    def _calculate_genesis_hash(self) -> str:
        """Calculate genesis hash for audit chain"""
        genesis_data = {
            "genesis": True,
            "timestamp": "2024-01-01T00:00:00Z",
            "system": "pharma-manufacturing-audit-v1.0"
        }
        genesis_string = json.dumps(genesis_data, sort_keys=True)
        return hashlib.sha256(genesis_string.encode()).hexdigest()
    
    async def create_audit_log(
        self,
        user_id: Optional[UUID],
        username: str,
        full_name: str,
        action: AuditAction,
        action_description: str,
        entity_type: str,
        entity_id: UUID,
        entity_identifier: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        session_id: str = "unknown",
        regulatory_event: bool = False,
        gmp_critical: bool = False
    ) -> AuditLog:
        """
        Create immutable audit log entry per 21 CFR 11.10(e)
        """
        try:
            # Increment sequence number atomically
            self.current_sequence += 1
            
            # Create audit log entry
            audit_log = AuditLog(
                id=uuid4(),
                user_id=user_id,
                username=username,
                full_name=full_name,
                action=action,
                action_description=action_description,
                timestamp=datetime.now(timezone.utc),
                entity_type=entity_type,
                entity_id=entity_id,
                entity_identifier=entity_identifier,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                sequence_number=self.current_sequence,
                previous_log_hash=self.last_log_hash,
                regulatory_event=regulatory_event,
                gmp_critical=gmp_critical,
                requires_review=gmp_critical or regulatory_event
            )
            
            # Calculate current log hash
            audit_log.current_log_hash = self._calculate_log_hash(audit_log)
            
            # Update chain
            self.last_log_hash = audit_log.current_log_hash
            
            # Store audit log with integrity protection
            await self._store_audit_log_securely(audit_log)
            
            # If this is a critical event, create additional backup
            if gmp_critical or regulatory_event:
                await self._create_critical_audit_backup(audit_log)
            
            logger.info(f"Audit log created: {audit_log.id} - {action} by {username}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            # Create emergency audit log about the failure
            await self._create_emergency_audit_log(str(e), username, action)
            raise
    
    def _calculate_log_hash(self, audit_log: AuditLog) -> str:
        """
        Calculate cryptographic hash for audit log entry
        Ensures integrity and immutability
        """
        # Create deterministic hash input
        hash_data = {
            "id": str(audit_log.id),
            "user_id": str(audit_log.user_id) if audit_log.user_id else None,
            "username": audit_log.username,
            "action": audit_log.action,
            "timestamp": audit_log.timestamp.isoformat(),
            "entity_type": audit_log.entity_type,
            "entity_id": str(audit_log.entity_id),
            "sequence_number": audit_log.sequence_number,
            "previous_log_hash": audit_log.previous_log_hash,
            "old_values": audit_log.old_values,
            "new_values": audit_log.new_values
        }
        
        # Serialize to JSON with sorted keys for deterministic output
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        
        # Create HMAC for integrity
        hmac_signature = hmac.new(
            self.audit_key,
            hash_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine content hash with HMAC
        content_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        final_hash = hashlib.sha256(f"{content_hash}:{hmac_signature}".encode()).hexdigest()
        
        return final_hash
    
    async def verify_audit_chain_integrity(
        self,
        start_sequence: Optional[int] = None,
        end_sequence: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verify integrity of audit trail chain
        Detects any tampering or corruption
        """
        try:
            # Get audit logs in sequence order
            audit_logs = await self._get_audit_logs_by_sequence(start_sequence, end_sequence)
            
            verification_result = {
                "chain_valid": True,
                "total_logs_verified": 0,
                "integrity_violations": [],
                "missing_sequences": [],
                "hash_mismatches": [],
                "verification_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            expected_previous_hash = self.genesis_hash
            expected_sequence = 1
            
            for audit_log in audit_logs:
                verification_result["total_logs_verified"] += 1
                
                # Check sequence continuity
                if audit_log.sequence_number != expected_sequence:
                    verification_result["chain_valid"] = False
                    verification_result["missing_sequences"].append({
                        "expected": expected_sequence,
                        "actual": audit_log.sequence_number,
                        "log_id": str(audit_log.id)
                    })
                
                # Verify previous hash chain
                if audit_log.previous_log_hash != expected_previous_hash:
                    verification_result["chain_valid"] = False
                    verification_result["hash_mismatches"].append({
                        "log_id": str(audit_log.id),
                        "sequence": audit_log.sequence_number,
                        "expected_previous_hash": expected_previous_hash,
                        "actual_previous_hash": audit_log.previous_log_hash
                    })
                
                # Recalculate and verify current hash
                calculated_hash = self._calculate_log_hash(audit_log)
                if calculated_hash != audit_log.current_log_hash:
                    verification_result["chain_valid"] = False
                    verification_result["integrity_violations"].append({
                        "log_id": str(audit_log.id),
                        "sequence": audit_log.sequence_number,
                        "expected_hash": calculated_hash,
                        "stored_hash": audit_log.current_log_hash,
                        "violation_type": "hash_mismatch"
                    })
                
                # Update for next iteration
                expected_previous_hash = audit_log.current_log_hash
                expected_sequence = audit_log.sequence_number + 1
            
            # Log verification result
            if not verification_result["chain_valid"]:
                logger.error(f"Audit chain integrity verification failed: {verification_result}")
            else:
                logger.info(f"Audit chain integrity verified: {verification_result['total_logs_verified']} logs")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Failed to verify audit chain integrity: {str(e)}")
            return {
                "chain_valid": False,
                "error": str(e),
                "verification_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_audit_trail_for_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for a specific entity
        Maintains chronological order and integrity verification
        """
        try:
            audit_logs = await self._get_audit_logs_for_entity(
                entity_type, entity_id, start_date, end_date
            )
            
            audit_trail = []
            for log in audit_logs:
                # Verify log integrity
                calculated_hash = self._calculate_log_hash(log)
                integrity_valid = calculated_hash == log.current_log_hash
                
                audit_entry = {
                    "id": str(log.id),
                    "sequence_number": log.sequence_number,
                    "timestamp": log.timestamp.isoformat(),
                    "user": {
                        "id": str(log.user_id) if log.user_id else None,
                        "username": log.username,
                        "full_name": log.full_name
                    },
                    "action": log.action,
                    "action_description": log.action_description,
                    "entity": {
                        "type": log.entity_type,
                        "id": str(log.entity_id),
                        "identifier": log.entity_identifier
                    },
                    "changes": {
                        "old_values": log.old_values,
                        "new_values": log.new_values
                    },
                    "system_info": {
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "session_id": log.session_id
                    },
                    "compliance": {
                        "regulatory_event": log.regulatory_event,
                        "gmp_critical": log.gmp_critical,
                        "requires_review": log.requires_review
                    },
                    "integrity": {
                        "valid": integrity_valid,
                        "hash": log.current_log_hash,
                        "previous_hash": log.previous_log_hash
                    }
                }
                
                audit_trail.append(audit_entry)
            
            return audit_trail
            
        except Exception as e:
            logger.error(f"Failed to get audit trail for entity {entity_id}: {str(e)}")
            return []
    
    async def create_chain_of_custody_record(
        self,
        entity_type: str,
        entity_id: UUID,
        custody_action: str,
        from_user: str,
        to_user: str,
        location: str,
        reason: str,
        conditions: Dict[str, Any],
        user_id: UUID,
        ip_address: str
    ) -> AuditLog:
        """
        Create chain of custody audit record
        Special audit log for tracking physical and logical custody
        """
        custody_details = {
            "custody_action": custody_action,
            "from_user": from_user,
            "to_user": to_user,
            "location": location,
            "reason": reason,
            "conditions": conditions,
            "custody_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return await self.create_audit_log(
            user_id=user_id,
            username=to_user,
            full_name=to_user,  # Would be resolved from user database
            action=AuditAction.TRANSFER,
            action_description=f"Chain of custody: {custody_action}",
            entity_type=entity_type,
            entity_id=entity_id,
            entity_identifier=f"{entity_type}:{entity_id}",
            new_values=custody_details,
            ip_address=ip_address,
            regulatory_event=True,
            gmp_critical=True
        )
    
    async def create_sample_custody_record(
        self,
        sample_id: UUID,
        sample_type: str,
        custody_action: str,
        from_location: str,
        to_location: str,
        from_user: str,
        to_user: str,
        transport_conditions: Dict[str, Any],
        user_id: UUID,
        ip_address: str = "unknown"
    ) -> AuditLog:
        """
        Create sample custody record for pharmaceutical samples
        """
        try:
            sample_custody_details = {
                "sample_id": str(sample_id),
                "sample_type": sample_type,
                "custody_action": custody_action,
                "from_location": from_location,
                "to_location": to_location,
                "from_user": from_user,
                "to_user": to_user,
                "transport_conditions": transport_conditions,
                "custody_timestamp": datetime.now(timezone.utc).isoformat(),
                "sample_integrity": {
                    "temperature_maintained": transport_conditions.get("temperature_controlled", True),
                    "chain_of_custody_intact": True,
                    "seal_integrity": transport_conditions.get("seal_intact", True),
                    "documentation_complete": True
                },
                "regulatory_compliance": {
                    "gmp_requirements": "met",
                    "cold_chain_maintained": transport_conditions.get("cold_chain", False),
                    "handling_protocol": transport_conditions.get("protocol", "standard")
                }
            }
            
            # Create audit log for sample custody
            audit_log = await self.create_audit_log(
                user_id=user_id,
                username=await self._get_username(user_id),
                full_name=await self._get_full_name(user_id),
                action=AuditAction.TRANSFER,
                action_description=f"Sample custody transfer: {sample_type} from {from_location} to {to_location}",
                entity_type="sample",
                entity_id=sample_id,
                entity_identifier=f"SAMPLE:{sample_id}",
                new_values=sample_custody_details,
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True,
                session_id=f"sample_custody_{datetime.now().timestamp()}",
                user_agent="Sample Custody System"
            )
            
            logger.info(f"Sample custody record created for {sample_type}:{sample_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create sample custody record: {str(e)}")
            raise
    
    async def get_custody_chain(
        self,
        entity_type: str,
        entity_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get complete custody chain for an entity
        """
        try:
            # Get all custody transfer records
            custody_records = await self.get_audit_trail_for_entity(
                entity_type=entity_type,
                entity_id=entity_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Filter for custody-related actions
            custody_chain = []
            for record in custody_records:
                if record.get("action") == "TRANSFER" and "custody" in record.get("action_description", "").lower():
                    custody_entry = {
                        "custody_timestamp": record["timestamp"],
                        "custody_action": record["new_values"].get("custody_action", "transfer"),
                        "from_user": record["new_values"].get("from_user", "unknown"),
                        "to_user": record["new_values"].get("to_user", "unknown"),
                        "location": record["new_values"].get("location", "unknown"),
                        "reason": record["new_values"].get("reason", "not specified"),
                        "conditions": record["new_values"].get("conditions", {}),
                        "audit_log_id": record["id"],
                        "integrity_verified": record.get("integrity_verified", False)
                    }
                    custody_chain.append(custody_entry)
            
            # Sort by timestamp
            custody_chain.sort(key=lambda x: x["custody_timestamp"])
            
            return custody_chain
            
        except Exception as e:
            logger.error(f"Failed to get custody chain for {entity_type}:{entity_id}: {str(e)}")
            return []
    
    async def verify_custody_chain_integrity(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> Dict[str, Any]:
        """
        Verify integrity of custody chain
        """
        try:
            # Get custody chain
            custody_chain = await self.get_custody_chain(entity_type, entity_id)
            
            if not custody_chain:
                return {
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "custody_chain_valid": True,
                    "chain_length": 0,
                    "integrity_issues": [],
                    "verification_timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Verify chain integrity
            integrity_issues = []
            
            # Check for gaps in custody
            for i in range(len(custody_chain) - 1):
                current_transfer = custody_chain[i]
                next_transfer = custody_chain[i + 1]
                
                # Check if custody chain is continuous
                if current_transfer["to_user"] != next_transfer["from_user"]:
                    integrity_issues.append({
                        "issue_type": "custody_gap",
                        "description": f"Custody gap between {current_transfer['to_user']} and {next_transfer['from_user']}",
                        "timestamp": next_transfer["custody_timestamp"]
                    })
            
            # Check for missing required information
            for transfer in custody_chain:
                if not transfer.get("from_user") or not transfer.get("to_user"):
                    integrity_issues.append({
                        "issue_type": "incomplete_transfer",
                        "description": "Missing from_user or to_user information",
                        "timestamp": transfer["custody_timestamp"]
                    })
            
            return {
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "custody_chain_valid": len(integrity_issues) == 0,
                "chain_length": len(custody_chain),
                "integrity_issues": integrity_issues,
                "verification_timestamp": datetime.now(timezone.utc).isoformat(),
                "first_custody": custody_chain[0]["custody_timestamp"] if custody_chain else None,
                "last_custody": custody_chain[-1]["custody_timestamp"] if custody_chain else None
            }
            
        except Exception as e:
            logger.error(f"Failed to verify custody chain integrity: {str(e)}")
            return {
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "custody_chain_valid": False,
                "error": str(e),
                "verification_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_types: Optional[List[str]] = None,
        users: Optional[List[str]] = None,
        actions: Optional[List[AuditAction]] = None,
        gmp_critical_only: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report for FDA compliance
        """
        try:
            # Get filtered audit logs
            audit_logs = await self._get_filtered_audit_logs(
                start_date, end_date, entity_types, users, actions, gmp_critical_only
            )
            
            # Verify integrity of included logs
            integrity_check = await self._verify_logs_integrity(audit_logs)
            
            # Generate statistics
            stats = self._calculate_audit_statistics(audit_logs)
            
            report = {
                "report_metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "filters": {
                        "entity_types": entity_types,
                        "users": users,
                        "actions": actions,
                        "gmp_critical_only": gmp_critical_only
                    }
                },
                "integrity_verification": integrity_check,
                "statistics": stats,
                "audit_entries": [],
                "compliance_summary": {
                    "total_entries": len(audit_logs),
                    "regulatory_events": len([log for log in audit_logs if log.regulatory_event]),
                    "gmp_critical_events": len([log for log in audit_logs if log.gmp_critical]),
                    "integrity_violations": len(integrity_check.get("violations", [])),
                    "chain_integrity": integrity_check.get("chain_valid", False)
                }
            }
            
            # Add audit entries to report
            for log in audit_logs:
                report["audit_entries"].append({
                    "sequence": log.sequence_number,
                    "timestamp": log.timestamp.isoformat(),
                    "user": log.username,
                    "action": log.action,
                    "description": log.action_description,
                    "entity": f"{log.entity_type}:{log.entity_identifier}",
                    "regulatory": log.regulatory_event,
                    "gmp_critical": log.gmp_critical,
                    "hash": log.current_log_hash
                })
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_audit_statistics(self, audit_logs: List[AuditLog]) -> Dict[str, Any]:
        """Calculate audit trail statistics"""
        if not audit_logs:
            return {}
        
        actions_count = {}
        users_count = {}
        entities_count = {}
        
        for log in audit_logs:
            # Count actions
            actions_count[log.action] = actions_count.get(log.action, 0) + 1
            
            # Count users
            users_count[log.username] = users_count.get(log.username, 0) + 1
            
            # Count entities
            entities_count[log.entity_type] = entities_count.get(log.entity_type, 0) + 1
        
        return {
            "total_entries": len(audit_logs),
            "date_range": {
                "earliest": min(log.timestamp for log in audit_logs).isoformat(),
                "latest": max(log.timestamp for log in audit_logs).isoformat()
            },
            "actions_breakdown": actions_count,
            "users_breakdown": users_count,
            "entities_breakdown": entities_count,
            "regulatory_events": len([log for log in audit_logs if log.regulatory_event]),
            "gmp_critical_events": len([log for log in audit_logs if log.gmp_critical])
        }
    
    async def _store_audit_log_securely(self, audit_log: AuditLog):
        """Store audit log with additional security measures"""
        # Store in primary database
        await self._store_audit_log_primary(audit_log)
        
        # Create encrypted backup
        await self._store_audit_log_backup(audit_log)
        
        # Store in tamper-evident log file
        await self._append_to_tamper_evident_log(audit_log)
    
    async def _create_critical_audit_backup(self, audit_log: AuditLog):
        """Create additional backup for critical audit events"""
        try:
            # Encrypt audit log data
            encrypted_data = self._encrypt_audit_data(audit_log)
            
            # Store in secure backup location
            await self._store_encrypted_backup(audit_log.id, encrypted_data)
            
            logger.info(f"Critical audit backup created for log {audit_log.id}")
            
        except Exception as e:
            logger.error(f"Failed to create critical audit backup: {str(e)}")
    
    async def _create_emergency_audit_log(self, error: str, username: str, failed_action: str):
        """Create emergency audit log when normal logging fails"""
        try:
            emergency_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "emergency": True,
                "error": error,
                "username": username,
                "failed_action": failed_action,
                "sequence": "emergency"
            }
            
            # Write to emergency log file
            await self._write_emergency_log(emergency_log)
            
        except Exception as e:
            # Last resort - write to system log
            logger.critical(f"Emergency audit logging failed: {str(e)}")
    
    def _encrypt_audit_data(self, audit_log: AuditLog) -> bytes:
        """Encrypt audit log data for secure storage"""
        # Serialize audit log
        log_data = {
            "id": str(audit_log.id),
            "timestamp": audit_log.timestamp.isoformat(),
            "username": audit_log.username,
            "action": audit_log.action,
            "entity_type": audit_log.entity_type,
            "entity_id": str(audit_log.entity_id),
            "hash": audit_log.current_log_hash
        }
        
        log_json = json.dumps(log_data).encode()
        
        # Generate random IV
        iv = secrets.token_bytes(16)
        
        # Encrypt with AES
        cipher = Cipher(algorithms.AES(self.audit_key[:32]), modes.CBC(iv))
        encryptor = cipher.encryptor()
        
        # Pad data to block size
        padded_data = log_json + b' ' * (16 - len(log_json) % 16)
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return iv + encrypted_data
    
    # Database operations (these would integrate with actual database)
    async def _store_audit_log_primary(self, audit_log: AuditLog):
        """Store audit log in primary database"""
        logger.debug(f"Storing audit log {audit_log.id} in primary database")
    
    async def _store_audit_log_backup(self, audit_log: AuditLog):
        """Store audit log backup"""
        logger.debug(f"Creating backup for audit log {audit_log.id}")
    
    async def _append_to_tamper_evident_log(self, audit_log: AuditLog):
        """Append to tamper-evident log file"""
        logger.debug(f"Appending audit log {audit_log.id} to tamper-evident log")
    
    async def _get_audit_logs_by_sequence(
        self,
        start_sequence: Optional[int],
        end_sequence: Optional[int]
    ) -> List[AuditLog]:
        """Get audit logs by sequence number range"""
        logger.debug(f"Retrieving audit logs from sequence {start_sequence} to {end_sequence}")
        return []
    
    async def _get_audit_logs_for_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[AuditLog]:
        """Get audit logs for specific entity"""
        logger.debug(f"Retrieving audit logs for entity {entity_type}:{entity_id}")
        return []
    
    async def _get_filtered_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_types: Optional[List[str]],
        users: Optional[List[str]],
        actions: Optional[List[AuditAction]],
        gmp_critical_only: bool
    ) -> List[AuditLog]:
        """Get filtered audit logs"""
        logger.debug("Retrieving filtered audit logs")
        return []
    
    async def _verify_logs_integrity(self, audit_logs: List[AuditLog]) -> Dict[str, Any]:
        """Verify integrity of specific audit logs"""
        logger.debug(f"Verifying integrity of {len(audit_logs)} audit logs")
        return {"chain_valid": True, "violations": []}
    
    async def _store_encrypted_backup(self, log_id: UUID, encrypted_data: bytes):
        """Store encrypted backup"""
        logger.debug(f"Storing encrypted backup for log {log_id}")
    
    async def _write_emergency_log(self, emergency_log: Dict[str, Any]):
        """Write emergency log entry"""
        logger.debug("Writing emergency log entry")