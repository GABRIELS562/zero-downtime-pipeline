"""
Inventory Management API
Raw material inventory and usage tracking for pharmaceutical manufacturing
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.manufacturing import RawMaterial, MaterialLot, MaterialUsage
from src.services.inventory_service import InventoryService
from src.services.audit_service import AuditService

router = APIRouter()

# Pydantic models for API
class RawMaterialResponse(BaseModel):
    id: UUID
    material_code: str
    name: str
    supplier: str
    grade: Optional[str]
    cas_number: Optional[str]
    molecular_formula: Optional[str]
    current_stock: float
    unit_of_measure: str
    reorder_level: float
    specifications: Optional[dict]
    storage_conditions: Optional[str]
    regulatory_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MaterialLotResponse(BaseModel):
    id: UUID
    lot_number: str
    raw_material_id: UUID
    quantity_received: float
    quantity_remaining: float
    expiry_date: datetime
    coa_number: Optional[str]
    test_results: Optional[dict]
    status: str
    quarantine_reason: Optional[str]
    received_date: datetime
    tested_date: Optional[datetime]
    approved_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MaterialUsageResponse(BaseModel):
    id: UUID
    batch_id: UUID
    raw_material_id: UUID
    theoretical_quantity: float
    actual_quantity: float
    variance: Optional[float]
    variance_percentage: Optional[float]
    lot_numbers: Optional[list]
    workflow_stage: str
    dispensed_by: str
    verified_by: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class RawMaterialCreate(BaseModel):
    material_code: str = Field(..., description="Unique material code")
    name: str = Field(..., description="Material name")
    supplier: str = Field(..., description="Supplier name")
    grade: Optional[str] = Field(None, description="Material grade")
    cas_number: Optional[str] = Field(None, description="Chemical Abstract Service number")
    molecular_formula: Optional[str] = Field(None, description="Molecular formula")
    unit_of_measure: str = Field(..., description="Unit of measure (kg, L, etc.)")
    reorder_level: float = Field(..., gt=0, description="Reorder level threshold")
    specifications: Optional[dict] = Field(None, description="Quality specifications")
    storage_conditions: Optional[str] = Field(None, description="Storage conditions")

class MaterialLotCreate(BaseModel):
    lot_number: str = Field(..., description="Lot number from supplier")
    raw_material_id: UUID = Field(..., description="Raw material ID")
    quantity_received: float = Field(..., gt=0, description="Quantity received")
    expiry_date: datetime = Field(..., description="Expiry date")
    coa_number: Optional[str] = Field(None, description="Certificate of Analysis number")
    test_results: Optional[dict] = Field(None, description="Test results")
    received_date: datetime = Field(default_factory=datetime.utcnow, description="Date received")

class MaterialUsageCreate(BaseModel):
    batch_id: UUID = Field(..., description="Batch ID")
    raw_material_id: UUID = Field(..., description="Raw material ID")
    theoretical_quantity: float = Field(..., gt=0, description="Theoretical quantity needed")
    actual_quantity: float = Field(..., gt=0, description="Actual quantity used")
    lot_numbers: List[str] = Field(..., description="Lot numbers used")
    workflow_stage: str = Field(..., description="Manufacturing stage where material was used")
    dispensed_by: str = Field(..., description="Person who dispensed the material")
    verified_by: Optional[str] = Field(None, description="Person who verified the dispensing")

class StockAdjustment(BaseModel):
    adjustment_quantity: float = Field(..., description="Adjustment quantity (positive or negative)")
    reason: str = Field(..., description="Reason for adjustment")
    adjusted_by: str = Field(..., description="Person making the adjustment")

@router.get("/materials", response_model=List[RawMaterialResponse])
async def get_all_raw_materials(
    supplier: Optional[str] = Query(None, description="Filter by supplier"),
    low_stock_only: bool = Query(False, description="Show only materials below reorder level"),
    regulatory_status: Optional[str] = Query(None, description="Filter by regulatory status"),
    inventory_service: InventoryService = Depends()
):
    """Get list of all raw materials with optional filtering"""
    try:
        materials = await inventory_service.get_raw_materials(
            supplier=supplier,
            low_stock_only=low_stock_only,
            regulatory_status=regulatory_status
        )
        return materials
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve materials: {str(e)}")

@router.get("/materials/{material_id}", response_model=RawMaterialResponse)
async def get_raw_material_details(
    material_id: UUID,
    inventory_service: InventoryService = Depends()
):
    """Get detailed information about a specific raw material"""
    try:
        material = await inventory_service.get_raw_material_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        return material
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve material: {str(e)}")

@router.get("/materials/code/{material_code}", response_model=RawMaterialResponse)
async def get_raw_material_by_code(
    material_code: str,
    inventory_service: InventoryService = Depends()
):
    """Get raw material information by material code"""
    try:
        material = await inventory_service.get_raw_material_by_code(material_code)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        return material
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve material: {str(e)}")

@router.post("/materials", response_model=RawMaterialResponse)
async def create_raw_material(
    material_data: RawMaterialCreate,
    created_by: str = Query(..., description="User creating the material"),
    inventory_service: InventoryService = Depends(),
    audit_service: AuditService = Depends()
):
    """Create a new raw material"""
    try:
        # Check if material code already exists
        existing_material = await inventory_service.get_raw_material_by_code(material_data.material_code)
        if existing_material:
            raise HTTPException(status_code=400, detail="Material code already exists")
        
        # Create the material
        new_material = await inventory_service.create_raw_material(material_data)
        
        # Log audit trail
        await audit_service.log_material_creation(new_material.id, created_by)
        
        return new_material
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create material: {str(e)}")

@router.get("/materials/{material_id}/lots", response_model=List[MaterialLotResponse])
async def get_material_lots(
    material_id: UUID,
    status: Optional[str] = Query(None, description="Filter by lot status"),
    expired_only: bool = Query(False, description="Show only expired lots"),
    inventory_service: InventoryService = Depends()
):
    """Get all lots for a specific raw material"""
    try:
        lots = await inventory_service.get_material_lots(
            material_id=material_id,
            status=status,
            expired_only=expired_only
        )
        return lots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve material lots: {str(e)}")

@router.post("/lots", response_model=MaterialLotResponse)
async def create_material_lot(
    lot_data: MaterialLotCreate,
    received_by: str = Query(..., description="User receiving the lot"),
    inventory_service: InventoryService = Depends(),
    audit_service: AuditService = Depends()
):
    """Create a new material lot (receive material)"""
    try:
        # Verify material exists
        material = await inventory_service.get_raw_material_by_id(lot_data.raw_material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Raw material not found")
        
        # Create the lot
        new_lot = await inventory_service.create_material_lot(lot_data)
        
        # Update material stock
        await inventory_service.update_material_stock(
            lot_data.raw_material_id, 
            lot_data.quantity_received
        )
        
        # Log audit trail
        await audit_service.log_material_receipt(new_lot.id, received_by, lot_data.quantity_received)
        
        return new_lot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create material lot: {str(e)}")

@router.put("/lots/{lot_id}/status")
async def update_lot_status(
    lot_id: UUID,
    status: str = Query(..., description="New lot status"),
    quarantine_reason: Optional[str] = Query(None, description="Reason for quarantine"),
    updated_by: str = Query(..., description="User updating the status"),
    inventory_service: InventoryService = Depends(),
    audit_service: AuditService = Depends()
):
    """Update material lot status"""
    try:
        updated_lot = await inventory_service.update_lot_status(lot_id, status, quarantine_reason)
        if not updated_lot:
            raise HTTPException(status_code=404, detail="Material lot not found")
        
        # Log audit trail
        await audit_service.log_lot_status_change(lot_id, updated_by, status, quarantine_reason)
        
        return {
            "message": "Lot status updated successfully",
            "lot_id": lot_id,
            "new_status": status,
            "updated_by": updated_by,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update lot status: {str(e)}")

@router.post("/usage", response_model=MaterialUsageResponse)
async def record_material_usage(
    usage_data: MaterialUsageCreate,
    inventory_service: InventoryService = Depends(),
    audit_service: AuditService = Depends()
):
    """Record material usage for a batch"""
    try:
        # Verify sufficient stock is available
        material = await inventory_service.get_raw_material_by_id(usage_data.raw_material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Raw material not found")
        
        if material.current_stock < usage_data.actual_quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock available")
        
        # Record the usage
        usage_record = await inventory_service.record_material_usage(usage_data)
        
        # Update material stock
        await inventory_service.update_material_stock(
            usage_data.raw_material_id, 
            -usage_data.actual_quantity
        )
        
        # Log audit trail
        await audit_service.log_material_usage(
            usage_record.id, 
            usage_data.dispensed_by, 
            usage_data.actual_quantity
        )
        
        return usage_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record material usage: {str(e)}")

@router.get("/usage/batch/{batch_id}", response_model=List[MaterialUsageResponse])
async def get_batch_material_usage(
    batch_id: UUID,
    inventory_service: InventoryService = Depends()
):
    """Get all material usage for a specific batch"""
    try:
        usage_records = await inventory_service.get_batch_material_usage(batch_id)
        return usage_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch material usage: {str(e)}")

@router.put("/materials/{material_id}/stock")
async def adjust_material_stock(
    material_id: UUID,
    adjustment: StockAdjustment,
    inventory_service: InventoryService = Depends(),
    audit_service: AuditService = Depends()
):
    """Adjust material stock (for corrections, waste, etc.)"""
    try:
        # Verify material exists
        material = await inventory_service.get_raw_material_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        # Perform stock adjustment
        updated_stock = await inventory_service.adjust_material_stock(
            material_id, 
            adjustment.adjustment_quantity,
            adjustment.reason
        )
        
        # Log audit trail
        await audit_service.log_stock_adjustment(
            material_id, 
            adjustment.adjusted_by, 
            adjustment.adjustment_quantity,
            adjustment.reason
        )
        
        return {
            "message": "Stock adjustment completed successfully",
            "material_id": material_id,
            "adjustment_quantity": adjustment.adjustment_quantity,
            "new_stock_level": updated_stock,
            "reason": adjustment.reason,
            "adjusted_by": adjustment.adjusted_by,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to adjust stock: {str(e)}")

@router.get("/reports/low-stock")
async def get_low_stock_report(
    inventory_service: InventoryService = Depends()
):
    """Get report of materials below reorder level"""
    try:
        low_stock_materials = await inventory_service.get_low_stock_materials()
        
        return {
            "report_type": "low_stock",
            "materials_count": len(low_stock_materials),
            "materials": low_stock_materials,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate low stock report: {str(e)}")

@router.get("/reports/expiring-lots")
async def get_expiring_lots_report(
    days: int = Query(30, description="Number of days to check for expiring lots"),
    inventory_service: InventoryService = Depends()
):
    """Get report of lots expiring within specified days"""
    try:
        expiry_date_threshold = datetime.utcnow() + timedelta(days=days)
        expiring_lots = await inventory_service.get_expiring_lots(expiry_date_threshold)
        
        return {
            "report_type": "expiring_lots",
            "check_period_days": days,
            "lots_count": len(expiring_lots),
            "lots": expiring_lots,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate expiring lots report: {str(e)}")

@router.get("/reports/usage-variance")
async def get_usage_variance_report(
    batch_id: Optional[UUID] = Query(None, description="Specific batch ID"),
    threshold_percentage: float = Query(5.0, description="Variance threshold percentage"),
    days: int = Query(30, description="Number of days to analyze"),
    inventory_service: InventoryService = Depends()
):
    """Get report of material usage variances"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        variance_report = await inventory_service.get_usage_variance_report(
            batch_id=batch_id,
            threshold_percentage=threshold_percentage,
            start_date=start_date
        )
        
        return {
            "report_type": "usage_variance",
            "threshold_percentage": threshold_percentage,
            "analysis_period_days": days,
            "batch_id": batch_id,
            "variances": variance_report,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate variance report: {str(e)}")

@router.get("/health/inventory-management")
async def inventory_management_health_check(
    inventory_service: InventoryService = Depends()
):
    """Health check endpoint for inventory management system"""
    try:
        health_status = await inventory_service.perform_health_check()
        
        return {
            "service": "inventory_management",
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "details": health_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "service": "inventory_management",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }