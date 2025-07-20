"""
Equipment and Sensor Data Models
Equipment tracking, calibration, and sensor data management
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional

from .base import BaseModel, TimestampMixin, StatusMixin, ApprovalMixin, CalibrationMixin

class EquipmentType(BaseModel):
    """Equipment type master data"""
    __tablename__ = "equipment_types"
    
    # Type information
    type_code = Column(String(50), nullable=False, unique=True)
    type_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # analytical, production, utility, cleaning
    
    # Manufacturer information
    manufacturer = Column(String(200), nullable=True)
    model_family = Column(String(100), nullable=True)
    
    # Calibration requirements
    calibration_required = Column(Boolean, nullable=False, default=True)
    calibration_frequency_days = Column(Integer, nullable=True)
    calibration_procedure = Column(String(200), nullable=True)
    
    # Validation requirements
    validation_required = Column(Boolean, nullable=False, default=True)
    validation_frequency_months = Column(Integer, nullable=True)
    
    # Maintenance requirements
    preventive_maintenance_required = Column(Boolean, nullable=False, default=True)
    maintenance_frequency_days = Column(Integer, nullable=True)
    
    # Specifications
    specifications = Column(JSON, nullable=True)
    
    # Relationships
    equipment_items = relationship("Equipment", back_populates="equipment_type")
    
    __table_args__ = (
        Index('idx_equipment_type_code', 'type_code'),
        Index('idx_equipment_category', 'category'),
        Index('idx_manufacturer', 'manufacturer'),
        CheckConstraint("calibration_frequency_days IS NULL OR calibration_frequency_days > 0", name="positive_calibration_frequency"),
        CheckConstraint("validation_frequency_months IS NULL OR validation_frequency_months > 0", name="positive_validation_frequency"),
        CheckConstraint("maintenance_frequency_days IS NULL OR maintenance_frequency_days > 0", name="positive_maintenance_frequency"),
    )

class Equipment(BaseModel, StatusMixin, CalibrationMixin):
    """Equipment master data and tracking"""
    __tablename__ = "equipment"
    
    # Equipment identification
    equipment_id = Column(String(100), nullable=False, unique=True)
    equipment_name = Column(String(200), nullable=False)
    
    # Equipment type relationship
    equipment_type_id = Column(UUID(as_uuid=True), ForeignKey('equipment_types.id'), nullable=False)
    equipment_type = relationship("EquipmentType", back_populates="equipment_items")
    
    # Manufacturer information
    manufacturer = Column(String(200), nullable=False)
    model_number = Column(String(100), nullable=False)
    serial_number = Column(String(100), nullable=False)
    
    # Installation information
    installation_date = Column(DateTime(timezone=True), nullable=False)
    installation_location = Column(String(200), nullable=False)
    installed_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Operational information
    operational_status = Column(String(50), nullable=False, default="operational")
    operational_since = Column(DateTime(timezone=True), nullable=False)
    
    # Maintenance information
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    maintenance_contract = Column(String(200), nullable=True)
    
    # Validation information
    validation_status = Column(String(50), nullable=False, default="pending")
    last_validation_date = Column(DateTime(timezone=True), nullable=True)
    next_validation_date = Column(DateTime(timezone=True), nullable=True)
    validation_protocol = Column(String(200), nullable=True)
    
    # Critical equipment designation
    critical_equipment = Column(Boolean, nullable=False, default=False)
    criticality_level = Column(String(20), nullable=True)  # low, medium, high, critical
    
    # Spare parts information
    spare_parts_required = Column(JSON, nullable=True)
    
    # Relationships
    calibration_records = relationship("EquipmentCalibration", back_populates="equipment", cascade="all, delete-orphan")
    maintenance_records = relationship("EquipmentMaintenance", back_populates="equipment", cascade="all, delete-orphan")
    validation_records = relationship("EquipmentValidation", back_populates="equipment", cascade="all, delete-orphan")
    sensor_data = relationship("SensorData", back_populates="equipment", cascade="all, delete-orphan")
    usage_logs = relationship("EquipmentUsageLog", back_populates="equipment", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_equipment_id', 'equipment_id'),
        Index('idx_equipment_name', 'equipment_name'),
        Index('idx_equipment_type', 'equipment_type_id'),
        Index('idx_installation_location', 'installation_location'),
        Index('idx_operational_status', 'operational_status'),
        Index('idx_validation_status', 'validation_status'),
        Index('idx_critical_equipment', 'critical_equipment'),
        Index('idx_serial_number', 'serial_number'),
        UniqueConstraint('equipment_id', name='uq_equipment_id'),
        UniqueConstraint('serial_number', name='uq_serial_number'),
        CheckConstraint("operational_status IN ('operational', 'maintenance', 'calibration', 'out_of_service', 'decommissioned')", name="valid_operational_status"),
        CheckConstraint("validation_status IN ('pending', 'in_progress', 'completed', 'expired', 'failed')", name="valid_validation_status"),
        CheckConstraint("criticality_level IS NULL OR criticality_level IN ('low', 'medium', 'high', 'critical')", name="valid_criticality_level"),
    )
    
    def is_maintenance_due(self) -> bool:
        """Check if maintenance is due"""
        if not self.next_maintenance_date:
            return False
        return datetime.now(timezone.utc) >= self.next_maintenance_date.replace(tzinfo=timezone.utc)
    
    def is_validation_due(self) -> bool:
        """Check if validation is due"""
        if not self.next_validation_date:
            return False
        return datetime.now(timezone.utc) >= self.next_validation_date.replace(tzinfo=timezone.utc)
    
    def calculate_uptime(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate equipment uptime percentage"""
        # This would query usage logs and maintenance records
        # For now, return a placeholder
        return 98.5

