"""
Pydantic Schemas for API Validation
Data models for request/response validation with proper typing
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict, EmailStr, SecretStr


# Enum schemas
class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class TimeInForce(str, Enum):
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill
    DAY = "DAY"  # Day Order

class AccountType(str, Enum):
    TRADING = "TRADING"
    DEMO = "DEMO"
    PAPER = "PAPER"
    MARGIN = "MARGIN"

class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    COMMODITY = "COMMODITY"

class TransactionType(str, Enum):
    TRADE = "TRADE"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"
    FEE = "FEE"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
            UUID: lambda v: str(v)
        }
    )


# User schemas
class UserBase(BaseSchema):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    date_of_birth: Optional[datetime] = None
    risk_level: str = Field("medium", regex=r'^(low|medium|high)$')
    kyc_status: str = Field("pending", regex=r'^(pending|verified|rejected)$')
    accredited_investor: bool = False

class UserCreate(UserBase):
    """User creation schema"""
    password: SecretStr = Field(..., min_length=8, max_length=255)
    confirm_password: SecretStr = Field(..., min_length=8, max_length=255)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdate(BaseSchema):
    """User update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    risk_level: Optional[str] = Field(None, regex=r'^(low|medium|high)$')

class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


# Account schemas
class AccountBase(BaseSchema):
    """Base account schema"""
    account_type: AccountType
    account_name: str = Field(..., min_length=1, max_length=100)
    currency: str = Field("USD", regex=r'^[A-Z]{3}$')
    margin_enabled: bool = False
    options_enabled: bool = False

class AccountCreate(AccountBase):
    """Account creation schema"""
    pass

class AccountUpdate(BaseSchema):
    """Account update schema"""
    account_name: Optional[str] = Field(None, min_length=1, max_length=100)
    margin_enabled: Optional[bool] = None
    options_enabled: Optional[bool] = None

class AccountResponse(AccountBase):
    """Account response schema"""
    id: UUID
    user_id: UUID
    account_number: str
    cash_balance: Decimal
    available_balance: Decimal
    margin_balance: Decimal
    buying_power: Decimal
    day_trade_buying_power: Decimal
    maintenance_margin_requirement: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Instrument schemas
class InstrumentBase(BaseSchema):
    """Base instrument schema"""
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    asset_class: AssetClass
    sector: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    exchange: str = Field(..., min_length=1, max_length=20)
    tick_size: Decimal = Field(Decimal('0.01'), gt=0)
    lot_size: int = Field(1, gt=0)
    min_quantity: Decimal = Field(Decimal('1'), gt=0)
    max_quantity: Optional[Decimal] = Field(None, gt=0)
    is_tradable: bool = True
    is_shortable: bool = False
    margin_requirement: Decimal = Field(Decimal('0.5'), ge=0, le=1)

class InstrumentCreate(InstrumentBase):
    """Instrument creation schema"""
    pass

