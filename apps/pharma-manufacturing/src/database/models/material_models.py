"""
Raw Material and Inventory Models
Material tracking, inventory management, and COA tracking
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional
from decimal import Decimal

from .base import BaseModel, TimestampMixin, StatusMixin, ApprovalMixin, TestResultMixin

class MaterialType(BaseModel):
    """Material type master data"""
    __tablename__ = "material_types"
    
    # Type information
    type_code = Column(String(50), nullable=False, unique=True)
    type_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # api, excipient, packaging, solvent, reagent
    
    # Regulatory classification
    regulatory_class = Column(String(50), nullable=False)  # controlled, non_controlled, hazardous
    
    # Storage requirements
    storage_conditions = Column(JSON, nullable=False)
    special_handling = Column(Boolean, nullable=False, default=False)
    handling_requirements = Column(JSON, nullable=True)
    
    # Testing requirements
    testing_required = Column(Boolean, nullable=False, default=True)
    testing_frequency = Column(String(50), nullable=True)  # per_lot, periodic, skip_lot
    
    # Shelf life
    typical_shelf_life_months = Column(Integer, nullable=True)
    
    # Relationships
    materials = relationship("Material", back_populates="material_type")
    
    __table_args__ = (
        Index('idx_material_type_code', 'type_code'),
        Index('idx_material_category', 'category'),
        Index('idx_regulatory_class', 'regulatory_class'),
        CheckConstraint("category IN ('api', 'excipient', 'packaging', 'solvent', 'reagent')", name="valid_category"),
        CheckConstraint("regulatory_class IN ('controlled', 'non_controlled', 'hazardous')", name="valid_regulatory_class"),
        CheckConstraint("testing_frequency IS NULL OR testing_frequency IN ('per_lot', 'periodic', 'skip_lot')", name="valid_testing_frequency"),
        CheckConstraint("typical_shelf_life_months IS NULL OR typical_shelf_life_months > 0", name="positive_shelf_life"),
    )

class Material(BaseModel, StatusMixin):
    """Material master data"""
    __tablename__ = "materials"
    
    # Material identification
    material_code = Column(String(100), nullable=False, unique=True)
    material_name = Column(String(200), nullable=False)
    common_name = Column(String(200), nullable=True)
    
    # Material type relationship
    material_type_id = Column(UUID(as_uuid=True), ForeignKey('material_types.id'), nullable=False)
    material_type = relationship("MaterialType", back_populates="materials")
    
    # Chemical information
    cas_number = Column(String(20), nullable=True)
    molecular_formula = Column(String(100), nullable=True)
    molecular_weight = Column(Float, nullable=True)
    
    # Physical properties
    physical_form = Column(String(50), nullable=True)  # solid, liquid, gas, powder
    color = Column(String(50), nullable=True)
    odor = Column(String(100), nullable=True)
    
    # Regulatory information
    pharmacopoeia_grade = Column(String(50), nullable=True)  # USP, EP, BP, JP
    regulatory_status = Column(String(50), nullable=False, default="approved")
    
    # Supplier information
    primary_supplier = Column(String(200), nullable=True)
    approved_suppliers = Column(JSON, nullable=True)
    
    # Unit of measure
    base_unit = Column(String(20), nullable=False)  # kg, L, each, etc.
    
    # Cost information
    standard_cost = Column(Float, nullable=True)
    cost_currency = Column(String(3), nullable=True)
    
    # Specifications
    specifications = Column(JSON, nullable=False)
    
    # Relationships
    inventory_lots = relationship("InventoryLot", back_populates="material", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="material", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_material_code', 'material_code'),
        Index('idx_material_name', 'material_name'),
        Index('idx_material_type', 'material_type_id'),
        Index('idx_cas_number', 'cas_number'),
        Index('idx_regulatory_status', 'regulatory_status'),
        Index('idx_primary_supplier', 'primary_supplier'),
        CheckConstraint("physical_form IS NULL OR physical_form IN ('solid', 'liquid', 'gas', 'powder')", name="valid_physical_form"),
        CheckConstraint("regulatory_status IN ('approved', 'pending', 'rejected', 'discontinued')", name="valid_regulatory_status"),
        CheckConstraint("standard_cost IS NULL OR standard_cost >= 0", name="non_negative_cost"),
    )

class Supplier(BaseModel, StatusMixin):
    """Supplier master data"""
    __tablename__ = "suppliers"
    
    # Supplier information
    supplier_code = Column(String(50), nullable=False, unique=True)
    supplier_name = Column(String(200), nullable=False)
    supplier_type = Column(String(50), nullable=False)  # manufacturer, distributor, broker
    
    # Contact information
    contact_name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Address information
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Qualification information
    qualification_status = Column(String(50), nullable=False, default="pending")
    qualified_date = Column(DateTime(timezone=True), nullable=True)
    qualification_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Audit information
    last_audit_date = Column(DateTime(timezone=True), nullable=True)
    next_audit_date = Column(DateTime(timezone=True), nullable=True)
    audit_findings = Column(JSON, nullable=True)
    
    # Performance metrics
    performance_score = Column(Float, nullable=True)
    on_time_delivery_rate = Column(Float, nullable=True)
    quality_rating = Column(Float, nullable=True)
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_supplier_code', 'supplier_code'),
        Index('idx_supplier_name', 'supplier_name'),
        Index('idx_supplier_type', 'supplier_type'),
        Index('idx_qualification_status', 'qualification_status'),
        Index('idx_qualified_date', 'qualified_date'),
        CheckConstraint("supplier_type IN ('manufacturer', 'distributor', 'broker')", name="valid_supplier_type"),
        CheckConstraint("qualification_status IN ('pending', 'approved', 'rejected', 'expired')", name="valid_qualification_status"),
        CheckConstraint("performance_score IS NULL OR (performance_score >= 0 AND performance_score <= 100)", name="valid_performance_score"),
        CheckConstraint("on_time_delivery_rate IS NULL OR (on_time_delivery_rate >= 0 AND on_time_delivery_rate <= 100)", name="valid_delivery_rate"),
        CheckConstraint("quality_rating IS NULL OR (quality_rating >= 0 AND quality_rating <= 100)", name="valid_quality_rating"),
    )

class PurchaseOrder(BaseModel, StatusMixin, ApprovalMixin):
    """Purchase order tracking"""
    __tablename__ = "purchase_orders"
    
    # Purchase order information
    po_number = Column(String(100), nullable=False, unique=True)
    po_date = Column(DateTime(timezone=True), nullable=False)
    
    # Supplier relationship
    supplier_id = Column(UUID(as_uuid=True), ForeignKey('suppliers.id'), nullable=False)
    supplier = relationship("Supplier", back_populates="purchase_orders")
    
    # Material relationship
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id'), nullable=False)
    material = relationship("Material", back_populates="purchase_orders")
    
    # Order details
    quantity_ordered = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Delivery information
    requested_delivery_date = Column(DateTime(timezone=True), nullable=False)
    promised_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Terms and conditions
    payment_terms = Column(String(100), nullable=True)
    delivery_terms = Column(String(100), nullable=True)
    
    # Special requirements
    special_requirements = Column(Text, nullable=True)
    coa_required = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    receipts = relationship("MaterialReceipt", back_populates="purchase_order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_po_number', 'po_number'),
        Index('idx_po_date', 'po_date'),
        Index('idx_po_supplier', 'supplier_id'),
        Index('idx_po_material', 'material_id'),
        Index('idx_requested_delivery', 'requested_delivery_date'),
        CheckConstraint("quantity_ordered > 0", name="positive_quantity"),
        CheckConstraint("unit_price >= 0", name="non_negative_price"),
        CheckConstraint("total_amount >= 0", name="non_negative_total"),
    )

class MaterialReceipt(BaseModel, StatusMixin):
    """Material receipt tracking"""
    __tablename__ = "material_receipts"
    
    # Receipt information
    receipt_number = Column(String(100), nullable=False, unique=True)
    receipt_date = Column(DateTime(timezone=True), nullable=False)
    
    # Purchase order relationship
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey('purchase_orders.id'), nullable=False)
    purchase_order = relationship("PurchaseOrder", back_populates="receipts")
    
    # Received quantities
    quantity_received = Column(Float, nullable=False)
    quantity_accepted = Column(Float, nullable=True)
    quantity_rejected = Column(Float, nullable=True)
    
    # Lot information
    supplier_lot_number = Column(String(100), nullable=False)
    manufacturing_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Receipt personnel
    received_by = Column(UUID(as_uuid=True), nullable=False)
    inspected_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Quality information
    coa_received = Column(Boolean, nullable=False, default=False)
    coa_number = Column(String(100), nullable=True)
    
    # Storage information
    storage_location = Column(String(200), nullable=False)
    quarantine_status = Column(Boolean, nullable=False, default=True)
    
    # Inspection results
    visual_inspection = Column(Boolean, nullable=True)
    inspection_notes = Column(Text, nullable=True)
    
    # Relationships
    inventory_lots = relationship("InventoryLot", back_populates="receipt", cascade="all, delete-orphan")
    test_results = relationship("MaterialTestResult", back_populates="receipt", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_receipt_number', 'receipt_number'),
        Index('idx_receipt_date', 'receipt_date'),
        Index('idx_purchase_order', 'purchase_order_id'),
        Index('idx_supplier_lot', 'supplier_lot_number'),
        Index('idx_quarantine_status', 'quarantine_status'),
        Index('idx_received_by', 'received_by'),
        CheckConstraint("quantity_received > 0", name="positive_received_quantity"),
        CheckConstraint("quantity_accepted IS NULL OR quantity_accepted >= 0", name="non_negative_accepted_quantity"),
        CheckConstraint("quantity_rejected IS NULL OR quantity_rejected >= 0", name="non_negative_rejected_quantity"),
        CheckConstraint("quantity_accepted IS NULL OR quantity_rejected IS NULL OR (quantity_accepted + quantity_rejected) <= quantity_received", name="valid_quantity_disposition"),
    )

class InventoryLot(BaseModel, StatusMixin):
    """Inventory lot tracking"""
    __tablename__ = "inventory_lots"
    
    # Lot identification
    internal_lot_number = Column(String(100), nullable=False, unique=True)
    
    # Material relationship
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id'), nullable=False)
    material = relationship("Material", back_populates="inventory_lots")
    
    # Receipt relationship
    receipt_id = Column(UUID(as_uuid=True), ForeignKey('material_receipts.id'), nullable=False)
    receipt = relationship("MaterialReceipt", back_populates="inventory_lots")
    
    # Quantity information
    original_quantity = Column(Float, nullable=False)
    current_quantity = Column(Float, nullable=False)
    reserved_quantity = Column(Float, nullable=False, default=0)
    available_quantity = Column(Float, nullable=False)
    
    # Dates
    received_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    retest_date = Column(DateTime(timezone=True), nullable=True)
    
    # Storage information
    storage_location = Column(String(200), nullable=False)
    storage_conditions = Column(JSON, nullable=True)
    
    # Quality status
    quality_status = Column(String(50), nullable=False, default="pending")
    released_for_use = Column(Boolean, nullable=False, default=False)
    release_date = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Cost information
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    
    # Relationships
    transactions = relationship("InventoryTransaction", back_populates="inventory_lot", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_internal_lot_number', 'internal_lot_number'),
        Index('idx_inventory_material', 'material_id'),
        Index('idx_inventory_receipt', 'receipt_id'),
        Index('idx_storage_location', 'storage_location'),
        Index('idx_quality_status', 'quality_status'),
        Index('idx_released_for_use', 'released_for_use'),
        Index('idx_expiry_date', 'expiry_date'),
        CheckConstraint("original_quantity > 0", name="positive_original_quantity"),
        CheckConstraint("current_quantity >= 0", name="non_negative_current_quantity"),
        CheckConstraint("reserved_quantity >= 0", name="non_negative_reserved_quantity"),
        CheckConstraint("available_quantity >= 0", name="non_negative_available_quantity"),
        CheckConstraint("current_quantity >= reserved_quantity", name="reserved_not_exceeding_current"),
        CheckConstraint("quality_status IN ('pending', 'approved', 'rejected', 'expired')", name="valid_quality_status"),
        CheckConstraint("unit_cost IS NULL OR unit_cost >= 0", name="non_negative_unit_cost"),
        CheckConstraint("total_cost IS NULL OR total_cost >= 0", name="non_negative_total_cost"),
    )
    
    def calculate_available_quantity(self):
        """Calculate available quantity"""
        self.available_quantity = self.current_quantity - self.reserved_quantity
    
    def is_expired(self) -> bool:
        """Check if lot is expired"""
        if not self.expiry_date:
            return False
        return datetime.now(timezone.utc) >= self.expiry_date.replace(tzinfo=timezone.utc)
    
    def is_retest_due(self) -> bool:
        """Check if retest is due"""
        if not self.retest_date:
            return False
        return datetime.now(timezone.utc) >= self.retest_date.replace(tzinfo=timezone.utc)

class InventoryTransaction(BaseModel, TimestampMixin):
    """Inventory transaction tracking"""
    __tablename__ = "inventory_transactions"
    
    # Transaction identification
    transaction_number = Column(String(100), nullable=False, unique=True)
    
    # Inventory lot relationship
    inventory_lot_id = Column(UUID(as_uuid=True), ForeignKey('inventory_lots.id'), nullable=False)
    inventory_lot = relationship("InventoryLot", back_populates="transactions")
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # receipt, issue, adjustment, transfer
    transaction_reason = Column(String(200), nullable=False)
    
    # Quantity information
    quantity = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    
    # Reference information
    reference_number = Column(String(100), nullable=True)  # batch number, work order, etc.
    reference_type = Column(String(50), nullable=True)
    
    # Personnel
    performed_by = Column(UUID(as_uuid=True), nullable=False)
    authorized_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Location information
    from_location = Column(String(200), nullable=True)
    to_location = Column(String(200), nullable=True)
    
    # Balance information
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('idx_transaction_number', 'transaction_number'),
        Index('idx_inventory_transaction', 'inventory_lot_id'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_timestamp', 'timestamp'),
        Index('idx_performed_by', 'performed_by'),
        Index('idx_reference_number', 'reference_number'),
        CheckConstraint("transaction_type IN ('receipt', 'issue', 'adjustment', 'transfer', 'disposal')", name="valid_transaction_type"),
        CheckConstraint("quantity != 0", name="non_zero_quantity"),
        CheckConstraint("balance_before >= 0", name="non_negative_balance_before"),
        CheckConstraint("balance_after >= 0", name="non_negative_balance_after"),
    )

class MaterialTestResult(BaseModel, TestResultMixin, ApprovalMixin):
    """Material test results and COA tracking"""
    __tablename__ = "material_test_results"
    
    # Receipt relationship
    receipt_id = Column(UUID(as_uuid=True), ForeignKey('material_receipts.id'), nullable=False)
    receipt = relationship("MaterialReceipt", back_populates="test_results")
    
    # Test identification
    test_report_number = Column(String(100), nullable=False, unique=True)
    coa_number = Column(String(100), nullable=True)
    
    # Sample information
    sample_id = Column(String(100), nullable=False)
    sample_description = Column(String(200), nullable=True)
    sampling_date = Column(DateTime(timezone=True), nullable=False)
    
    # Laboratory information
    testing_laboratory = Column(String(200), nullable=False)
    laboratory_accreditation = Column(String(100), nullable=True)
    
    # Analysis dates
    analysis_start_date = Column(DateTime(timezone=True), nullable=True)
    analysis_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    test_results_summary = Column(JSON, nullable=True)
    overall_conclusion = Column(String(50), nullable=False)  # pass, fail, conditional
    
    # Certificate information
    certificate_number = Column(String(100), nullable=True)
    certificate_date = Column(DateTime(timezone=True), nullable=True)
    certificate_valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    individual_tests = relationship("MaterialTestDetail", back_populates="test_result", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_material_test_receipt', 'receipt_id'),
        Index('idx_test_report_number', 'test_report_number'),
        Index('idx_coa_number', 'coa_number'),
        Index('idx_sample_id', 'sample_id'),
        Index('idx_testing_laboratory', 'testing_laboratory'),
        Index('idx_overall_conclusion', 'overall_conclusion'),
        CheckConstraint("overall_conclusion IN ('pass', 'fail', 'conditional')", name="valid_conclusion"),
        CheckConstraint("analysis_start_date IS NULL OR analysis_completion_date IS NULL OR analysis_start_date <= analysis_completion_date", name="valid_analysis_dates"),
    )

class MaterialTestDetail(BaseModel):
    """Individual test details within material test results"""
    __tablename__ = "material_test_details"
    
    # Test result relationship
    test_result_id = Column(UUID(as_uuid=True), ForeignKey('material_test_results.id'), nullable=False)
    test_result = relationship("MaterialTestResult", back_populates="individual_tests")
    
    # Test information
    test_name = Column(String(100), nullable=False)
    test_parameter = Column(String(100), nullable=False)
    test_method = Column(String(100), nullable=False)
    
    # Specification
    specification = Column(String(200), nullable=False)
    specification_min = Column(Float, nullable=True)
    specification_max = Column(Float, nullable=True)
    specification_units = Column(String(20), nullable=True)
    
    # Results
    result_value = Column(Float, nullable=True)
    result_text = Column(String(200), nullable=True)
    result_units = Column(String(20), nullable=True)
    
    # Compliance
    result_compliant = Column(Boolean, nullable=False)
    deviation_percentage = Column(Float, nullable=True)
    
    # Test conditions
    test_conditions = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_material_test_detail', 'test_result_id'),
        Index('idx_test_name', 'test_name'),
        Index('idx_test_parameter', 'test_parameter'),
        Index('idx_result_compliant', 'result_compliant'),
        CheckConstraint("specification_min IS NULL OR specification_max IS NULL OR specification_min <= specification_max", name="valid_specification_range"),
        CheckConstraint("result_value IS NULL OR result_text IS NULL OR (result_value IS NOT NULL AND result_text IS NOT NULL)", name="result_value_or_text"),
    )

class MaterialReservation(BaseModel, StatusMixin):
    """Material reservation for batch manufacturing"""
    __tablename__ = "material_reservations"
    
    # Reservation identification
    reservation_number = Column(String(100), nullable=False, unique=True)
    
    # Inventory lot relationship
    inventory_lot_id = Column(UUID(as_uuid=True), ForeignKey('inventory_lots.id'), nullable=False)
    
    # Reservation details
    reserved_quantity = Column(Float, nullable=False)
    reservation_date = Column(DateTime(timezone=True), nullable=False)
    reservation_expiry = Column(DateTime(timezone=True), nullable=False)
    
    # Purpose
    purpose = Column(String(200), nullable=False)
    batch_number = Column(String(100), nullable=True)
    work_order = Column(String(100), nullable=True)
    
    # Personnel
    reserved_by = Column(UUID(as_uuid=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Status tracking
    consumed_quantity = Column(Float, nullable=False, default=0)
    remaining_quantity = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('idx_reservation_number', 'reservation_number'),
        Index('idx_reservation_lot', 'inventory_lot_id'),
        Index('idx_reservation_date', 'reservation_date'),
        Index('idx_batch_number', 'batch_number'),
        Index('idx_reserved_by', 'reserved_by'),
        CheckConstraint("reserved_quantity > 0", name="positive_reserved_quantity"),
        CheckConstraint("consumed_quantity >= 0", name="non_negative_consumed_quantity"),
        CheckConstraint("remaining_quantity >= 0", name="non_negative_remaining_quantity"),
        CheckConstraint("consumed_quantity <= reserved_quantity", name="consumed_not_exceeding_reserved"),
        CheckConstraint("reservation_date <= reservation_expiry", name="valid_reservation_dates"),
    )

class MaterialDisposal(BaseModel, StatusMixin, ApprovalMixin):
    """Material disposal tracking"""
    __tablename__ = "material_disposals"
    
    # Disposal identification
    disposal_number = Column(String(100), nullable=False, unique=True)
    
    # Inventory lot relationship
    inventory_lot_id = Column(UUID(as_uuid=True), ForeignKey('inventory_lots.id'), nullable=False)
    
    # Disposal details
    disposal_quantity = Column(Float, nullable=False)
    disposal_date = Column(DateTime(timezone=True), nullable=False)
    
    # Disposal reason
    disposal_reason = Column(String(200), nullable=False)
    disposal_method = Column(String(100), nullable=False)
    
    # Environmental compliance
    hazardous_waste = Column(Boolean, nullable=False, default=False)
    waste_manifest = Column(String(100), nullable=True)
    disposal_facility = Column(String(200), nullable=True)
    
    # Authorization
    authorized_by = Column(UUID(as_uuid=True), nullable=False)
    disposal_witnessed_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Documentation
    disposal_certificate = Column(String(500), nullable=True)
    
    __table_args__ = (
        Index('idx_disposal_number', 'disposal_number'),
        Index('idx_disposal_lot', 'inventory_lot_id'),
        Index('idx_disposal_date', 'disposal_date'),
        Index('idx_disposal_reason', 'disposal_reason'),
        Index('idx_hazardous_waste', 'hazardous_waste'),
        CheckConstraint("disposal_quantity > 0", name="positive_disposal_quantity"),
    )