class EquipmentCalibration(BaseModel, CalibrationMixin, ApprovalMixin):
    """Equipment calibration records"""
    __tablename__ = "equipment_calibration"
    
    # Equipment relationship
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'), nullable=False)
    equipment = relationship("Equipment", back_populates="calibration_records")
    
    # Calibration details
    calibration_type = Column(String(50), nullable=False)  # initial, periodic, repair, modification
    calibration_reason = Column(String(200), nullable=False)
    
    # Environmental conditions during calibration
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    
    # Calibration standards used
    standards_used = Column(JSON, nullable=False)
    
    # Calibration points and results
    calibration_points = Column(JSON, nullable=False)
    measurement_results = Column(JSON, nullable=False)
    
    # Uncertainty analysis
    measurement_uncertainty = Column(Float, nullable=True)
    expanded_uncertainty = Column(Float, nullable=True)
    confidence_level = Column(Float, nullable=True)
    
    # Calibration status
    calibration_status = Column(String(50), nullable=False, default="pending")
    
    # Traceability
    traceability_chain = Column(JSON, nullable=True)
    nist_traceable = Column(Boolean, nullable=False, default=False)
    
    # Certificate information
    calibration_certificate = Column(String(200), nullable=True)
    certificate_number = Column(String(100), nullable=True)
    certificate_issued_date = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_equipment_calibration', 'equipment_id'),
        Index('idx_calibration_date', 'calibration_date'),
        Index('idx_calibration_type', 'calibration_type'),
        Index('idx_calibration_status', 'calibration_status'),
        Index('idx_certificate_number', 'certificate_number'),
        CheckConstraint("calibration_type IN ('initial', 'periodic', 'repair', 'modification')", name="valid_calibration_type"),
        CheckConstraint("calibration_status IN ('pending', 'in_progress', 'completed', 'failed')", name="valid_calibration_status"),
        CheckConstraint("confidence_level IS NULL OR (confidence_level > 0 AND confidence_level <= 100)", name="valid_confidence_level"),
    )

