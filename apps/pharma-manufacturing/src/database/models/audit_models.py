"""
Audit Trail Models
Comprehensive audit trail and event tracking for pharmaceutical manufacturing compliance
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional
import json
import hashlib
import secrets

from .base import BaseModel, TimestampMixin, StatusMixin

class AuditTrail(BaseModel, TimestampMixin):
    """Comprehensive audit trail for all system events"""
    __tablename__ = "audit_trail"
    
    # Audit identification
    audit_id = Column(String(100), nullable=False, unique=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # create, update, delete, login, logout, sign, approve
    event_category = Column(String(50), nullable=False)  # data, security, system, process, compliance
    event_description = Column(Text, nullable=False)
    
    # Source information
    table_name = Column(String(100), nullable=True)
    record_id = Column(UUID(as_uuid=True), nullable=True)
    field_name = Column(String(100), nullable=True)
    
    # User information
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_name = Column(String(100), nullable=False)
    user_role = Column(String(100), nullable=False)
    
    # Action details
    action = Column(String(100), nullable=False)
    action_status = Column(String(50), nullable=False)  # success, failure, pending
    
    # Data changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changed_fields = Column(JSON, nullable=True)
    
    # System information
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=False)
    session_id = Column(String(100), nullable=False)
    
    # Request details
    request_method = Column(String(10), nullable=True)
    request_url = Column(String(500), nullable=True)
    request_parameters = Column(JSON, nullable=True)
    
    # Response details
    response_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Business context
    business_process = Column(String(100), nullable=True)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    lot_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Compliance information
    regulatory_significance = Column(Boolean, nullable=False, default=False)
    gmp_critical = Column(Boolean, nullable=False, default=False)
    audit_trail_type = Column(String(50), nullable=False, default="standard")
    
    # Data integrity
    event_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)
    
    # Retention
    retention_period_years = Column(Integer, nullable=False, default=7)
    purge_date = Column(DateTime(timezone=True), nullable=True)
    
    # Alert generation
    alert_triggered = Column(Boolean, nullable=False, default=False)
    alert_level = Column(String(20), nullable=True)
    
    __table_args__ = (
        Index('idx_audit_id', 'audit_id'),
        Index('idx_event_type', 'event_type'),
        Index('idx_event_category', 'event_category'),
        Index('idx_table_name', 'table_name'),
        Index('idx_record_id', 'record_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_action', 'action'),
        Index('idx_action_status', 'action_status'),
        Index('idx_timestamp', 'timestamp'),
        Index('idx_ip_address', 'ip_address'),
        Index('idx_session_id', 'session_id'),
        Index('idx_batch_id', 'batch_id'),
        Index('idx_regulatory_significance', 'regulatory_significance'),
        Index('idx_gmp_critical', 'gmp_critical'),
        Index('idx_alert_triggered', 'alert_triggered'),
        # Composite indexes for common queries
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_table_timestamp', 'table_name', 'timestamp'),
        Index('idx_event_timestamp', 'event_type', 'timestamp'),
        CheckConstraint("event_type IN ('create', 'update', 'delete', 'login', 'logout', 'sign', 'approve', 'reject', 'review')", name="valid_event_type"),
        CheckConstraint("event_category IN ('data', 'security', 'system', 'process', 'compliance')", name="valid_event_category"),
        CheckConstraint("action_status IN ('success', 'failure', 'pending')", name="valid_action_status"),
        CheckConstraint("audit_trail_type IN ('standard', 'security', 'compliance', 'system')", name="valid_audit_trail_type"),
        CheckConstraint("alert_level IS NULL OR alert_level IN ('info', 'warning', 'critical')", name="valid_alert_level"),
        CheckConstraint("retention_period_years > 0", name="positive_retention_period"),
        CheckConstraint("response_code IS NULL OR (response_code >= 100 AND response_code <= 599)", name="valid_response_code"),
        CheckConstraint("response_time_ms IS NULL OR response_time_ms >= 0", name="non_negative_response_time"),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generate_audit_id()
        self.calculate_event_hash()
    
    def generate_audit_id(self):
        """Generate unique audit ID"""
        if not self.audit_id:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            self.audit_id = f"AUD-{timestamp}-{secrets.token_hex(4).upper()}"
    
    def calculate_event_hash(self):
        """Calculate event hash for data integrity"""
        hash_data = {
            'event_type': self.event_type,
            'table_name': self.table_name,
            'record_id': str(self.record_id) if self.record_id else None,
            'user_id': str(self.user_id),
            'action': self.action,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'old_values': json.dumps(self.old_values, sort_keys=True) if self.old_values else None,
            'new_values': json.dumps(self.new_values, sort_keys=True) if self.new_values else None
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        self.event_hash = hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify audit trail integrity"""
        original_hash = self.event_hash
        self.calculate_event_hash()
        current_hash = self.event_hash
        self.event_hash = original_hash
        return original_hash == current_hash
    
    def set_retention_date(self):
        """Set purge date based on retention period"""
        if self.timestamp:
            self.purge_date = self.timestamp + timedelta(days=self.retention_period_years * 365)

class SecurityEvent(BaseModel, TimestampMixin):
    """Security-specific events and violations"""
    __tablename__ = "security_events"
    
    # Event identification
    event_id = Column(String(100), nullable=False, unique=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # failed_login, unauthorized_access, privilege_escalation
    event_severity = Column(String(20), nullable=False)  # low, medium, high, critical
    event_description = Column(Text, nullable=False)
    
    # User information
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(100), nullable=True)
    user_role = Column(String(100), nullable=True)
    
    # System information
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=False)
    session_id = Column(String(100), nullable=True)
    
    # Attack details
    attack_type = Column(String(100), nullable=True)
    attack_vector = Column(String(100), nullable=True)
    attack_signature = Column(String(200), nullable=True)
    
    # Resource information
    resource_accessed = Column(String(200), nullable=True)
    resource_type = Column(String(100), nullable=True)
    access_denied = Column(Boolean, nullable=False, default=False)
    
    # Geolocation
    country_code = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    coordinates = Column(String(50), nullable=True)
    
    # Response information
    response_action = Column(String(100), nullable=True)
    account_locked = Column(Boolean, nullable=False, default=False)
    admin_notified = Column(Boolean, nullable=False, default=False)
    
    # Investigation
    investigated = Column(Boolean, nullable=False, default=False)
    investigation_result = Column(Text, nullable=True)
    false_positive = Column(Boolean, nullable=False, default=False)
    
    # Correlation
    correlation_id = Column(String(100), nullable=True)
    related_events = Column(JSON, nullable=True)
    
    # Risk assessment
    risk_score = Column(Float, nullable=False, default=0.0)
    threat_level = Column(String(20), nullable=False, default="low")
    
    __table_args__ = (
        Index('idx_security_event_id', 'event_id'),
        Index('idx_security_event_type', 'event_type'),
        Index('idx_security_event_severity', 'event_severity'),
        Index('idx_security_user_id', 'user_id'),
        Index('idx_security_ip_address', 'ip_address'),
        Index('idx_security_timestamp', 'timestamp'),
        Index('idx_security_attack_type', 'attack_type'),
        Index('idx_security_access_denied', 'access_denied'),
        Index('idx_security_investigated', 'investigated'),
        Index('idx_security_threat_level', 'threat_level'),
        CheckConstraint("event_type IN ('failed_login', 'unauthorized_access', 'privilege_escalation', 'data_breach', 'malware')", name="valid_security_event_type"),
        CheckConstraint("event_severity IN ('low', 'medium', 'high', 'critical')", name="valid_security_event_severity"),
        CheckConstraint("threat_level IN ('low', 'medium', 'high', 'critical')", name="valid_threat_level"),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="valid_risk_score"),
    )

class ChangeLog(BaseModel):
    """Detailed change log for critical data modifications"""
    __tablename__ = "change_logs"
    
    # Change identification
    change_id = Column(String(100), nullable=False, unique=True)
    
    # Source information
    table_name = Column(String(100), nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    field_name = Column(String(100), nullable=False)
    
    # Change details
    change_type = Column(String(20), nullable=False)  # insert, update, delete
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # User information
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    change_reason = Column(Text, nullable=True)
    
    # Approval workflow
    approval_required = Column(Boolean, nullable=False, default=False)
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Electronic signature
    signature_required = Column(Boolean, nullable=False, default=False)
    signature_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Business impact
    business_impact = Column(String(50), nullable=False, default="low")
    impact_description = Column(Text, nullable=True)
    
    # Regulatory significance
    regulatory_impact = Column(Boolean, nullable=False, default=False)
    regulatory_authority = Column(String(100), nullable=True)
    
    # Change control
    change_control_id = Column(String(100), nullable=True)
    change_control_required = Column(Boolean, nullable=False, default=False)
    
    # Validation
    validation_required = Column(Boolean, nullable=False, default=False)
    validation_completed = Column(Boolean, nullable=False, default=False)
    validation_results = Column(JSON, nullable=True)
    
    # Rollback information
    rollback_possible = Column(Boolean, nullable=False, default=True)
    rollback_data = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_change_id', 'change_id'),
        Index('idx_change_table', 'table_name'),
        Index('idx_change_record', 'record_id'),
        Index('idx_change_field', 'field_name'),
        Index('idx_change_type', 'change_type'),
        Index('idx_changed_by', 'changed_by'),
        Index('idx_approval_required', 'approval_required'),
        Index('idx_approved', 'approved'),
        Index('idx_regulatory_impact', 'regulatory_impact'),
        Index('idx_change_control_id', 'change_control_id'),
        CheckConstraint("change_type IN ('insert', 'update', 'delete')", name="valid_change_type"),
        CheckConstraint("business_impact IN ('low', 'medium', 'high', 'critical')", name="valid_business_impact"),
        CheckConstraint("approved = FALSE OR approved_by IS NOT NULL", name="approved_requires_user"),
        CheckConstraint("signature_required = FALSE OR signature_id IS NOT NULL", name="signature_required_has_id"),
    )

class SystemEvent(BaseModel, TimestampMixin):
    """System-level events and monitoring"""
    __tablename__ = "system_events"
    
    # Event identification
    event_id = Column(String(100), nullable=False, unique=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # startup, shutdown, error, warning, info
    event_category = Column(String(50), nullable=False)  # application, database, network, security
    event_source = Column(String(100), nullable=False)
    event_message = Column(Text, nullable=False)
    
    # Severity
    severity_level = Column(String(20), nullable=False)  # debug, info, warning, error, critical
    
    # System information
    hostname = Column(String(100), nullable=False)
    service_name = Column(String(100), nullable=False)
    process_id = Column(Integer, nullable=True)
    thread_id = Column(Integer, nullable=True)
    
    # Error details
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Performance metrics
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    response_time = Column(Float, nullable=True)
    
    # Business context
    user_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(String(100), nullable=True)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Monitoring
    alert_generated = Column(Boolean, nullable=False, default=False)
    notification_sent = Column(Boolean, nullable=False, default=False)
    
    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolution_time = Column(DateTime(timezone=True), nullable=True)
    resolution_action = Column(Text, nullable=True)
    
    # Correlation
    correlation_id = Column(String(100), nullable=True)
    parent_event_id = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_system_event_id', 'event_id'),
        Index('idx_system_event_type', 'event_type'),
        Index('idx_system_event_category', 'event_category'),
        Index('idx_system_event_source', 'event_source'),
        Index('idx_system_severity', 'severity_level'),
        Index('idx_system_timestamp', 'timestamp'),
        Index('idx_system_hostname', 'hostname'),
        Index('idx_system_service', 'service_name'),
        Index('idx_system_alert_generated', 'alert_generated'),
        Index('idx_system_resolved', 'resolved'),
        Index('idx_system_correlation', 'correlation_id'),
        CheckConstraint("event_type IN ('startup', 'shutdown', 'error', 'warning', 'info', 'debug')", name="valid_system_event_type"),
        CheckConstraint("event_category IN ('application', 'database', 'network', 'security', 'performance')", name="valid_system_event_category"),
        CheckConstraint("severity_level IN ('debug', 'info', 'warning', 'error', 'critical')", name="valid_severity_level"),
        CheckConstraint("cpu_usage IS NULL OR (cpu_usage >= 0 AND cpu_usage <= 100)", name="valid_cpu_usage"),
        CheckConstraint("memory_usage IS NULL OR memory_usage >= 0", name="valid_memory_usage"),
        CheckConstraint("disk_usage IS NULL OR disk_usage >= 0", name="valid_disk_usage"),
        CheckConstraint("response_time IS NULL OR response_time >= 0", name="valid_response_time"),
    )

