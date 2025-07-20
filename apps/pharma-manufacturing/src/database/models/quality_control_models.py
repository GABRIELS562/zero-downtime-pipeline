"""
Quality Control Testing Models
Comprehensive testing and quality assurance data models for pharmaceutical manufacturing
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional
from decimal import Decimal

from .base import BaseModel, TimestampMixin, StatusMixin, ApprovalMixin, TestResultMixin

class TestType(BaseModel):
    """Test type master data"""
    __tablename__ = "test_types"
    
    # Test type information
    test_type_code = Column(String(50), nullable=False, unique=True)
    test_type_name = Column(String(200), nullable=False)
    test_category = Column(String(100), nullable=False)  # analytical, microbiological, physical, chemical
    
    # Test requirements
    test_frequency = Column(String(50), nullable=False)  # per_batch, per_lot, periodic, skip_lot
    regulatory_requirement = Column(Boolean, nullable=False, default=True)
    
    # Test parameters
    standard_test_method = Column(String(100), nullable=False)
    test_procedure = Column(String(200), nullable=False)
    
    # Specifications
    default_specifications = Column(JSON, nullable=False)
    
    # Laboratory requirements
    laboratory_type = Column(String(50), nullable=False)  # in_house, contract, both
    required_equipment = Column(JSON, nullable=True)
    
    # Timing requirements
    standard_test_duration_hours = Column(Float, nullable=False)
    sample_stability_hours = Column(Float, nullable=True)
    
    # Quality requirements
    accuracy_requirement = Column(Float, nullable=True)
    precision_requirement = Column(Float, nullable=True)
    
    # Relationships
    test_plans = relationship("TestPlan", back_populates="test_type")
    test_results = relationship("QualityTestResult", back_populates="test_type")
    
    __table_args__ = (
        Index('idx_test_type_code', 'test_type_code'),
        Index('idx_test_category', 'test_category'),
        Index('idx_test_frequency', 'test_frequency'),
        Index('idx_laboratory_type', 'laboratory_type'),
        CheckConstraint("test_category IN ('analytical', 'microbiological', 'physical', 'chemical')", name="valid_test_category"),
        CheckConstraint("test_frequency IN ('per_batch', 'per_lot', 'periodic', 'skip_lot')", name="valid_test_frequency"),
        CheckConstraint("laboratory_type IN ('in_house', 'contract', 'both')", name="valid_laboratory_type"),
        CheckConstraint("standard_test_duration_hours > 0", name="positive_test_duration"),
        CheckConstraint("accuracy_requirement IS NULL OR accuracy_requirement > 0", name="positive_accuracy"),
        CheckConstraint("precision_requirement IS NULL OR precision_requirement > 0", name="positive_precision"),
    )

class TestPlan(BaseModel, StatusMixin, ApprovalMixin):
    """Test plan definitions for products and materials"""
    __tablename__ = "test_plans"
    
    # Plan identification
    plan_number = Column(String(100), nullable=False, unique=True)
    plan_name = Column(String(200), nullable=False)
    plan_version = Column(String(20), nullable=False, default="1.0")
    
    # Test type relationship
    test_type_id = Column(UUID(as_uuid=True), ForeignKey('test_types.id'), nullable=False)
    test_type = relationship("TestType", back_populates="test_plans")
    
    # Product/Material applicability
    product_id = Column(UUID(as_uuid=True), nullable=True)
    material_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Testing requirements
    sampling_requirements = Column(JSON, nullable=False)
    test_specifications = Column(JSON, nullable=False)
    
    # Analytical method
    analytical_method = Column(String(100), nullable=False)
    method_validation_status = Column(String(50), nullable=False, default="pending")
    
    # Timing requirements
    test_frequency = Column(String(50), nullable=False)
    test_schedule = Column(JSON, nullable=True)
    
    # Laboratory assignment
    assigned_laboratory = Column(String(200), nullable=False)
    backup_laboratory = Column(String(200), nullable=True)
    
    # Quality requirements
    acceptance_criteria = Column(JSON, nullable=False)
    critical_quality_attributes = Column(JSON, nullable=True)
    
    # Regulatory information
    regulatory_references = Column(JSON, nullable=True)
    compendial_method = Column(String(100), nullable=True)
    
    # Effective dates
    effective_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    test_results = relationship("QualityTestResult", back_populates="test_plan")
    
    __table_args__ = (
        Index('idx_plan_number', 'plan_number'),
        Index('idx_plan_test_type', 'test_type_id'),
        Index('idx_plan_product', 'product_id'),
        Index('idx_plan_material', 'material_id'),
        Index('idx_effective_date', 'effective_date'),
        Index('idx_method_validation_status', 'method_validation_status'),
        CheckConstraint("method_validation_status IN ('pending', 'in_progress', 'completed', 'failed')", name="valid_method_validation_status"),
        CheckConstraint("test_frequency IN ('per_batch', 'per_lot', 'periodic', 'skip_lot')", name="valid_test_frequency"),
        CheckConstraint("effective_date <= expiry_date OR expiry_date IS NULL", name="valid_plan_dates"),
        CheckConstraint("product_id IS NOT NULL OR material_id IS NOT NULL", name="product_or_material_required"),
    )

class Laboratory(BaseModel, StatusMixin):
    """Laboratory master data"""
    __tablename__ = "laboratories"
    
    # Laboratory identification
    laboratory_code = Column(String(50), nullable=False, unique=True)
    laboratory_name = Column(String(200), nullable=False)
    laboratory_type = Column(String(50), nullable=False)  # in_house, contract, reference
    
    # Location information
    location = Column(String(200), nullable=False)
    facility_id = Column(String(100), nullable=True)
    
    # Accreditation information
    accreditation_body = Column(String(100), nullable=True)
    accreditation_number = Column(String(100), nullable=True)
    accreditation_scope = Column(JSON, nullable=True)
    accreditation_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Capabilities
    testing_capabilities = Column(JSON, nullable=False)
    equipment_list = Column(JSON, nullable=True)
    
    # Quality system
    quality_system = Column(String(100), nullable=True)  # ISO 17025, cGMP, etc.
    last_audit_date = Column(DateTime(timezone=True), nullable=True)
    next_audit_date = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    turnaround_time_days = Column(Float, nullable=True)
    accuracy_rating = Column(Float, nullable=True)
    on_time_delivery_rate = Column(Float, nullable=True)
    
    # Contact information
    contact_person = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Relationships
    test_results = relationship("QualityTestResult", back_populates="laboratory")
    
    __table_args__ = (
        Index('idx_laboratory_code', 'laboratory_code'),
        Index('idx_laboratory_name', 'laboratory_name'),
        Index('idx_laboratory_type', 'laboratory_type'),
        Index('idx_accreditation_expiry', 'accreditation_expiry'),
        CheckConstraint("laboratory_type IN ('in_house', 'contract', 'reference')", name="valid_laboratory_type"),
        CheckConstraint("turnaround_time_days IS NULL OR turnaround_time_days > 0", name="positive_turnaround_time"),
        CheckConstraint("accuracy_rating IS NULL OR (accuracy_rating >= 0 AND accuracy_rating <= 100)", name="valid_accuracy_rating"),
        CheckConstraint("on_time_delivery_rate IS NULL OR (on_time_delivery_rate >= 0 AND on_time_delivery_rate <= 100)", name="valid_delivery_rate"),
    )

class QualityTestResult(BaseModel, TestResultMixin, ApprovalMixin):
    """Quality test results for batches, lots, and materials"""
    __tablename__ = "quality_test_results"
    
    # Test identification
    test_report_number = Column(String(100), nullable=False, unique=True)
    
    # Test type relationship
    test_type_id = Column(UUID(as_uuid=True), ForeignKey('test_types.id'), nullable=False)
    test_type = relationship("TestType", back_populates="test_results")
    
    # Test plan relationship
    test_plan_id = Column(UUID(as_uuid=True), ForeignKey('test_plans.id'), nullable=False)
    test_plan = relationship("TestPlan", back_populates="test_results")
    
    # Laboratory relationship
    laboratory_id = Column(UUID(as_uuid=True), ForeignKey('laboratories.id'), nullable=False)
    laboratory = relationship("Laboratory", back_populates="test_results")
    
    # Sample information
    sample_id = Column(String(100), nullable=False)
    sample_type = Column(String(50), nullable=False)  # batch, lot, material, stability
    sample_description = Column(String(200), nullable=True)
    
    # Sample relationships
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    lot_id = Column(UUID(as_uuid=True), nullable=True)
    material_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Sampling information
    sampling_date = Column(DateTime(timezone=True), nullable=False)
    sampling_location = Column(String(200), nullable=False)
    sampling_method = Column(String(100), nullable=False)
    sampled_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Sample handling
    sample_container = Column(String(100), nullable=False)
    storage_conditions = Column(JSON, nullable=False)
    sample_stability = Column(String(50), nullable=False, default="stable")
    
    # Test execution
    test_request_date = Column(DateTime(timezone=True), nullable=False)
    test_priority = Column(String(20), nullable=False, default="normal")
    
    # Results summary
    overall_result = Column(String(50), nullable=False)  # pass, fail, pending, invalid
    test_conclusion = Column(Text, nullable=True)
    
    # Analyst information
    primary_analyst = Column(UUID(as_uuid=True), nullable=False)
    secondary_analyst = Column(UUID(as_uuid=True), nullable=True)
    
    # Instrument information
    instruments_used = Column(JSON, nullable=True)
    
    # Environmental conditions
    test_environment = Column(JSON, nullable=True)
    
    # Relationships
    test_parameters = relationship("TestParameter", back_populates="test_result", cascade="all, delete-orphan")
    stability_data = relationship("StabilityTestData", back_populates="test_result", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_test_report_number', 'test_report_number'),
        Index('idx_test_type', 'test_type_id'),
        Index('idx_test_plan', 'test_plan_id'),
        Index('idx_laboratory', 'laboratory_id'),
        Index('idx_sample_id', 'sample_id'),
        Index('idx_batch_test', 'batch_id'),
        Index('idx_lot_test', 'lot_id'),
        Index('idx_material_test', 'material_id'),
        Index('idx_sampling_date', 'sampling_date'),
        Index('idx_overall_result', 'overall_result'),
        Index('idx_test_priority', 'test_priority'),
        CheckConstraint("sample_type IN ('batch', 'lot', 'material', 'stability', 'retain')", name="valid_sample_type"),
        CheckConstraint("overall_result IN ('pass', 'fail', 'pending', 'invalid')", name="valid_overall_result"),
        CheckConstraint("test_priority IN ('low', 'normal', 'high', 'urgent')", name="valid_test_priority"),
        CheckConstraint("sample_stability IN ('stable', 'unstable', 'degraded')", name="valid_sample_stability"),
        CheckConstraint("batch_id IS NOT NULL OR lot_id IS NOT NULL OR material_id IS NOT NULL", name="sample_source_required"),
    )

class TestParameter(BaseModel):
    """Individual test parameters within test results"""
    __tablename__ = "test_parameters"
    
    # Test result relationship
    test_result_id = Column(UUID(as_uuid=True), ForeignKey('quality_test_results.id'), nullable=False)
    test_result = relationship("QualityTestResult", back_populates="test_parameters")
    
    # Parameter information
    parameter_name = Column(String(100), nullable=False)
    parameter_code = Column(String(50), nullable=False)
    parameter_type = Column(String(50), nullable=False)  # quantitative, qualitative, limit
    
    # Specification
    specification = Column(JSON, nullable=False)
    specification_min = Column(Float, nullable=True)
    specification_max = Column(Float, nullable=True)
    specification_target = Column(Float, nullable=True)
    specification_units = Column(String(20), nullable=True)
    
    # Results
    result_value = Column(Float, nullable=True)
    result_text = Column(String(200), nullable=True)
    result_units = Column(String(20), nullable=True)
    
    # Calculation details
    calculation_method = Column(String(100), nullable=True)
    calculation_formula = Column(String(500), nullable=True)
    raw_data = Column(JSON, nullable=True)
    
    # Compliance
    result_status = Column(String(50), nullable=False)  # pass, fail, warning, info
    deviation_percentage = Column(Float, nullable=True)
    
    # Uncertainty
    measurement_uncertainty = Column(Float, nullable=True)
    confidence_level = Column(Float, nullable=True)
    
    # Instrument information
    instrument_id = Column(UUID(as_uuid=True), nullable=True)
    instrument_calibration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Analyst notes
    analyst_notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_test_parameter', 'test_result_id'),
        Index('idx_parameter_name', 'parameter_name'),
        Index('idx_parameter_code', 'parameter_code'),
        Index('idx_parameter_type', 'parameter_type'),
        Index('idx_result_status', 'result_status'),
        CheckConstraint("parameter_type IN ('quantitative', 'qualitative', 'limit')", name="valid_parameter_type"),
        CheckConstraint("result_status IN ('pass', 'fail', 'warning', 'info')", name="valid_result_status"),
        CheckConstraint("specification_min IS NULL OR specification_max IS NULL OR specification_min <= specification_max", name="valid_specification_range"),
        CheckConstraint("result_value IS NULL OR result_text IS NULL OR (result_value IS NOT NULL AND result_text IS NOT NULL)", name="result_value_or_text"),
        CheckConstraint("confidence_level IS NULL OR (confidence_level > 0 AND confidence_level <= 100)", name="valid_confidence_level"),
    )

class StabilityTestData(BaseModel, TimestampMixin):
    """Stability testing data for pharmaceutical products"""
    __tablename__ = "stability_test_data"
    
    # Test result relationship
    test_result_id = Column(UUID(as_uuid=True), ForeignKey('quality_test_results.id'), nullable=False)
    test_result = relationship("QualityTestResult", back_populates="stability_data")
    
    # Stability study information
    study_id = Column(String(100), nullable=False)
    study_type = Column(String(50), nullable=False)  # accelerated, long_term, intermediate
    study_protocol = Column(String(200), nullable=False)
    
    # Time point information
    time_point = Column(Integer, nullable=False)  # months
    time_point_description = Column(String(100), nullable=False)
    
    # Storage conditions
    storage_temperature = Column(Float, nullable=False)
    storage_humidity = Column(Float, nullable=True)
    storage_conditions_description = Column(String(200), nullable=False)
    
    # Batch information
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    batch_number = Column(String(100), nullable=False)
    manufacturing_date = Column(DateTime(timezone=True), nullable=False)
    
    # Test data
    test_parameters = Column(JSON, nullable=False)
    test_results = Column(JSON, nullable=False)
    
    # Stability assessment
    stability_status = Column(String(50), nullable=False)  # stable, unstable, degraded
    degradation_rate = Column(Float, nullable=True)
    shelf_life_impact = Column(Text, nullable=True)
    
    # Trend analysis
    trend_analysis = Column(JSON, nullable=True)
    statistical_analysis = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_stability_test_result', 'test_result_id'),
        Index('idx_stability_study', 'study_id'),
        Index('idx_stability_batch', 'batch_id'),
        Index('idx_time_point', 'time_point'),
        Index('idx_storage_conditions', 'storage_temperature', 'storage_humidity'),
        Index('idx_stability_status', 'stability_status'),
        CheckConstraint("study_type IN ('accelerated', 'long_term', 'intermediate')", name="valid_study_type"),
        CheckConstraint("time_point >= 0", name="non_negative_time_point"),
        CheckConstraint("storage_temperature >= -80 AND storage_temperature <= 60", name="valid_storage_temperature"),
        CheckConstraint("storage_humidity IS NULL OR (storage_humidity >= 0 AND storage_humidity <= 100)", name="valid_storage_humidity"),
        CheckConstraint("stability_status IN ('stable', 'unstable', 'degraded')", name="valid_stability_status"),
        CheckConstraint("degradation_rate IS NULL OR degradation_rate >= 0", name="non_negative_degradation_rate"),
    )

class QualityInvestigation(BaseModel, StatusMixin, ApprovalMixin):
    """Quality investigations for failed tests and deviations"""
    __tablename__ = "quality_investigations"
    
    # Investigation identification
    investigation_number = Column(String(100), nullable=False, unique=True)
    investigation_type = Column(String(50), nullable=False)  # oos, oot, deviation, complaint
    
    # Test result relationship
    test_result_id = Column(UUID(as_uuid=True), ForeignKey('quality_test_results.id'), nullable=True)
    
    # Investigation details
    investigation_title = Column(String(200), nullable=False)
    investigation_description = Column(Text, nullable=False)
    
    # Severity and priority
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    priority = Column(String(20), nullable=False)  # low, normal, high, urgent
    
    # Investigation team
    investigation_leader = Column(UUID(as_uuid=True), nullable=False)
    investigation_team = Column(JSON, nullable=False)
    
    # Timeline
    investigation_start_date = Column(DateTime(timezone=True), nullable=False)
    target_completion_date = Column(DateTime(timezone=True), nullable=False)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Investigation phases
    phase1_completed = Column(Boolean, nullable=False, default=False)
    phase1_conclusion = Column(Text, nullable=True)
    phase2_required = Column(Boolean, nullable=False, default=False)
    phase2_completed = Column(Boolean, nullable=False, default=False)
    phase2_conclusion = Column(Text, nullable=True)
    
    # Root cause analysis
    root_cause_identified = Column(Boolean, nullable=False, default=False)
    root_cause_description = Column(Text, nullable=True)
    root_cause_category = Column(String(50), nullable=True)
    
    # Impact assessment
    impact_assessment = Column(JSON, nullable=True)
    other_batches_affected = Column(Boolean, nullable=False, default=False)
    affected_batches = Column(JSON, nullable=True)
    
    # Corrective actions
    corrective_actions = Column(JSON, nullable=True)
    preventive_actions = Column(JSON, nullable=True)
    
    # Investigation conclusion
    investigation_conclusion = Column(Text, nullable=True)
    final_disposition = Column(String(50), nullable=True)  # accept, reject, rework, investigate_further
    
    # Regulatory reporting
    regulatory_reporting_required = Column(Boolean, nullable=False, default=False)
    regulatory_authority = Column(String(100), nullable=True)
    reporting_deadline = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_investigation_number', 'investigation_number'),
        Index('idx_investigation_type', 'investigation_type'),
        Index('idx_test_result', 'test_result_id'),
        Index('idx_severity', 'severity'),
        Index('idx_priority', 'priority'),
        Index('idx_investigation_leader', 'investigation_leader'),
        Index('idx_investigation_start', 'investigation_start_date'),
        Index('idx_target_completion', 'target_completion_date'),
        CheckConstraint("investigation_type IN ('oos', 'oot', 'deviation', 'complaint')", name="valid_investigation_type"),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="valid_severity"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="valid_priority"),
        CheckConstraint("final_disposition IS NULL OR final_disposition IN ('accept', 'reject', 'rework', 'investigate_further')", name="valid_final_disposition"),
        CheckConstraint("investigation_start_date <= target_completion_date", name="valid_investigation_dates"),
    )

class QualityMetrics(BaseModel, TimestampMixin):
    """Quality metrics and KPIs for manufacturing operations"""
    __tablename__ = "quality_metrics"
    
    # Metric identification
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50), nullable=False)  # efficiency, quality, compliance, cost
    
    # Time period
    measurement_period = Column(String(50), nullable=False)  # daily, weekly, monthly, quarterly
    period_start_date = Column(DateTime(timezone=True), nullable=False)
    period_end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Metric values
    metric_value = Column(Float, nullable=False)
    metric_target = Column(Float, nullable=True)
    metric_units = Column(String(20), nullable=False)
    
    # Performance assessment
    performance_status = Column(String(50), nullable=False)  # excellent, good, acceptable, poor
    variance_percentage = Column(Float, nullable=True)
    
    # Trend analysis
    trend_direction = Column(String(20), nullable=False)  # improving, stable, declining
    trend_strength = Column(Float, nullable=True)
    
    # Context information
    contributing_factors = Column(JSON, nullable=True)
    improvement_opportunities = Column(JSON, nullable=True)
    
    # Calculation details
    calculation_method = Column(String(200), nullable=False)
    data_sources = Column(JSON, nullable=False)
    
    # Organizational level
    organizational_level = Column(String(50), nullable=False)  # site, department, line, batch
    organizational_unit = Column(String(100), nullable=False)
    
    __table_args__ = (
        Index('idx_metric_name', 'metric_name'),
        Index('idx_metric_category', 'metric_category'),
        Index('idx_measurement_period', 'measurement_period'),
        Index('idx_period_start', 'period_start_date'),
        Index('idx_performance_status', 'performance_status'),
        Index('idx_trend_direction', 'trend_direction'),
        Index('idx_organizational_level', 'organizational_level'),
        Index('idx_organizational_unit', 'organizational_unit'),
        CheckConstraint("metric_category IN ('efficiency', 'quality', 'compliance', 'cost')", name="valid_metric_category"),
        CheckConstraint("measurement_period IN ('daily', 'weekly', 'monthly', 'quarterly')", name="valid_measurement_period"),
        CheckConstraint("performance_status IN ('excellent', 'good', 'acceptable', 'poor')", name="valid_performance_status"),
        CheckConstraint("trend_direction IN ('improving', 'stable', 'declining')", name="valid_trend_direction"),
        CheckConstraint("organizational_level IN ('site', 'department', 'line', 'batch')", name="valid_organizational_level"),
        CheckConstraint("period_start_date <= period_end_date", name="valid_period_dates"),
    )

class QualityAlert(BaseModel, TimestampMixin, StatusMixin):
    """Quality alerts and notifications"""
    __tablename__ = "quality_alerts"
    
    # Alert identification
    alert_id = Column(String(100), nullable=False, unique=True)
    alert_type = Column(String(50), nullable=False)  # test_failure, trend_alert, specification_limit, system_alert
    
    # Alert details
    alert_title = Column(String(200), nullable=False)
    alert_message = Column(Text, nullable=False)
    alert_level = Column(String(20), nullable=False)  # info, warning, critical, emergency
    
    # Source information
    source_system = Column(String(100), nullable=False)
    source_reference = Column(String(200), nullable=True)
    
    # Test result relationship (if applicable)
    test_result_id = Column(UUID(as_uuid=True), ForeignKey('quality_test_results.id'), nullable=True)
    
    # Alert conditions
    trigger_condition = Column(String(200), nullable=False)
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    
    # Recipients
    alert_recipients = Column(JSON, nullable=False)
    notification_methods = Column(JSON, nullable=False)
    
    # Response tracking
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution tracking
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_action = Column(Text, nullable=True)
    
    # Escalation
    escalated = Column(Boolean, nullable=False, default=False)
    escalation_level = Column(Integer, nullable=False, default=1)
    escalated_to = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_alert_id', 'alert_id'),
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_level', 'alert_level'),
        Index('idx_test_result_alert', 'test_result_id'),
        Index('idx_acknowledged', 'acknowledged'),
        Index('idx_resolved', 'resolved'),
        Index('idx_escalated', 'escalated'),
        Index('idx_alert_timestamp', 'timestamp'),
        CheckConstraint("alert_type IN ('test_failure', 'trend_alert', 'specification_limit', 'system_alert')", name="valid_alert_type"),
        CheckConstraint("alert_level IN ('info', 'warning', 'critical', 'emergency')", name="valid_alert_level"),
        CheckConstraint("escalation_level >= 1", name="positive_escalation_level"),
        CheckConstraint("acknowledged = FALSE OR acknowledged_by IS NOT NULL", name="acknowledged_requires_user"),
        CheckConstraint("resolved = FALSE OR resolved_by IS NOT NULL", name="resolved_requires_user"),
    )

class QualityTrend(BaseModel, TimestampMixin):
    """Quality trend analysis data"""
    __tablename__ = "quality_trends"
    
    # Trend identification
    trend_id = Column(String(100), nullable=False, unique=True)
    trend_name = Column(String(200), nullable=False)
    trend_type = Column(String(50), nullable=False)  # parameter_trend, failure_trend, efficiency_trend
    
    # Data source
    data_source = Column(String(100), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    
    # Time period
    analysis_period = Column(String(50), nullable=False)  # 7d, 30d, 90d, 365d
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Trend statistics
    data_points = Column(Integer, nullable=False)
    trend_direction = Column(String(20), nullable=False)  # increasing, decreasing, stable
    trend_strength = Column(Float, nullable=False)  # correlation coefficient
    
    # Statistical analysis
    mean_value = Column(Float, nullable=True)
    median_value = Column(Float, nullable=True)
    standard_deviation = Column(Float, nullable=True)
    coefficient_of_variation = Column(Float, nullable=True)
    
    # Trend analysis
    slope = Column(Float, nullable=True)
    r_squared = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    
    # Alert thresholds
    upper_control_limit = Column(Float, nullable=True)
    lower_control_limit = Column(Float, nullable=True)
    upper_warning_limit = Column(Float, nullable=True)
    lower_warning_limit = Column(Float, nullable=True)
    
    # Trend assessment
    trend_significance = Column(String(20), nullable=False)  # significant, not_significant, marginal
    trend_assessment = Column(Text, nullable=True)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)
    action_required = Column(Boolean, nullable=False, default=False)
    
    # Organizational context
    organizational_level = Column(String(50), nullable=False)
    organizational_unit = Column(String(100), nullable=False)
    
    __table_args__ = (
        Index('idx_trend_id', 'trend_id'),
        Index('idx_trend_name', 'trend_name'),
        Index('idx_trend_type', 'trend_type'),
        Index('idx_parameter_name', 'parameter_name'),
        Index('idx_analysis_period', 'analysis_period'),
        Index('idx_trend_direction', 'trend_direction'),
        Index('idx_trend_significance', 'trend_significance'),
        Index('idx_action_required', 'action_required'),
        Index('idx_organizational_level', 'organizational_level'),
        CheckConstraint("trend_type IN ('parameter_trend', 'failure_trend', 'efficiency_trend')", name="valid_trend_type"),
        CheckConstraint("analysis_period IN ('7d', '30d', '90d', '365d')", name="valid_analysis_period"),
        CheckConstraint("trend_direction IN ('increasing', 'decreasing', 'stable')", name="valid_trend_direction"),
        CheckConstraint("trend_significance IN ('significant', 'not_significant', 'marginal')", name="valid_trend_significance"),
        CheckConstraint("organizational_level IN ('site', 'department', 'line', 'batch')", name="valid_organizational_level"),
        CheckConstraint("data_points > 0", name="positive_data_points"),
        CheckConstraint("trend_strength >= -1 AND trend_strength <= 1", name="valid_trend_strength"),
        CheckConstraint("start_date <= end_date", name="valid_trend_dates"),
    )