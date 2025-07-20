"""
Deviation and CAPA Tracking Models
Comprehensive deviation management and corrective/preventive action tracking for pharmaceutical manufacturing
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional
import secrets

from .base import BaseModel, TimestampMixin, StatusMixin, ApprovalMixin

class DeviationType(BaseModel):
    """Deviation type master data"""
    __tablename__ = "deviation_types"
    
    # Type identification
    type_code = Column(String(50), nullable=False, unique=True)
    type_name = Column(String(200), nullable=False)
    type_description = Column(Text, nullable=False)
    
    # Category
    category = Column(String(100), nullable=False)  # process, equipment, material, testing, environmental
    subcategory = Column(String(100), nullable=True)
    
    # Severity classification
    default_severity = Column(String(20), nullable=False, default="medium")
    risk_level = Column(String(20), nullable=False, default="medium")
    
    # Investigation requirements
    investigation_required = Column(Boolean, nullable=False, default=True)
    investigation_timeline_days = Column(Integer, nullable=False, default=30)
    
    # Approval requirements
    approval_required = Column(Boolean, nullable=False, default=True)
    approval_level = Column(String(50), nullable=False, default="supervisor")
    
    # Regulatory impact
    regulatory_reportable = Column(Boolean, nullable=False, default=False)
    regulatory_timeline_days = Column(Integer, nullable=True)
    
    # CAPA requirements
    capa_required = Column(Boolean, nullable=False, default=True)
    capa_timeline_days = Column(Integer, nullable=False, default=90)
    
    # Workflow
    workflow_template = Column(JSON, nullable=True)
    escalation_rules = Column(JSON, nullable=True)
    
    # Relationships
    deviations = relationship("Deviation", back_populates="deviation_type")
    
    __table_args__ = (
        Index('idx_deviation_type_code', 'type_code'),
        Index('idx_deviation_type_name', 'type_name'),
        Index('idx_deviation_category', 'category'),
        Index('idx_default_severity', 'default_severity'),
        Index('idx_regulatory_reportable', 'regulatory_reportable'),
        CheckConstraint("category IN ('process', 'equipment', 'material', 'testing', 'environmental', 'documentation')", name="valid_deviation_category"),
        CheckConstraint("default_severity IN ('low', 'medium', 'high', 'critical')", name="valid_default_severity"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", name="valid_risk_level"),
        CheckConstraint("approval_level IN ('supervisor', 'manager', 'director', 'qa_manager')", name="valid_approval_level"),
        CheckConstraint("investigation_timeline_days > 0", name="positive_investigation_timeline"),
        CheckConstraint("capa_timeline_days > 0", name="positive_capa_timeline"),
    )

class Deviation(BaseModel, StatusMixin, ApprovalMixin):
    """Deviation tracking and management"""
    __tablename__ = "deviations"
    
    # Deviation identification
    deviation_number = Column(String(100), nullable=False, unique=True)
    
    # Deviation type relationship
    deviation_type_id = Column(UUID(as_uuid=True), ForeignKey('deviation_types.id'), nullable=False)
    deviation_type = relationship("DeviationType", back_populates="deviations")
    
    # Deviation details
    deviation_title = Column(String(300), nullable=False)
    deviation_description = Column(Text, nullable=False)
    
    # Discovery information
    discovered_at = Column(DateTime(timezone=True), nullable=False)
    discovered_by = Column(UUID(as_uuid=True), nullable=False)
    discovery_method = Column(String(100), nullable=False)
    
    # Location and context
    location = Column(String(200), nullable=False)
    department = Column(String(100), nullable=False)
    
    # Entity relationships
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    lot_id = Column(UUID(as_uuid=True), nullable=True)
    material_id = Column(UUID(as_uuid=True), nullable=True)
    equipment_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Classification
    severity = Column(String(20), nullable=False)
    priority = Column(String(20), nullable=False)
    impact_assessment = Column(String(50), nullable=False)
    
    # Root cause analysis
    root_cause_analysis_required = Column(Boolean, nullable=False, default=True)
    root_cause_analysis_completed = Column(Boolean, nullable=False, default=False)
    root_cause_identified = Column(Boolean, nullable=False, default=False)
    root_cause_description = Column(Text, nullable=True)
    root_cause_category = Column(String(100), nullable=True)
    
    # Investigation
    investigation_required = Column(Boolean, nullable=False, default=True)
    investigation_assigned_to = Column(UUID(as_uuid=True), nullable=True)
    investigation_start_date = Column(DateTime(timezone=True), nullable=True)
    investigation_due_date = Column(DateTime(timezone=True), nullable=True)
    investigation_completed = Column(Boolean, nullable=False, default=False)
    investigation_completion_date = Column(DateTime(timezone=True), nullable=True)
    investigation_findings = Column(Text, nullable=True)
    
    # Impact assessment
    product_impact = Column(Boolean, nullable=False, default=False)
    affected_batches = Column(JSON, nullable=True)
    affected_lots = Column(JSON, nullable=True)
    customer_impact = Column(Boolean, nullable=False, default=False)
    
    # Immediate actions
    immediate_actions_taken = Column(Text, nullable=True)
    immediate_actions_effective = Column(Boolean, nullable=True)
    
    # Containment
    containment_required = Column(Boolean, nullable=False, default=False)
    containment_actions = Column(JSON, nullable=True)
    containment_effective = Column(Boolean, nullable=True)
    
    # Regulatory impact
    regulatory_reportable = Column(Boolean, nullable=False, default=False)
    regulatory_authority = Column(String(100), nullable=True)
    regulatory_report_due = Column(DateTime(timezone=True), nullable=True)
    regulatory_report_submitted = Column(Boolean, nullable=False, default=False)
    
    # CAPA requirements
    capa_required = Column(Boolean, nullable=False, default=True)
    capa_created = Column(Boolean, nullable=False, default=False)
    capa_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolution_date = Column(DateTime(timezone=True), nullable=True)
    resolution_description = Column(Text, nullable=True)
    
    # Effectiveness verification
    effectiveness_check_required = Column(Boolean, nullable=False, default=True)
    effectiveness_check_completed = Column(Boolean, nullable=False, default=False)
    effectiveness_check_date = Column(DateTime(timezone=True), nullable=True)
    effectiveness_verified = Column(Boolean, nullable=True)
    
    # Cost impact
    cost_impact_estimated = Column(Float, nullable=True)
    cost_impact_actual = Column(Float, nullable=True)
    cost_impact_currency = Column(String(3), nullable=False, default="USD")
    
    # Trend analysis
    recurring_deviation = Column(Boolean, nullable=False, default=False)
    previous_occurrences = Column(Integer, nullable=False, default=0)
    trend_analysis_required = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    capa_actions = relationship("CAPA", back_populates="deviation")
    investigation_team = relationship("DeviationInvestigation", back_populates="deviation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_deviation_number', 'deviation_number'),
        Index('idx_deviation_type', 'deviation_type_id'),
        Index('idx_discovered_at', 'discovered_at'),
        Index('idx_discovered_by', 'discovered_by'),
        Index('idx_severity', 'severity'),
        Index('idx_priority', 'priority'),
        Index('idx_batch_deviation', 'batch_id'),
        Index('idx_investigation_required', 'investigation_required'),
        Index('idx_investigation_completed', 'investigation_completed'),
        Index('idx_capa_required', 'capa_required'),
        Index('idx_resolved', 'resolved'),
        Index('idx_regulatory_reportable', 'regulatory_reportable'),
        Index('idx_recurring_deviation', 'recurring_deviation'),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="valid_severity"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="valid_priority"),
        CheckConstraint("impact_assessment IN ('none', 'low', 'medium', 'high', 'critical')", name="valid_impact_assessment"),
        CheckConstraint("discovery_method IN ('routine_inspection', 'audit', 'customer_complaint', 'testing', 'monitoring')", name="valid_discovery_method"),
        CheckConstraint("cost_impact_estimated IS NULL OR cost_impact_estimated >= 0", name="non_negative_estimated_cost"),
        CheckConstraint("cost_impact_actual IS NULL OR cost_impact_actual >= 0", name="non_negative_actual_cost"),
        CheckConstraint("previous_occurrences >= 0", name="non_negative_previous_occurrences"),
        CheckConstraint("investigation_start_date IS NULL OR investigation_due_date IS NULL OR investigation_start_date <= investigation_due_date", name="valid_investigation_dates"),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generate_deviation_number()
    
    def generate_deviation_number(self):
        """Generate unique deviation number"""
        if not self.deviation_number:
            year = datetime.now().year
            timestamp = datetime.now().strftime("%m%d%H%M")
            self.deviation_number = f"DEV-{year}-{timestamp}-{secrets.token_hex(3).upper()}"
    
    def calculate_risk_score(self) -> float:
        """Calculate risk score based on severity and impact"""
        severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        impact_weights = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        
        severity_score = severity_weights.get(self.severity, 2)
        impact_score = impact_weights.get(self.impact_assessment, 2)
        
        # Additional factors
        regulatory_factor = 1.5 if self.regulatory_reportable else 1.0
        product_factor = 1.3 if self.product_impact else 1.0
        recurring_factor = 1.2 if self.recurring_deviation else 1.0
        
        risk_score = (severity_score * impact_score * regulatory_factor * 
                     product_factor * recurring_factor)
        
        return min(100, risk_score * 6.25)  # Scale to 0-100
    
    def is_overdue(self) -> bool:
        """Check if deviation investigation is overdue"""
        if not self.investigation_due_date or self.investigation_completed:
            return False
        
        return datetime.now(timezone.utc) > self.investigation_due_date.replace(tzinfo=timezone.utc)

class DeviationInvestigation(BaseModel, StatusMixin):
    """Deviation investigation team and activities"""
    __tablename__ = "deviation_investigations"
    
    # Investigation identification
    investigation_id = Column(String(100), nullable=False, unique=True)
    
    # Deviation relationship
    deviation_id = Column(UUID(as_uuid=True), ForeignKey('deviations.id'), nullable=False)
    deviation = relationship("Deviation", back_populates="investigation_team")
    
    # Investigation details
    investigation_type = Column(String(50), nullable=False)  # phase1, phase2, full_investigation, trend_analysis
    investigation_scope = Column(Text, nullable=False)
    investigation_methodology = Column(Text, nullable=False)
    
    # Team composition
    investigation_leader = Column(UUID(as_uuid=True), nullable=False)
    team_members = Column(JSON, nullable=False)
    subject_matter_experts = Column(JSON, nullable=True)
    
    # Timeline
    planned_start_date = Column(DateTime(timezone=True), nullable=False)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    planned_completion_date = Column(DateTime(timezone=True), nullable=False)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Investigation activities
    data_collection_completed = Column(Boolean, nullable=False, default=False)
    interviews_completed = Column(Boolean, nullable=False, default=False)
    testing_completed = Column(Boolean, nullable=False, default=False)
    analysis_completed = Column(Boolean, nullable=False, default=False)
    
    # Findings
    investigation_findings = Column(Text, nullable=True)
    evidence_collected = Column(JSON, nullable=True)
    witness_statements = Column(JSON, nullable=True)
    
    # Root cause analysis
    root_cause_analysis_method = Column(String(100), nullable=False)
    root_causes_identified = Column(JSON, nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    
    # Conclusions
    investigation_conclusions = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Quality assurance
    peer_review_required = Column(Boolean, nullable=False, default=True)
    peer_review_completed = Column(Boolean, nullable=False, default=False)
    peer_reviewer = Column(UUID(as_uuid=True), nullable=True)
    peer_review_comments = Column(Text, nullable=True)
    
    # Documentation
    investigation_report = Column(String(500), nullable=True)
    supporting_documents = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_investigation_id', 'investigation_id'),
        Index('idx_investigation_deviation', 'deviation_id'),
        Index('idx_investigation_type', 'investigation_type'),
        Index('idx_investigation_leader', 'investigation_leader'),
        Index('idx_planned_start_date', 'planned_start_date'),
        Index('idx_planned_completion_date', 'planned_completion_date'),
        Index('idx_peer_review_required', 'peer_review_required'),
        Index('idx_peer_review_completed', 'peer_review_completed'),
        CheckConstraint("investigation_type IN ('phase1', 'phase2', 'full_investigation', 'trend_analysis')", name="valid_investigation_type"),
        CheckConstraint("root_cause_analysis_method IN ('5_why', 'fishbone', 'fault_tree', 'failure_mode', 'pareto')", name="valid_rca_method"),
        CheckConstraint("planned_start_date <= planned_completion_date", name="valid_planned_investigation_dates"),
        CheckConstraint("actual_start_date IS NULL OR actual_completion_date IS NULL OR actual_start_date <= actual_completion_date", name="valid_actual_investigation_dates"),
    )

class CAPA(BaseModel, StatusMixin, ApprovalMixin):
    """Corrective and Preventive Action tracking"""
    __tablename__ = "capa"
    
    # CAPA identification
    capa_number = Column(String(100), nullable=False, unique=True)
    
    # Source deviation relationship
    deviation_id = Column(UUID(as_uuid=True), ForeignKey('deviations.id'), nullable=True)
    deviation = relationship("Deviation", back_populates="capa_actions")
    
    # CAPA details
    capa_title = Column(String(300), nullable=False)
    capa_description = Column(Text, nullable=False)
    capa_type = Column(String(50), nullable=False)  # corrective, preventive, both
    
    # Initiation
    initiated_by = Column(UUID(as_uuid=True), nullable=False)
    initiation_date = Column(DateTime(timezone=True), nullable=False)
    initiation_reason = Column(Text, nullable=False)
    
    # Classification
    priority = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)
    complexity = Column(String(20), nullable=False)
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), nullable=False)
    capa_owner = Column(UUID(as_uuid=True), nullable=False)
    capa_team = Column(JSON, nullable=True)
    
    # Root cause
    root_cause_description = Column(Text, nullable=False)
    root_cause_category = Column(String(100), nullable=False)
    
    # Actions
    corrective_actions = Column(JSON, nullable=True)
    preventive_actions = Column(JSON, nullable=True)
    
    # Timeline
    target_completion_date = Column(DateTime(timezone=True), nullable=False)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Implementation
    implementation_plan = Column(Text, nullable=False)
    implementation_status = Column(String(50), nullable=False, default="planned")
    implementation_progress = Column(Float, nullable=False, default=0.0)
    
    # Resources
    resource_requirements = Column(JSON, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    cost_currency = Column(String(3), nullable=False, default="USD")
    
    # Verification
    verification_method = Column(String(100), nullable=False)
    verification_criteria = Column(Text, nullable=False)
    verification_completed = Column(Boolean, nullable=False, default=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_results = Column(Text, nullable=True)
    
    # Effectiveness
    effectiveness_review_required = Column(Boolean, nullable=False, default=True)
    effectiveness_review_date = Column(DateTime(timezone=True), nullable=True)
    effectiveness_verified = Column(Boolean, nullable=True)
    effectiveness_comments = Column(Text, nullable=True)
    
    # Monitoring
    monitoring_required = Column(Boolean, nullable=False, default=True)
    monitoring_period_months = Column(Integer, nullable=True)
    monitoring_frequency = Column(String(50), nullable=True)
    monitoring_metrics = Column(JSON, nullable=True)
    
    # Closure
    closed = Column(Boolean, nullable=False, default=False)
    closure_date = Column(DateTime(timezone=True), nullable=True)
    closure_approved_by = Column(UUID(as_uuid=True), nullable=True)
    closure_comments = Column(Text, nullable=True)
    
    # Regulatory impact
    regulatory_notification_required = Column(Boolean, nullable=False, default=False)
    regulatory_authority = Column(String(100), nullable=True)
    regulatory_notification_sent = Column(Boolean, nullable=False, default=False)
    
    # Related CAPAs
    parent_capa_id = Column(UUID(as_uuid=True), ForeignKey('capa.id'), nullable=True)
    parent_capa = relationship("CAPA", remote_side="CAPA.id")
    
    # Relationships
    action_items = relationship("CAPAAction", back_populates="capa", cascade="all, delete-orphan")
    monitoring_records = relationship("CAPAMonitoring", back_populates="capa", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_capa_number', 'capa_number'),
        Index('idx_capa_deviation', 'deviation_id'),
        Index('idx_capa_type', 'capa_type'),
        Index('idx_initiated_by', 'initiated_by'),
        Index('idx_assigned_to', 'assigned_to'),
        Index('idx_capa_owner', 'capa_owner'),
        Index('idx_priority', 'priority'),
        Index('idx_severity', 'severity'),
        Index('idx_implementation_status', 'implementation_status'),
        Index('idx_target_completion_date', 'target_completion_date'),
        Index('idx_verification_completed', 'verification_completed'),
        Index('idx_effectiveness_verified', 'effectiveness_verified'),
        Index('idx_closed', 'closed'),
        Index('idx_parent_capa', 'parent_capa_id'),
        CheckConstraint("capa_type IN ('corrective', 'preventive', 'both')", name="valid_capa_type"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="valid_capa_priority"),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="valid_capa_severity"),
        CheckConstraint("complexity IN ('low', 'medium', 'high')", name="valid_complexity"),
        CheckConstraint("implementation_status IN ('planned', 'in_progress', 'completed', 'on_hold', 'cancelled')", name="valid_implementation_status"),
        CheckConstraint("implementation_progress >= 0 AND implementation_progress <= 100", name="valid_implementation_progress"),
        CheckConstraint("estimated_cost IS NULL OR estimated_cost >= 0", name="non_negative_estimated_cost"),
        CheckConstraint("actual_cost IS NULL OR actual_cost >= 0", name="non_negative_actual_cost"),
        CheckConstraint("monitoring_period_months IS NULL OR monitoring_period_months > 0", name="positive_monitoring_period"),
        CheckConstraint("monitoring_frequency IS NULL OR monitoring_frequency IN ('daily', 'weekly', 'monthly', 'quarterly')", name="valid_monitoring_frequency"),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generate_capa_number()
    
    def generate_capa_number(self):
        """Generate unique CAPA number"""
        if not self.capa_number:
            year = datetime.now().year
            timestamp = datetime.now().strftime("%m%d%H%M")
            self.capa_number = f"CAPA-{year}-{timestamp}-{secrets.token_hex(3).upper()}"
    
    def calculate_completion_percentage(self) -> float:
        """Calculate CAPA completion percentage"""
        if not self.action_items:
            return self.implementation_progress
        
        completed_actions = sum(1 for action in self.action_items if action.completed)
        total_actions = len(self.action_items)
        
        if total_actions == 0:
            return self.implementation_progress
        
        return (completed_actions / total_actions) * 100
    
    def is_overdue(self) -> bool:
        """Check if CAPA is overdue"""
        if self.closed or not self.target_completion_date:
            return False
        
        return datetime.now(timezone.utc) > self.target_completion_date.replace(tzinfo=timezone.utc)

class CAPAAction(BaseModel, StatusMixin):
    """Individual action items within a CAPA"""
    __tablename__ = "capa_actions"
    
    # Action identification
    action_id = Column(String(100), nullable=False, unique=True)
    
    # CAPA relationship
    capa_id = Column(UUID(as_uuid=True), ForeignKey('capa.id'), nullable=False)
    capa = relationship("CAPA", back_populates="action_items")
    
    # Action details
    action_description = Column(Text, nullable=False)
    action_type = Column(String(50), nullable=False)  # corrective, preventive, verification, monitoring
    action_category = Column(String(100), nullable=False)
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), nullable=False)
    responsible_department = Column(String(100), nullable=False)
    
    # Timeline
    due_date = Column(DateTime(timezone=True), nullable=False)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Implementation
    implementation_plan = Column(Text, nullable=False)
    implementation_status = Column(String(50), nullable=False, default="not_started")
    progress_percentage = Column(Float, nullable=False, default=0.0)
    
    # Resources
    resource_requirements = Column(JSON, nullable=True)
    estimated_effort_hours = Column(Float, nullable=True)
    actual_effort_hours = Column(Float, nullable=True)
    
    # Completion
    completed = Column(Boolean, nullable=False, default=False)
    completion_evidence = Column(Text, nullable=True)
    supporting_documents = Column(JSON, nullable=True)
    
    # Verification
    verification_required = Column(Boolean, nullable=False, default=True)
    verification_method = Column(String(100), nullable=True)
    verification_completed = Column(Boolean, nullable=False, default=False)
    verification_results = Column(Text, nullable=True)
    
    # Dependencies
    depends_on = Column(JSON, nullable=True)
    blocks = Column(JSON, nullable=True)
    
    # Notes and comments
    progress_notes = Column(Text, nullable=True)
    completion_comments = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_action_id', 'action_id'),
        Index('idx_capa_action', 'capa_id'),
        Index('idx_action_type', 'action_type'),
        Index('idx_assigned_to', 'assigned_to'),
        Index('idx_due_date', 'due_date'),
        Index('idx_implementation_status', 'implementation_status'),
        Index('idx_completed', 'completed'),
        Index('idx_verification_required', 'verification_required'),
        Index('idx_verification_completed', 'verification_completed'),
        CheckConstraint("action_type IN ('corrective', 'preventive', 'verification', 'monitoring')", name="valid_action_type"),
        CheckConstraint("implementation_status IN ('not_started', 'in_progress', 'completed', 'on_hold', 'cancelled')", name="valid_action_implementation_status"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="valid_progress_percentage"),
        CheckConstraint("estimated_effort_hours IS NULL OR estimated_effort_hours >= 0", name="non_negative_estimated_effort"),
        CheckConstraint("actual_effort_hours IS NULL OR actual_effort_hours >= 0", name="non_negative_actual_effort"),
    )
    
    def is_overdue(self) -> bool:
        """Check if action is overdue"""
        if self.completed or not self.due_date:
            return False
        
        return datetime.now(timezone.utc) > self.due_date.replace(tzinfo=timezone.utc)

class CAPAMonitoring(BaseModel, TimestampMixin):
    """CAPA effectiveness monitoring records"""
    __tablename__ = "capa_monitoring"
    
    # Monitoring identification
    monitoring_id = Column(String(100), nullable=False, unique=True)
    
    # CAPA relationship
    capa_id = Column(UUID(as_uuid=True), ForeignKey('capa.id'), nullable=False)
    capa = relationship("CAPA", back_populates="monitoring_records")
    
    # Monitoring details
    monitoring_date = Column(DateTime(timezone=True), nullable=False)
    monitoring_type = Column(String(50), nullable=False)  # scheduled, ad_hoc, follow_up
    monitoring_period = Column(String(50), nullable=False)
    
    # Metrics
    metrics_measured = Column(JSON, nullable=False)
    baseline_values = Column(JSON, nullable=True)
    current_values = Column(JSON, nullable=False)
    target_values = Column(JSON, nullable=False)
    
    # Assessment
    effectiveness_rating = Column(String(20), nullable=False)  # effective, partially_effective, ineffective
    improvement_observed = Column(Boolean, nullable=False, default=False)
    trend_analysis = Column(JSON, nullable=True)
    
    # Findings
    monitoring_findings = Column(Text, nullable=True)
    gaps_identified = Column(JSON, nullable=True)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)
    additional_actions_required = Column(Boolean, nullable=False, default=False)
    
    # Personnel
    monitored_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Next monitoring
    next_monitoring_date = Column(DateTime(timezone=True), nullable=True)
    monitoring_frequency = Column(String(50), nullable=True)
    
    __table_args__ = (
        Index('idx_monitoring_id', 'monitoring_id'),
        Index('idx_monitoring_capa', 'capa_id'),
        Index('idx_monitoring_date', 'monitoring_date'),
        Index('idx_monitoring_type', 'monitoring_type'),
        Index('idx_effectiveness_rating', 'effectiveness_rating'),
        Index('idx_monitored_by', 'monitored_by'),
        Index('idx_next_monitoring_date', 'next_monitoring_date'),
        Index('idx_additional_actions_required', 'additional_actions_required'),
        CheckConstraint("monitoring_type IN ('scheduled', 'ad_hoc', 'follow_up')", name="valid_monitoring_type"),
        CheckConstraint("effectiveness_rating IN ('effective', 'partially_effective', 'ineffective', 'too_early')", name="valid_effectiveness_rating"),
        CheckConstraint("monitoring_frequency IS NULL OR monitoring_frequency IN ('daily', 'weekly', 'monthly', 'quarterly')", name="valid_monitoring_frequency"),
    )

class DeviationTrend(BaseModel, TimestampMixin):
    """Deviation trend analysis and patterns"""
    __tablename__ = "deviation_trends"
    
    # Trend identification
    trend_id = Column(String(100), nullable=False, unique=True)
    trend_name = Column(String(200), nullable=False)
    
    # Analysis period
    analysis_period = Column(String(50), nullable=False)  # monthly, quarterly, annual
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Scope
    deviation_types = Column(JSON, nullable=False)
    departments = Column(JSON, nullable=True)
    products = Column(JSON, nullable=True)
    
    # Statistics
    total_deviations = Column(Integer, nullable=False)
    previous_period_deviations = Column(Integer, nullable=True)
    percentage_change = Column(Float, nullable=True)
    
    # Categorization
    deviation_by_type = Column(JSON, nullable=False)
    deviation_by_severity = Column(JSON, nullable=False)
    deviation_by_department = Column(JSON, nullable=False)
    
    # Trends
    trend_direction = Column(String(20), nullable=False)  # increasing, decreasing, stable
    trend_significance = Column(String(20), nullable=False)  # significant, not_significant
    
    # Root cause analysis
    top_root_causes = Column(JSON, nullable=False)
    recurring_issues = Column(JSON, nullable=True)
    
    # CAPA effectiveness
    capa_effectiveness = Column(JSON, nullable=True)
    outstanding_capas = Column(Integer, nullable=False, default=0)
    
    # Recommendations
    trend_recommendations = Column(JSON, nullable=True)
    priority_actions = Column(JSON, nullable=True)
    
    # Report generation
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_trend_id', 'trend_id'),
        Index('idx_trend_name', 'trend_name'),
        Index('idx_analysis_period', 'analysis_period'),
        Index('idx_period_start', 'period_start'),
        Index('idx_trend_direction', 'trend_direction'),
        Index('idx_trend_significance', 'trend_significance'),
        Index('idx_generated_by', 'generated_by'),
        CheckConstraint("analysis_period IN ('monthly', 'quarterly', 'annual')", name="valid_analysis_period"),
        CheckConstraint("trend_direction IN ('increasing', 'decreasing', 'stable')", name="valid_trend_direction"),
        CheckConstraint("trend_significance IN ('significant', 'not_significant')", name="valid_trend_significance"),
        CheckConstraint("total_deviations >= 0", name="non_negative_total_deviations"),
        CheckConstraint("previous_period_deviations IS NULL OR previous_period_deviations >= 0", name="non_negative_previous_deviations"),
        CheckConstraint("outstanding_capas >= 0", name="non_negative_outstanding_capas"),
        CheckConstraint("period_start <= period_end", name="valid_trend_period"),
    )