class BusinessEvent(BaseModel, TimestampMixin):
    """Business process events and workflow tracking"""
    __tablename__ = "business_events"
    
    # Event identification
    event_id = Column(String(100), nullable=False, unique=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # batch_start, batch_complete, test_start, approval
    event_name = Column(String(200), nullable=False)
    event_description = Column(Text, nullable=False)
    
    # Business process
    process_name = Column(String(100), nullable=False)
    process_stage = Column(String(100), nullable=False)
    process_status = Column(String(50), nullable=False)
    
    # Entity relationships
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    lot_id = Column(UUID(as_uuid=True), nullable=True)
    material_id = Column(UUID(as_uuid=True), nullable=True)
    equipment_id = Column(UUID(as_uuid=True), nullable=True)
    
    # User information
    initiated_by = Column(UUID(as_uuid=True), nullable=False)
    performed_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Workflow
    workflow_id = Column(String(100), nullable=True)
    workflow_step = Column(String(100), nullable=True)
    next_step = Column(String(100), nullable=True)
    
    # Business data
    event_data = Column(JSON, nullable=True)
    business_metrics = Column(JSON, nullable=True)
    
    # Duration tracking
    duration_minutes = Column(Float, nullable=True)
    planned_duration = Column(Float, nullable=True)
    variance_percentage = Column(Float, nullable=True)
    
    # Quality impact
    quality_impact = Column(String(50), nullable=False, default="none")
    quality_review_required = Column(Boolean, nullable=False, default=False)
    
    # Compliance
    regulatory_significant = Column(Boolean, nullable=False, default=False)
    gmp_critical = Column(Boolean, nullable=False, default=False)
    
    # Outcome
    event_outcome = Column(String(50), nullable=False)  # success, failure, partial, cancelled
    outcome_description = Column(Text, nullable=True)
    
    # Monitoring
    kpi_impact = Column(JSON, nullable=True)
    alert_conditions = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_business_event_id', 'event_id'),
        Index('idx_business_event_type', 'event_type'),
        Index('idx_business_process', 'process_name'),
        Index('idx_business_stage', 'process_stage'),
        Index('idx_business_status', 'process_status'),
        Index('idx_business_batch', 'batch_id'),
        Index('idx_business_initiated_by', 'initiated_by'),
        Index('idx_business_timestamp', 'timestamp'),
        Index('idx_business_workflow', 'workflow_id'),
        Index('idx_business_outcome', 'event_outcome'),
        Index('idx_business_regulatory', 'regulatory_significant'),
        Index('idx_business_gmp', 'gmp_critical'),
        CheckConstraint("event_type IN ('batch_start', 'batch_complete', 'test_start', 'approval', 'deviation', 'investigation')", name="valid_business_event_type"),
        CheckConstraint("process_status IN ('pending', 'in_progress', 'completed', 'cancelled', 'failed')", name="valid_process_status"),
        CheckConstraint("quality_impact IN ('none', 'low', 'medium', 'high', 'critical')", name="valid_quality_impact"),
        CheckConstraint("event_outcome IN ('success', 'failure', 'partial', 'cancelled')", name="valid_event_outcome"),
        CheckConstraint("duration_minutes IS NULL OR duration_minutes >= 0", name="non_negative_duration"),
        CheckConstraint("planned_duration IS NULL OR planned_duration >= 0", name="non_negative_planned_duration"),
    )

