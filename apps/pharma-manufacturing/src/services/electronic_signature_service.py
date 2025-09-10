"""
Electronic Signature Service
Implementation of FDA 21 CFR Part 11 electronic signature requirements
"""

import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import json
import logging
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_pem_x509_certificate
import jwt

from src.models.fda_compliance import (
    ElectronicSignature, SignatureType, SignatureIntent,
    FDAUser, DocumentType
)
from src.services.audit_service import AuditService

logger = logging.getLogger(__name__)

class ElectronicSignatureService:
    """
    Service for managing electronic signatures per 21 CFR Part 11
    Implements secure signature creation, validation, and management
    """
    
    def __init__(self):
        self.audit_service = AuditService()
        self.signature_secret = self._get_signature_secret()
        
    def _get_signature_secret(self) -> bytes:
        """Get or generate signature secret for HMAC operations"""
        # In production, this should come from secure key management
        return b"pharma_signature_secret_key_change_in_production"
    
    async def create_electronic_signature(
        self,
        user_id: UUID,
        document_type: DocumentType,
        document_id: UUID,
        document_version: str,
        document_content: str,
        signature_intent: SignatureIntent,
        signature_meaning: str,
        authentication_method: str,
        authentication_factors: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        session_id: str,
        password: Optional[str] = None,
        biometric_data: Optional[bytes] = None,
        certificate_data: Optional[bytes] = None
    ) -> ElectronicSignature:
        """
        Create electronic signature per 21 CFR 11.50 and 11.70
        """
        try:
            # Validate user authentication
            await self._validate_user_authentication(
                user_id, password, biometric_data, authentication_factors
            )
            
            # Calculate document hash
            document_hash = hashlib.sha256(document_content.encode()).hexdigest()
            
            # Determine signature type based on authentication method
            signature_type = self._determine_signature_type(
                authentication_method, biometric_data, certificate_data
            )
            
            # Generate signature data
            signature_data = await self._generate_signature_data(
                user_id=user_id,
                document_hash=document_hash,
                signature_intent=signature_intent,
                timestamp=datetime.now(timezone.utc),
                authentication_factors=authentication_factors
            )
            
            # Create signature record
            signature = ElectronicSignature(
                id=uuid4(),
                user_id=user_id,
                signature_type=signature_type,
                signature_intent=signature_intent,
                signature_meaning=signature_meaning,
                document_type=document_type,
                document_id=document_id,
                document_version=document_version,
                document_hash=document_hash,
                signed_at=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                authentication_method=authentication_method,
                authentication_factors=authentication_factors,
                signature_data=signature_data,
                signature_algorithm="HMAC-SHA256",
                certificate_data=certificate_data,
                is_valid=True
            )
            
            # Store signature in database
            await self._store_signature(signature)
            
            # Create audit log entry
            await self.audit_service.log_signature_creation(
                user_id=user_id,
                signature_id=signature.id,
                document_type=document_type,
                document_id=document_id,
                signature_intent=signature_intent,
                ip_address=ip_address
            )
            
            logger.info(f"Electronic signature created: {signature.id} by user {user_id}")
            return signature
            
        except Exception as e:
            logger.error(f"Failed to create electronic signature: {str(e)}")
            await self.audit_service.log_signature_failure(
                user_id=user_id,
                document_type=document_type,
                document_id=document_id,
                error=str(e),
                ip_address=ip_address
            )
            raise
    
    async def validate_signature(
        self,
        signature_id: UUID,
        document_content: str
    ) -> Dict[str, Any]:
        """
        Validate electronic signature integrity and authenticity
        """
        try:
            # Retrieve signature from database
            signature = await self._get_signature(signature_id)
            if not signature:
                return {"valid": False, "reason": "Signature not found"}
            
            # Check if signature is marked as invalid
            if not signature.is_valid:
                return {
                    "valid": False,
                    "reason": f"Signature invalidated: {signature.invalidation_reason}",
                    "invalidated_at": signature.invalidated_at,
                    "invalidated_by": signature.invalidated_by
                }
            
            # Verify document hash
            current_document_hash = hashlib.sha256(document_content.encode()).hexdigest()
            if current_document_hash != signature.document_hash:
                return {
                    "valid": False,
                    "reason": "Document content has been modified",
                    "expected_hash": signature.document_hash,
                    "actual_hash": current_document_hash
                }
            
            # Verify signature data
            signature_valid = await self._verify_signature_data(
                signature=signature,
                document_hash=current_document_hash
            )
            
            if not signature_valid:
                return {"valid": False, "reason": "Signature data verification failed"}
            
            # Check signature expiration (if applicable)
            if await self._is_signature_expired(signature):
                return {"valid": False, "reason": "Signature has expired"}
            
            return {
                "valid": True,
                "signature": {
                    "id": signature.id,
                    "user_id": signature.user_id,
                    "signed_at": signature.signed_at,
                    "signature_type": signature.signature_type,
                    "signature_intent": signature.signature_intent,
                    "signature_meaning": signature.signature_meaning,
                    "authentication_method": signature.authentication_method
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to validate signature {signature_id}: {str(e)}")
            return {"valid": False, "reason": f"Validation error: {str(e)}"}
    
    async def invalidate_signature(
        self,
        signature_id: UUID,
        invalidated_by: UUID,
        reason: str
    ) -> bool:
        """
        Invalidate an electronic signature with proper audit trail
        """
        try:
            signature = await self._get_signature(signature_id)
            if not signature:
                raise ValueError("Signature not found")
            
            # Update signature status
            signature.is_valid = False
            signature.invalidated_at = datetime.now(timezone.utc)
            signature.invalidated_by = invalidated_by
            signature.invalidation_reason = reason
            
            # Update in database
            await self._update_signature(signature)
            
            # Create audit log
            await self.audit_service.log_signature_invalidation(
                signature_id=signature_id,
                invalidated_by=invalidated_by,
                reason=reason
            )
            
            logger.warning(f"Signature {signature_id} invalidated by {invalidated_by}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate signature {signature_id}: {str(e)}")
            return False
    
    async def get_signature_history(
        self,
        document_id: UUID,
        document_type: DocumentType
    ) -> List[Dict[str, Any]]:
        """
        Get complete signature history for a document
        """
        try:
            signatures = await self._get_document_signatures(document_id, document_type)
            
            signature_history = []
            for sig in signatures:
                signature_info = {
                    "id": sig.id,
                    "user_id": sig.user_id,
                    "signed_at": sig.signed_at,
                    "signature_type": sig.signature_type,
                    "signature_intent": sig.signature_intent,
                    "signature_meaning": sig.signature_meaning,
                    "is_valid": sig.is_valid,
                    "authentication_method": sig.authentication_method,
                    "ip_address": sig.ip_address
                }
                
                if not sig.is_valid:
                    signature_info.update({
                        "invalidated_at": sig.invalidated_at,
                        "invalidated_by": sig.invalidated_by,
                        "invalidation_reason": sig.invalidation_reason
                    })
                
                signature_history.append(signature_info)
            
            return signature_history
            
        except Exception as e:
            logger.error(f"Failed to get signature history for document {document_id}: {str(e)}")
            return []
    
    async def verify_signature_chain(
        self,
        document_id: UUID,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Verify the complete signature chain for a document
        """
        try:
            signatures = await self._get_document_signatures(document_id, document_type)
            
            chain_valid = True
            chain_issues = []
            verified_signatures = []
            
            for signature in signatures:
                # Validate each signature
                validation_result = await self.validate_signature(
                    signature.id,
                    ""  # Document content would need to be retrieved
                )
                
                verified_signatures.append({
                    "signature_id": signature.id,
                    "user_id": signature.user_id,
                    "signed_at": signature.signed_at,
                    "valid": validation_result["valid"],
                    "validation_details": validation_result
                })
                
                if not validation_result["valid"]:
                    chain_valid = False
                    chain_issues.append({
                        "signature_id": signature.id,
                        "issue": validation_result.get("reason", "Unknown validation failure")
                    })
            
            return {
                "chain_valid": chain_valid,
                "total_signatures": len(signatures),
                "valid_signatures": len([s for s in verified_signatures if s["valid"]]),
                "invalid_signatures": len([s for s in verified_signatures if not s["valid"]]),
                "chain_issues": chain_issues,
                "signatures": verified_signatures
            }
            
        except Exception as e:
            logger.error(f"Failed to verify signature chain for document {document_id}: {str(e)}")
            return {
                "chain_valid": False,
                "error": str(e)
            }
    
    async def _validate_user_authentication(
        self,
        user_id: UUID,
        password: Optional[str],
        biometric_data: Optional[bytes],
        authentication_factors: Dict[str, Any]
    ):
        """Validate user authentication per 21 CFR 11.300"""
        # Get user from database
        user = await self._get_user(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Validate password if provided
        if password:
            if not self._verify_password(password, user.password_hash, user.salt):
                raise ValueError("Invalid password")
        
        # Validate biometric data if provided
        if biometric_data:
            if not await self._verify_biometric_data(user_id, biometric_data):
                raise ValueError("Biometric verification failed")
        
        # Validate multi-factor authentication
        if "mfa_token" in authentication_factors:
            if not await self._verify_mfa_token(user_id, authentication_factors["mfa_token"]):
                raise ValueError("MFA verification failed")
    
    def _determine_signature_type(
        self,
        authentication_method: str,
        biometric_data: Optional[bytes],
        certificate_data: Optional[bytes]
    ) -> SignatureType:
        """Determine signature type based on authentication method"""
        if certificate_data:
            return SignatureType.QUALIFIED
        elif biometric_data or "biometric" in authentication_method.lower():
            return SignatureType.ADVANCED
        else:
            return SignatureType.BASIC
    
    async def _generate_signature_data(
        self,
        user_id: UUID,
        document_hash: str,
        signature_intent: SignatureIntent,
        timestamp: datetime,
        authentication_factors: Dict[str, Any]
    ) -> bytes:
        """Generate cryptographic signature data"""
        # Create signature payload
        signature_payload = {
            "user_id": str(user_id),
            "document_hash": document_hash,
            "signature_intent": signature_intent,
            "timestamp": timestamp.isoformat(),
            "authentication_factors": authentication_factors
        }
        
        # Serialize payload
        payload_bytes = json.dumps(signature_payload, sort_keys=True).encode()
        
        # Generate HMAC signature
        signature_data = hmac.new(
            self.signature_secret,
            payload_bytes,
            hashlib.sha256
        ).digest()
        
        return signature_data
    
    async def _verify_signature_data(
        self,
        signature: ElectronicSignature,
        document_hash: str
    ) -> bool:
        """Verify signature data integrity"""
        try:
            # Recreate signature payload
            signature_payload = {
                "user_id": str(signature.user_id),
                "document_hash": document_hash,
                "signature_intent": signature.signature_intent,
                "timestamp": signature.signed_at.isoformat(),
                "authentication_factors": signature.authentication_factors
            }
            
            # Serialize payload
            payload_bytes = json.dumps(signature_payload, sort_keys=True).encode()
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.signature_secret,
                payload_bytes,
                hashlib.sha256
            ).digest()
            
            # Compare signatures
            return hmac.compare_digest(signature.signature_data, expected_signature)
            
        except Exception as e:
            logger.error(f"Failed to verify signature data: {str(e)}")
            return False
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify user password"""
        # Hash the provided password with salt
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000  # iterations
        )
        
        # Compare with stored hash
        return hmac.compare_digest(
            computed_hash,
            base64.b64decode(password_hash.encode())
        )
    
    async def _verify_biometric_data(self, user_id: UUID, biometric_data: bytes) -> bool:
        """Verify biometric authentication data"""
        # In a real implementation, this would verify biometric data
        # against stored biometric templates
        # For now, we'll just validate that data is present
        return len(biometric_data) > 0
    
    async def _verify_mfa_token(self, user_id: UUID, mfa_token: str) -> bool:
        """Verify multi-factor authentication token"""
        # In a real implementation, this would verify TOTP/HOTP tokens
        # For now, we'll do basic token validation
        return len(mfa_token) >= 6
    
    async def _is_signature_expired(self, signature: ElectronicSignature) -> bool:
        """Check if signature has expired"""
        # For basic signatures, check if they're older than configured expiry
        if signature.signature_type == SignatureType.BASIC:
            expiry_hours = 24  # Basic signatures expire after 24 hours
            expiry_time = signature.signed_at + timedelta(hours=expiry_hours)
            return datetime.now(timezone.utc) > expiry_time
        
        # Advanced and qualified signatures don't expire by default
        return False
    
    # Database operations (these would integrate with actual database)
    async def _store_signature(self, signature: ElectronicSignature):
        """Store signature in database"""
        # Implementation would use actual database session
        logger.debug(f"Storing signature {signature.id} in database")
    
    async def _get_signature(self, signature_id: UUID) -> Optional[ElectronicSignature]:
        """Retrieve signature from database"""
        # Implementation would use actual database session
        logger.debug(f"Retrieving signature {signature_id} from database")
        return None
    
    async def _update_signature(self, signature: ElectronicSignature):
        """Update signature in database"""
        # Implementation would use actual database session
        logger.debug(f"Updating signature {signature.id} in database")
    
    async def _get_document_signatures(
        self,
        document_id: UUID,
        document_type: DocumentType
    ) -> List[ElectronicSignature]:
        """Get all signatures for a document"""
        # Implementation would use actual database session
        logger.debug(f"Retrieving signatures for document {document_id}")
        return []
    
    async def _get_user(self, user_id: UUID) -> Optional[FDAUser]:
        """Get user from database"""
        # Implementation would use actual database session
        logger.debug(f"Retrieving user {user_id} from database")
        return None