class InstrumentUpdate(BaseSchema):
    """Instrument update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_tradable: Optional[bool] = None
    is_shortable: Optional[bool] = None
    margin_requirement: Optional[Decimal] = Field(None, ge=0, le=1)

class InstrumentResponse(InstrumentBase):
    """Instrument response schema"""
    id: UUID
    last_price: Optional[Decimal] = None
    bid_price: Optional[Decimal] = None
    ask_price: Optional[Decimal] = None
    volume: Decimal
    created_at: datetime
    updated_at: datetime


# Market data schemas
class MarketDataBase(BaseSchema):
    """Base market data schema"""
    price: Decimal = Field(..., gt=0)
    bid: Optional[Decimal] = Field(None, gt=0)
    ask: Optional[Decimal] = Field(None, gt=0)
    high: Optional[Decimal] = Field(None, gt=0)
    low: Optional[Decimal] = Field(None, gt=0)
    open: Optional[Decimal] = Field(None, gt=0)
    close: Optional[Decimal] = Field(None, gt=0)
    volume: Decimal = Field(Decimal('0'), ge=0)
    bid_size: Decimal = Field(Decimal('0'), ge=0)
    ask_size: Decimal = Field(Decimal('0'), ge=0)
    vwap: Optional[Decimal] = Field(None, gt=0)
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    data_source: str = Field(..., min_length=1, max_length=50)
    is_delayed: bool = False

class MarketDataCreate(MarketDataBase):
    """Market data creation schema"""
    instrument_id: UUID

class MarketDataResponse(MarketDataBase):
    """Market data response schema"""
    id: UUID
    instrument_id: UUID
    timestamp: datetime


# Order schemas
class OrderBase(BaseSchema):
    """Base order schema"""
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)
    time_in_force: TimeInForce = TimeInForce.GTC
    client_order_id: Optional[str] = Field(None, max_length=100)

    @validator('price')
    def validate_price_for_limit_orders(cls, v, values):
        if values.get('order_type') in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('Price is required for limit orders')
        return v

    @validator('stop_price')
    def validate_stop_price_for_stop_orders(cls, v, values):
        if values.get('order_type') in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('Stop price is required for stop orders')
        return v

class OrderCreate(OrderBase):
    """Order creation schema"""
    instrument_id: UUID
    account_id: UUID

class OrderUpdate(BaseSchema):
    """Order update schema"""
    quantity: Optional[Decimal] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)
    time_in_force: Optional[TimeInForce] = None

class OrderResponse(OrderBase):
    """Order response schema"""
    id: UUID
    user_id: UUID
    account_id: UUID
    instrument_id: UUID
    exchange_order_id: Optional[str] = None
    status: OrderStatus
    filled_quantity: Decimal
    remaining_quantity: Decimal
    avg_fill_price: Decimal
    order_value: Optional[Decimal] = None
    commission: Decimal
    fees: Decimal
    risk_checked: bool
    compliance_checked: bool
    reject_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


# Execution schemas
class ExecutionBase(BaseSchema):
    """Base execution schema"""
    execution_id: str = Field(..., min_length=1, max_length=100)
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    side: OrderSide
    commission: Decimal = Field(Decimal('0'), ge=0)
    fees: Decimal = Field(Decimal('0'), ge=0)
    net_amount: Decimal
    exchange: Optional[str] = Field(None, max_length=20)
    venue: Optional[str] = Field(None, max_length=20)

class ExecutionCreate(ExecutionBase):
    """Execution creation schema"""
    order_id: UUID

class ExecutionResponse(ExecutionBase):
    """Execution response schema"""
    id: UUID
    order_id: UUID
    executed_at: datetime


# Position schemas
class PositionBase(BaseSchema):
    """Base position schema"""
    quantity: Decimal = Field(Decimal('0'))
    avg_cost: Decimal = Field(Decimal('0'), ge=0)
    market_value: Decimal = Field(Decimal('0'), ge=0)
    unrealized_pnl: Decimal = Field(Decimal('0'))
    realized_pnl: Decimal = Field(Decimal('0'))
    day_pnl: Decimal = Field(Decimal('0'))
    delta: Decimal = Field(Decimal('0'))
    gamma: Decimal = Field(Decimal('0'))
    theta: Decimal = Field(Decimal('0'))
    vega: Decimal = Field(Decimal('0'))

class PositionResponse(PositionBase):
    """Position response schema"""
    id: UUID
    account_id: UUID
    instrument_id: UUID
    created_at: datetime
    updated_at: datetime


# Transaction schemas
class TransactionBase(BaseSchema):
    """Base transaction schema"""
    transaction_type: TransactionType
    amount: Decimal = Field(..., ne=0)
    currency: str = Field("USD", regex=r'^[A-Z]{3}$')
    description: Optional[str] = None
    reference_id: Optional[str] = Field(None, max_length=100)
    status: str = Field("PENDING", regex=r'^(PENDING|PROCESSED|SETTLED|CANCELLED|FAILED)$')

class TransactionCreate(TransactionBase):
    """Transaction creation schema"""
    account_id: UUID
    related_order_id: Optional[UUID] = None

class TransactionResponse(TransactionBase):
    """Transaction response schema"""
    id: UUID
    user_id: UUID
    account_id: UUID
    related_order_id: Optional[UUID] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None


# Audit log schemas
class AuditLogBase(BaseSchema):
    """Base audit log schema"""
    event_type: str = Field(..., min_length=1, max_length=50)
    event_description: str = Field(..., min_length=1)
    table_name: Optional[str] = Field(None, max_length=50)
    record_id: Optional[UUID] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = Field(None, max_length=128)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    compliance_tags: Optional[Dict[str, Any]] = None
    sox_relevant: bool = False

class AuditLogCreate(AuditLogBase):
    """Audit log creation schema"""
    user_id: Optional[UUID] = None

class AuditLogResponse(AuditLogBase):
    """Audit log response schema"""
    id: UUID
    user_id: Optional[UUID] = None
    retention_until: datetime
    hash_value: str
    signature: Optional[str] = None
    created_at: datetime


# Portfolio schemas
class PortfolioSummary(BaseSchema):
    """Portfolio summary schema"""
    account_id: UUID
    total_value: Decimal
    cash_balance: Decimal
    positions_value: Decimal
    available_balance: Decimal
    buying_power: Decimal
    total_pnl: Decimal
    day_pnl: Decimal
    positions_count: int
    updated_at: datetime

class PortfolioPosition(BaseSchema):
    """Portfolio position schema"""
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    day_pnl: Decimal
    percentage_of_portfolio: Decimal

class PortfolioResponse(BaseSchema):
    """Portfolio response schema"""
    summary: PortfolioSummary
    positions: List[PortfolioPosition]
    performance_metrics: Dict[str, Any]


# Trading statistics schemas
class TradingStatistics(BaseSchema):
    """Trading statistics schema"""
    period: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    total_pnl: Decimal
    average_win: Decimal
    average_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    profit_factor: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal


# Risk metrics schemas
class RiskMetrics(BaseSchema):
    """Risk metrics schema"""
    account_id: UUID
    var_95: Decimal
    var_99: Decimal
    expected_shortfall: Decimal
    maximum_drawdown: Decimal
    position_concentration: Decimal
    leverage_ratio: Decimal
    beta: Decimal
    correlation_matrix: Dict[str, Dict[str, Decimal]]
    risk_score: Decimal
    risk_limit_utilization: Decimal
    updated_at: datetime


# Compliance schemas
class ComplianceCheck(BaseSchema):
    """Compliance check schema"""
    check_type: str
    status: str
    details: Dict[str, Any]
    timestamp: datetime

class ComplianceReport(BaseSchema):
    """Compliance report schema"""
    report_id: UUID
    report_type: str
    period_start: datetime
    period_end: datetime
    compliance_score: Decimal
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime


# Error schemas
class ErrorResponse(BaseSchema):
    """Error response schema"""
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None


# Pagination schemas
class PaginationParams(BaseSchema):
    """Pagination parameters schema"""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class PaginatedResponse(BaseSchema):
    """Paginated response schema"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool