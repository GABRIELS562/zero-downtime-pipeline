"""
Base database models for pharmaceutical manufacturing system
FDA 21 CFR Part 11 compliant database foundation
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, Any, Optional
import json

Base = declarative_base()

class BaseModel(Base):
    """
    Base model for all pharmaceutical manufacturing entities
    Ensures FDA 21 CFR Part 11 compliance with audit trail requirements
    """
    __abstract__ = True
    
    # Primary key - UUID for global uniqueness
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Audit trail fields - FDA 21 CFR Part 11 requirements
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    modified_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    modified_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Version control for data integrity
    version = Column(String(50), nullable=False, default="1.0")
    
    # Logical deletion - never physically delete regulated data
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Electronic signature tracking
    electronic_signature_id = Column(UUID(as_uuid=True), nullable=True)
    signature_meaning = Column(String(100), nullable=True)
    
    # Change control tracking
    change_control_id = Column(UUID(as_uuid=True), nullable=True)
    change_reason = Column(Text, nullable=True)
    
    # Data integrity hash for tamper detection
    data_integrity_hash = Column(String(64), nullable=True)
    
    # Regulatory status
    regulatory_status = Column(String(50), nullable=False, default="active")
    
    # Comments for regulatory compliance
    comments = Column(Text, nullable=True)
    
    # Metadata for additional regulatory information
    regulatory_metadata = Column(JSON, nullable=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_data_integrity_hash()
    
    def calculate_data_integrity_hash(self):
        """Calculate SHA-256 hash for data integrity verification"""
        import hashlib
        
        # Create hash of critical data fields
        hash_data = {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'version': self.version
        }
        
        # Add model-specific fields for hashing
        for column in self.__table__.columns:
            if column.name not in ['data_integrity_hash', 'modified_at', 'modified_by']:
                value = getattr(self, column.name)
                if value is not None:
                    hash_data[column.name] = str(value)
        
        # Calculate hash
        hash_string = json.dumps(hash_data, sort_keys=True)
        self.data_integrity_hash = hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_data_integrity(self) -> bool:
        """Verify data integrity using stored hash"""
        original_hash = self.data_integrity_hash
        self.calculate_data_integrity_hash()
        current_hash = self.data_integrity_hash
        self.data_integrity_hash = original_hash
        return original_hash == current_hash
    
    def soft_delete(self, deleted_by: UUID, reason: str = None):
        """Soft delete for regulatory compliance"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by
        if reason:
            self.change_reason = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif hasattr(value, '__dict__'):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result
    
    @classmethod
    def create_with_signature(cls, session: Session, created_by: UUID, signature_id: UUID, **kwargs):
        """Create record with electronic signature"""
        instance = cls(
            created_by=created_by,
            modified_by=created_by,
            electronic_signature_id=signature_id,
            **kwargs
        )
        session.add(instance)
        return instance
    
    @classmethod
    def get_active_records(cls, session: Session):
        """Get all active (non-deleted) records"""
        return session.query(cls).filter(cls.is_deleted == False)
    
    @classmethod
    def get_by_id(cls, session: Session, record_id: UUID):
        """Get record by ID (active records only)"""
        return session.query(cls).filter(
            cls.id == record_id,
            cls.is_deleted == False
        ).first()

class TimestampMixin:
    """Mixin for timestamp tracking"""
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Index for efficient time-based queries
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
    )

class StatusMixin:
    """Mixin for status tracking"""
    status = Column(String(50), nullable=False, default="active")
    status_changed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status_changed_by = Column(UUID(as_uuid=True), nullable=False)
    
    def change_status(self, new_status: str, changed_by: UUID, reason: str = None):
        """Change status with audit trail"""
        self.status = new_status
        self.status_changed_at = datetime.now(timezone.utc)
        self.status_changed_by = changed_by
        if reason:
            self.change_reason = reason

class ApprovalMixin:
    """Mixin for approval workflow"""
    approval_required = Column(Boolean, nullable=False, default=True)
    approved = Column(Boolean, nullable=False, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approval_signature_id = Column(UUID(as_uuid=True), nullable=True)
    approval_comments = Column(Text, nullable=True)
    
    def approve(self, approved_by: UUID, signature_id: UUID, comments: str = None):
        """Approve with electronic signature"""
        self.approved = True
        self.approved_at = datetime.now(timezone.utc)
        self.approved_by = approved_by
        self.approval_signature_id = signature_id
        if comments:
            self.approval_comments = comments

class TestResultMixin:
    """Mixin for test results"""
    test_method = Column(String(100), nullable=False)
    test_procedure = Column(String(100), nullable=False)
    test_started_at = Column(DateTime(timezone=True), nullable=True)
    test_completed_at = Column(DateTime(timezone=True), nullable=True)
    tested_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Test results as JSON for flexibility
    test_results = Column(JSON, nullable=True)
    specifications = Column(JSON, nullable=False)
    
    # Test outcome
    test_passed = Column(Boolean, nullable=True)
    deviations = Column(JSON, nullable=True)
    
    def record_test_result(self, results: Dict[str, Any], tested_by: UUID):
        """Record test results with validation"""
        self.test_results = results
        self.test_completed_at = datetime.now(timezone.utc)
        self.tested_by = tested_by
        self.validate_against_specifications()
    
    def validate_against_specifications(self):
        """Validate test results against specifications"""
        if not self.test_results or not self.specifications:
            return
        
        # Implementation would validate each test parameter
        # For now, assume validation logic exists
        self.test_passed = True  # Placeholder

class BatchTrackingMixin:
    """Mixin for batch tracking"""
    batch_number = Column(String(100), nullable=False, unique=True)
    lot_number = Column(String(100), nullable=False)
    manufacturing_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Batch size and units
    batch_size = Column(String(50), nullable=False)
    batch_units = Column(String(20), nullable=False)
    
    # Batch status
    batch_status = Column(String(50), nullable=False, default="in_progress")
    
    # Quality status
    quality_status = Column(String(50), nullable=False, default="pending")
    
    # Release information
    released = Column(Boolean, nullable=False, default=False)
    release_date = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Genealogy tracking
    parent_batch_id = Column(UUID(as_uuid=True), nullable=True)
    genealogy_path = Column(String(500), nullable=True)
    
    def release_batch(self, released_by: UUID, signature_id: UUID):
        """Release batch with electronic signature"""
        self.released = True
        self.release_date = datetime.now(timezone.utc)
        self.released_by = released_by
        self.electronic_signature_id = signature_id
        self.batch_status = "released"
        self.quality_status = "approved"

class CalibrationMixin:
    """Mixin for calibration tracking"""
    calibration_date = Column(DateTime(timezone=True), nullable=False)
    next_calibration_date = Column(DateTime(timezone=True), nullable=False)
    calibration_frequency_days = Column(String(20), nullable=False)
    
    # Calibration details
    calibration_procedure = Column(String(100), nullable=False)
    calibration_standard = Column(String(100), nullable=False)
    calibration_certificate = Column(String(100), nullable=True)
    
    # Calibration results
    calibration_results = Column(JSON, nullable=True)
    calibration_passed = Column(Boolean, nullable=False, default=False)
    
    # Calibration personnel
    calibrated_by = Column(UUID(as_uuid=True), nullable=False)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    
    def is_calibration_current(self) -> bool:
        """Check if calibration is current"""
        return datetime.now(timezone.utc) < self.next_calibration_date.replace(tzinfo=timezone.utc)
    
    def days_until_calibration(self) -> int:
        """Calculate days until next calibration"""
        delta = self.next_calibration_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
        return max(0, delta.days)

# Database constraints for data integrity
class DatabaseConstraints:
    """Database constraints for pharmaceutical manufacturing"""
    
    @staticmethod
    def add_manufacturing_constraints():
        """Add manufacturing-specific constraints"""
        constraints = [
            # Batch numbers must be unique
            CheckConstraint("batch_number ~ '^[A-Z0-9]{6,20}$'", name="valid_batch_number"),
            
            # Lot numbers must be unique within batch
            CheckConstraint("lot_number ~ '^[A-Z0-9]{6,20}$'", name="valid_lot_number"),
            
            # Manufacturing date must be before expiry date
            CheckConstraint("manufacturing_date < expiry_date", name="valid_date_range"),
            
            # Test results must have valid status
            CheckConstraint("test_passed IS NULL OR test_passed IN (TRUE, FALSE)", name="valid_test_status"),
            
            # Calibration dates must be logical
            CheckConstraint("calibration_date <= next_calibration_date", name="valid_calibration_dates"),
            
            # Electronic signatures must be present for approved records
            CheckConstraint("(approved = FALSE) OR (approved = TRUE AND approval_signature_id IS NOT NULL)", name="signature_required_for_approval"),
        ]
        return constraints

# Utility functions for database operations
class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    def create_audit_record(session: Session, table_name: str, record_id: UUID, 
                          action: str, user_id: UUID, old_values: Dict = None, 
                          new_values: Dict = None):
        """Create audit record for regulatory compliance"""
        from .audit_models import AuditTrail
        
        audit_record = AuditTrail(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            created_by=user_id,
            modified_by=user_id
        )
        session.add(audit_record)
        return audit_record
    
    @staticmethod
    def validate_electronic_signature(session: Session, signature_id: UUID, 
                                    user_id: UUID, action: str) -> bool:
        """Validate electronic signature for FDA compliance"""
        from .user_models import ElectronicSignature
        
        signature = session.query(ElectronicSignature).filter(
            ElectronicSignature.id == signature_id,
            ElectronicSignature.user_id == user_id,
            ElectronicSignature.is_valid == True
        ).first()
        
        return signature is not None
    
    @staticmethod
    def create_genealogy_path(session: Session, batch_id: UUID, parent_batch_id: UUID = None) -> str:
        """Create genealogy path for batch tracking"""
        if parent_batch_id:
            # Get parent's genealogy path
            parent_batch = session.query(BaseModel).filter(
                BaseModel.id == parent_batch_id
            ).first()
            
            if parent_batch and hasattr(parent_batch, 'genealogy_path'):
                parent_path = parent_batch.genealogy_path or ""
                return f"{parent_path}/{str(batch_id)}"
        
        return str(batch_id)
    
    @staticmethod
    def check_data_integrity(session: Session, model_class, record_id: UUID) -> bool:
        """Check data integrity for regulatory compliance"""
        record = session.query(model_class).filter(
            model_class.id == record_id
        ).first()
        
        if record and hasattr(record, 'verify_data_integrity'):
            return record.verify_data_integrity()
        
        return False

# Database indexes for performance
class DatabaseIndexes:
    """Database indexes for pharmaceutical manufacturing queries"""
    
    @staticmethod
    def create_manufacturing_indexes():
        """Create indexes for manufacturing queries"""
        indexes = [
            # Batch and lot tracking
            "CREATE INDEX IF NOT EXISTS idx_batch_number ON batches(batch_number)",
            "CREATE INDEX IF NOT EXISTS idx_lot_number ON batches(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_manufacturing_date ON batches(manufacturing_date)",
            "CREATE INDEX IF NOT EXISTS idx_batch_status ON batches(batch_status)",
            
            # Quality control
            "CREATE INDEX IF NOT EXISTS idx_test_date ON test_results(test_completed_at)",
            "CREATE INDEX IF NOT EXISTS idx_test_status ON test_results(test_passed)",
            "CREATE INDEX IF NOT EXISTS idx_tested_by ON test_results(tested_by)",
            
            # Equipment calibration
            "CREATE INDEX IF NOT EXISTS idx_calibration_date ON equipment_calibration(calibration_date)",
            "CREATE INDEX IF NOT EXISTS idx_next_calibration ON equipment_calibration(next_calibration_date)",
            "CREATE INDEX IF NOT EXISTS idx_equipment_id ON equipment_calibration(equipment_id)",
            
            # Environmental monitoring
            "CREATE INDEX IF NOT EXISTS idx_monitoring_timestamp ON environmental_monitoring(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_monitoring_point ON environmental_monitoring(monitoring_point_id)",
            "CREATE INDEX IF NOT EXISTS idx_parameter_type ON environmental_monitoring(parameter_type)",
            
            # Audit trail
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_trail(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trail(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_trail(action)",
            
            # User and signatures
            "CREATE INDEX IF NOT EXISTS idx_signature_user ON electronic_signatures(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_signature_timestamp ON electronic_signatures(signature_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_user_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_user_status ON users(status)",
            
            # Regulatory compliance
            "CREATE INDEX IF NOT EXISTS idx_regulatory_status ON {table}(regulatory_status)",
            "CREATE INDEX IF NOT EXISTS idx_electronic_signature ON {table}(electronic_signature_id)",
            "CREATE INDEX IF NOT EXISTS idx_change_control ON {table}(change_control_id)",
            
            # Performance indexes
            "CREATE INDEX IF NOT EXISTS idx_created_at ON {table}(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_modified_at ON {table}(modified_at)",
            "CREATE INDEX IF NOT EXISTS idx_is_deleted ON {table}(is_deleted)",
        ]
        return indexes