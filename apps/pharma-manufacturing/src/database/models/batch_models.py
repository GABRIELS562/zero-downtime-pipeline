"""
Batch and Lot Tracking Models
Complete genealogy tracking for pharmaceutical manufacturing batches
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Any, Optional

from .base import BaseModel, TimestampMixin, StatusMixin, ApprovalMixin, BatchTrackingMixin

class Product(BaseModel):
    """Product master data for pharmaceutical products"""
    __tablename__ = "products"
    
    # Product identification
    product_code = Column(String(50), nullable=False, unique=True)
    product_name = Column(String(200), nullable=False)
    product_type = Column(String(50), nullable=False)  # tablet, capsule, liquid, injection
    
    # Regulatory information
    nda_number = Column(String(20), nullable=True)  # New Drug Application
    anda_number = Column(String(20), nullable=True)  # Abbreviated New Drug Application
    
    # Product specifications
    active_ingredient = Column(String(100), nullable=False)
    strength = Column(String(50), nullable=False)
    dosage_form = Column(String(50), nullable=False)
    
    # Manufacturing information
    manufacturing_process = Column(String(100), nullable=False)
    standard_batch_size = Column(Float, nullable=False)
    batch_size_units = Column(String(20), nullable=False)
    
    # Shelf life and storage
    shelf_life_months = Column(Integer, nullable=False)
    storage_conditions = Column(JSON, nullable=False)
    
    # Bill of materials
    bom_version = Column(String(20), nullable=False, default="1.0")
    bom_data = Column(JSON, nullable=False)
    
    # Relationships
    batches = relationship("Batch", back_populates="product", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_product_code', 'product_code'),
        Index('idx_product_name', 'product_name'),
        Index('idx_product_type', 'product_type'),
        CheckConstraint("strength ~ '^[0-9.]+[a-zA-Z]+$'", name="valid_strength_format"),
        CheckConstraint("shelf_life_months > 0", name="positive_shelf_life"),
        CheckConstraint("standard_batch_size > 0", name="positive_batch_size"),
    )

class Batch(BaseModel, BatchTrackingMixin, StatusMixin, ApprovalMixin):
    """Main batch tracking table with complete genealogy"""
    __tablename__ = "batches"
    
    # Product relationship
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    product = relationship("Product", back_populates="batches")
    
    # Manufacturing information
    manufacturing_line = Column(String(50), nullable=False)
    manufacturing_order = Column(String(100), nullable=False)
    planned_start_date = Column(DateTime(timezone=True), nullable=False)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    planned_completion_date = Column(DateTime(timezone=True), nullable=False)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Batch size and yield
    theoretical_yield = Column(Float, nullable=False)
    actual_yield = Column(Float, nullable=True)
    yield_percentage = Column(Float, nullable=True)
    
    # Quality information
    quality_review_required = Column(Boolean, nullable=False, default=True)
    quality_review_completed = Column(Boolean, nullable=False, default=False)
    quality_reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    quality_review_date = Column(DateTime(timezone=True), nullable=True)
    
    # Genealogy tracking
    parent_batches = relationship(
        "BatchGenealogy", 
        foreign_keys="BatchGenealogy.child_batch_id",
        back_populates="child_batch"
    )
    child_batches = relationship(
        "BatchGenealogy",
        foreign_keys="BatchGenealogy.parent_batch_id", 
        back_populates="parent_batch"
    )
    
    # Manufacturing stages
    stages = relationship("BatchStage", back_populates="batch", cascade="all, delete-orphan")
    
    # Materials used
    materials_used = relationship("BatchMaterial", back_populates="batch", cascade="all, delete-orphan")
    
    # Test results
    test_results = relationship("BatchTestResult", back_populates="batch", cascade="all, delete-orphan")
    
    # Deviations
    deviations = relationship("BatchDeviation", back_populates="batch", cascade="all, delete-orphan")
    
    # Lots produced from this batch
    lots = relationship("Lot", back_populates="batch", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_batch_number', 'batch_number'),
        Index('idx_manufacturing_date', 'manufacturing_date'),
        Index('idx_batch_status', 'batch_status'),
        Index('idx_quality_status', 'quality_status'),
        Index('idx_manufacturing_line', 'manufacturing_line'),
        Index('idx_manufacturing_order', 'manufacturing_order'),
        UniqueConstraint('batch_number', name='uq_batch_number'),
        CheckConstraint("actual_yield IS NULL OR actual_yield >= 0", name="non_negative_yield"),
        CheckConstraint("yield_percentage IS NULL OR (yield_percentage >= 0 AND yield_percentage <= 150)", name="valid_yield_percentage"),
        CheckConstraint("planned_start_date <= planned_completion_date", name="valid_planned_dates"),
        CheckConstraint("actual_start_date IS NULL OR actual_completion_date IS NULL OR actual_start_date <= actual_completion_date", name="valid_actual_dates"),
    )
    
    def calculate_yield_percentage(self):
        """Calculate yield percentage"""
        if self.actual_yield and self.theoretical_yield:
            self.yield_percentage = (self.actual_yield / self.theoretical_yield) * 100
    
    def get_genealogy_tree(self, session) -> Dict[str, Any]:
        """Get complete genealogy tree for this batch"""
        def build_tree(batch_id):
            parents = session.query(BatchGenealogy).filter(
                BatchGenealogy.child_batch_id == batch_id
            ).all()
            
            tree = {
                'batch_id': str(batch_id),
                'parents': []
            }
            
            for parent_rel in parents:
                parent_tree = build_tree(parent_rel.parent_batch_id)
                tree['parents'].append(parent_tree)
            
            return tree
        
        return build_tree(self.id)
    
    def get_all_descendants(self, session) -> List['Batch']:
        """Get all descendant batches"""
        descendants = []
        
        def collect_descendants(batch_id):
            children = session.query(BatchGenealogy).filter(
                BatchGenealogy.parent_batch_id == batch_id
            ).all()
            
            for child_rel in children:
                child_batch = session.query(Batch).filter(
                    Batch.id == child_rel.child_batch_id
                ).first()
                if child_batch:
                    descendants.append(child_batch)
                    collect_descendants(child_batch.id)
        
        collect_descendants(self.id)
        return descendants

class BatchGenealogy(BaseModel):
    """Batch genealogy tracking for parent-child relationships"""
    __tablename__ = "batch_genealogy"
    
    # Parent-child relationship
    parent_batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    child_batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    
    # Relationship type
    relationship_type = Column(String(50), nullable=False)  # split, blend, rework, etc.
    
    # Quantity transferred
    quantity_transferred = Column(Float, nullable=False)
    quantity_units = Column(String(20), nullable=False)
    
    # Transfer information
    transfer_date = Column(DateTime(timezone=True), nullable=False)
    transfer_reason = Column(Text, nullable=False)
    
    # Relationships
    parent_batch = relationship("Batch", foreign_keys=[parent_batch_id], back_populates="child_batches")
    child_batch = relationship("Batch", foreign_keys=[child_batch_id], back_populates="parent_batches")
    
    __table_args__ = (
        Index('idx_parent_batch', 'parent_batch_id'),
        Index('idx_child_batch', 'child_batch_id'),
        Index('idx_relationship_type', 'relationship_type'),
        Index('idx_transfer_date', 'transfer_date'),
        UniqueConstraint('parent_batch_id', 'child_batch_id', name='uq_batch_genealogy'),
        CheckConstraint("quantity_transferred > 0", name="positive_quantity"),
        CheckConstraint("parent_batch_id != child_batch_id", name="no_self_reference"),
    )

class BatchStage(BaseModel, TimestampMixin, StatusMixin):
    """Manufacturing stages within a batch"""
    __tablename__ = "batch_stages"
    
    # Batch relationship
    batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    batch = relationship("Batch", back_populates="stages")
    
    # Stage information
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    
    # Timing
    planned_start_time = Column(DateTime(timezone=True), nullable=False)
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    planned_end_time = Column(DateTime(timezone=True), nullable=False)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Stage parameters
    stage_parameters = Column(JSON, nullable=True)
    
    # Equipment used
    equipment_id = Column(UUID(as_uuid=True), nullable=True)
    equipment_name = Column(String(100), nullable=True)
    
    # Personnel
    operator_id = Column(UUID(as_uuid=True), nullable=False)
    supervisor_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Stage results
    stage_results = Column(JSON, nullable=True)
    stage_passed = Column(Boolean, nullable=True)
    
    # Environmental conditions
    environmental_conditions = relationship("BatchStageEnvironment", back_populates="stage", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_batch_stage', 'batch_id'),
        Index('idx_stage_name', 'stage_name'),
        Index('idx_stage_order', 'stage_order'),
        Index('idx_operator', 'operator_id'),
        UniqueConstraint('batch_id', 'stage_order', name='uq_batch_stage_order'),
        CheckConstraint("stage_order > 0", name="positive_stage_order"),
        CheckConstraint("planned_start_time <= planned_end_time", name="valid_planned_stage_times"),
        CheckConstraint("actual_start_time IS NULL OR actual_end_time IS NULL OR actual_start_time <= actual_end_time", name="valid_actual_stage_times"),
    )

class BatchStageEnvironment(BaseModel, TimestampMixin):
    """Environmental conditions during batch stages"""
    __tablename__ = "batch_stage_environment"
    
    # Stage relationship
    stage_id = Column(UUID(as_uuid=True), ForeignKey('batch_stages.id'), nullable=False)
    stage = relationship("BatchStage", back_populates="environmental_conditions")
    
    # Environmental parameters
    parameter_name = Column(String(50), nullable=False)
    measured_value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=True)
    min_limit = Column(Float, nullable=True)
    max_limit = Column(Float, nullable=True)
    units = Column(String(20), nullable=False)
    
    # Measurement details
    measurement_time = Column(DateTime(timezone=True), nullable=False)
    measurement_method = Column(String(100), nullable=False)
    measured_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Compliance
    within_limits = Column(Boolean, nullable=False)
    deviation_percentage = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('idx_stage_environment', 'stage_id'),
        Index('idx_parameter_name', 'parameter_name'),
        Index('idx_measurement_time', 'measurement_time'),
        Index('idx_within_limits', 'within_limits'),
        CheckConstraint("min_limit IS NULL OR max_limit IS NULL OR min_limit <= max_limit", name="valid_limits"),
    )

class BatchMaterial(BaseModel):
    """Materials used in batch manufacturing"""
    __tablename__ = "batch_materials"
    
    # Batch relationship
    batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    batch = relationship("Batch", back_populates="materials_used")
    
    # Material information
    material_id = Column(UUID(as_uuid=True), nullable=False)
    material_name = Column(String(200), nullable=False)
    material_type = Column(String(50), nullable=False)  # raw_material, intermediate, packaging
    
    # Lot information
    lot_number = Column(String(100), nullable=False)
    supplier = Column(String(200), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Usage information
    planned_quantity = Column(Float, nullable=False)
    actual_quantity = Column(Float, nullable=True)
    quantity_units = Column(String(20), nullable=False)
    
    # Dispensing information
    dispensed_at = Column(DateTime(timezone=True), nullable=False)
    dispensed_by = Column(UUID(as_uuid=True), nullable=False)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Quality status
    coa_number = Column(String(100), nullable=True)
    quality_approved = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        Index('idx_batch_material', 'batch_id'),
        Index('idx_material_id', 'material_id'),
        Index('idx_lot_number', 'lot_number'),
        Index('idx_dispensed_at', 'dispensed_at'),
        CheckConstraint("planned_quantity > 0", name="positive_planned_quantity"),
        CheckConstraint("actual_quantity IS NULL OR actual_quantity >= 0", name="non_negative_actual_quantity"),
    )

class BatchTestResult(BaseModel, TimestampMixin):
    """Test results for batches"""
    __tablename__ = "batch_test_results"
    
    # Batch relationship
    batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    batch = relationship("Batch", back_populates="test_results")
    
    # Test information
    test_name = Column(String(100), nullable=False)
    test_type = Column(String(50), nullable=False)  # in_process, release, stability, retain
    test_method = Column(String(100), nullable=False)
    
    # Sample information
    sample_id = Column(String(100), nullable=False)
    sampling_date = Column(DateTime(timezone=True), nullable=False)
    sample_location = Column(String(100), nullable=True)
    
    # Test execution
    test_started_at = Column(DateTime(timezone=True), nullable=False)
    test_completed_at = Column(DateTime(timezone=True), nullable=True)
    tested_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Test results
    test_results = Column(JSON, nullable=True)
    specifications = Column(JSON, nullable=False)
    test_passed = Column(Boolean, nullable=True)
    
    # Deviations
    deviations_found = Column(Boolean, nullable=False, default=False)
    deviation_details = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_batch_test', 'batch_id'),
        Index('idx_test_name', 'test_name'),
        Index('idx_test_type', 'test_type'),
        Index('idx_sample_id', 'sample_id'),
        Index('idx_test_completed', 'test_completed_at'),
        Index('idx_test_passed', 'test_passed'),
        CheckConstraint("test_started_at <= test_completed_at OR test_completed_at IS NULL", name="valid_test_times"),
    )

class BatchDeviation(BaseModel, StatusMixin, ApprovalMixin):
    """Deviations identified during batch manufacturing"""
    __tablename__ = "batch_deviations"
    
    # Batch relationship
    batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    batch = relationship("Batch", back_populates="deviations")
    
    # Deviation information
    deviation_number = Column(String(100), nullable=False, unique=True)
    deviation_type = Column(String(50), nullable=False)  # process, equipment, material, testing
    severity = Column(String(20), nullable=False)  # minor, major, critical
    
    # Description
    description = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    
    # Discovery
    discovered_at = Column(DateTime(timezone=True), nullable=False)
    discovered_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Investigation
    investigation_required = Column(Boolean, nullable=False, default=True)
    investigation_completed = Column(Boolean, nullable=False, default=False)
    investigated_by = Column(UUID(as_uuid=True), nullable=True)
    investigation_date = Column(DateTime(timezone=True), nullable=True)
    
    # Impact assessment
    impact_assessment = Column(Text, nullable=True)
    batch_impact = Column(String(50), nullable=True)  # none, minor, major, critical
    
    # Corrective actions
    corrective_actions = Column(JSON, nullable=True)
    preventive_actions = Column(JSON, nullable=True)
    
    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_batch_deviation', 'batch_id'),
        Index('idx_deviation_number', 'deviation_number'),
        Index('idx_deviation_type', 'deviation_type'),
        Index('idx_severity', 'severity'),
        Index('idx_discovered_at', 'discovered_at'),
        Index('idx_resolved', 'resolved'),
        CheckConstraint("severity IN ('minor', 'major', 'critical')", name="valid_severity"),
        CheckConstraint("batch_impact IS NULL OR batch_impact IN ('none', 'minor', 'major', 'critical')", name="valid_batch_impact"),
    )

class Lot(BaseModel, BatchTrackingMixin, StatusMixin):
    """Individual lots produced from batches"""
    __tablename__ = "lots"
    
    # Batch relationship
    batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    batch = relationship("Batch", back_populates="lots")
    
    # Lot-specific information
    lot_size = Column(Float, nullable=False)
    lot_units = Column(String(20), nullable=False)
    
    # Packaging information
    packaging_date = Column(DateTime(timezone=True), nullable=False)
    packaging_line = Column(String(50), nullable=False)
    packaged_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Container information
    container_type = Column(String(50), nullable=False)
    container_size = Column(String(50), nullable=False)
    containers_count = Column(Integer, nullable=False)
    
    # Labeling information
    label_version = Column(String(20), nullable=False)
    label_verified = Column(Boolean, nullable=False, default=False)
    label_verified_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Distribution
    distributed = Column(Boolean, nullable=False, default=False)
    distribution_date = Column(DateTime(timezone=True), nullable=True)
    distribution_records = Column(JSON, nullable=True)
    
    # Stability testing
    stability_testing_required = Column(Boolean, nullable=False, default=True)
    stability_program_id = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_lot_batch', 'batch_id'),
        Index('idx_lot_number', 'lot_number'),
        Index('idx_packaging_date', 'packaging_date'),
        Index('idx_distributed', 'distributed'),
        UniqueConstraint('lot_number', name='uq_lot_number'),
        CheckConstraint("lot_size > 0", name="positive_lot_size"),
        CheckConstraint("containers_count > 0", name="positive_containers"),
    )

class BatchDocument(BaseModel):
    """Documents associated with batches"""
    __tablename__ = "batch_documents"
    
    # Batch relationship
    batch_id = Column(UUID(as_uuid=True), ForeignKey('batches.id'), nullable=False)
    
    # Document information
    document_type = Column(String(50), nullable=False)  # manufacturing_record, coa, investigation
    document_name = Column(String(200), nullable=False)
    document_path = Column(String(500), nullable=False)
    
    # Version control
    document_version = Column(String(20), nullable=False, default="1.0")
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_batch_document', 'batch_id'),
        Index('idx_document_type', 'document_type'),
        Index('idx_document_name', 'document_name'),
        Index('idx_approved', 'approved'),
    )