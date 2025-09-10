"""
Order Processing Service
Ultra-low latency order processing for high-frequency trading
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from prometheus_client import Counter, Histogram, Gauge
from src.models.trading import Order, OrderSide, OrderType, OrderStatus, TimeInForce

logger = logging.getLogger(__name__)

# Prometheus metrics
orders_processed = Counter('orders_processed_total', 'Total orders processed', ['side', 'status'])
order_processing_latency = Histogram('order_processing_latency_seconds', 'Order processing latency')
pending_orders = Gauge('pending_orders_count', 'Number of pending orders')
order_errors = Counter('order_errors_total', 'Order processing errors', ['error_type'])
fill_rate = Gauge('order_fill_rate_percent', 'Order fill rate percentage')

@dataclass
class OrderExecution:
    """Order execution details"""
    order_id: str
    execution_id: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    side: OrderSide
    commission: Decimal = Decimal('0.00')

class OrderProcessor:
    """
    High-performance order processing engine
    Handles order validation, execution, and lifecycle management
    """
    
    def __init__(self):
        self.pending_orders: Dict[str, Order] = {}
        self.order_history: Dict[str, Order] = {}
        self.executions: Dict[str, List[OrderExecution]] = {}
        self.is_running = False
        self.processing_task = None
        self.market_data_service = None
        self.risk_manager = None
        
        # Performance tracking
        self.total_orders = 0
        self.successful_fills = 0
        self.rejected_orders = 0
        self.avg_processing_time = 0.0
        
        # Market simulation parameters
        self.market_impact_factor = Decimal('0.001')  # 0.1% market impact
        self.slippage_factor = Decimal('0.0005')  # 0.05% slippage
        self.commission_rate = Decimal('0.001')  # 0.1% commission
    
    async def start(self):
        """Start the order processing service"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._process_orders())
        logger.info("Order processor started")
    
    async def stop(self):
        """Stop the order processing service"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Order processor stopped")
    
    def set_market_data_service(self, market_data_service):
        """Set market data service dependency"""
        self.market_data_service = market_data_service
    
    def set_risk_manager(self, risk_manager):
        """Set risk manager dependency"""
        self.risk_manager = risk_manager
    
    async def submit_order(self, order: Order) -> Tuple[bool, str]:
        """
        Submit a new order for processing
        Returns: (success, message)
        """
        start_time = time.time()
        
        try:
            # Validate order
            validation_result = await self._validate_order(order)
            if not validation_result[0]:
                order.status = OrderStatus.REJECTED
                order.reject_reason = validation_result[1]
                self.rejected_orders += 1
                orders_processed.labels(side=order.side, status="rejected").inc()
                order_errors.labels(error_type="validation_error").inc()
                return False, validation_result[1]
            
            # Risk check
            if self.risk_manager:
                risk_check = await self.risk_manager.check_order_risk(order)
                if not risk_check[0]:
                    order.status = OrderStatus.REJECTED
                    order.reject_reason = f"Risk check failed: {risk_check[1]}"
                    self.rejected_orders += 1
                    orders_processed.labels(side=order.side, status="rejected").inc()
                    order_errors.labels(error_type="risk_check_failed").inc()
                    return False, order.reject_reason
            
            # Add to pending orders
            order.status = OrderStatus.PENDING
            order.created_at = datetime.now(timezone.utc)
            order.updated_at = order.created_at
            
            self.pending_orders[str(order.id)] = order
            self.total_orders += 1
            
            # Update metrics
            pending_orders.set(len(self.pending_orders))
            processing_time = time.time() - start_time
            order_processing_latency.observe(processing_time)
            
            logger.info(f"Order submitted: {order.id} - {order.side} {order.quantity} {order.symbol} @ {order.price}")
            
            return True, "Order submitted successfully"
            
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            order_errors.labels(error_type="submission_error").inc()
            return False, f"Order submission failed: {str(e)}"
    
    async def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """Cancel a pending order"""
        try:
            if order_id not in self.pending_orders:
                return False, "Order not found or already processed"
            
            order = self.pending_orders[order_id]
            
            # Check if order can be cancelled
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                return False, f"Order cannot be cancelled - status: {order.status}"
            
            # Cancel the order
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now(timezone.utc)
            
            # Move to history
            self.order_history[order_id] = order
            del self.pending_orders[order_id]
            
            # Update metrics
            pending_orders.set(len(self.pending_orders))
            orders_processed.labels(side=order.side, status="cancelled").inc()
            
            logger.info(f"Order cancelled: {order_id}")
            
            return True, "Order cancelled successfully"
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            order_errors.labels(error_type="cancellation_error").inc()
            return False, f"Order cancellation failed: {str(e)}"
    
    async def _process_orders(self):
        """Main order processing loop"""
        while self.is_running:
            try:
                if self.pending_orders:
                    await self._process_pending_orders()
                
                # High-frequency processing (every 1ms for ultra-low latency)
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Error in order processing loop: {e}")
                order_errors.labels(error_type="processing_loop_error").inc()
                await asyncio.sleep(0.01)
    
    async def _process_pending_orders(self):
        """Process all pending orders"""
        orders_to_process = list(self.pending_orders.values())
        
        for order in orders_to_process:
            try:
                await self._process_single_order(order)
            except Exception as e:
                logger.error(f"Error processing order {order.id}: {e}")
                order_errors.labels(error_type="single_order_error").inc()
    
    async def _process_single_order(self, order: Order):
        """Process a single order"""
        start_time = time.time()
        
        try:
            # Check if order has expired
            if await self._is_order_expired(order):
                await self._expire_order(order)
                return
            
            # Get current market data
            if not self.market_data_service:
                return
            
            market_data = self.market_data_service.get_symbol_data(order.symbol)
            if not market_data:
                return
            
            # Determine if order should be filled
            should_fill, fill_price = await self._should_fill_order(order, market_data)
            
            if should_fill:
                await self._fill_order(order, fill_price)
            
            # Update processing metrics
            processing_time = time.time() - start_time
            self.avg_processing_time = (self.avg_processing_time + processing_time) / 2
            
        except Exception as e:
            logger.error(f"Error processing order {order.id}: {e}")
            order_errors.labels(error_type="order_processing_error").inc()
    
    async def _validate_order(self, order: Order) -> Tuple[bool, str]:
        """Validate order parameters"""
        # Check required fields
        if not order.symbol or not order.side or not order.order_type:
            return False, "Missing required order fields"
        
        # Check quantity
        if order.quantity <= 0:
            return False, "Order quantity must be positive"
        
        # Check price for limit orders
        if order.order_type == OrderType.LIMIT and (not order.price or order.price <= 0):
            return False, "Limit orders must have a positive price"
        
        # Check stop price for stop orders
        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if not order.stop_price or order.stop_price <= 0:
                return False, "Stop orders must have a positive stop price"
        
        # Check symbol exists
        if self.market_data_service:
            if order.symbol not in self.market_data_service.get_all_symbols():
                return False, f"Symbol {order.symbol} is not available for trading"
        
        return True, "Order validation passed"
    
    async def _should_fill_order(self, order: Order, market_data) -> Tuple[bool, Decimal]:
        """Determine if order should be filled and at what price"""
        current_price = market_data.price
        
        if order.order_type == OrderType.MARKET:
            # Market orders fill immediately at current price + slippage
            if order.side == OrderSide.BUY:
                fill_price = current_price + (current_price * self.slippage_factor)
            else:
                fill_price = current_price - (current_price * self.slippage_factor)
            return True, fill_price
        
        elif order.order_type == OrderType.LIMIT:
            # Limit orders fill when price reaches limit
            if order.side == OrderSide.BUY and current_price <= order.price:
                return True, min(order.price, current_price)
            elif order.side == OrderSide.SELL and current_price >= order.price:
                return True, max(order.price, current_price)
        
        elif order.order_type == OrderType.STOP:
            # Stop orders become market orders when stop price is hit
            if order.side == OrderSide.BUY and current_price >= order.stop_price:
                fill_price = current_price + (current_price * self.slippage_factor)
                return True, fill_price
            elif order.side == OrderSide.SELL and current_price <= order.stop_price:
                fill_price = current_price - (current_price * self.slippage_factor)
                return True, fill_price
        
        elif order.order_type == OrderType.STOP_LIMIT:
            # Stop-limit orders become limit orders when stop price is hit
            if order.side == OrderSide.BUY and current_price >= order.stop_price:
                if current_price <= order.price:
                    return True, min(order.price, current_price)
            elif order.side == OrderSide.SELL and current_price <= order.stop_price:
                if current_price >= order.price:
                    return True, max(order.price, current_price)
        
        return False, Decimal('0.00')
    
    async def _fill_order(self, order: Order, fill_price: Decimal):
        """Fill an order"""
        try:
            # Calculate commission
            commission = order.quantity * fill_price * self.commission_rate
            
            # Create execution
            execution = OrderExecution(
                order_id=str(order.id),
                execution_id=str(uuid.uuid4()),
                quantity=order.quantity,
                price=fill_price,
                timestamp=datetime.now(timezone.utc),
                side=order.side,
                commission=commission
            )
            
            # Update order
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.avg_fill_price = fill_price
            order.filled_at = datetime.now(timezone.utc)
            order.updated_at = order.filled_at
            
            # Store execution
            if str(order.id) not in self.executions:
                self.executions[str(order.id)] = []
            self.executions[str(order.id)].append(execution)
            
            # Move to history
            self.order_history[str(order.id)] = order
            del self.pending_orders[str(order.id)]
            
            # Update metrics
            self.successful_fills += 1
            pending_orders.set(len(self.pending_orders))
            orders_processed.labels(side=order.side, status="filled").inc()
            fill_rate.set((self.successful_fills / self.total_orders) * 100 if self.total_orders > 0 else 0)
            
            logger.info(f"Order filled: {order.id} - {order.quantity} @ {fill_price}")
            
        except Exception as e:
            logger.error(f"Error filling order {order.id}: {e}")
            order_errors.labels(error_type="fill_error").inc()
    
    async def _is_order_expired(self, order: Order) -> bool:
        """Check if order has expired"""
        if order.time_in_force == TimeInForce.IOC:
            # Immediate or Cancel - expire if not filled immediately
            return True
        elif order.time_in_force == TimeInForce.FOK:
            # Fill or Kill - expire if cannot be filled completely
            return True
        elif order.time_in_force == TimeInForce.DAY:
            # Day order - expire at end of trading day
            now = datetime.now(timezone.utc)
            # Simplified: expire after 8 hours
            return (now - order.created_at).total_seconds() > 8 * 3600
        
        return False
    
    async def _expire_order(self, order: Order):
        """Expire an order"""
        order.status = OrderStatus.EXPIRED
        order.updated_at = datetime.now(timezone.utc)
        
        # Move to history
        self.order_history[str(order.id)] = order
        del self.pending_orders[str(order.id)]
        
        # Update metrics
        pending_orders.set(len(self.pending_orders))
        orders_processed.labels(side=order.side, status="expired").inc()
        
        logger.info(f"Order expired: {order.id}")
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        if order_id in self.pending_orders:
            return self.pending_orders[order_id]
        return self.order_history.get(order_id)
    
    def get_pending_orders(self, account_id: Optional[str] = None) -> List[Order]:
        """Get pending orders for account"""
        orders = list(self.pending_orders.values())
        if account_id:
            orders = [order for order in orders if str(order.account_id) == account_id]
        return orders
    
    def get_order_history(self, account_id: Optional[str] = None, limit: int = 100) -> List[Order]:
        """Get order history for account"""
        orders = list(self.order_history.values())
        if account_id:
            orders = [order for order in orders if str(order.account_id) == account_id]
        
        # Sort by created_at descending
        orders.sort(key=lambda x: x.created_at, reverse=True)
        return orders[:limit]
    
    def get_executions(self, order_id: str) -> List[OrderExecution]:
        """Get executions for an order"""
        return self.executions.get(order_id, [])
    
    def get_processing_stats(self) -> Dict[str, any]:
        """Get order processing statistics"""
        return {
            "total_orders": self.total_orders,
            "successful_fills": self.successful_fills,
            "rejected_orders": self.rejected_orders,
            "pending_orders": len(self.pending_orders),
            "fill_rate_percent": (self.successful_fills / self.total_orders) * 100 if self.total_orders > 0 else 0,
            "avg_processing_time_ms": self.avg_processing_time * 1000,
            "is_running": self.is_running
        }