class AuditReport(BaseModel, StatusMixin, ApprovalMixin):
    """Audit reports and compliance documentation"""
    __tablename__ = "audit_reports"
    
    # Report identification
    report_id = Column(String(100), nullable=False, unique=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, annual, ad_hoc
    report_title = Column(String(200), nullable=False)
    
    # Reporting period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Scope
    scope_description = Column(Text, nullable=False)
    systems_included = Column(JSON, nullable=False)
    processes_included = Column(JSON, nullable=False)
    
    # Report content
    summary_statistics = Column(JSON, nullable=False)
    key_findings = Column(JSON, nullable=True)
    compliance_status = Column(String(50), nullable=False)
    
    # Analysis
    trend_analysis = Column(JSON, nullable=True)
    risk_assessment = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Generation
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    generation_date = Column(DateTime(timezone=True), nullable=False)
    generation_method = Column(String(50), nullable=False)  # automated, manual, hybrid
    
    # Review process
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    review_comments = Column(Text, nullable=True)
    
    # Distribution
    distribution_list = Column(JSON, nullable=False)
    external_submission = Column(Boolean, nullable=False, default=False)
    regulatory_authority = Column(String(100), nullable=True)
    
    # File information
    report_file_path = Column(String(500), nullable=True)
    report_format = Column(String(20), nullable=False, default="PDF")
    file_size_bytes = Column(Integer, nullable=True)
    
    # Retention
    retention_period_years = Column(Integer, nullable=False, default=7)
    archive_date = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_audit_report_id', 'report_id'),
        Index('idx_audit_report_type', 'report_type'),
        Index('idx_audit_period', 'period_start', 'period_end'),
        Index('idx_audit_compliance_status', 'compliance_status'),
        Index('idx_audit_generated_by', 'generated_by'),
        Index('idx_audit_generation_date', 'generation_date'),
        Index('idx_audit_external_submission', 'external_submission'),
        CheckConstraint("report_type IN ('daily', 'weekly', 'monthly', 'annual', 'ad_hoc')", name="valid_audit_report_type"),
        CheckConstraint("compliance_status IN ('compliant', 'non_compliant', 'conditional', 'under_review')", name="valid_compliance_status"),
        CheckConstraint("generation_method IN ('automated', 'manual', 'hybrid')", name="valid_generation_method"),
        CheckConstraint("report_format IN ('PDF', 'Excel', 'Word', 'CSV', 'JSON')", name="valid_report_format"),
        CheckConstraint("period_start <= period_end", name="valid_reporting_period"),
        CheckConstraint("retention_period_years > 0", name="positive_retention_period"),
        CheckConstraint("file_size_bytes IS NULL OR file_size_bytes > 0", name="positive_file_size"),
    )

class AuditTrailArchive(BaseModel):
    """Archived audit trail records for long-term retention"""
    __tablename__ = "audit_trail_archive"
    
    # Archive identification
    archive_id = Column(String(100), nullable=False, unique=True)
    
    # Original audit trail reference
    original_audit_id = Column(String(100), nullable=False)
    
    # Archive details
    archive_date = Column(DateTime(timezone=True), nullable=False)
    archive_reason = Column(String(100), nullable=False)
    
    # Archived data
    archived_data = Column(JSON, nullable=False)
    data_integrity_hash = Column(String(64), nullable=False)
    
    # Retention information
    retention_period_years = Column(Integer, nullable=False)
    destroy_date = Column(DateTime(timezone=True), nullable=True)
    
    # Access control
    access_restricted = Column(Boolean, nullable=False, default=True)
    access_approval_required = Column(Boolean, nullable=False, default=True)
    
    # Regulatory compliance
    regulatory_requirement = Column(String(200), nullable=True)
    legal_hold = Column(Boolean, nullable=False, default=False)
    
    # Storage information
    storage_location = Column(String(200), nullable=False)
    storage_medium = Column(String(50), nullable=False)
    compression_used = Column(Boolean, nullable=False, default=True)
    
    __table_args__ = (
        Index('idx_archive_id', 'archive_id'),
        Index('idx_original_audit_id', 'original_audit_id'),
        Index('idx_archive_date', 'archive_date'),
        Index('idx_destroy_date', 'destroy_date'),
        Index('idx_legal_hold', 'legal_hold'),
        Index('idx_access_restricted', 'access_restricted'),
        CheckConstraint("archive_reason IN ('routine', 'space_management', 'regulatory', 'legal_hold')", name="valid_archive_reason"),
        CheckConstraint("storage_medium IN ('database', 'file_system', 'tape', 'cloud')", name="valid_storage_medium"),
        CheckConstraint("retention_period_years > 0", name="positive_archive_retention"),
    )
    
    def verify_archive_integrity(self) -> bool:
        """Verify archived data integrity"""
        if not self.archived_data:
            return False
        
        data_string = json.dumps(self.archived_data, sort_keys=True)
        calculated_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        return calculated_hash == self.data_integrity_hash