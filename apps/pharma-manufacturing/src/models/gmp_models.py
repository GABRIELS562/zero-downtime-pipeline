"""
Good Manufacturing Practice (GMP) Data Models
Comprehensive models for pharmaceutical quality control and validation
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4
import enum

Base = declarative_base()

class EnvironmentalParameterType(enum.Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    PARTICLE_COUNT = "particle_count"
    AIRFLOW = "airflow"
    CO2_LEVEL = "co2_level"
    VIABLE_COUNT = "viable_count"

class EquipmentStatus(enum.Enum):
    OPERATIONAL = "operational"
    CALIBRATION_DUE = "calibration_due"
    OUT_OF_SERVICE = "out_of_service"
    MAINTENANCE = "maintenance"
    VALIDATION_REQUIRED = "validation_required"

class TestStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    OUT_OF_SPECIFICATION = "out_of_specification"
    RETESTING = "retesting"

class ValidationStatus(enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    EXECUTED = "executed"
    COMPLETED = "completed"
    EXPIRED = "expired"

class TrainingStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"

class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EnvironmentalMonitoring(Base):
    """Environmental monitoring records for clean rooms and manufacturing areas"""
    __tablename__ = "environmental_monitoring"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    monitoring_point_id = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)
    area_classification = Column(String(20), nullable=False)  # ISO 5, ISO 7, ISO 8, etc.
    parameter_type = Column(Enum(EnvironmentalParameterType), nullable=False)
    measured_value = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    specification_min = Column(Float)
    specification_max = Column(Float)
    is_within_specification = Column(Boolean, nullable=False)
    deviation_percentage = Column(Float)
    measurement_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    equipment_id = Column(UUID(as_uuid=True))
    calibration_due_date = Column(DateTime(timezone=True))
    operator_id = Column(UUID(as_uuid=True))
    alert_triggered = Column(Boolean, default=False)
    corrective_action_required = Column(Boolean, default=False)
    notes = Column(Text)
    
class EquipmentCalibration(Base):
    """Equipment calibration and validation records"""
    __tablename__ = "equipment_calibration"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    equipment_id = Column(UUID(as_uuid=True), nullable=False)
    equipment_name = Column(String(100), nullable=False)
    equipment_type = Column(String(50), nullable=False)
    manufacturer = Column(String(100))
    model_number = Column(String(50))
    serial_number = Column(String(50))
    location = Column(String(100), nullable=False)
    calibration_procedure = Column(String(100), nullable=False)
    calibration_date = Column(DateTime(timezone=True), nullable=False)
    next_calibration_date = Column(DateTime(timezone=True), nullable=False)
    calibration_frequency_months = Column(Integer, nullable=False)
    performed_by = Column(UUID(as_uuid=True), nullable=False)
    verified_by = Column(UUID(as_uuid=True))
    calibration_standard = Column(String(100))
    standard_certificate = Column(String(100))
    calibration_results = Column(JSON)
    accuracy_achieved = Column(Float)
    status = Column(Enum(EquipmentStatus), nullable=False)
    is_qualified = Column(Boolean, default=False)
    qualification_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    
class RawMaterialTesting(Base):
    """Raw material testing and certificate of analysis management"""
    __tablename__ = "raw_material_testing"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    material_id = Column(UUID(as_uuid=True), nullable=False)
    material_name = Column(String(100), nullable=False)
    supplier = Column(String(100), nullable=False)
    lot_number = Column(String(50), nullable=False)
    receipt_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True))
    quantity_received = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    coa_number = Column(String(50))
    coa_received = Column(Boolean, default=False)
    testing_required = Column(Boolean, default=True)
    testing_status = Column(Enum(TestStatus), default=TestStatus.PENDING)
    test_started_date = Column(DateTime(timezone=True))
    test_completed_date = Column(DateTime(timezone=True))
    tested_by = Column(UUID(as_uuid=True))
    reviewed_by = Column(UUID(as_uuid=True))
    approved_by = Column(UUID(as_uuid=True))
    test_results = Column(JSON)
    specifications = Column(JSON)
    overall_result = Column(Enum(TestStatus))
    quarantine_status = Column(Boolean, default=True)
    release_date = Column(DateTime(timezone=True))
    storage_conditions = Column(JSON)
    notes = Column(Text)

class InProcessTesting(Base):
    """In-process quality control testing during manufacturing"""
    __tablename__ = "in_process_testing"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    manufacturing_stage = Column(String(50), nullable=False)
    test_point_id = Column(String(50), nullable=False)
    test_name = Column(String(100), nullable=False)
    test_method = Column(String(100), nullable=False)
    sample_id = Column(String(50), nullable=False)
    sampling_time = Column(DateTime(timezone=True), nullable=False)
    test_start_time = Column(DateTime(timezone=True))
    test_completion_time = Column(DateTime(timezone=True))
    performed_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True))
    test_parameters = Column(JSON)
    specifications = Column(JSON)
    test_results = Column(JSON)
    result_status = Column(Enum(TestStatus), nullable=False)
    deviation_investigation = Column(Text)
    corrective_action = Column(Text)
    impact_assessment = Column(Text)
    batch_disposition = Column(String(50))
    notes = Column(Text)

class FinishedProductTesting(Base):
    """Finished product testing and release criteria validation"""
    __tablename__ = "finished_product_testing"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    product_name = Column(String(100), nullable=False)
    product_code = Column(String(50), nullable=False)
    batch_size = Column(Float, nullable=False)
    manufacturing_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    sampling_plan = Column(JSON)
    test_suite = Column(JSON)
    testing_started = Column(DateTime(timezone=True))
    testing_completed = Column(DateTime(timezone=True))
    performed_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True))
    approved_by = Column(UUID(as_uuid=True))
    test_results = Column(JSON)
    release_specifications = Column(JSON)
    overall_result = Column(Enum(TestStatus), nullable=False)
    release_decision = Column(String(20))  # Released, Rejected, Quarantine
    release_date = Column(DateTime(timezone=True))
    certificate_of_analysis = Column(Text)
    stability_data = Column(JSON)
    packaging_integrity = Column(JSON)
    labeling_verification = Column(JSON)
    notes = Column(Text)

class CleanRoomMonitoring(Base):
    """Clean room monitoring and contamination control"""
    __tablename__ = "clean_room_monitoring"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clean_room_id = Column(String(50), nullable=False)
    room_classification = Column(String(20), nullable=False)  # ISO 5, ISO 7, etc.
    monitoring_date = Column(DateTime(timezone=True), nullable=False)
    particle_counts = Column(JSON)  # Different particle sizes
    viable_counts = Column(JSON)  # Microbial counts
    environmental_conditions = Column(JSON)  # Temp, humidity, pressure
    personnel_count = Column(Integer)
    activity_level = Column(String(20))
    hvac_status = Column(JSON)
    cleaning_performed = Column(Boolean, default=False)
    cleaning_agent = Column(String(100))
    disinfection_performed = Column(Boolean, default=False)
    disinfectant_used = Column(String(100))
    monitoring_frequency = Column(String(20))  # Continuous, hourly, daily
    alert_levels_exceeded = Column(Boolean, default=False)
    corrective_actions = Column(JSON)
    performed_by = Column(UUID(as_uuid=True), nullable=False)
    verified_by = Column(UUID(as_uuid=True))
    notes = Column(Text)

class PersonnelTraining(Base):
    """Personnel training and qualification tracking"""
    __tablename__ = "personnel_training"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=False)
    training_program_id = Column(String(50), nullable=False)
    training_name = Column(String(100), nullable=False)
    training_type = Column(String(50), nullable=False)  # GMP, Safety, SOP, etc.
    training_category = Column(String(50), nullable=False)  # Initial, Refresher, Change Control
    trainer = Column(String(100), nullable=False)
    training_date = Column(DateTime(timezone=True), nullable=False)
    completion_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    training_duration_hours = Column(Float)
    training_materials = Column(JSON)
    assessment_required = Column(Boolean, default=True)
    assessment_score = Column(Float)
    passing_score = Column(Float, default=80.0)
    status = Column(Enum(TrainingStatus), nullable=False)
    certificate_issued = Column(Boolean, default=False)
    certificate_number = Column(String(50))
    retraining_required = Column(Boolean, default=False)
    competency_demonstrated = Column(Boolean, default=False)
    supervisor_approval = Column(UUID(as_uuid=True))
    notes = Column(Text)

class ValidationProtocol(Base):
    """Validation protocols for equipment and processes"""
    __tablename__ = "validation_protocol"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    protocol_number = Column(String(50), nullable=False, unique=True)
    validation_type = Column(String(50), nullable=False)  # IQ, OQ, PQ, CSV, etc.
    equipment_process_id = Column(UUID(as_uuid=True), nullable=False)
    equipment_process_name = Column(String(100), nullable=False)
    validation_scope = Column(Text, nullable=False)
    validation_objectives = Column(JSON)
    acceptance_criteria = Column(JSON)
    test_protocols = Column(JSON)
    responsible_person = Column(UUID(as_uuid=True), nullable=False)
    validation_team = Column(JSON)
    planned_start_date = Column(DateTime(timezone=True), nullable=False)
    planned_completion_date = Column(DateTime(timezone=True), nullable=False)
    actual_start_date = Column(DateTime(timezone=True))
    actual_completion_date = Column(DateTime(timezone=True))
    status = Column(Enum(ValidationStatus), nullable=False)
    approval_date = Column(DateTime(timezone=True))
    approved_by = Column(UUID(as_uuid=True))
    validation_results = Column(JSON)
    deviations_identified = Column(JSON)
    corrective_actions = Column(JSON)
    revalidation_date = Column(DateTime(timezone=True))
    change_control_impact = Column(Boolean, default=False)
    notes = Column(Text)

class QualityMetrics(Base):
    """Quality metrics for manufacturing efficiency tracking"""
    __tablename__ = "quality_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metric_date = Column(DateTime(timezone=True), nullable=False)
    production_line = Column(String(50), nullable=False)
    product_family = Column(String(50))
    total_batches_produced = Column(Integer, default=0)
    batches_passed = Column(Integer, default=0)
    batches_failed = Column(Integer, default=0)
    batches_reworked = Column(Integer, default=0)
    first_pass_yield = Column(Float)  # Percentage
    overall_yield = Column(Float)  # Percentage
    defect_rate = Column(Float)  # PPM
    right_first_time = Column(Float)  # Percentage
    cost_of_quality = Column(Float)
    cost_of_poor_quality = Column(Float)
    customer_complaints = Column(Integer, default=0)
    regulatory_observations = Column(Integer, default=0)
    environmental_excursions = Column(Integer, default=0)
    equipment_downtime_hours = Column(Float, default=0)
    calibration_overdue = Column(Integer, default=0)
    training_compliance = Column(Float)  # Percentage
    cycle_time_minutes = Column(Float)
    changeover_time_minutes = Column(Float)
    calculated_by = Column(UUID(as_uuid=True), nullable=False)
    notes = Column(Text)

class RiskAssessment(Base):
    """Risk assessment and mitigation tracking"""
    __tablename__ = "risk_assessment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    risk_id = Column(String(50), nullable=False, unique=True)
    risk_category = Column(String(50), nullable=False)  # Product Quality, Patient Safety, etc.
    process_area = Column(String(100), nullable=False)
    risk_description = Column(Text, nullable=False)
    potential_causes = Column(JSON)
    potential_effects = Column(JSON)
    current_controls = Column(JSON)
    probability_score = Column(Integer, nullable=False)  # 1-5 scale
    severity_score = Column(Integer, nullable=False)  # 1-5 scale
    detectability_score = Column(Integer, nullable=False)  # 1-5 scale
    risk_priority_number = Column(Integer)  # Probability × Severity × Detectability
    risk_level = Column(Enum(RiskLevel), nullable=False)
    mitigation_actions = Column(JSON)
    responsible_person = Column(UUID(as_uuid=True), nullable=False)
    target_completion_date = Column(DateTime(timezone=True))
    actual_completion_date = Column(DateTime(timezone=True))
    residual_probability = Column(Integer)
    residual_severity = Column(Integer)
    residual_detectability = Column(Integer)
    residual_rpn = Column(Integer)
    residual_risk_level = Column(Enum(RiskLevel))
    review_date = Column(DateTime(timezone=True))
    reviewed_by = Column(UUID(as_uuid=True))
    effectiveness_verified = Column(Boolean, default=False)
    created_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)