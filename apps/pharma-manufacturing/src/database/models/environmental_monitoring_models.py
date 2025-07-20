"""
Environmental Monitoring Data Models
Real-time environmental monitoring and compliance tracking for pharmaceutical manufacturing
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional
from decimal import Decimal

from .base import BaseModel, TimestampMixin, StatusMixin, ApprovalMixin

class MonitoringLocation(BaseModel, StatusMixin):
    """Environmental monitoring location master data"""
    __tablename__ = "monitoring_locations"
    
    # Location identification
    location_code = Column(String(50), nullable=False, unique=True)
    location_name = Column(String(200), nullable=False)
    location_type = Column(String(50), nullable=False)  # clean_room, warehouse, laboratory, production_area
    
    # Physical location
    building = Column(String(100), nullable=False)
    floor = Column(String(50), nullable=False)
    room = Column(String(100), nullable=False)
    area = Column(String(100), nullable=True)
    coordinates = Column(String(100), nullable=True)
    
    # Classification
    cleanliness_class = Column(String(20), nullable=True)  # ISO 5, ISO 7, ISO 8, unclassified
    containment_level = Column(String(20), nullable=True)  # BSL-1, BSL-2, BSL-3, none
    
    # Environmental requirements
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    humidity_min = Column(Float, nullable=True)
    humidity_max = Column(Float, nullable=True)
    pressure_min = Column(Float, nullable=True)
    pressure_max = Column(Float, nullable=True)
    
    # Air quality requirements
    particle_count_limits = Column(JSON, nullable=True)
    viable_particle_limits = Column(JSON, nullable=True)
    air_changes_per_hour = Column(Float, nullable=True)
    
    # Monitoring requirements
    monitoring_frequency_minutes = Column(Integer, nullable=False, default=15)
    critical_monitoring = Column(Boolean, nullable=False, default=False)
    
    # Alert thresholds
    temperature_alert_min = Column(Float, nullable=True)
    temperature_alert_max = Column(Float, nullable=True)
    humidity_alert_min = Column(Float, nullable=True)
    humidity_alert_max = Column(Float, nullable=True)
    pressure_alert_min = Column(Float, nullable=True)
    pressure_alert_max = Column(Float, nullable=True)
    
    # Validation information
    qualification_status = Column(String(50), nullable=False, default="pending")
    last_qualification_date = Column(DateTime(timezone=True), nullable=True)
    next_qualification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    monitoring_data = relationship("EnvironmentalData", back_populates="location", cascade="all, delete-orphan")
    excursions = relationship("EnvironmentalExcursion", back_populates="location", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_location_code', 'location_code'),
        Index('idx_location_name', 'location_name'),
        Index('idx_location_type', 'location_type'),
        Index('idx_building', 'building'),
        Index('idx_cleanliness_class', 'cleanliness_class'),
        Index('idx_critical_monitoring', 'critical_monitoring'),
        Index('idx_qualification_status', 'qualification_status'),
        CheckConstraint("location_type IN ('clean_room', 'warehouse', 'laboratory', 'production_area', 'corridor', 'airlock')", name="valid_location_type"),
        CheckConstraint("cleanliness_class IS NULL OR cleanliness_class IN ('ISO 5', 'ISO 6', 'ISO 7', 'ISO 8', 'unclassified')", name="valid_cleanliness_class"),
        CheckConstraint("containment_level IS NULL OR containment_level IN ('BSL-1', 'BSL-2', 'BSL-3', 'none')", name="valid_containment_level"),
        CheckConstraint("qualification_status IN ('pending', 'qualified', 'requalification_required', 'failed')", name="valid_qualification_status"),
        CheckConstraint("monitoring_frequency_minutes > 0", name="positive_monitoring_frequency"),
        CheckConstraint("temperature_min IS NULL OR temperature_max IS NULL OR temperature_min <= temperature_max", name="valid_temperature_range"),
        CheckConstraint("humidity_min IS NULL OR humidity_max IS NULL OR humidity_min <= humidity_max", name="valid_humidity_range"),
        CheckConstraint("pressure_min IS NULL OR pressure_max IS NULL OR pressure_min <= pressure_max", name="valid_pressure_range"),
    )

class EnvironmentalParameter(BaseModel):
    """Environmental parameter master data"""
    __tablename__ = "environmental_parameters"
    
    # Parameter identification
    parameter_code = Column(String(50), nullable=False, unique=True)
    parameter_name = Column(String(200), nullable=False)
    parameter_type = Column(String(50), nullable=False)  # temperature, humidity, pressure, particle_count, viable_count
    
    # Measurement details
    measurement_units = Column(String(20), nullable=False)
    measurement_range_min = Column(Float, nullable=True)
    measurement_range_max = Column(Float, nullable=True)
    
    # Sensor requirements
    sensor_type = Column(String(100), nullable=False)
    calibration_frequency_days = Column(Integer, nullable=False, default=365)
    
    # Data quality
    accuracy_requirement = Column(Float, nullable=True)
    precision_requirement = Column(Float, nullable=True)
    
    # Regulatory significance
    regulatory_requirement = Column(Boolean, nullable=False, default=True)
    gmp_critical = Column(Boolean, nullable=False, default=False)
    
    # Alert configuration
    default_alert_deviation = Column(Float, nullable=True)
    default_critical_deviation = Column(Float, nullable=True)
    
    # Data retention
    data_retention_days = Column(Integer, nullable=False, default=365)
    
    __table_args__ = (
        Index('idx_parameter_code', 'parameter_code'),
        Index('idx_parameter_name', 'parameter_name'),
        Index('idx_parameter_type', 'parameter_type'),
        Index('idx_regulatory_requirement', 'regulatory_requirement'),
        Index('idx_gmp_critical', 'gmp_critical'),
        CheckConstraint("parameter_type IN ('temperature', 'humidity', 'pressure', 'particle_count', 'viable_count', 'air_velocity', 'co2')", name="valid_parameter_type"),
        CheckConstraint("measurement_range_min IS NULL OR measurement_range_max IS NULL OR measurement_range_min <= measurement_range_max", name="valid_measurement_range"),
        CheckConstraint("calibration_frequency_days > 0", name="positive_calibration_frequency"),
        CheckConstraint("accuracy_requirement IS NULL OR accuracy_requirement > 0", name="positive_accuracy"),
        CheckConstraint("precision_requirement IS NULL OR precision_requirement > 0", name="positive_precision"),
        CheckConstraint("data_retention_days > 0", name="positive_retention_days"),
    )

class EnvironmentalData(BaseModel, TimestampMixin):
    """Real-time environmental monitoring data"""
    __tablename__ = "environmental_data"
    
    # Location relationship
    location_id = Column(UUID(as_uuid=True), ForeignKey('monitoring_locations.id'), nullable=False)
    location = relationship("MonitoringLocation", back_populates="monitoring_data")
    
    # Parameter relationship
    parameter_id = Column(UUID(as_uuid=True), ForeignKey('environmental_parameters.id'), nullable=False)
    parameter = relationship("EnvironmentalParameter")
    
    # Measurement data
    measured_value = Column(Float, nullable=False)
    measurement_units = Column(String(20), nullable=False)
    
    # Data quality
    data_quality = Column(String(20), nullable=False, default="good")  # good, uncertain, bad
    measurement_status = Column(String(20), nullable=False, default="normal")  # normal, alert, alarm
    
    # Sensor information
    sensor_id = Column(UUID(as_uuid=True), nullable=True)
    sensor_reading = Column(Float, nullable=True)  # Raw sensor reading
    calibration_factor = Column(Float, nullable=True)
    
    # Compliance assessment
    within_specification = Column(Boolean, nullable=False)
    specification_min = Column(Float, nullable=True)
    specification_max = Column(Float, nullable=True)
    deviation_percentage = Column(Float, nullable=True)
    
    # Alert information
    alert_triggered = Column(Boolean, nullable=False, default=False)
    alert_level = Column(String(20), nullable=True)  # warning, critical, emergency
    alert_message = Column(String(500), nullable=True)
    
    # Batch context (if applicable)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    batch_stage = Column(String(100), nullable=True)
    
    # Environmental conditions
    ambient_conditions = Column(JSON, nullable=True)
    weather_conditions = Column(JSON, nullable=True)
    
    # System information
    data_source = Column(String(100), nullable=False)
    system_timestamp = Column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        Index('idx_env_data_location', 'location_id'),
        Index('idx_env_data_parameter', 'parameter_id'),
        Index('idx_env_data_timestamp', 'timestamp'),
        Index('idx_env_data_batch', 'batch_id'),
        Index('idx_env_data_quality', 'data_quality'),
        Index('idx_env_data_status', 'measurement_status'),
        Index('idx_env_data_alert', 'alert_triggered'),
        Index('idx_env_data_compliance', 'within_specification'),
        Index('idx_env_data_sensor', 'sensor_id'),
        # Composite indexes for common queries
        Index('idx_env_data_location_timestamp', 'location_id', 'timestamp'),
        Index('idx_env_data_parameter_timestamp', 'parameter_id', 'timestamp'),
        Index('idx_env_data_location_parameter', 'location_id', 'parameter_id'),
        CheckConstraint("data_quality IN ('good', 'uncertain', 'bad')", name="valid_data_quality"),
        CheckConstraint("measurement_status IN ('normal', 'alert', 'alarm')", name="valid_measurement_status"),
        CheckConstraint("alert_level IS NULL OR alert_level IN ('warning', 'critical', 'emergency')", name="valid_alert_level"),
        CheckConstraint("specification_min IS NULL OR specification_max IS NULL OR specification_min <= specification_max", name="valid_specification_range"),
    )

class EnvironmentalExcursion(BaseModel, StatusMixin, ApprovalMixin):
    """Environmental excursions and deviations"""
    __tablename__ = "environmental_excursions"
    
    # Excursion identification
    excursion_number = Column(String(100), nullable=False, unique=True)
    excursion_type = Column(String(50), nullable=False)  # temperature, humidity, pressure, particle_count, system_failure
    
    # Location relationship
    location_id = Column(UUID(as_uuid=True), ForeignKey('monitoring_locations.id'), nullable=False)
    location = relationship("MonitoringLocation", back_populates="excursions")
    
    # Parameter relationship
    parameter_id = Column(UUID(as_uuid=True), ForeignKey('environmental_parameters.id'), nullable=False)
    parameter = relationship("EnvironmentalParameter")
    
    # Excursion details
    excursion_start = Column(DateTime(timezone=True), nullable=False)
    excursion_end = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Severity assessment
    severity = Column(String(20), nullable=False)  # minor, major, critical
    impact_assessment = Column(String(50), nullable=False)  # none, low, medium, high
    
    # Measurement data
    trigger_value = Column(Float, nullable=False)
    specification_limit = Column(Float, nullable=False)
    deviation_amount = Column(Float, nullable=False)
    peak_deviation = Column(Float, nullable=True)
    
    # Root cause analysis
    root_cause_identified = Column(Boolean, nullable=False, default=False)
    root_cause_description = Column(Text, nullable=True)
    root_cause_category = Column(String(50), nullable=True)
    
    # Impact on operations
    batch_impact = Column(Boolean, nullable=False, default=False)
    affected_batches = Column(JSON, nullable=True)
    product_impact = Column(Boolean, nullable=False, default=False)
    affected_products = Column(JSON, nullable=True)
    
    # Investigation details
    investigation_required = Column(Boolean, nullable=False, default=True)
    investigation_completed = Column(Boolean, nullable=False, default=False)
    investigated_by = Column(UUID(as_uuid=True), nullable=True)
    investigation_date = Column(DateTime(timezone=True), nullable=True)
    investigation_findings = Column(Text, nullable=True)
    
    # Corrective actions
    immediate_action_taken = Column(Text, nullable=True)
    corrective_actions = Column(JSON, nullable=True)
    preventive_actions = Column(JSON, nullable=True)
    
    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolution_date = Column(DateTime(timezone=True), nullable=True)
    resolution_description = Column(Text, nullable=True)
    
    # Regulatory reporting
    regulatory_reportable = Column(Boolean, nullable=False, default=False)
    regulatory_authority = Column(String(100), nullable=True)
    report_submitted = Column(Boolean, nullable=False, default=False)
    report_date = Column(DateTime(timezone=True), nullable=True)
    
    # Trend analysis
    trending_pattern = Column(String(50), nullable=True)
    frequency_analysis = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_excursion_number', 'excursion_number'),
        Index('idx_excursion_type', 'excursion_type'),
        Index('idx_excursion_location', 'location_id'),
        Index('idx_excursion_parameter', 'parameter_id'),
        Index('idx_excursion_start', 'excursion_start'),
        Index('idx_severity', 'severity'),
        Index('idx_impact_assessment', 'impact_assessment'),
        Index('idx_investigation_required', 'investigation_required'),
        Index('idx_resolved', 'resolved'),
        Index('idx_regulatory_reportable', 'regulatory_reportable'),
        CheckConstraint("excursion_type IN ('temperature', 'humidity', 'pressure', 'particle_count', 'system_failure')", name="valid_excursion_type"),
        CheckConstraint("severity IN ('minor', 'major', 'critical')", name="valid_severity"),
        CheckConstraint("impact_assessment IN ('none', 'low', 'medium', 'high')", name="valid_impact_assessment"),
        CheckConstraint("excursion_start <= excursion_end OR excursion_end IS NULL", name="valid_excursion_dates"),
        CheckConstraint("duration_minutes IS NULL OR duration_minutes > 0", name="positive_duration"),
        CheckConstraint("deviation_amount >= 0", name="non_negative_deviation"),
    )

class EnvironmentalCalibration(BaseModel, StatusMixin, ApprovalMixin):
    """Environmental sensor calibration records"""
    __tablename__ = "environmental_calibration"
    
    # Calibration identification
    calibration_number = Column(String(100), nullable=False, unique=True)
    calibration_type = Column(String(50), nullable=False)  # routine, repair, installation, validation
    
    # Sensor information
    sensor_id = Column(UUID(as_uuid=True), nullable=False)
    sensor_model = Column(String(100), nullable=False)
    sensor_serial = Column(String(100), nullable=False)
    
    # Location relationship
    location_id = Column(UUID(as_uuid=True), ForeignKey('monitoring_locations.id'), nullable=False)
    location = relationship("MonitoringLocation")
    
    # Parameter relationship
    parameter_id = Column(UUID(as_uuid=True), ForeignKey('environmental_parameters.id'), nullable=False)
    parameter = relationship("EnvironmentalParameter")
    
    # Calibration details
    calibration_date = Column(DateTime(timezone=True), nullable=False)
    calibration_procedure = Column(String(200), nullable=False)
    calibration_standard = Column(String(200), nullable=False)
    
    # Environmental conditions
    calibration_temperature = Column(Float, nullable=True)
    calibration_humidity = Column(Float, nullable=True)
    calibration_pressure = Column(Float, nullable=True)
    
    # Calibration points
    calibration_points = Column(JSON, nullable=False)
    reference_values = Column(JSON, nullable=False)
    sensor_readings = Column(JSON, nullable=False)
    
    # Calibration results
    calibration_curve = Column(JSON, nullable=True)
    calibration_factor = Column(Float, nullable=True)
    calibration_offset = Column(Float, nullable=True)
    linearity = Column(Float, nullable=True)
    
    # Accuracy assessment
    accuracy_achieved = Column(Float, nullable=True)
    measurement_uncertainty = Column(Float, nullable=True)
    
    # Calibration status
    calibration_passed = Column(Boolean, nullable=False, default=False)
    calibration_results = Column(JSON, nullable=True)
    
    # Next calibration
    next_calibration_date = Column(DateTime(timezone=True), nullable=False)
    calibration_frequency_days = Column(Integer, nullable=False)
    
    # Personnel
    calibrated_by = Column(UUID(as_uuid=True), nullable=False)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Documentation
    calibration_certificate = Column(String(500), nullable=True)
    
    __table_args__ = (
        Index('idx_calibration_number', 'calibration_number'),
        Index('idx_calibration_sensor', 'sensor_id'),
        Index('idx_calibration_location', 'location_id'),
        Index('idx_calibration_parameter', 'parameter_id'),
        Index('idx_calibration_date', 'calibration_date'),
        Index('idx_next_calibration', 'next_calibration_date'),
        Index('idx_calibration_passed', 'calibration_passed'),
        Index('idx_calibrated_by', 'calibrated_by'),
        CheckConstraint("calibration_type IN ('routine', 'repair', 'installation', 'validation')", name="valid_calibration_type"),
        CheckConstraint("calibration_frequency_days > 0", name="positive_calibration_frequency"),
        CheckConstraint("accuracy_achieved IS NULL OR accuracy_achieved > 0", name="positive_accuracy"),
        CheckConstraint("linearity IS NULL OR (linearity >= 0 AND linearity <= 1)", name="valid_linearity"),
        CheckConstraint("calibration_date <= next_calibration_date", name="valid_calibration_dates"),
    )

class EnvironmentalReport(BaseModel, StatusMixin, ApprovalMixin):
    """Environmental monitoring reports"""
    __tablename__ = "environmental_reports"
    
    # Report identification
    report_number = Column(String(100), nullable=False, unique=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, annual, excursion
    report_title = Column(String(200), nullable=False)
    
    # Reporting period
    report_period_start = Column(DateTime(timezone=True), nullable=False)
    report_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Scope
    locations_included = Column(JSON, nullable=False)
    parameters_included = Column(JSON, nullable=False)
    
    # Report data
    summary_statistics = Column(JSON, nullable=False)
    excursion_summary = Column(JSON, nullable=True)
    trend_analysis = Column(JSON, nullable=True)
    
    # Compliance assessment
    compliance_status = Column(String(50), nullable=False)  # compliant, non_compliant, conditional
    compliance_percentage = Column(Float, nullable=True)
    
    # Key findings
    key_findings = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Action items
    action_items = Column(JSON, nullable=True)
    corrective_actions = Column(JSON, nullable=True)
    
    # Report generation
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    generation_date = Column(DateTime(timezone=True), nullable=False)
    
    # Distribution
    distribution_list = Column(JSON, nullable=False)
    regulatory_submission = Column(Boolean, nullable=False, default=False)
    
    # Report file
    report_file_path = Column(String(500), nullable=True)
    report_format = Column(String(20), nullable=False, default="PDF")
    
    __table_args__ = (
        Index('idx_report_number', 'report_number'),
        Index('idx_report_type', 'report_type'),
        Index('idx_report_period', 'report_period_start', 'report_period_end'),
        Index('idx_compliance_status', 'compliance_status'),
        Index('idx_generated_by', 'generated_by'),
        Index('idx_generation_date', 'generation_date'),
        Index('idx_regulatory_submission', 'regulatory_submission'),
        CheckConstraint("report_type IN ('daily', 'weekly', 'monthly', 'annual', 'excursion', 'trend')", name="valid_report_type"),
        CheckConstraint("compliance_status IN ('compliant', 'non_compliant', 'conditional')", name="valid_compliance_status"),
        CheckConstraint("compliance_percentage IS NULL OR (compliance_percentage >= 0 AND compliance_percentage <= 100)", name="valid_compliance_percentage"),
        CheckConstraint("report_period_start <= report_period_end", name="valid_report_period"),
        CheckConstraint("report_format IN ('PDF', 'Excel', 'Word', 'CSV')", name="valid_report_format"),
    )

class EnvironmentalAlert(BaseModel, TimestampMixin, StatusMixin):
    """Environmental monitoring alerts"""
    __tablename__ = "environmental_alerts"
    
    # Alert identification
    alert_id = Column(String(100), nullable=False, unique=True)
    alert_type = Column(String(50), nullable=False)  # excursion, trend, calibration_due, sensor_failure
    
    # Location relationship
    location_id = Column(UUID(as_uuid=True), ForeignKey('monitoring_locations.id'), nullable=False)
    location = relationship("MonitoringLocation")
    
    # Parameter relationship
    parameter_id = Column(UUID(as_uuid=True), ForeignKey('environmental_parameters.id'), nullable=False)
    parameter = relationship("EnvironmentalParameter")
    
    # Alert details
    alert_title = Column(String(200), nullable=False)
    alert_message = Column(Text, nullable=False)
    alert_level = Column(String(20), nullable=False)  # info, warning, critical, emergency
    
    # Trigger information
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    
    # Alert conditions
    alert_condition = Column(String(200), nullable=False)
    persistence_time = Column(Integer, nullable=True)  # minutes
    
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
    
    # Related excursion
    excursion_id = Column(UUID(as_uuid=True), ForeignKey('environmental_excursions.id'), nullable=True)
    excursion = relationship("EnvironmentalExcursion")
    
    __table_args__ = (
        Index('idx_env_alert_id', 'alert_id'),
        Index('idx_env_alert_type', 'alert_type'),
        Index('idx_env_alert_location', 'location_id'),
        Index('idx_env_alert_parameter', 'parameter_id'),
        Index('idx_env_alert_level', 'alert_level'),
        Index('idx_env_alert_acknowledged', 'acknowledged'),
        Index('idx_env_alert_resolved', 'resolved'),
        Index('idx_env_alert_escalated', 'escalated'),
        Index('idx_env_alert_timestamp', 'timestamp'),
        Index('idx_env_alert_excursion', 'excursion_id'),
        CheckConstraint("alert_type IN ('excursion', 'trend', 'calibration_due', 'sensor_failure')", name="valid_alert_type"),
        CheckConstraint("alert_level IN ('info', 'warning', 'critical', 'emergency')", name="valid_alert_level"),
        CheckConstraint("escalation_level >= 1", name="positive_escalation_level"),
        CheckConstraint("persistence_time IS NULL OR persistence_time > 0", name="positive_persistence_time"),
        CheckConstraint("acknowledged = FALSE OR acknowledged_by IS NOT NULL", name="acknowledged_requires_user"),
        CheckConstraint("resolved = FALSE OR resolved_by IS NOT NULL", name="resolved_requires_user"),
    )

class EnvironmentalTrend(BaseModel, TimestampMixin):
    """Environmental monitoring trend analysis"""
    __tablename__ = "environmental_trends"
    
    # Trend identification
    trend_id = Column(String(100), nullable=False, unique=True)
    trend_name = Column(String(200), nullable=False)
    
    # Location relationship
    location_id = Column(UUID(as_uuid=True), ForeignKey('monitoring_locations.id'), nullable=False)
    location = relationship("MonitoringLocation")
    
    # Parameter relationship
    parameter_id = Column(UUID(as_uuid=True), ForeignKey('environmental_parameters.id'), nullable=False)
    parameter = relationship("EnvironmentalParameter")
    
    # Analysis period
    analysis_period = Column(String(50), nullable=False)  # 24h, 7d, 30d, 90d
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Trend statistics
    data_points = Column(Integer, nullable=False)
    mean_value = Column(Float, nullable=False)
    median_value = Column(Float, nullable=False)
    standard_deviation = Column(Float, nullable=False)
    
    # Trend analysis
    trend_direction = Column(String(20), nullable=False)  # increasing, decreasing, stable
    trend_strength = Column(Float, nullable=False)  # correlation coefficient
    slope = Column(Float, nullable=True)
    r_squared = Column(Float, nullable=True)
    
    # Control limits
    upper_control_limit = Column(Float, nullable=True)
    lower_control_limit = Column(Float, nullable=True)
    
    # Trend assessment
    trend_significance = Column(String(20), nullable=False)  # significant, not_significant
    process_capability = Column(Float, nullable=True)
    
    # Seasonality analysis
    seasonal_pattern = Column(Boolean, nullable=False, default=False)
    seasonal_period = Column(Integer, nullable=True)
    
    # Forecast
    forecast_values = Column(JSON, nullable=True)
    forecast_confidence = Column(Float, nullable=True)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)
    action_required = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        Index('idx_env_trend_id', 'trend_id'),
        Index('idx_env_trend_location', 'location_id'),
        Index('idx_env_trend_parameter', 'parameter_id'),
        Index('idx_env_trend_period', 'analysis_period'),
        Index('idx_env_trend_direction', 'trend_direction'),
        Index('idx_env_trend_significance', 'trend_significance'),
        Index('idx_env_trend_action', 'action_required'),
        CheckConstraint("analysis_period IN ('24h', '7d', '30d', '90d')", name="valid_analysis_period"),
        CheckConstraint("trend_direction IN ('increasing', 'decreasing', 'stable')", name="valid_trend_direction"),
        CheckConstraint("trend_significance IN ('significant', 'not_significant')", name="valid_trend_significance"),
        CheckConstraint("data_points > 0", name="positive_data_points"),
        CheckConstraint("trend_strength >= -1 AND trend_strength <= 1", name="valid_trend_strength"),
        CheckConstraint("start_date <= end_date", name="valid_trend_dates"),
        CheckConstraint("seasonal_period IS NULL OR seasonal_period > 0", name="positive_seasonal_period"),
    )