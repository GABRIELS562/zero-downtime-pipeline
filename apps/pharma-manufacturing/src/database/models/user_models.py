"""
User and Electronic Signature Models
FDA 21 CFR Part 11 compliant user management and electronic signature tracking
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional
from passlib.context import CryptContext
import hashlib
import secrets

from .base import BaseModel, TimestampMixin, StatusMixin, ApprovalMixin

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRole(BaseModel):
    """User role definitions for pharmaceutical manufacturing"""
    __tablename__ = "user_roles"
    
    # Role identification
    role_code = Column(String(50), nullable=False, unique=True)
    role_name = Column(String(200), nullable=False)
    role_description = Column(Text, nullable=False)
    
    # Role hierarchy
    role_level = Column(Integer, nullable=False, default=1)
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey('user_roles.id'), nullable=True)
    parent_role = relationship("UserRole", remote_side="UserRole.id")
    
    # Permissions
    permissions = Column(JSON, nullable=False)
    system_access = Column(JSON, nullable=False)
    
    # GMP requirements
    gmp_critical_role = Column(Boolean, nullable=False, default=False)
    training_required = Column(Boolean, nullable=False, default=True)
    qualification_required = Column(Boolean, nullable=False, default=False)
    
    # Electronic signature privileges
    can_sign_batches = Column(Boolean, nullable=False, default=False)
    can_sign_investigations = Column(Boolean, nullable=False, default=False)
    can_sign_deviations = Column(Boolean, nullable=False, default=False)
    can_approve_procedures = Column(Boolean, nullable=False, default=False)
    
    # Regulatory significance
    regulatory_oversight = Column(Boolean, nullable=False, default=False)
    audit_trail_exempt = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    __table_args__ = (
        Index('idx_role_code', 'role_code'),
        Index('idx_role_name', 'role_name'),
        Index('idx_role_level', 'role_level'),
        Index('idx_gmp_critical_role', 'gmp_critical_role'),
        Index('idx_can_sign_batches', 'can_sign_batches'),
        CheckConstraint("role_level >= 1", name="positive_role_level"),
    )

class User(BaseModel, StatusMixin):
    """FDA 21 CFR Part 11 compliant user management"""
    __tablename__ = "users"
    
    # User identification
    username = Column(String(50), nullable=False, unique=True)
    user_id = Column(String(20), nullable=False, unique=True)  # Employee ID
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    email = Column(String(200), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    
    # Role relationship
    role_id = Column(UUID(as_uuid=True), ForeignKey('user_roles.id'), nullable=False)
    role = relationship("UserRole", back_populates="users")
    
    # Authentication
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(String(32), nullable=False)
    password_changed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    password_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Two-factor authentication
    tfa_enabled = Column(Boolean, nullable=False, default=False)
    tfa_secret = Column(String(32), nullable=True)
    backup_codes = Column(JSON, nullable=True)
    
    # Account status
    account_locked = Column(Boolean, nullable=False, default=False)
    lock_reason = Column(String(200), nullable=True)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    
    # Session management
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    active_sessions = Column(Integer, nullable=False, default=0)
    
    # Electronic signature credentials
    signature_pin = Column(String(255), nullable=True)  # Hashed PIN
    signature_meaning = Column(String(100), nullable=True)
    signature_enabled = Column(Boolean, nullable=False, default=False)
    signature_attempts = Column(Integer, nullable=False, default=0)
    
    # Training and qualification
    training_completed = Column(Boolean, nullable=False, default=False)
    training_completion_date = Column(DateTime(timezone=True), nullable=True)
    training_expires_at = Column(DateTime(timezone=True), nullable=True)
    qualification_status = Column(String(50), nullable=False, default="pending")
    
    # Organizational information
    department = Column(String(100), nullable=False)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    supervisor = relationship("User", remote_side="User.id")
    
    # Employment details
    hire_date = Column(DateTime(timezone=True), nullable=False)
    termination_date = Column(DateTime(timezone=True), nullable=True)
    employment_status = Column(String(50), nullable=False, default="active")
    
    # Compliance tracking
    gmp_training_current = Column(Boolean, nullable=False, default=False)
    gmp_training_date = Column(DateTime(timezone=True), nullable=True)
    regulatory_training_current = Column(Boolean, nullable=False, default=False)
    
    # Preferences
    timezone = Column(String(50), nullable=False, default="UTC")
    language = Column(String(10), nullable=False, default="en")
    
    # Relationships
    electronic_signatures = relationship("ElectronicSignature", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    training_records = relationship("UserTraining", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_user_id', 'user_id'),
        Index('idx_email', 'email'),
        Index('idx_role', 'role_id'),
        Index('idx_department', 'department'),
        Index('idx_employment_status', 'employment_status'),
        Index('idx_qualification_status', 'qualification_status'),
        Index('idx_account_locked', 'account_locked'),
        Index('idx_signature_enabled', 'signature_enabled'),
        Index('idx_last_login', 'last_login'),
        CheckConstraint("employment_status IN ('active', 'inactive', 'terminated', 'suspended')", name="valid_employment_status"),
        CheckConstraint("qualification_status IN ('pending', 'qualified', 'requalification_required', 'disqualified')", name="valid_qualification_status"),
        CheckConstraint("failed_login_attempts >= 0", name="non_negative_failed_attempts"),
        CheckConstraint("signature_attempts >= 0", name="non_negative_signature_attempts"),
        CheckConstraint("active_sessions >= 0", name="non_negative_active_sessions"),
    )
    
    def set_password(self, password: str):
        """Set password with salt and hash"""
        self.password_salt = secrets.token_hex(16)
        self.password_hash = pwd_context.hash(password + self.password_salt)
        self.password_changed_at = datetime.now(timezone.utc)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password + self.password_salt, self.password_hash)
    
    def set_signature_pin(self, pin: str):
        """Set electronic signature PIN"""
        pin_salt = secrets.token_hex(8)
        self.signature_pin = pwd_context.hash(pin + pin_salt + self.password_salt)
        self.signature_enabled = True
    
    def verify_signature_pin(self, pin: str) -> bool:
        """Verify electronic signature PIN"""
        if not self.signature_pin:
            return False
        pin_salt = secrets.token_hex(8)
        return pwd_context.verify(pin + pin_salt + self.password_salt, self.signature_pin)
    
    def is_password_expired(self) -> bool:
        """Check if password has expired"""
        if not self.password_expires_at:
            return False
        return datetime.now(timezone.utc) >= self.password_expires_at.replace(tzinfo=timezone.utc)
    
    def is_training_current(self) -> bool:
        """Check if training is current"""
        if not self.training_expires_at:
            return self.training_completed
        return self.training_completed and datetime.now(timezone.utc) < self.training_expires_at.replace(tzinfo=timezone.utc)
    
    def can_perform_electronic_signature(self) -> bool:
        """Check if user can perform electronic signatures"""
        return (self.signature_enabled and 
                self.employment_status == "active" and 
                self.qualification_status == "qualified" and
                not self.account_locked and
                self.is_training_current())

class ElectronicSignature(BaseModel):
    """FDA 21 CFR Part 11 compliant electronic signatures"""
    __tablename__ = "electronic_signatures"
    
    # Signature identification
    signature_id = Column(String(100), nullable=False, unique=True)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="electronic_signatures")
    
    # Signature details
    signature_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    signature_meaning = Column(String(200), nullable=False)
    signature_type = Column(String(50), nullable=False)  # approval, review, verification, acknowledgment
    
    # Document/record being signed
    document_type = Column(String(100), nullable=False)
    document_id = Column(UUID(as_uuid=True), nullable=False)
    document_version = Column(String(50), nullable=False)
    
    # Signature validation
    signature_valid = Column(Boolean, nullable=False, default=True)
    validation_method = Column(String(50), nullable=False)  # password_pin, biometric, token
    
    # Authentication details
    authentication_timestamp = Column(DateTime(timezone=True), nullable=False)
    authentication_method = Column(String(50), nullable=False)
    authentication_factors = Column(JSON, nullable=False)
    
    # System information
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=False)
    session_id = Column(String(100), nullable=False)
    
    # Integrity verification
    signature_hash = Column(String(64), nullable=False)
    document_hash = Column(String(64), nullable=False)
    signature_chain = Column(JSON, nullable=True)
    
    # Regulatory compliance
    regulatory_requirement = Column(String(200), nullable=False)
    witness_required = Column(Boolean, nullable=False, default=False)
    witness_signature_id = Column(UUID(as_uuid=True), ForeignKey('electronic_signatures.id'), nullable=True)
    witness_signature = relationship("ElectronicSignature", remote_side="ElectronicSignature.id")
    
    # Signature context
    signature_context = Column(JSON, nullable=True)
    business_reason = Column(Text, nullable=False)
    
    # Revocation tracking
    revoked = Column(Boolean, nullable=False, default=False)
    revocation_timestamp = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    revoked_by = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_signature_id', 'signature_id'),
        Index('idx_signature_user', 'user_id'),
        Index('idx_signature_timestamp', 'signature_timestamp'),
        Index('idx_signature_type', 'signature_type'),
        Index('idx_document_type', 'document_type'),
        Index('idx_document_id', 'document_id'),
        Index('idx_signature_valid', 'signature_valid'),
        Index('idx_revoked', 'revoked'),
        Index('idx_witness_signature', 'witness_signature_id'),
        CheckConstraint("signature_type IN ('approval', 'review', 'verification', 'acknowledgment')", name="valid_signature_type"),
        CheckConstraint("validation_method IN ('password_pin', 'biometric', 'token', 'multi_factor')", name="valid_validation_method"),
        CheckConstraint("revoked = FALSE OR revocation_timestamp IS NOT NULL", name="revoked_requires_timestamp"),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_signature_hash()
    
    def calculate_signature_hash(self):
        """Calculate signature hash for integrity verification"""
        hash_data = {
            'user_id': str(self.user_id),
            'signature_timestamp': self.signature_timestamp.isoformat() if self.signature_timestamp else None,
            'signature_meaning': self.signature_meaning,
            'document_type': self.document_type,
            'document_id': str(self.document_id),
            'document_version': self.document_version
        }
        
        hash_string = str(hash_data)
        self.signature_hash = hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_signature_integrity(self) -> bool:
        """Verify signature integrity"""
        original_hash = self.signature_hash
        self.calculate_signature_hash()
        current_hash = self.signature_hash
        self.signature_hash = original_hash
        return original_hash == current_hash
    
    def is_valid(self) -> bool:
        """Check if signature is valid"""
        return (self.signature_valid and 
                not self.revoked and 
                self.verify_signature_integrity())

class UserSession(BaseModel):
    """User session tracking for audit purposes"""
    __tablename__ = "user_sessions"
    
    # Session identification
    session_id = Column(String(100), nullable=False, unique=True)
    session_token = Column(String(255), nullable=False)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="user_sessions")
    
    # Session details
    login_timestamp = Column(DateTime(timezone=True), nullable=False)
    logout_timestamp = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=False)
    session_duration = Column(Integer, nullable=True)  # minutes
    
    # Authentication details
    authentication_method = Column(String(50), nullable=False)
    authentication_factors = Column(JSON, nullable=False)
    
    # System information
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=False)
    device_fingerprint = Column(String(64), nullable=True)
    
    # Geolocation
    location_country = Column(String(2), nullable=True)
    location_city = Column(String(100), nullable=True)
    location_coordinates = Column(String(50), nullable=True)
    
    # Session status
    session_status = Column(String(50), nullable=False, default="active")
    termination_reason = Column(String(100), nullable=True)
    
    # Activity tracking
    page_views = Column(Integer, nullable=False, default=0)
    actions_performed = Column(Integer, nullable=False, default=0)
    
    # Security monitoring
    suspicious_activity = Column(Boolean, nullable=False, default=False)
    security_events = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_session_user', 'user_id'),
        Index('idx_login_timestamp', 'login_timestamp'),
        Index('idx_last_activity', 'last_activity'),
        Index('idx_session_status', 'session_status'),
        Index('idx_ip_address', 'ip_address'),
        Index('idx_suspicious_activity', 'suspicious_activity'),
        CheckConstraint("session_status IN ('active', 'expired', 'terminated', 'locked')", name="valid_session_status"),
        CheckConstraint("page_views >= 0", name="non_negative_page_views"),
        CheckConstraint("actions_performed >= 0", name="non_negative_actions"),
    )
    
    def is_active(self) -> bool:
        """Check if session is active"""
        if self.session_status != "active":
            return False
        
        # Check session timeout (30 minutes of inactivity)
        timeout_minutes = 30
        timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        
        return self.last_activity.replace(tzinfo=timezone.utc) > timeout_threshold
    
    def extend_session(self):
        """Extend session activity"""
        self.last_activity = datetime.now(timezone.utc)
        self.actions_performed += 1
    
    def terminate_session(self, reason: str = None):
        """Terminate session"""
        self.logout_timestamp = datetime.now(timezone.utc)
        self.session_status = "terminated"
        self.termination_reason = reason
        
        if self.login_timestamp:
            delta = self.logout_timestamp - self.login_timestamp
            self.session_duration = int(delta.total_seconds() / 60)

class UserTraining(BaseModel, StatusMixin, ApprovalMixin):
    """User training records for GMP compliance"""
    __tablename__ = "user_training"
    
    # Training identification
    training_id = Column(String(100), nullable=False, unique=True)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="training_records")
    
    # Training details
    training_program = Column(String(200), nullable=False)
    training_category = Column(String(100), nullable=False)  # gmp, safety, technical, regulatory
    training_type = Column(String(50), nullable=False)  # initial, refresher, remedial, qualification
    
    # Training content
    training_title = Column(String(300), nullable=False)
    training_description = Column(Text, nullable=False)
    training_version = Column(String(50), nullable=False)
    
    # Delivery method
    delivery_method = Column(String(50), nullable=False)  # classroom, online, hands_on, self_study
    training_duration_hours = Column(Float, nullable=False)
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Assessment
    assessment_required = Column(Boolean, nullable=False, default=True)
    assessment_type = Column(String(50), nullable=True)  # quiz, exam, practical, observation
    assessment_score = Column(Float, nullable=True)
    passing_score = Column(Float, nullable=True)
    assessment_passed = Column(Boolean, nullable=True)
    
    # Instructor information
    instructor_name = Column(String(200), nullable=False)
    instructor_qualification = Column(String(200), nullable=False)
    
    # Training materials
    training_materials = Column(JSON, nullable=True)
    
    # Compliance
    regulatory_requirement = Column(String(200), nullable=True)
    compliance_period_months = Column(Integer, nullable=True)
    
    # Effectiveness evaluation
    effectiveness_evaluated = Column(Boolean, nullable=False, default=False)
    effectiveness_score = Column(Float, nullable=True)
    effectiveness_comments = Column(Text, nullable=True)
    
    # Retraining requirements
    retraining_required = Column(Boolean, nullable=False, default=False)
    retraining_reason = Column(Text, nullable=True)
    retraining_due_date = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_training_id', 'training_id'),
        Index('idx_training_user', 'user_id'),
        Index('idx_training_category', 'training_category'),
        Index('idx_training_type', 'training_type'),
        Index('idx_scheduled_date', 'scheduled_date'),
        Index('idx_completion_date', 'completion_date'),
        Index('idx_expiration_date', 'expiration_date'),
        Index('idx_assessment_passed', 'assessment_passed'),
        Index('idx_retraining_required', 'retraining_required'),
        CheckConstraint("training_category IN ('gmp', 'safety', 'technical', 'regulatory', 'quality')", name="valid_training_category"),
        CheckConstraint("training_type IN ('initial', 'refresher', 'remedial', 'qualification')", name="valid_training_type"),
        CheckConstraint("delivery_method IN ('classroom', 'online', 'hands_on', 'self_study')", name="valid_delivery_method"),
        CheckConstraint("assessment_type IS NULL OR assessment_type IN ('quiz', 'exam', 'practical', 'observation')", name="valid_assessment_type"),
        CheckConstraint("training_duration_hours > 0", name="positive_training_duration"),
        CheckConstraint("assessment_score IS NULL OR assessment_score >= 0", name="non_negative_assessment_score"),
        CheckConstraint("passing_score IS NULL OR passing_score >= 0", name="non_negative_passing_score"),
        CheckConstraint("effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 100)", name="valid_effectiveness_score"),
        CheckConstraint("scheduled_date <= completion_date OR completion_date IS NULL", name="valid_training_dates"),
    )
    
    def is_current(self) -> bool:
        """Check if training is current"""
        if not self.completion_date or not self.assessment_passed:
            return False
        
        if not self.expiration_date:
            return True
        
        return datetime.now(timezone.utc) < self.expiration_date.replace(tzinfo=timezone.utc)
    
    def calculate_effectiveness(self) -> float:
        """Calculate training effectiveness score"""
        if not self.assessment_score or not self.passing_score:
            return 0.0
        
        base_score = min(100, (self.assessment_score / self.passing_score) * 100)
        
        # Adjust for completion time (bonus for early completion)
        if self.completion_date and self.scheduled_date:
            delta = self.completion_date - self.scheduled_date
            if delta.days <= 0:  # Completed on or before scheduled date
                base_score *= 1.1  # 10% bonus
        
        return min(100, base_score)

class UserQualification(BaseModel, StatusMixin, ApprovalMixin):
    """User qualification records for pharmaceutical operations"""
    __tablename__ = "user_qualifications"
    
    # Qualification identification
    qualification_id = Column(String(100), nullable=False, unique=True)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    user = relationship("User")
    
    # Qualification details
    qualification_type = Column(String(100), nullable=False)  # role, equipment, process, system
    qualification_name = Column(String(200), nullable=False)
    qualification_description = Column(Text, nullable=False)
    
    # Requirements
    prerequisites = Column(JSON, nullable=True)
    training_requirements = Column(JSON, nullable=False)
    experience_requirements = Column(JSON, nullable=True)
    
    # Qualification process
    qualification_method = Column(String(100), nullable=False)  # written_exam, practical_test, observation
    qualification_criteria = Column(JSON, nullable=False)
    
    # Assessment
    assessment_date = Column(DateTime(timezone=True), nullable=False)
    assessor_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    assessor = relationship("User", foreign_keys=[assessor_id])
    
    # Results
    qualification_score = Column(Float, nullable=True)
    qualification_result = Column(String(50), nullable=False)  # qualified, not_qualified, conditional
    
    # Validity
    effective_date = Column(DateTime(timezone=True), nullable=False)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Requalification
    requalification_required = Column(Boolean, nullable=False, default=False)
    requalification_frequency_months = Column(Integer, nullable=True)
    next_requalification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Documentation
    qualification_evidence = Column(JSON, nullable=True)
    qualification_certificate = Column(String(500), nullable=True)
    
    __table_args__ = (
        Index('idx_qualification_id', 'qualification_id'),
        Index('idx_qualification_user', 'user_id'),
        Index('idx_qualification_type', 'qualification_type'),
        Index('idx_assessment_date', 'assessment_date'),
        Index('idx_qualification_result', 'qualification_result'),
        Index('idx_effective_date', 'effective_date'),
        Index('idx_expiration_date', 'expiration_date'),
        Index('idx_requalification_required', 'requalification_required'),
        CheckConstraint("qualification_type IN ('role', 'equipment', 'process', 'system')", name="valid_qualification_type"),
        CheckConstraint("qualification_result IN ('qualified', 'not_qualified', 'conditional')", name="valid_qualification_result"),
        CheckConstraint("qualification_score IS NULL OR qualification_score >= 0", name="non_negative_qualification_score"),
        CheckConstraint("effective_date <= expiration_date OR expiration_date IS NULL", name="valid_qualification_dates"),
        CheckConstraint("requalification_frequency_months IS NULL OR requalification_frequency_months > 0", name="positive_requalification_frequency"),
    )
    
    def is_current(self) -> bool:
        """Check if qualification is current"""
        if self.qualification_result != "qualified":
            return False
        
        now = datetime.now(timezone.utc)
        
        if now < self.effective_date.replace(tzinfo=timezone.utc):
            return False
        
        if self.expiration_date and now >= self.expiration_date.replace(tzinfo=timezone.utc):
            return False
        
        return True
    
    def is_requalification_due(self) -> bool:
        """Check if requalification is due"""
        if not self.requalification_required or not self.next_requalification_date:
            return False
        
        return datetime.now(timezone.utc) >= self.next_requalification_date.replace(tzinfo=timezone.utc)

class AccessLog(BaseModel, TimestampMixin):
    """Access log for audit trail compliance"""
    __tablename__ = "access_logs"
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    user = relationship("User")
    
    # Access details
    access_type = Column(String(50), nullable=False)  # login, logout, page_view, action, download
    resource_accessed = Column(String(200), nullable=False)
    action_performed = Column(String(100), nullable=False)
    
    # System information
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=False)
    session_id = Column(String(100), nullable=False)
    
    # Request details
    request_method = Column(String(10), nullable=False)
    request_url = Column(String(500), nullable=False)
    request_parameters = Column(JSON, nullable=True)
    
    # Response details
    response_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    
    # Data access
    data_accessed = Column(JSON, nullable=True)
    data_modified = Column(JSON, nullable=True)
    
    # Risk assessment
    risk_score = Column(Float, nullable=False, default=0.0)
    anomaly_detected = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        Index('idx_access_user', 'user_id'),
        Index('idx_access_timestamp', 'timestamp'),
        Index('idx_access_type', 'access_type'),
        Index('idx_resource_accessed', 'resource_accessed'),
        Index('idx_ip_address', 'ip_address'),
        Index('idx_session_id', 'session_id'),
        Index('idx_anomaly_detected', 'anomaly_detected'),
        CheckConstraint("access_type IN ('login', 'logout', 'page_view', 'action', 'download', 'api_call')", name="valid_access_type"),
        CheckConstraint("response_code >= 100 AND response_code <= 599", name="valid_response_code"),
        CheckConstraint("response_time_ms >= 0", name="non_negative_response_time"),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="valid_risk_score"),
    )