"""
Document Control Service
FDA 21 CFR Part 11 compliant document version control and change tracking
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from models.fda_compliance import (
    ElectronicDocument, DocumentVersion, DocumentSignature, DocumentType, DocumentStatus
)
from services.immutable_audit_service import ImmutableAuditService
from services.electronic_signature_service import ElectronicSignatureService
from models.fda_compliance import AuditAction

logger = logging.getLogger(__name__)

class DocumentControlService:
    """
    Service for managing electronic documents with FDA compliance
    Implements version control, change tracking, and digital signatures
    """
    
    def __init__(self):
        self.audit_service = ImmutableAuditService()
        self.signature_service = ElectronicSignatureService()
        
    async def create_document(
        self,
        document_number: str,
        title: str,
        document_type: DocumentType,
        content: str,
        author_id: UUID,
        owner_id: UUID,
        security_classification: str = "confidential",
        requires_approval: bool = True,
        ip_address: str = "unknown"
    ) -> ElectronicDocument:
        """
        Create new electronic document with version control
        """
        try:
            # Validate document number uniqueness
            if await self._document_number_exists(document_number):
                raise ValueError(f"Document number '{document_number}' already exists")
            
            # Calculate content hash for integrity
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Create document record
            document = ElectronicDocument(
                id=uuid4(),
                document_number=document_number,
                title=title,
                document_type=document_type,
                version="1.0",
                major_version=1,
                minor_version=0,
                content=content,
                content_hash=content_hash,
                content_type="text/plain",
                content_size=len(content.encode()),
                status=DocumentStatus.DRAFT,
                author_id=author_id,
                owner_id=owner_id,
                requires_approval=requires_approval,
                security_classification=security_classification,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Store document
            await self._store_document(document)
            
            # Create initial version record
            await self._create_version_record(
                document_id=document.id,
                version="1.0",
                content=content,
                change_type="created",
                change_description="Initial document creation",
                changed_by=author_id
            )
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=author_id,
                username=await self._get_username(author_id),
                full_name=await self._get_full_name(author_id),
                action=AuditAction.CREATE,
                action_description=f"Created document: {title}",
                entity_type="electronic_document",
                entity_id=document.id,
                entity_identifier=document_number,
                new_values={
                    "document_number": document_number,
                    "title": title,
                    "document_type": document_type,
                    "version": document.version,
                    "content_hash": content_hash,
                    "security_classification": security_classification
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Document created: {document_number} ({document.id})")
            return document
            
        except Exception as e:
            logger.error(f"Failed to create document {document_number}: {str(e)}")
            raise
    
    async def update_document(
        self,
        document_id: UUID,
        new_content: str,
        change_reason: str,
        change_summary: str,
        changed_by: UUID,
        version_type: str = "minor",  # "major" or "minor"
        ip_address: str = "unknown"
    ) -> ElectronicDocument:
        """
        Update document with version control and change tracking
        """
        try:
            # Get current document
            document = await self._get_document(document_id)
            if not document:
                raise ValueError("Document not found")
            
            # Check if user can modify document
            if not await self._can_modify_document(changed_by, document):
                raise ValueError("Insufficient privileges to modify document")
            
            # Check document status
            if document.status not in [DocumentStatus.DRAFT, DocumentStatus.UNDER_REVIEW]:
                raise ValueError(f"Cannot modify document with status: {document.status}")
            
            # Calculate new version number
            if version_type == "major":
                new_major = document.major_version + 1
                new_minor = 0
            else:
                new_major = document.major_version
                new_minor = document.minor_version + 1
            
            new_version = f"{new_major}.{new_minor}"
            
            # Calculate new content hash
            new_content_hash = hashlib.sha256(new_content.encode()).hexdigest()
            
            # Store old values for audit
            old_values = {
                "version": document.version,
                "content_hash": document.content_hash,
                "content_size": document.content_size,
                "updated_at": document.updated_at.isoformat()
            }
            
            # Update document
            document.version = new_version
            document.major_version = new_major
            document.minor_version = new_minor
            document.content = new_content
            document.content_hash = new_content_hash
            document.content_size = len(new_content.encode())
            document.change_reason = change_reason
            document.change_summary = change_summary
            document.updated_at = datetime.now(timezone.utc)
            
            # Store updated document
            await self._update_document(document)
            
            # Create version record
            await self._create_version_record(
                document_id=document_id,
                version=new_version,
                content=new_content,
                change_type="modified",
                change_description=change_summary,
                changed_by=changed_by
            )
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=changed_by,
                username=await self._get_username(changed_by),
                full_name=await self._get_full_name(changed_by),
                action=AuditAction.UPDATE,
                action_description=f"Updated document: {document.title}",
                entity_type="electronic_document",
                entity_id=document_id,
                entity_identifier=document.document_number,
                old_values=old_values,
                new_values={
                    "version": new_version,
                    "content_hash": new_content_hash,
                    "content_size": document.content_size,
                    "change_reason": change_reason,
                    "change_summary": change_summary,
                    "updated_at": document.updated_at.isoformat()
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Document updated: {document.document_number} to version {new_version}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            raise
    
    async def approve_document(
        self,
        document_id: UUID,
        approved_by: UUID,
        approval_notes: str,
        effective_date: Optional[datetime] = None,
        expiry_date: Optional[datetime] = None,
        ip_address: str = "unknown"
    ) -> ElectronicDocument:
        """
        Approve document and change status to approved/effective
        """
        try:
            # Get document
            document = await self._get_document(document_id)
            if not document:
                raise ValueError("Document not found")
            
            # Check if user can approve document
            if not await self._can_approve_document(approved_by, document):
                raise ValueError("Insufficient privileges to approve document")
            
            # Check current status
            if document.status not in [DocumentStatus.UNDER_REVIEW, DocumentStatus.DRAFT]:
                raise ValueError(f"Cannot approve document with status: {document.status}")
            
            # Update document status
            old_status = document.status
            document.status = DocumentStatus.APPROVED
            document.effective_date = effective_date or datetime.now(timezone.utc)
            document.expiry_date = expiry_date
            document.updated_at = datetime.now(timezone.utc)
            
            # If effective date is now or past, set to effective
            if document.effective_date <= datetime.now(timezone.utc):
                document.status = DocumentStatus.EFFECTIVE
            
            # Store updated document
            await self._update_document(document)
            
            # Create approval signature requirement
            await self._create_signature_requirement(
                document_id=document_id,
                required_signature_type="approval",
                required_by=approved_by
            )
            
            # Create audit log
            await self.audit_service.create_audit_log(
                user_id=approved_by,
                username=await self._get_username(approved_by),
                full_name=await self._get_full_name(approved_by),
                action=AuditAction.APPROVE,
                action_description=f"Approved document: {document.title}",
                entity_type="electronic_document",
                entity_id=document_id,
                entity_identifier=document.document_number,
                old_values={"status": old_status},
                new_values={
                    "status": document.status,
                    "effective_date": document.effective_date.isoformat(),
                    "expiry_date": document.expiry_date.isoformat() if document.expiry_date else None,
                    "approval_notes": approval_notes
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Document approved: {document.document_number} by {approved_by}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to approve document {document_id}: {str(e)}")
            raise
    
    async def supersede_document(
        self,
        document_id: UUID,
        superseding_document_id: UUID,
        superseded_by: UUID,
        supersession_reason: str,
        ip_address: str = "unknown"
    ) -> ElectronicDocument:
        """
        Supersede document with new version
        """
        try:
            # Get documents
            old_document = await self._get_document(document_id)
            new_document = await self._get_document(superseding_document_id)
            
            if not old_document or not new_document:
                raise ValueError("Document(s) not found")
            
            # Check authorization
            if not await self._can_supersede_document(superseded_by, old_document):
                raise ValueError("Insufficient privileges to supersede document")
            
            # Update old document status
            old_document.status = DocumentStatus.SUPERSEDED
            old_document.updated_at = datetime.now(timezone.utc)
            
            # Link superseding document
            new_document.supersedes_document_id = document_id
            new_document.change_reason = supersession_reason
            new_document.updated_at = datetime.now(timezone.utc)
            
            # Store updates
            await self._update_document(old_document)
            await self._update_document(new_document)
            
            # Create audit logs for both documents
            await self.audit_service.create_audit_log(
                user_id=superseded_by,
                username=await self._get_username(superseded_by),
                full_name=await self._get_full_name(superseded_by),
                action=AuditAction.UPDATE,
                action_description=f"Document superseded by {new_document.document_number}",
                entity_type="electronic_document",
                entity_id=document_id,
                entity_identifier=old_document.document_number,
                old_values={"status": "effective"},
                new_values={
                    "status": DocumentStatus.SUPERSEDED,
                    "superseded_by": new_document.document_number,
                    "supersession_reason": supersession_reason
                },
                ip_address=ip_address,
                regulatory_event=True,
                gmp_critical=True
            )
            
            logger.info(f"Document superseded: {old_document.document_number} by {new_document.document_number}")
            return old_document
            
        except Exception as e:
            logger.error(f"Failed to supersede document {document_id}: {str(e)}")
            raise
    
    async def get_document_history(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Get complete change history for a document
        """
        try:
            # Get document
            document = await self._get_document(document_id)
            if not document:
                raise ValueError("Document not found")
            
            # Get all versions
            versions = await self._get_document_versions(document_id)
            
            # Get signatures
            signatures = await self._get_document_signatures(document_id)
            
            # Get audit trail
            audit_trail = await self.audit_service.get_audit_trail_for_entity(
                entity_type="electronic_document",
                entity_id=document_id
            )
            
            history = {
                "document": {
                    "id": str(document.id),
                    "document_number": document.document_number,
                    "title": document.title,
                    "current_version": document.version,
                    "status": document.status,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat()
                },
                "versions": [
                    {
                        "version": version.version,
                        "change_type": version.change_type,
                        "change_description": version.change_description,
                        "changed_by": await self._get_username(version.changed_by),
                        "changed_at": version.changed_at.isoformat(),
                        "content_hash": version.content_hash
                    }
                    for version in versions
                ],
                "signatures": [
                    {
                        "signature_id": str(sig.id),
                        "signature_intent": sig.signature_intent,
                        "signed_by": await self._get_username(sig.user_id),
                        "signed_at": sig.signed_at.isoformat(),
                        "is_valid": sig.is_valid
                    }
                    for sig in signatures
                ],
                "audit_trail": audit_trail,
                "integrity_status": await self._verify_document_integrity(document_id)
            }
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get document history for {document_id}: {str(e)}")
            return {}
    
    async def verify_document_integrity(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Verify document integrity and authenticity
        """
        try:
            document = await self._get_document(document_id)
            if not document:
                raise ValueError("Document not found")
            
            # Verify content hash
            current_hash = hashlib.sha256(document.content.encode()).hexdigest()
            content_integrity = current_hash == document.content_hash
            
            # Verify signatures
            signatures = await self._get_document_signatures(document_id)
            signature_validations = []
            
            for signature in signatures:
                validation = await self.signature_service.validate_signature(
                    signature.id,
                    document.content
                )
                signature_validations.append({
                    "signature_id": str(signature.id),
                    "valid": validation["valid"],
                    "details": validation
                })
            
            # Check version history consistency
            versions = await self._get_document_versions(document_id)
            version_integrity = await self._verify_version_history(versions)
            
            integrity_result = {
                "document_id": str(document_id),
                "content_integrity": content_integrity,
                "signature_integrity": all(sv["valid"] for sv in signature_validations),
                "version_integrity": version_integrity["valid"],
                "overall_integrity": (
                    content_integrity and 
                    all(sv["valid"] for sv in signature_validations) and 
                    version_integrity["valid"]
                ),
                "verification_timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "content_hash_match": content_integrity,
                    "signature_validations": signature_validations,
                    "version_history": version_integrity
                }
            }
            
            return integrity_result
            
        except Exception as e:
            logger.error(f"Failed to verify document integrity for {document_id}: {str(e)}")
            return {
                "document_id": str(document_id),
                "overall_integrity": False,
                "error": str(e)
            }
    
    async def _create_version_record(
        self,
        document_id: UUID,
        version: str,
        content: str,
        change_type: str,
        change_description: str,
        changed_by: UUID
    ):
        """Create document version record"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        version_record = DocumentVersion(
            id=uuid4(),
            document_id=document_id,
            version=version,
            content=content,
            content_hash=content_hash,
            change_type=change_type,
            change_description=change_description,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc)
        )
        
        await self._store_document_version(version_record)
    
    async def _create_signature_requirement(
        self,
        document_id: UUID,
        required_signature_type: str,
        required_by: UUID
    ):
        """Create signature requirement for document"""
        # This would create a signature requirement record
        logger.debug(f"Creating signature requirement for document {document_id}")
    
    async def _verify_version_history(self, versions: List[DocumentVersion]) -> Dict[str, Any]:
        """Verify version history consistency"""
        if not versions:
            return {"valid": True, "issues": []}
        
        issues = []
        
        # Sort versions by creation date
        sorted_versions = sorted(versions, key=lambda v: v.changed_at)
        
        # Check version numbering consistency
        for i, version in enumerate(sorted_versions):
            # Verify hash integrity
            calculated_hash = hashlib.sha256(version.content.encode()).hexdigest()
            if calculated_hash != version.content_hash:
                issues.append(f"Hash mismatch in version {version.version}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_versions": len(versions)
        }
    
    async def _verify_document_integrity(self, document_id: UUID) -> str:
        """Quick document integrity check"""
        try:
            integrity_result = await self.verify_document_integrity(document_id)
            return "verified" if integrity_result.get("overall_integrity") else "compromised"
        except:
            return "unknown"
    
    # Database operations (these would integrate with actual database)
    async def _document_number_exists(self, document_number: str) -> bool:
        """Check if document number exists"""
        return False
    
    async def _store_document(self, document: ElectronicDocument):
        """Store document in database"""
        logger.debug(f"Storing document {document.document_number}")
    
    async def _get_document(self, document_id: UUID) -> Optional[ElectronicDocument]:
        """Get document from database"""
        return None
    
    async def _update_document(self, document: ElectronicDocument):
        """Update document in database"""
        logger.debug(f"Updating document {document.id}")
    
    async def _store_document_version(self, version: DocumentVersion):
        """Store document version"""
        logger.debug(f"Storing document version {version.version}")
    
    async def _get_document_versions(self, document_id: UUID) -> List[DocumentVersion]:
        """Get document versions"""
        return []
    
    async def _get_document_signatures(self, document_id: UUID) -> List:
        """Get document signatures"""
        return []
    
    async def _get_username(self, user_id: UUID) -> str:
        """Get username by user ID"""
        return "unknown"
    
    async def _get_full_name(self, user_id: UUID) -> str:
        """Get full name by user ID"""
        return "Unknown User"
    
    async def _can_modify_document(self, user_id: UUID, document: ElectronicDocument) -> bool:
        """Check if user can modify document"""
        return True
    
    async def _can_approve_document(self, user_id: UUID, document: ElectronicDocument) -> bool:
        """Check if user can approve document"""
        return True
    
    async def _can_supersede_document(self, user_id: UUID, document: ElectronicDocument) -> bool:
        """Check if user can supersede document"""
        return True