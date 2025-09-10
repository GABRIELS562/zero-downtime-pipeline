"""
Inventory Management Service
Manages pharmaceutical inventory, stock levels, and supplies
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class InventoryStatus(Enum):
    """Inventory item status"""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"
    QUARANTINE = "quarantine"

@dataclass
class InventoryItem:
    """Inventory item model"""
    item_id: str
    name: str
    category: str
    quantity: int
    unit: str
    batch_number: str
    expiry_date: datetime
    status: InventoryStatus
    location: str
    minimum_stock: int
    reorder_level: int

class InventoryService:
    """Service for managing pharmaceutical inventory"""
    
    def __init__(self):
        self.inventory: Dict[str, InventoryItem] = {}
        self._initialize_inventory()
        logger.info("Inventory Service initialized")
    
    def _initialize_inventory(self):
        """Initialize sample inventory items"""
        sample_items = [
            InventoryItem(
                item_id="INV-001",
                name="Acetaminophen 500mg",
                category="Raw Material",
                quantity=5000,
                unit="kg",
                batch_number="BATCH-2024-001",
                expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
                status=InventoryStatus.IN_STOCK,
                location="Warehouse A, Shelf 12",
                minimum_stock=1000,
                reorder_level=2000
            ),
            InventoryItem(
                item_id="INV-002",
                name="Gelatin Capsules",
                category="Packaging",
                quantity=100000,
                unit="units",
                batch_number="BATCH-2024-002",
                expiry_date=datetime.now(timezone.utc) + timedelta(days=730),
                status=InventoryStatus.IN_STOCK,
                location="Warehouse B, Section 5",
                minimum_stock=20000,
                reorder_level=50000
            ),
            InventoryItem(
                item_id="INV-003",
                name="Lactose Monohydrate",
                category="Excipient",
                quantity=2000,
                unit="kg",
                batch_number="BATCH-2024-003",
                expiry_date=datetime.now(timezone.utc) + timedelta(days=545),
                status=InventoryStatus.IN_STOCK,
                location="Warehouse A, Shelf 8",
                minimum_stock=500,
                reorder_level=1000
            )
        ]
        
        for item in sample_items:
            self.inventory[item.item_id] = item
    
    async def get_inventory(self) -> List[Dict[str, Any]]:
        """Get all inventory items"""
        return [
            {
                "item_id": item.item_id,
                "name": item.name,
                "category": item.category,
                "quantity": item.quantity,
                "unit": item.unit,
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date.isoformat(),
                "status": item.status.value,
                "location": item.location,
                "minimum_stock": item.minimum_stock,
                "reorder_level": item.reorder_level
            }
            for item in self.inventory.values()
        ]
    
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get specific inventory item"""
        item = self.inventory.get(item_id)
        if not item:
            return None
        
        return {
            "item_id": item.item_id,
            "name": item.name,
            "category": item.category,
            "quantity": item.quantity,
            "unit": item.unit,
            "batch_number": item.batch_number,
            "expiry_date": item.expiry_date.isoformat(),
            "status": item.status.value,
            "location": item.location,
            "minimum_stock": item.minimum_stock,
            "reorder_level": item.reorder_level
        }
    
    async def update_quantity(self, item_id: str, quantity_change: int) -> bool:
        """Update inventory quantity"""
        item = self.inventory.get(item_id)
        if not item:
            return False
        
        item.quantity += quantity_change
        
        # Update status based on quantity
        if item.quantity <= 0:
            item.status = InventoryStatus.OUT_OF_STOCK
        elif item.quantity < item.minimum_stock:
            item.status = InventoryStatus.LOW_STOCK
        else:
            item.status = InventoryStatus.IN_STOCK
        
        logger.info(f"Updated inventory for {item.name}: {item.quantity} {item.unit}")
        return True
    
    async def check_expiry(self) -> List[Dict[str, Any]]:
        """Check for expired or soon-to-expire items"""
        expiring_items = []
        current_time = datetime.now(timezone.utc)
        warning_period = timedelta(days=90)
        
        for item in self.inventory.values():
            time_to_expiry = item.expiry_date - current_time
            
            if time_to_expiry <= timedelta(0):
                item.status = InventoryStatus.EXPIRED
                expiring_items.append({
                    "item_id": item.item_id,
                    "name": item.name,
                    "batch_number": item.batch_number,
                    "expiry_date": item.expiry_date.isoformat(),
                    "status": "expired"
                })
            elif time_to_expiry <= warning_period:
                expiring_items.append({
                    "item_id": item.item_id,
                    "name": item.name,
                    "batch_number": item.batch_number,
                    "expiry_date": item.expiry_date.isoformat(),
                    "days_until_expiry": time_to_expiry.days,
                    "status": "expiring_soon"
                })
        
        return expiring_items
    
    async def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get items with low stock"""
        low_stock = []
        
        for item in self.inventory.values():
            if item.quantity < item.reorder_level:
                low_stock.append({
                    "item_id": item.item_id,
                    "name": item.name,
                    "current_quantity": item.quantity,
                    "reorder_level": item.reorder_level,
                    "minimum_stock": item.minimum_stock,
                    "unit": item.unit,
                    "location": item.location
                })
        
        return low_stock