class EquipmentMaintenance(BaseModel, StatusMixin, ApprovalMixin):
    """Equipment maintenance records"""
    __tablename__ = "equipment_maintenance"
    
    # Equipment relationship
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'), nullable=False)
    equipment = relationship("Equipment", back_populates="maintenance_records")
    
    # Maintenance information
    maintenance_type = Column(String(50), nullable=False)  # preventive, corrective, emergency
    maintenance_description = Column(Text, nullable=False)
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    started_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Personnel
    maintenance_technician = Column(UUID(as_uuid=True), nullable=False)
    supervisor = Column(UUID(as_uuid=True), nullable=True)
    
    # Work performed
    work_performed = Column(Text, nullable=True)
    parts_replaced = Column(JSON, nullable=True)
    parts_cost = Column(Float, nullable=True)
    labor_hours = Column(Float, nullable=True)
    
    # Results
    maintenance_results = Column(Text, nullable=True)
    maintenance_successful = Column(Boolean, nullable=True)
    
    # Follow-up required
    follow_up_required = Column(Boolean, nullable=False, default=False)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_description = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_equipment_maintenance', 'equipment_id'),
        Index('idx_maintenance_type', 'maintenance_type'),
        Index('idx_scheduled_date', 'scheduled_date'),
        Index('idx_maintenance_technician', 'maintenance_technician'),
        Index('idx_completed_date', 'completed_date'),
        CheckConstraint("maintenance_type IN ('preventive', 'corrective', 'emergency')", name="valid_maintenance_type"),
        CheckConstraint("parts_cost IS NULL OR parts_cost >= 0", name="non_negative_parts_cost"),
        CheckConstraint("labor_hours IS NULL OR labor_hours >= 0", name="non_negative_labor_hours"),
    )

class EquipmentValidation(BaseModel, StatusMixin, ApprovalMixin):
    """Equipment validation records (IQ/OQ/PQ)"""
    __tablename__ = "equipment_validation"
    
    # Equipment relationship
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'), nullable=False)
    equipment = relationship("Equipment", back_populates="validation_records")
    
    # Validation information
    validation_type = Column(String(20), nullable=False)  # IQ, OQ, PQ, CSV
    validation_protocol = Column(String(200), nullable=False)
    validation_reason = Column(String(200), nullable=False)
    
    # Validation team
    validation_manager = Column(UUID(as_uuid=True), nullable=False)
    validation_team = Column(JSON, nullable=False)
    
    # Validation dates
    validation_start_date = Column(DateTime(timezone=True), nullable=False)
    validation_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Validation results
    validation_results = Column(JSON, nullable=True)
    validation_passed = Column(Boolean, nullable=True)
    
    # Deviations
    deviations_found = Column(Boolean, nullable=False, default=False)
    deviation_details = Column(JSON, nullable=True)
    
    # Documentation
    validation_report = Column(String(500), nullable=True)
    validation_certificate = Column(String(500), nullable=True)
    
    # Revalidation
    revalidation_required = Column(Boolean, nullable=False, default=False)
    revalidation_date = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_equipment_validation', 'equipment_id'),
        Index('idx_validation_type', 'validation_type'),
        Index('idx_validation_start_date', 'validation_start_date'),
        Index('idx_validation_manager', 'validation_manager'),
        Index('idx_validation_passed', 'validation_passed'),
        CheckConstraint("validation_type IN ('IQ', 'OQ', 'PQ', 'CSV')", name="valid_validation_type"),
        CheckConstraint("validation_start_date <= validation_end_date OR validation_end_date IS NULL", name="valid_validation_dates"),
    )

class SensorType(BaseModel):
    """Sensor type master data"""
    __tablename__ = "sensor_types"
    
    # Type information
    sensor_type_code = Column(String(50), nullable=False, unique=True)
    sensor_type_name = Column(String(200), nullable=False)
    measurement_type = Column(String(100), nullable=False)  # temperature, pressure, flow, ph, etc.
    
    # Measurement specifications
    measurement_range_min = Column(Float, nullable=True)
    measurement_range_max = Column(Float, nullable=True)
    measurement_units = Column(String(20), nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    
    # Calibration requirements
    calibration_frequency_days = Column(Integer, nullable=False, default=365)
    calibration_tolerance = Column(Float, nullable=True)
    
    # Communication protocol
    communication_protocol = Column(String(50), nullable=True)
    data_format = Column(String(50), nullable=True)
    
    # Relationships
    sensors = relationship("Sensor", back_populates="sensor_type")
    
    __table_args__ = (
        Index('idx_sensor_type_code', 'sensor_type_code'),
        Index('idx_measurement_type', 'measurement_type'),
        CheckConstraint("measurement_range_min IS NULL OR measurement_range_max IS NULL OR measurement_range_min <= measurement_range_max", name="valid_measurement_range"),
        CheckConstraint("accuracy IS NULL OR accuracy >= 0", name="non_negative_accuracy"),
        CheckConstraint("precision IS NULL OR precision >= 0", name="non_negative_precision"),
        CheckConstraint("calibration_frequency_days > 0", name="positive_calibration_frequency"),
    )

class Sensor(BaseModel, StatusMixin):
    """Individual sensor instances"""
    __tablename__ = "sensors"
    
    # Sensor identification
    sensor_id = Column(String(100), nullable=False, unique=True)
    sensor_name = Column(String(200), nullable=False)
    
    # Sensor type relationship
    sensor_type_id = Column(UUID(as_uuid=True), ForeignKey('sensor_types.id'), nullable=False)
    sensor_type = relationship("SensorType", back_populates="sensors")
    
    # Equipment relationship (optional)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'), nullable=True)
    equipment = relationship("Equipment", back_populates="sensor_data")
    
    # Installation information
    installation_date = Column(DateTime(timezone=True), nullable=False)
    installation_location = Column(String(200), nullable=False)
    physical_location = Column(String(500), nullable=True)
    
    # Manufacturer information
    manufacturer = Column(String(200), nullable=False)
    model_number = Column(String(100), nullable=False)
    serial_number = Column(String(100), nullable=False)
    
    # Operational parameters
    sampling_frequency_seconds = Column(Integer, nullable=False, default=60)
    data_retention_days = Column(Integer, nullable=False, default=365)
    
    # Calibration information
    last_calibration_date = Column(DateTime(timezone=True), nullable=True)
    next_calibration_date = Column(DateTime(timezone=True), nullable=True)
    calibration_status = Column(String(50), nullable=False, default="pending")
    
    # Alert thresholds
    alert_min_threshold = Column(Float, nullable=True)
    alert_max_threshold = Column(Float, nullable=True)
    critical_min_threshold = Column(Float, nullable=True)
    critical_max_threshold = Column(Float, nullable=True)
    
    # Relationships
    sensor_data = relationship("SensorData", back_populates="sensor", cascade="all, delete-orphan")
    calibration_records = relationship("SensorCalibration", back_populates="sensor", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_sensor_id', 'sensor_id'),
        Index('idx_sensor_name', 'sensor_name'),
        Index('idx_sensor_type', 'sensor_type_id'),
        Index('idx_equipment_sensor', 'equipment_id'),
        Index('idx_installation_location', 'installation_location'),
        Index('idx_calibration_status', 'calibration_status'),
        Index('idx_serial_number', 'serial_number'),
        UniqueConstraint('sensor_id', name='uq_sensor_id'),
        UniqueConstraint('serial_number', name='uq_sensor_serial_number'),
        CheckConstraint("sampling_frequency_seconds > 0", name="positive_sampling_frequency"),
        CheckConstraint("data_retention_days > 0", name="positive_data_retention"),
        CheckConstraint("alert_min_threshold IS NULL OR alert_max_threshold IS NULL OR alert_min_threshold <= alert_max_threshold", name="valid_alert_thresholds"),
        CheckConstraint("critical_min_threshold IS NULL OR critical_max_threshold IS NULL OR critical_min_threshold <= critical_max_threshold", name="valid_critical_thresholds"),
    )
    
    def is_calibration_due(self) -> bool:
        """Check if sensor calibration is due"""
        if not self.next_calibration_date:
            return True
        return datetime.now(timezone.utc) >= self.next_calibration_date.replace(tzinfo=timezone.utc)
    
    def check_alert_conditions(self, value: float) -> Dict[str, bool]:
        """Check if sensor reading triggers alerts"""
        alerts = {
            'warning': False,
            'critical': False
        }
        
        if self.alert_min_threshold is not None and value < self.alert_min_threshold:
            alerts['warning'] = True
        if self.alert_max_threshold is not None and value > self.alert_max_threshold:
            alerts['warning'] = True
        if self.critical_min_threshold is not None and value < self.critical_min_threshold:
            alerts['critical'] = True
        if self.critical_max_threshold is not None and value > self.critical_max_threshold:
            alerts['critical'] = True
        
        return alerts

class SensorData(BaseModel, TimestampMixin):
    """Sensor data readings"""
    __tablename__ = "sensor_data"
    
    # Sensor relationship
    sensor_id = Column(UUID(as_uuid=True), ForeignKey('sensors.id'), nullable=False)
    sensor = relationship("Sensor", back_populates="sensor_data")
    
    # Equipment relationship (denormalized for performance)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'), nullable=True)
    equipment = relationship("Equipment", back_populates="sensor_data")
    
    # Measurement data
    measured_value = Column(Float, nullable=False)
    measurement_units = Column(String(20), nullable=False)
    
    # Data quality
    data_quality = Column(String(20), nullable=False, default="good")  # good, uncertain, bad
    data_status = Column(String(20), nullable=False, default="normal")  # normal, alarm, warning
    
    # Alert information
    alert_triggered = Column(Boolean, nullable=False, default=False)
    alert_level = Column(String(20), nullable=True)  # warning, critical
    alert_message = Column(String(500), nullable=True)
    
    # Calibration information
    calibration_factor = Column(Float, nullable=True)
    calibration_offset = Column(Float, nullable=True)
    
    # Raw data (before calibration)
    raw_value = Column(Float, nullable=True)
    
    # Batch context (if applicable)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    batch_stage = Column(String(100), nullable=True)
    
    # Environmental context
    ambient_temperature = Column(Float, nullable=True)
    ambient_humidity = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('idx_sensor_data_sensor', 'sensor_id'),
        Index('idx_sensor_data_timestamp', 'timestamp'),
        Index('idx_sensor_data_equipment', 'equipment_id'),
        Index('idx_sensor_data_batch', 'batch_id'),
        Index('idx_sensor_data_quality', 'data_quality'),
        Index('idx_sensor_data_status', 'data_status'),
        Index('idx_sensor_data_alert', 'alert_triggered'),
        # Partition by timestamp for performance
        Index('idx_sensor_data_timestamp_sensor', 'timestamp', 'sensor_id'),
        CheckConstraint("data_quality IN ('good', 'uncertain', 'bad')", name="valid_data_quality"),
        CheckConstraint("data_status IN ('normal', 'alarm', 'warning')", name="valid_data_status"),
        CheckConstraint("alert_level IS NULL OR alert_level IN ('warning', 'critical')", name="valid_alert_level"),
    )

