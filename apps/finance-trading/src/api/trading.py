"""
Trading API Endpoints
High-performance REST API for trading operations
"""

import asyncio
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from ..models.trading import (
    OrderCreate, OrderResponse, PositionResponse, MarketDataResponse,
    AccountResponse, PortfolioSummary, TradingMetrics,
    OrderSide, OrderType, OrderStatus, TimeInForce
)
from ..services.market_data_service import MarketDataService
from ..services.order_processor import OrderProcessor
from ..services.risk_manager import RiskManager

logger = logging.getLogger(__name__)

trading_router = APIRouter()

class OrderSubmissionResponse(BaseModel):
    """Response model for order submission"""
    success: bool
    message: str
    order_id: Optional[UUID] = None
    timestamp: datetime

class OrderCancellationResponse(BaseModel):
    """Response model for order cancellation"""
    success: bool
    message: str
    order_id: UUID
    timestamp: datetime

class MarketDataStream(BaseModel):
    """Market data streaming response"""
    symbol: str
    data: MarketDataResponse
    timestamp: datetime

# Dependency injection placeholders
# These would be properly injected in a real application
market_data_service = None
order_processor = None
risk_manager = None

def get_market_data_service() -> MarketDataService:
    """Get market data service instance"""
    global market_data_service
    if market_data_service is None:
        market_data_service = MarketDataService()
    return market_data_service

def get_order_processor() -> OrderProcessor:
    """Get order processor instance"""
    global order_processor
    if order_processor is None:
        order_processor = OrderProcessor()
    return order_processor

def get_risk_manager() -> RiskManager:
    """Get risk manager instance"""
    global risk_manager
    if risk_manager is None:
        from ..services.risk_manager import RiskManager
        risk_manager = RiskManager()
    return risk_manager

@trading_router.post("/orders", response_model=OrderSubmissionResponse)
async def submit_order(
    order: OrderCreate,
    processor: OrderProcessor = Depends(get_order_processor)
):
    """
    Submit a new trading order
    Ultra-low latency order submission with comprehensive validation
    """
    start_time = time.time()
    
    try:
        # Create order object
        new_order = Order(
            id=uuid4(),
            user_id=uuid4(),  # Would be from authentication
            account_id=uuid4(),  # Would be from user context
            symbol_id=uuid4(),  # Would be looked up from symbol
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            time_in_force=order.time_in_force,
            client_order_id=order.client_order_id,
            status=OrderStatus.PENDING
        )
        
        # Submit order
        success, message = await processor.submit_order(new_order)
        
        # Calculate processing latency
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if success:
            logger.info(f"Order submitted successfully: {new_order.id} (latency: {processing_time:.2f}ms)")
            return OrderSubmissionResponse(
                success=True,
                message=message,
                order_id=new_order.id,
                timestamp=datetime.now(timezone.utc)
            )
        else:
            logger.warning(f"Order submission failed: {message} (latency: {processing_time:.2f}ms)")
            return OrderSubmissionResponse(
                success=False,
                message=message,
                order_id=None,
                timestamp=datetime.now(timezone.utc)
            )
    
    except Exception as e:
        logger.error(f"Error submitting order: {e}")
        raise HTTPException(status_code=500, detail=f"Order submission failed: {str(e)}")

@trading_router.delete("/orders/{order_id}", response_model=OrderCancellationResponse)
async def cancel_order(
    order_id: UUID = Path(..., description="Order ID to cancel"),
    processor: OrderProcessor = Depends(get_order_processor)
):
    """
    Cancel a pending order
    """
    try:
        success, message = await processor.cancel_order(str(order_id))
        
        return OrderCancellationResponse(
            success=success,
            message=message,
            order_id=order_id,
            timestamp=datetime.now(timezone.utc)
        )
    
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Order cancellation failed: {str(e)}")

@trading_router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID = Path(..., description="Order ID"),
    processor: OrderProcessor = Depends(get_order_processor)
):
    """
    Get order details by ID
    """
    try:
        order = processor.get_order(str(order_id))
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderResponse(
            id=order.id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            time_in_force=order.time_in_force,
            status=order.status,
            filled_quantity=order.filled_quantity,
            avg_fill_price=order.avg_fill_price,
            created_at=order.created_at,
            updated_at=order.updated_at,
            filled_at=order.filled_at,
            client_order_id=order.client_order_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve order: {str(e)}")

@trading_router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of orders to return"),
    processor: OrderProcessor = Depends(get_order_processor)
):
    """
    Get orders with optional filtering
    """
    try:
        # Get pending orders
        pending_orders = processor.get_pending_orders()
        
        # Get order history
        historical_orders = processor.get_order_history(limit=limit)
        
        # Combine and filter
        all_orders = pending_orders + historical_orders
        
        if status:
            all_orders = [order for order in all_orders if order.status == status]
        
        if symbol:
            all_orders = [order for order in all_orders if order.symbol == symbol]
        
        # Sort by created_at descending and limit
        all_orders.sort(key=lambda x: x.created_at, reverse=True)
        all_orders = all_orders[:limit]
        
        return [
            OrderResponse(
                id=order.id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                stop_price=order.stop_price,
                time_in_force=order.time_in_force,
                status=order.status,
                filled_quantity=order.filled_quantity,
                avg_fill_price=order.avg_fill_price,
                created_at=order.created_at,
                updated_at=order.updated_at,
                filled_at=order.filled_at,
                client_order_id=order.client_order_id
            ) for order in all_orders
        ]
    
    except Exception as e:
        logger.error(f"Error retrieving orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve orders: {str(e)}")

