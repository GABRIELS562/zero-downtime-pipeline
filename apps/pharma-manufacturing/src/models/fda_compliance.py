"""
FDA 21 CFR Part 11 Compliance Data Models
Electronic records and signatures for pharmaceutical manufacturing
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

Base = declarative_base()

# Enums for FDA compliance
class SignatureType(str, Enum):
    """Electronic signature types per 21 CFR 11.3"""
    BASIC = "basic"  # Username/password
    ADVANCED = "advanced"  # Biometric or token-based
    QUALIFIED = "qualified"  # Certificate-based

class SignatureIntent(str, Enum):
    """Intent of electronic signature"""
    AUTHORSHIP = "authorship"
    APPROVAL = "approval"
    REVIEW = "review"
    WITNESS = "witness"
    VALIDATION = "validation"

class DocumentType(str, Enum):
    """Types of electronic documents"""
    BATCH_RECORD = "batch_record"
    SOP = "standard_operating_procedure"
    SPECIFICATION = "specification"
    TEST_METHOD = "test_method"
    VALIDATION_PROTOCOL = "validation_protocol"
    DEVIATION_REPORT = "deviation_report"
    CAPA_RECORD = "capa_record"
    CHANGE_CONTROL = "change_control"

class DocumentStatus(str, Enum):
    """Document lifecycle status"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    EFFECTIVE = "effective"
    SUPERSEDED = "superseded"
    OBSOLETE = "obsolete"

class UserRole(str, Enum):
    """User roles for access control"""
    PRODUCTION_OPERATOR = "production_operator"
    PRODUCTION_SUPERVISOR = "production_supervisor"
    PRODUCTION_MANAGER = "production_manager"
    QC_ANALYST = "qc_analyst"
    QC_SUPERVISOR = "qc_supervisor"
    QC_MANAGER = "qc_manager"
    QA_SPECIALIST = "qa_specialist"
    QA_MANAGER = "qa_manager"
    MAINTENANCE_TECHNICIAN = "maintenance_technician"
    MAINTENANCE_SUPERVISOR = "maintenance_supervisor"
    REGULATORY_AFFAIRS = "regulatory_affairs"
    SYSTEM_ADMINISTRATOR = "system_administrator"

class AuditAction(str, Enum):
    """Audit trail actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SIGN = "sign"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    LOGIN = "login"
    LOGOUT = "logout"

# FDA User Management Models
class FDAUser(Base):
    __tablename__ = "fda_users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    
    # Authentication fields
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(64), nullable=False)
    failed_login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    account_locked_until = Column(DateTime(timezone=True))
    password_expires_at = Column(DateTime(timezone=True))
    last_password_change = Column(DateTime(timezone=True))
    
    # Profile information
    department = Column(String(100), nullable=False)
    title = Column(String(100))
    supervisor_id = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    phone = Column(String(20))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    training_complete = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    supervisor = relationship("FDAUser", remote_side=[id])
    roles = relationship("UserRole", back_populates="user")
    signatures = relationship("ElectronicSignature", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"), nullable=False)
    role = Column(String(50), nullable=False)
    
    # Role assignment details
    assigned_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    assigned_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    effective_from = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    effective_until = Column(DateTime(timezone=True))
    
    # Justification and approval
    assignment_reason = Column(Text)
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("FDAUser", back_populates="roles", foreign_keys=[user_id])
    assigned_by_user = relationship("FDAUser", foreign_keys=[assigned_by])
    approved_by_user = relationship("FDAUser", foreign_keys=[approved_by])

# Electronic Signature Models
class ElectronicSignature(Base):
    __tablename__ = "electronic_signatures"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"), nullable=False)
    
    # Signature details per 21 CFR 11.50
    signature_type = Column(String(20), nullable=False, default=SignatureType.BASIC)
    signature_intent = Column(String(20), nullable=False)
    signature_meaning = Column(Text, nullable=False)  # Human-readable meaning
    
    # Document/record being signed
    document_type = Column(String(50), nullable=False)
    document_id = Column(PGUUID(as_uuid=True), nullable=False)
    document_version = Column(String(20), nullable=False)
    document_hash = Column(String(64), nullable=False)  # SHA-256 hash
    
    # Signature metadata per 21 CFR 11.70
    signed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    ip_address = Column(String(45), nullable=False)  # IPv6 compatible
    user_agent = Column(Text)
    session_id = Column(String(128))
    
    # Authentication details
    authentication_method = Column(String(50), nullable=False)
    authentication_factors = Column(JSONB)  # Multi-factor auth details
    
    # Digital signature components per 21 CFR 11.3(b)(7)
    signature_data = Column(LargeBinary)  # Encrypted signature
    signature_algorithm = Column(String(50))
    certificate_data = Column(LargeBinary)  # X.509 certificate if applicable
    
    # Witness and co-signature
    witness_required = Column(Boolean, default=False)
    witness_signature_id = Column(PGUUID(as_uuid=True), ForeignKey("electronic_signatures.id"))
    
    # Validation and integrity
    is_valid = Column(Boolean, default=True)
    invalidated_at = Column(DateTime(timezone=True))
    invalidated_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    invalidation_reason = Column(Text)
    
    # Relationships
    user = relationship("FDAUser", back_populates="signatures", foreign_keys=[user_id])
    witness_signature = relationship("ElectronicSignature", remote_side=[id])
    invalidated_by_user = relationship("FDAUser", foreign_keys=[invalidated_by])

# Document Management Models
class ElectronicDocument(Base):
    __tablename__ = "electronic_documents"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    document_type = Column(String(50), nullable=False)
    
    # Version control per 21 CFR 11.10(c)
    version = Column(String(20), nullable=False, default="1.0")
    major_version = Column(Integer, nullable=False, default=1)
    minor_version = Column(Integer, nullable=False, default=0)
    
    # Document content and metadata
    content = Column(Text)
    content_hash = Column(String(64), nullable=False)  # SHA-256
    content_type = Column(String(100), default="text/plain")
    content_size = Column(Integer)
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default=DocumentStatus.DRAFT)
    effective_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    review_date = Column(DateTime(timezone=True))
    
    # Authorship and responsibility
    author_id = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"), nullable=False)
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"), nullable=False)
    
    # Approval workflow
    requires_approval = Column(Boolean, default=True)
    approval_workflow_id = Column(PGUUID(as_uuid=True))
    
    # Change control
    supersedes_document_id = Column(PGUUID(as_uuid=True), ForeignKey("electronic_documents.id"))
    change_reason = Column(Text)
    change_summary = Column(Text)
    
    # Security and access
    security_classification = Column(String(50), default="confidential")
    access_restrictions = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    author = relationship("FDAUser", foreign_keys=[author_id])
    owner = relationship("FDAUser", foreign_keys=[owner_id])
    supersedes_document = relationship("ElectronicDocument", remote_side=[id])
    signatures = relationship("DocumentSignature", back_populates="document")
    versions = relationship("DocumentVersion", back_populates="document")

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PGUUID(as_uuid=True), ForeignKey("electronic_documents.id"), nullable=False)
    
    version = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    
    # Change tracking
    change_type = Column(String(50), nullable=False)  # created, modified, approved, etc.
    change_description = Column(Text)
    changed_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Previous version reference
    previous_version_id = Column(PGUUID(as_uuid=True), ForeignKey("document_versions.id"))
    
    # Relationships
    document = relationship("ElectronicDocument", back_populates="versions")
    changed_by_user = relationship("FDAUser")
    previous_version = relationship("DocumentVersion", remote_side=[id])

class DocumentSignature(Base):
    __tablename__ = "document_signatures"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PGUUID(as_uuid=True), ForeignKey("electronic_documents.id"), nullable=False)
    signature_id = Column(PGUUID(as_uuid=True), ForeignKey("electronic_signatures.id"), nullable=False)
    
    # Signature order and workflow
    signature_order = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    
    # Relationships
    document = relationship("ElectronicDocument", back_populates="signatures")
    signature = relationship("ElectronicSignature")

# Audit Trail Models per 21 CFR 11.10(e)
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Who performed the action
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    username = Column(String(50), nullable=False)  # Redundant for integrity
    full_name = Column(String(200), nullable=False)
    
    # What action was performed
    action = Column(String(50), nullable=False)
    action_description = Column(Text, nullable=False)
    
    # When the action occurred (precise timestamp per 21 CFR 11.10(e)(1)(ii))
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # What was affected
    entity_type = Column(String(50), nullable=False)  # batch, document, user, etc.
    entity_id = Column(PGUUID(as_uuid=True), nullable=False)
    entity_identifier = Column(String(100))  # Human-readable identifier
    
    # Change details per 21 CFR 11.10(e)(1)(iii)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    
    # System information
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    session_id = Column(String(128))
    
    # Audit trail integrity per 21 CFR 11.10(e)(2)
    sequence_number = Column(Integer, nullable=False)
    previous_log_hash = Column(String(64))  # Hash of previous audit log
    current_log_hash = Column(String(64), nullable=False)  # Hash of this log
    
    # Regulatory context
    regulatory_event = Column(Boolean, default=False)
    gmp_critical = Column(Boolean, default=False)
    requires_review = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("FDAUser", back_populates="audit_logs")

# Electronic Batch Record Models
class ElectronicBatchRecord(Base):
    __tablename__ = "electronic_batch_records"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    
    # EBR identification
    ebr_number = Column(String(50), unique=True, nullable=False)
    template_id = Column(PGUUID(as_uuid=True), ForeignKey("electronic_documents.id"))
    template_version = Column(String(20), nullable=False)
    
    # Manufacturing instructions and procedures
    manufacturing_instructions = Column(JSONB, nullable=False)
    critical_process_parameters = Column(JSONB)
    quality_attributes = Column(JSONB)
    
    # Execution tracking
    started_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    started_at = Column(DateTime(timezone=True))
    completed_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    completed_at = Column(DateTime(timezone=True))
    
    # Status and approval
    status = Column(String(20), nullable=False, default="draft")
    approval_status = Column(String(20), default="pending")
    
    # Data integrity
    record_hash = Column(String(64), nullable=False)
    locked = Column(Boolean, default=False)
    locked_at = Column(DateTime(timezone=True))
    locked_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    
    # Relationships
    batch = relationship("Batch")
    template = relationship("ElectronicDocument")
    started_by_user = relationship("FDAUser", foreign_keys=[started_by])
    completed_by_user = relationship("FDAUser", foreign_keys=[completed_by])
    locked_by_user = relationship("FDAUser", foreign_keys=[locked_by])
    steps = relationship("EBRStep", back_populates="ebr")

class EBRStep(Base):
    __tablename__ = "ebr_steps"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ebr_id = Column(PGUUID(as_uuid=True), ForeignKey("electronic_batch_records.id"), nullable=False)
    
    # Step identification
    step_number = Column(String(20), nullable=False)
    step_name = Column(String(200), nullable=False)
    step_description = Column(Text, nullable=False)
    
    # Instructions and parameters
    instructions = Column(Text, nullable=False)
    critical_parameters = Column(JSONB)
    acceptance_criteria = Column(JSONB)
    
    # Execution
    executed_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    executed_at = Column(DateTime(timezone=True))
    verified_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    verified_at = Column(DateTime(timezone=True))
    
    # Results and observations
    actual_values = Column(JSONB)
    observations = Column(Text)
    deviations = Column(JSONB)
    
    # Status
    status = Column(String(20), nullable=False, default="pending")
    
    # Relationships
    ebr = relationship("ElectronicBatchRecord", back_populates="steps")
    executed_by_user = relationship("FDAUser", foreign_keys=[executed_by])
    verified_by_user = relationship("FDAUser", foreign_keys=[verified_by])

# CAPA (Corrective and Preventive Actions) Models
class CAPARecord(Base):
    __tablename__ = "capa_records"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    capa_number = Column(String(50), unique=True, nullable=False)
    
    # Problem identification
    problem_description = Column(Text, nullable=False)
    problem_category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    
    # Source information
    source_type = Column(String(50), nullable=False)  # deviation, complaint, audit, etc.
    source_id = Column(PGUUID(as_uuid=True))
    source_reference = Column(String(100))
    
    # Investigation
    root_cause_analysis = Column(Text)
    investigation_summary = Column(Text)
    
    # Corrective Actions
    corrective_actions = Column(JSONB)
    corrective_action_owner = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    corrective_action_due_date = Column(DateTime(timezone=True))
    corrective_action_completed = Column(Boolean, default=False)
    
    # Preventive Actions
    preventive_actions = Column(JSONB)
    preventive_action_owner = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    preventive_action_due_date = Column(DateTime(timezone=True))
    preventive_action_completed = Column(Boolean, default=False)
    
    # Status and workflow
    status = Column(String(20), nullable=False, default="open")
    assigned_to = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    
    # Dates
    initiated_date = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    target_completion_date = Column(DateTime(timezone=True))
    actual_completion_date = Column(DateTime(timezone=True))
    
    # Effectiveness verification
    effectiveness_check_due = Column(DateTime(timezone=True))
    effectiveness_verified = Column(Boolean, default=False)
    effectiveness_verification_notes = Column(Text)
    
    # Relationships
    corrective_action_owner_user = relationship("FDAUser", foreign_keys=[corrective_action_owner])
    preventive_action_owner_user = relationship("FDAUser", foreign_keys=[preventive_action_owner])
    assigned_to_user = relationship("FDAUser", foreign_keys=[assigned_to])

# Deviation Management Models
class Deviation(Base):
    __tablename__ = "deviations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deviation_number = Column(String(50), unique=True, nullable=False)
    
    # Deviation details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # minor, major, critical
    category = Column(String(50), nullable=False)
    
    # Associated records
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("batches.id"))
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"))
    equipment_id = Column(PGUUID(as_uuid=True), ForeignKey("equipment.id"))
    
    # Discovery and reporting
    discovered_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"), nullable=False)
    discovered_at = Column(DateTime(timezone=True), nullable=False)
    reported_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"), nullable=False)
    reported_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Investigation
    investigation_required = Column(Boolean, default=True)
    investigator_id = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    investigation_summary = Column(Text)
    root_cause = Column(Text)
    
    # Impact assessment
    quality_impact = Column(Text)
    regulatory_impact = Column(Text)
    customer_impact = Column(Text)
    
    # Resolution
    immediate_action = Column(Text)
    corrective_action = Column(Text)
    preventive_action = Column(Text)
    
    # Status and workflow
    status = Column(String(20), nullable=False, default="open")
    assigned_to = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    due_date = Column(DateTime(timezone=True))
    
    # Closure
    closed_by = Column(PGUUID(as_uuid=True), ForeignKey("fda_users.id"))
    closed_at = Column(DateTime(timezone=True))
    closure_summary = Column(Text)
    
    # CAPA linkage
    capa_required = Column(Boolean, default=False)
    capa_id = Column(PGUUID(as_uuid=True), ForeignKey("capa_records.id"))
    
    # Relationships
    batch = relationship("Batch")
    product = relationship("Product")
    equipment = relationship("Equipment")
    discovered_by_user = relationship("FDAUser", foreign_keys=[discovered_by])
    reported_by_user = relationship("FDAUser", foreign_keys=[reported_by])
    investigator = relationship("FDAUser", foreign_keys=[investigator_id])
    assigned_to_user = relationship("FDAUser", foreign_keys=[assigned_to])
    closed_by_user = relationship("FDAUser", foreign_keys=[closed_by])
    capa = relationship("CAPARecord")