class SensorCalibration(BaseModel, CalibrationMixin, ApprovalMixin):
    """Sensor calibration records"""
    __tablename__ = "sensor_calibration"
    
    # Sensor relationship
    sensor_id = Column(UUID(as_uuid=True), ForeignKey('sensors.id'), nullable=False)
    sensor = relationship("Sensor", back_populates="calibration_records")
    
    # Calibration points
    calibration_points = Column(JSON, nullable=False)
    reference_values = Column(JSON, nullable=False)
    measured_values = Column(JSON, nullable=False)
    
    # Calibration curve
    calibration_curve = Column(JSON, nullable=True)
    linearity = Column(Float, nullable=True)
    correlation_coefficient = Column(Float, nullable=True)
    
    # Calibration factors
    calibration_factor = Column(Float, nullable=True)
    calibration_offset = Column(Float, nullable=True)
    
    # Uncertainty
    measurement_uncertainty = Column(Float, nullable=True)
    
    # Environmental conditions
    calibration_temperature = Column(Float, nullable=True)
    calibration_humidity = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('idx_sensor_calibration_sensor', 'sensor_id'),
        Index('idx_sensor_calibration_date', 'calibration_date'),
        Index('idx_sensor_calibration_passed', 'calibration_passed'),
        CheckConstraint("linearity IS NULL OR (linearity >= 0 AND linearity <= 1)", name="valid_linearity"),
        CheckConstraint("correlation_coefficient IS NULL OR (correlation_coefficient >= -1 AND correlation_coefficient <= 1)", name="valid_correlation"),
    )

class EquipmentUsageLog(BaseModel, TimestampMixin):
    """Equipment usage logging"""
    __tablename__ = "equipment_usage_log"
    
    # Equipment relationship
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'), nullable=False)
    equipment = relationship("Equipment", back_populates="usage_logs")
    
    # Usage information
    usage_type = Column(String(50), nullable=False)  # startup, shutdown, operation, maintenance
    usage_description = Column(String(500), nullable=True)
    
    # User information
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_role = Column(String(100), nullable=False)
    
    # Batch context (if applicable)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    batch_stage = Column(String(100), nullable=True)
    
    # Operating parameters
    operating_parameters = Column(JSON, nullable=True)
    
    # Duration
    duration_minutes = Column(Integer, nullable=True)
    
    # Status
    operation_successful = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_equipment_usage_equipment', 'equipment_id'),
        Index('idx_equipment_usage_timestamp', 'timestamp'),
        Index('idx_equipment_usage_type', 'usage_type'),
        Index('idx_equipment_usage_user', 'user_id'),
        Index('idx_equipment_usage_batch', 'batch_id'),
        CheckConstraint("usage_type IN ('startup', 'shutdown', 'operation', 'maintenance', 'calibration')", name="valid_usage_type"),
        CheckConstraint("duration_minutes IS NULL OR duration_minutes >= 0", name="non_negative_duration"),
    )

class EquipmentAlarm(BaseModel, TimestampMixin, StatusMixin):
    """Equipment alarms and alerts"""
    __tablename__ = "equipment_alarms"
    
    # Equipment relationship
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'), nullable=False)
    
    # Sensor relationship (if applicable)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey('sensors.id'), nullable=True)
    
    # Alarm information
    alarm_type = Column(String(50), nullable=False)  # sensor, equipment, process, system
    alarm_level = Column(String(20), nullable=False)  # warning, critical, emergency
    alarm_message = Column(String(500), nullable=False)
    
    # Trigger information
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    parameter_name = Column(String(100), nullable=True)
    
    # Acknowledgment
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_action = Column(Text, nullable=True)
    
    # Batch context
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_equipment_alarm_equipment', 'equipment_id'),
        Index('idx_equipment_alarm_timestamp', 'timestamp'),
        Index('idx_equipment_alarm_type', 'alarm_type'),
        Index('idx_equipment_alarm_level', 'alarm_level'),
        Index('idx_equipment_alarm_acknowledged', 'acknowledged'),
        Index('idx_equipment_alarm_resolved', 'resolved'),
        CheckConstraint("alarm_type IN ('sensor', 'equipment', 'process', 'system')", name="valid_alarm_type"),
        CheckConstraint("alarm_level IN ('warning', 'critical', 'emergency')", name="valid_alarm_level"),
        CheckConstraint("acknowledged = FALSE OR acknowledged_by IS NOT NULL", name="acknowledged_requires_user"),
        CheckConstraint("resolved = FALSE OR resolved_by IS NOT NULL", name="resolved_requires_user"),
    )