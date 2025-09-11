"""
Trading System Data Models
High-performance models for ultra-low latency trading operations
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

Base = declarative_base()

class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TimeInForce(str, Enum):
    """Time in force enumeration"""
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    DAY = "day"  # Day order

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    orders = relationship("Order", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_type = Column(String(20), nullable=False)  # 'trading', 'demo', 'paper'
    balance = Column(Numeric(20, 8), nullable=False, default=0)
    available_balance = Column(Numeric(20, 8), nullable=False, default=0)
    margin_balance = Column(Numeric(20, 8), nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    orders = relationship("Order", back_populates="account")
    positions = relationship("Position", back_populates="account")

class Symbol(Base):
    __tablename__ = "symbols"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(20), nullable=False)
    asset_class = Column(String(20), nullable=False)  # 'equity', 'option', 'future', 'forex'
    is_tradable = Column(Boolean, default=True)
    tick_size = Column(Numeric(10, 8), nullable=False, default=0.01)
    lot_size = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    orders = relationship("Order", back_populates="symbol")
    positions = relationship("Position", back_populates="symbol")
    market_data = relationship("MarketData", back_populates="symbol")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    symbol_id = Column(PGUUID(as_uuid=True), ForeignKey("symbols.id"), nullable=False)
    
    side = Column(String(10), nullable=False)  # 'buy', 'sell'
    order_type = Column(String(20), nullable=False)  # 'market', 'limit', etc.
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8))  # Optional for market orders
    stop_price = Column(Numeric(20, 8))  # For stop orders
    time_in_force = Column(String(10), nullable=False, default="gtc")
    
    status = Column(String(20), nullable=False, default="pending")
    filled_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    avg_fill_price = Column(Numeric(20, 8), nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    filled_at = Column(DateTime(timezone=True))
    
    # Audit fields
    client_order_id = Column(String(100))
    exchange_order_id = Column(String(100))
    reject_reason = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    account = relationship("Account", back_populates="orders")
    symbol = relationship("Symbol", back_populates="orders")
    executions = relationship("Execution", back_populates="order")

class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    side = Column(String(10), nullable=False)
    
    executed_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    execution_id = Column(String(100))  # Exchange execution ID
    
    # Relationships
    order = relationship("Order", back_populates="executions")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    symbol_id = Column(PGUUID(as_uuid=True), ForeignKey("symbols.id"), nullable=False)
    
    quantity = Column(Numeric(20, 8), nullable=False, default=0)
    avg_price = Column(Numeric(20, 8), nullable=False, default=0)
    market_value = Column(Numeric(20, 8), nullable=False, default=0)
    unrealized_pnl = Column(Numeric(20, 8), nullable=False, default=0)
    realized_pnl = Column(Numeric(20, 8), nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    symbol = relationship("Symbol", back_populates="positions")

class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol_id = Column(PGUUID(as_uuid=True), ForeignKey("symbols.id"), nullable=False)
    
    price = Column(Numeric(20, 8), nullable=False)
    bid = Column(Numeric(20, 8))
    ask = Column(Numeric(20, 8))
    volume = Column(Numeric(20, 8), nullable=False, default=0)
    
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    symbol = relationship("Symbol", back_populates="market_data")

# Pydantic Models for API
class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: str = Field(..., min_length=2, max_length=200)

class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    """Order creation model"""
    symbol: str = Field(..., min_length=1, max_length=20)
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)
    time_in_force: TimeInForce = TimeInForce.GTC
    client_order_id: Optional[str] = Field(None, max_length=100)
    
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('order_type') == OrderType.LIMIT and v is None:
            raise ValueError('Price is required for limit orders')
        if values.get('order_type') == OrderType.MARKET and v is not None:
            raise ValueError('Price should not be set for market orders')
        return v

class OrderResponse(BaseModel):
    """Order response model"""
    id: UUID
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal]
    stop_price: Optional[Decimal]
    time_in_force: str
    status: str
    filled_quantity: Decimal
    avg_fill_price: Decimal
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime]
    client_order_id: Optional[str]
    
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    """Position response model"""
    id: UUID
    symbol: str
    quantity: Decimal
    avg_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MarketDataResponse(BaseModel):
    """Market data response model"""
    symbol: str
    price: Decimal
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    volume: Decimal
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AccountResponse(BaseModel):
    """Account response model"""
    id: UUID
    account_type: str
    balance: Decimal
    available_balance: Decimal
    margin_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PortfolioSummary(BaseModel):
    """Portfolio summary model"""
    account_id: UUID
    total_value: Decimal
    cash_balance: Decimal
    positions_value: Decimal
    total_pnl: Decimal
    day_pnl: Decimal
    positions_count: int
    last_updated: datetime

class TradingMetrics(BaseModel):
    """Trading performance metrics"""
    total_orders: int
    filled_orders: int
    cancelled_orders: int
    avg_fill_time_ms: float
    success_rate: float
    total_volume: Decimal
    total_pnl: Decimal
    win_rate: float
    avg_win: Decimal
    avg_loss: Decimal
    sharpe_ratio: float
    max_drawdown: Decimal