@trading_router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str = Path(..., description="Trading symbol"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get real-time market data for a symbol
    """
    try:
        data = market_service.get_symbol_data(symbol)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Market data not found for symbol: {symbol}")
        
        return MarketDataResponse(
            symbol=data.symbol,
            price=data.price,
            bid=data.bid,
            ask=data.ask,
            volume=data.volume,
            timestamp=data.timestamp
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market data: {str(e)}")

@trading_router.get("/market-data", response_model=Dict[str, MarketDataResponse])
async def get_all_market_data(
    symbols: Optional[List[str]] = Query(None, description="List of symbols to retrieve"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get market data for multiple symbols
    """
    try:
        if symbols:
            data = market_service.get_market_data(symbols)
        else:
            data = market_service.get_market_data()
        
        return {
            symbol: MarketDataResponse(
                symbol=point.symbol,
                price=point.price,
                bid=point.bid,
                ask=point.ask,
                volume=point.volume,
                timestamp=point.timestamp
            ) for symbol, point in data.items()
        }
    
    except Exception as e:
        logger.error(f"Error retrieving market data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market data: {str(e)}")

@trading_router.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    account_id: Optional[UUID] = Query(None, description="Account ID"),
    processor: OrderProcessor = Depends(get_order_processor),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get portfolio summary with P&L calculations
    """
    try:
        # This would normally calculate from actual positions
        # For demo purposes, we'll simulate portfolio data
        
        account_id = account_id or uuid4()
        
        # Simulate portfolio calculation
        total_value = Decimal('1000000.00')  # $1M portfolio
        cash_balance = Decimal('100000.00')  # $100K cash
        positions_value = total_value - cash_balance
        
        # Calculate P&L based on recent orders
        recent_orders = processor.get_order_history(str(account_id), limit=50)
        total_pnl = Decimal('0.00')
        
        for order in recent_orders:
            if order.status == OrderStatus.FILLED:
                # Simple P&L calculation
                if order.side == OrderSide.BUY:
                    total_pnl -= order.filled_quantity * order.avg_fill_price
                else:
                    total_pnl += order.filled_quantity * order.avg_fill_price
        
        return PortfolioSummary(
            account_id=account_id,
            total_value=total_value,
            cash_balance=cash_balance,
            positions_value=positions_value,
            total_pnl=total_pnl,
            day_pnl=total_pnl * Decimal('0.1'),  # Simulate daily P&L
            positions_count=len([o for o in recent_orders if o.status == OrderStatus.FILLED]),
            last_updated=datetime.now(timezone.utc)
        )
    
    except Exception as e:
        logger.error(f"Error calculating portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate portfolio: {str(e)}")

@trading_router.get("/trading/metrics", response_model=TradingMetrics)
async def get_trading_metrics(
    processor: OrderProcessor = Depends(get_order_processor)
):
    """
    Get trading performance metrics
    """
    try:
        stats = processor.get_processing_stats()
        
        # Calculate additional metrics
        filled_orders = stats['successful_fills']
        total_orders = stats['total_orders']
        
        return TradingMetrics(
            total_orders=total_orders,
            filled_orders=filled_orders,
            cancelled_orders=total_orders - filled_orders - stats['rejected_orders'],
            avg_fill_time_ms=stats['avg_processing_time_ms'],
            success_rate=stats['fill_rate_percent'],
            total_volume=Decimal('50000000.00'),  # Simulated
            total_pnl=Decimal('125000.00'),  # Simulated
            win_rate=65.5,  # Simulated
            avg_win=Decimal('2500.00'),  # Simulated
            avg_loss=Decimal('-1500.00'),  # Simulated
            sharpe_ratio=1.85,  # Simulated
            max_drawdown=Decimal('-25000.00')  # Simulated
        )
    
    except Exception as e:
        logger.error(f"Error calculating trading metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")

@trading_router.get("/symbols", response_model=List[str])
async def get_available_symbols(
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get list of available trading symbols
    """
    try:
        return market_service.get_all_symbols()
    
    except Exception as e:
        logger.error(f"Error retrieving symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve symbols: {str(e)}")

@trading_router.get("/market-status")
async def get_market_status(
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get current market status
    """
    try:
        return market_service.get_market_status()
    
    except Exception as e:
        logger.error(f"Error retrieving market status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market status: {str(e)}")

@trading_router.get("/stream/market-data/{symbol}")
async def stream_market_data(
    symbol: str = Path(..., description="Trading symbol"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Stream real-time market data for a symbol
    """
    async def generate_stream():
        """Generate market data stream"""
        try:
            while True:
                data = market_service.get_symbol_data(symbol)
                if data:
                    stream_data = MarketDataStream(
                        symbol=symbol,
                        data=MarketDataResponse(
                            symbol=data.symbol,
                            price=data.price,
                            bid=data.bid,
                            ask=data.ask,
                            volume=data.volume,
                            timestamp=data.timestamp
                        ),
                        timestamp=datetime.now(timezone.utc)
                    )
                    yield f"data: {stream_data.json()}\n\n"
                
                await asyncio.sleep(0.1)  # 100ms update interval
        
        except Exception as e:
            logger.error(f"Error in market data stream: {e}")
            yield f"error: {str(e)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )