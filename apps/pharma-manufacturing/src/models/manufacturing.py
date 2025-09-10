"""
Pharmaceutical Manufacturing Data Models
GMP-compliant database models for manufacturing operations
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

Base = declarative_base()

# Enums for manufacturing system
class BatchStatus(str, Enum):
    """Batch production status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    QC_TESTING = "qc_testing"
    QC_PASSED = "qc_passed"
    QC_FAILED = "qc_failed"
    RELEASED = "released"
    RECALLED = "recalled"
    QUARANTINED = "quarantined"

class WorkflowStage(str, Enum):
    """Manufacturing workflow stages"""
    DISPENSING = "dispensing"
    MIXING = "mixing"
    GRANULATION = "granulation"
    TABLETING = "tableting"
    COATING = "coating"
    PACKAGING = "packaging"
    LABELING = "labeling"
    COMPLETED = "completed"

class EquipmentStatus(str, Enum):
    """Equipment operational status"""
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    CALIBRATION = "calibration"
    OFFLINE = "offline"
    ERROR = "error"

class QualityTestStatus(str, Enum):
    """Quality test status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    RETEST = "retest"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# SQLAlchemy Models
class Product(Base):
    __tablename__ = "products"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    dosage_form = Column(String(50), nullable=False)  # tablet, capsule, liquid, etc.
    strength = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Regulatory information
    ndc_number = Column(String(20))  # National Drug Code
    regulatory_status = Column(String(50), nullable=False, default="approved")
    
    # Manufacturing specifications
    shelf_life_months = Column(Integer, nullable=False)
    storage_conditions = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    batches = relationship("Batch", back_populates="product")

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Production information
    planned_quantity = Column(Integer, nullable=False)
    actual_quantity = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default=BatchStatus.PLANNED)
    current_stage = Column(String(20), nullable=False, default=WorkflowStage.DISPENSING)
    
    # Dates
    planned_start_date = Column(DateTime(timezone=True), nullable=False)
    actual_start_date = Column(DateTime(timezone=True))
    planned_completion_date = Column(DateTime(timezone=True), nullable=False)
    actual_completion_date = Column(DateTime(timezone=True))
    
    # Quality and compliance
    manufacturing_instructions = Column(Text)
    deviations = Column(JSONB)  # JSON array of deviation records
    environmental_conditions = Column(JSONB)  # Environmental data during production
    
    # Audit trail
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    product = relationship("Product", back_populates="batches")
    workflow_stages = relationship("BatchWorkflowStage", back_populates="batch")
    quality_tests = relationship("QualityTest", back_populates="batch")
    material_usage = relationship("MaterialUsage", back_populates="batch")

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    equipment_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    equipment_type = Column(String(50), nullable=False)  # mixer, tablet_press, coater, etc.
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    
    # Operational status
    status = Column(String(20), nullable=False, default=EquipmentStatus.OPERATIONAL)
    location = Column(String(100), nullable=False)
    
    # Maintenance and calibration
    last_maintenance_date = Column(DateTime(timezone=True))
    next_maintenance_date = Column(DateTime(timezone=True))
    last_calibration_date = Column(DateTime(timezone=True))
    next_calibration_date = Column(DateTime(timezone=True))
    
    # Operating parameters
    operating_parameters = Column(JSONB)  # JSON of parameter specifications
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="equipment")
    workflow_stages = relationship("BatchWorkflowStage", back_populates="equipment")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    equipment_id = Column(PGUUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    
    # Sensor data
    sensor_type = Column(String(50), nullable=False)  # temperature, pressure, humidity, etc.
    value = Column(Numeric(10, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Specifications and limits
    lower_limit = Column(Numeric(10, 4))
    upper_limit = Column(Numeric(10, 4))
    target_value = Column(Numeric(10, 4))
    
    # Status
    in_specification = Column(Boolean, nullable=False, default=True)
    deviation_magnitude = Column(Numeric(10, 4))
    
    # Metadata
    measurement_method = Column(String(100))
    calibration_due_date = Column(DateTime(timezone=True))
    
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)
    
    # Relationships
    equipment = relationship("Equipment", back_populates="sensor_readings")

class RawMaterial(Base):
    __tablename__ = "raw_materials"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    material_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    supplier = Column(String(200), nullable=False)
    
    # Material specifications
    grade = Column(String(50))
    cas_number = Column(String(20))
    molecular_formula = Column(String(100))
    
    # Inventory management
    current_stock = Column(Numeric(10, 4), nullable=False, default=0)
    unit_of_measure = Column(String(20), nullable=False)
    reorder_level = Column(Numeric(10, 4), nullable=False)
    
    # Quality specifications
    specifications = Column(JSONB)  # JSON of quality specifications
    storage_conditions = Column(Text)
    
    # Regulatory information
    regulatory_status = Column(String(50), nullable=False, default="approved")
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    material_lots = relationship("MaterialLot", back_populates="raw_material")
    material_usage = relationship("MaterialUsage", back_populates="raw_material")

class MaterialLot(Base):
    __tablename__ = "material_lots"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    lot_number = Column(String(50), nullable=False, index=True)
    raw_material_id = Column(PGUUID(as_uuid=True), ForeignKey("raw_materials.id"), nullable=False)
    
    # Lot information
    quantity_received = Column(Numeric(10, 4), nullable=False)
    quantity_remaining = Column(Numeric(10, 4), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    
    # Quality information
    coa_number = Column(String(50))  # Certificate of Analysis
    test_results = Column(JSONB)  # JSON of test results
    
    # Status
    status = Column(String(20), nullable=False, default="approved")
    quarantine_reason = Column(Text)
    
    # Dates
    received_date = Column(DateTime(timezone=True), nullable=False)
    tested_date = Column(DateTime(timezone=True))
    approved_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    raw_material = relationship("RawMaterial", back_populates="material_lots")

class MaterialUsage(Base):
    __tablename__ = "material_usage"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    raw_material_id = Column(PGUUID(as_uuid=True), ForeignKey("raw_materials.id"), nullable=False)
    
    # Usage information
    theoretical_quantity = Column(Numeric(10, 4), nullable=False)
    actual_quantity = Column(Numeric(10, 4), nullable=False)
    variance = Column(Numeric(10, 4))
    variance_percentage = Column(Numeric(5, 2))
    
    # Lot tracking
    lot_numbers = Column(JSONB)  # JSON array of lot numbers used
    
    # Workflow stage where material was used
    workflow_stage = Column(String(20), nullable=False)
    
    # Personnel
    dispensed_by = Column(String(100), nullable=False)
    verified_by = Column(String(100))
    
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    batch = relationship("Batch", back_populates="material_usage")
    raw_material = relationship("RawMaterial", back_populates="material_usage")

class BatchWorkflowStage(Base):
    __tablename__ = "batch_workflow_stages"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    equipment_id = Column(PGUUID(as_uuid=True), ForeignKey("equipment.id"))
    
    # Stage information
    stage = Column(String(20), nullable=False)
    stage_order = Column(Integer, nullable=False)
    
    # Timing
    planned_start_time = Column(DateTime(timezone=True))
    actual_start_time = Column(DateTime(timezone=True))
    planned_end_time = Column(DateTime(timezone=True))
    actual_end_time = Column(DateTime(timezone=True))
    
    # Status and results
    status = Column(String(20), nullable=False, default="pending")
    stage_yield = Column(Numeric(5, 2))  # Percentage
    
    # Process parameters
    process_parameters = Column(JSONB)  # JSON of actual process parameters
    target_parameters = Column(JSONB)   # JSON of target process parameters
    
    # Personnel
    operator = Column(String(100), nullable=False)
    supervisor = Column(String(100))
    
    # Documentation
    batch_record_notes = Column(Text)
    deviations = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    batch = relationship("Batch", back_populates="workflow_stages")
    equipment = relationship("Equipment", back_populates="workflow_stages")

class QualityTest(Base):
    __tablename__ = "quality_tests"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    
    # Test information
    test_type = Column(String(100), nullable=False)
    test_method = Column(String(100), nullable=False)
    specification = Column(Text, nullable=False)
    
    # Results
    result_value = Column(String(200))
    result_units = Column(String(50))
    pass_fail = Column(Boolean)
    status = Column(String(20), nullable=False, default=QualityTestStatus.PENDING)
    
    # Limits and specifications
    lower_limit = Column(Numeric(10, 4))
    upper_limit = Column(Numeric(10, 4))
    target_value = Column(Numeric(10, 4))
    
    # Test execution
    tested_by = Column(String(100), nullable=False)
    reviewed_by = Column(String(100))
    approved_by = Column(String(100))
    
    # Timing
    test_date = Column(DateTime(timezone=True), nullable=False)
    reviewed_date = Column(DateTime(timezone=True))
    approved_date = Column(DateTime(timezone=True))
    
    # Documentation
    test_notes = Column(Text)
    deviation_reason = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    batch = relationship("Batch", back_populates="quality_tests")

class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Location information
    room_id = Column(String(50), nullable=False, index=True)
    room_name = Column(String(100), nullable=False)
    room_classification = Column(String(50), nullable=False)  # ISO class, etc.
    
    # Environmental parameters
    temperature = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    pressure = Column(Numeric(8, 4))
    particle_count = Column(Integer)
    air_changes_per_hour = Column(Numeric(5, 1))
    
    # Specifications
    temperature_spec_min = Column(Numeric(5, 2))
    temperature_spec_max = Column(Numeric(5, 2))
    humidity_spec_min = Column(Numeric(5, 2))
    humidity_spec_max = Column(Numeric(5, 2))
    
    # Status
    in_specification = Column(Boolean, nullable=False, default=True)
    alert_generated = Column(Boolean, nullable=False, default=False)
    
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Alert information
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Source information
    source_type = Column(String(50), nullable=False)  # equipment, environmental, quality, etc.
    source_id = Column(String(100))
    
    # Status
    status = Column(String(20), nullable=False, default="active")
    acknowledged = Column(Boolean, nullable=False, default=False)
    resolved = Column(Boolean, nullable=False, default=False)
    
    # Personnel
    acknowledged_by = Column(String(100))
    resolved_by = Column(String(100))
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Additional data
    batch_metadata = Column(JSONB)