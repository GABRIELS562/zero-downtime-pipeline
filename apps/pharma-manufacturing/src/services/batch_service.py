"""
Batch Service
Service layer for batch production tracking and management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)

class BatchService:
    """Service for managing pharmaceutical batch production"""
    
    def __init__(self):
        """Initialize batch service"""
        self.batches = {}
        logger.info("BatchService initialized")
    
    async def create_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new batch"""
        batch_id = str(uuid4())
        batch = {
            "id": batch_id,
            "batch_number": batch_data.get("batch_number"),
            "product_name": batch_data.get("product_name"),
            "product_code": batch_data.get("product_code"),
            "batch_size": batch_data.get("batch_size"),
            "manufacturing_date": datetime.now().isoformat(),
            "status": "in_progress",
            "created_at": datetime.now().isoformat(),
            **batch_data
        }
        self.batches[batch_id] = batch
        logger.info(f"Created batch {batch_id}")
        return batch
    
    async def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch by ID"""
        return self.batches.get(batch_id)
    
    async def list_batches(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all batches"""
        batch_list = list(self.batches.values())
        return batch_list[skip:skip + limit]
    
    async def update_batch_status(self, batch_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update batch status"""
        if batch_id in self.batches:
            self.batches[batch_id]["status"] = status
            self.batches[batch_id]["updated_at"] = datetime.now().isoformat()
            logger.info(f"Updated batch {batch_id} status to {status}")
            return self.batches[batch_id]
        return None
    
    async def get_batch_by_number(self, batch_number: str) -> Optional[Dict[str, Any]]:
        """Get batch by batch number"""
        for batch in self.batches.values():
            if batch.get("batch_number") == batch_number:
                return batch
        return None
    
    async def get_batches_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get batches by status"""
        return [b for b in self.batches.values() if b.get("status") == status]
    
    async def get_batches_in_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get batches within date range"""
        batches = []
        for batch in self.batches.values():
            batch_date = datetime.fromisoformat(batch.get("manufacturing_date", ""))
            if start_date <= batch_date <= end_date:
                batches.append(batch)
        return batches