"""
SQLAlchemy Database Models for Trading System
High-performance models designed for high-frequency trading with ACID compliance
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey,
    Index, UniqueConstraint, CheckConstraint, func, event, DDL
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.sql import text
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

# PostgreSQL Enums for type safety
order_side_enum = ENUM('BUY', 'SELL', name='order_side_enum')
order_type_enum = ENUM('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', name='order_type_enum')
order_status_enum = ENUM('PENDING', 'PARTIALLY_FILLED', 'FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED', name='order_status_enum')
time_in_force_enum = ENUM('GTC', 'IOC', 'FOK', 'DAY', name='time_in_force_enum')
account_type_enum = ENUM('TRADING', 'DEMO', 'PAPER', 'MARGIN', name='account_type_enum')
asset_class_enum = ENUM('EQUITY', 'OPTION', 'FUTURE', 'FOREX', 'CRYPTO', 'COMMODITY', name='asset_class_enum')
transaction_type_enum = ENUM('TRADE', 'DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST', 'FEE', name='transaction_type_enum')

class User(Base):
    """User management table with authentication and profile information"""
    __tablename__ = "users"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(32), nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(DateTime(timezone=True))
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Risk and compliance
    risk_level = Column(String(20), default='medium', nullable=False)
    kyc_status = Column(String(20), default='pending', nullable=False)
    accredited_investor = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True))
    last_ip = Column(String(45))
    
    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name='valid_risk_level'),
        CheckConstraint("kyc_status IN ('pending', 'verified', 'rejected')", name='valid_kyc_status'),
        Index('idx_users_active_verified', 'is_active', 'is_verified'),
        Index('idx_users_last_login', 'last_login'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Account(Base):
    """Account management table for different account types"""
    __tablename__ = "accounts"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Account details
    account_number = Column(String(20), unique=True, nullable=False, index=True)
    account_type = Column(account_type_enum, nullable=False)
    account_name = Column(String(100), nullable=False)
    
    # Balances (using NUMERIC for precision)
    cash_balance = Column(Numeric(20, 8), nullable=False, default=0)
    available_balance = Column(Numeric(20, 8), nullable=False, default=0)
    margin_balance = Column(Numeric(20, 8), nullable=False, default=0)
    buying_power = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Account settings
    currency = Column(String(3), nullable=False, default='USD')
    is_active = Column(Boolean, default=True, nullable=False)
    margin_enabled = Column(Boolean, default=False, nullable=False)
    options_enabled = Column(Boolean, default=False, nullable=False)
    
    # Risk management
    day_trade_buying_power = Column(Numeric(20, 8), nullable=False, default=0)
    maintenance_margin_requirement = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    orders = relationship("Order", back_populates="account")
    positions = relationship("Position", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("cash_balance >= 0", name='positive_cash_balance'),
        CheckConstraint("available_balance >= 0", name='positive_available_balance'),
        CheckConstraint("currency IN ('USD', 'EUR', 'GBP', 'JPY', 'CAD')", name='valid_currency'),
        Index('idx_accounts_user_type', 'user_id', 'account_type'),
        Index('idx_accounts_active', 'is_active'),
        Index('idx_accounts_balance', 'cash_balance'),
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, account_number='{self.account_number}')>"

class Instrument(Base):
    """Trading instruments/symbols master table"""
    __tablename__ = "instruments"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Symbol information
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Classification
    asset_class = Column(asset_class_enum, nullable=False)
    sector = Column(String(50))
    industry = Column(String(100))
    exchange = Column(String(20), nullable=False)
    
    # Trading specifications
    tick_size = Column(Numeric(10, 8), nullable=False, default=0.01)
    lot_size = Column(Integer, nullable=False, default=1)
    min_quantity = Column(Numeric(20, 8), nullable=False, default=1)
    max_quantity = Column(Numeric(20, 8))
    
    # Status and availability
    is_tradable = Column(Boolean, default=True, nullable=False)
    is_shortable = Column(Boolean, default=False, nullable=False)
    margin_requirement = Column(Numeric(5, 4), nullable=False, default=0.5)  # 50% margin
    
    # Market data
    last_price = Column(Numeric(20, 8))
    bid_price = Column(Numeric(20, 8))
    ask_price = Column(Numeric(20, 8))
    volume = Column(Numeric(20, 8), default=0)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    orders = relationship("Order", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")
    market_data = relationship("MarketData", back_populates="instrument", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("tick_size > 0", name='positive_tick_size'),
        CheckConstraint("lot_size > 0", name='positive_lot_size'),
        CheckConstraint("min_quantity > 0", name='positive_min_quantity'),
        CheckConstraint("margin_requirement >= 0 AND margin_requirement <= 1", name='valid_margin_requirement'),
        Index('idx_instruments_tradable', 'is_tradable'),
        Index('idx_instruments_asset_class', 'asset_class'),
        Index('idx_instruments_exchange', 'exchange'),
        Index('idx_instruments_sector', 'sector'),
    )
    
    def __repr__(self):
        return f"<Instrument(id={self.id}, symbol='{self.symbol}')>"

class MarketData(Base):
    """Real-time and historical market data table"""
    __tablename__ = "market_data"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    instrument_id = Column(PGUUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Price data
    price = Column(Numeric(20, 8), nullable=False)
    bid = Column(Numeric(20, 8))
    ask = Column(Numeric(20, 8))
    high = Column(Numeric(20, 8))
    low = Column(Numeric(20, 8))
    open = Column(Numeric(20, 8))
    close = Column(Numeric(20, 8))
    
    # Volume data
    volume = Column(Numeric(20, 8), nullable=False, default=0)
    bid_size = Column(Numeric(20, 8), default=0)
    ask_size = Column(Numeric(20, 8), default=0)
    
    # Calculated fields
    vwap = Column(Numeric(20, 8))  # Volume Weighted Average Price
    change = Column(Numeric(20, 8))
    change_percent = Column(Numeric(8, 4))
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    
    # Data quality
    data_source = Column(String(50), nullable=False)
    is_delayed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    instrument = relationship("Instrument", back_populates="market_data")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("price > 0", name='positive_price'),
        CheckConstraint("volume >= 0", name='non_negative_volume'),
        CheckConstraint("bid_size >= 0", name='non_negative_bid_size'),
        CheckConstraint("ask_size >= 0", name='non_negative_ask_size'),
        Index('idx_market_data_instrument_timestamp', 'instrument_id', 'timestamp'),
        Index('idx_market_data_timestamp', 'timestamp'),
        Index('idx_market_data_price', 'price'),
        # Unique constraint for time-series data
        UniqueConstraint('instrument_id', 'timestamp', name='unique_market_data_point'),
    )
    
    def __repr__(self):
        return f"<MarketData(instrument_id={self.instrument_id}, price={self.price}, timestamp={self.timestamp})>"

class Order(Base):
    """Order management table for high-frequency trading"""
    __tablename__ = "orders"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign keys
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(PGUUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Order identification
    client_order_id = Column(String(100), index=True)
    exchange_order_id = Column(String(100), index=True)
    
    # Order details
    side = Column(order_side_enum, nullable=False)
    order_type = Column(order_type_enum, nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8))  # Optional for market orders
    stop_price = Column(Numeric(20, 8))  # For stop orders
    time_in_force = Column(time_in_force_enum, nullable=False, default='GTC')
    
    # Order status
    status = Column(order_status_enum, nullable=False, default='PENDING')
    filled_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    remaining_quantity = Column(Numeric(20, 8), nullable=False)
    avg_fill_price = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    filled_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    
    # Risk and compliance
    risk_checked = Column(Boolean, default=False, nullable=False)
    compliance_checked = Column(Boolean, default=False, nullable=False)
    reject_reason = Column(Text)
    
    # Trading metadata
    order_value = Column(Numeric(20, 8))  # Computed field
    commission = Column(Numeric(20, 8), default=0)
    fees = Column(Numeric(20, 8), default=0)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    account = relationship("Account", back_populates="orders")
    instrument = relationship("Instrument", back_populates="orders")
    executions = relationship("Execution", back_populates="order", cascade="all, delete-orphan")
    
    # Hybrid properties for computed fields
    @hybrid_property
    def is_filled(self):
        return self.status == 'FILLED'
    
    @hybrid_property
    def fill_percentage(self):
        if self.quantity > 0:
            return (self.filled_quantity / self.quantity) * 100
        return 0
    
    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name='positive_quantity'),
        CheckConstraint("price IS NULL OR price > 0", name='positive_price'),
        CheckConstraint("stop_price IS NULL OR stop_price > 0", name='positive_stop_price'),
        CheckConstraint("filled_quantity >= 0", name='non_negative_filled_quantity'),
        CheckConstraint("filled_quantity <= quantity", name='filled_within_quantity'),
        CheckConstraint("avg_fill_price >= 0", name='non_negative_avg_fill_price'),
        CheckConstraint("commission >= 0", name='non_negative_commission'),
        CheckConstraint("fees >= 0", name='non_negative_fees'),
        # High-performance indexes for order processing
        Index('idx_orders_status_created', 'status', 'created_at'),
        Index('idx_orders_user_account', 'user_id', 'account_id'),
        Index('idx_orders_instrument_side', 'instrument_id', 'side'),
        Index('idx_orders_client_order_id', 'client_order_id'),
        Index('idx_orders_exchange_order_id', 'exchange_order_id'),
        Index('idx_orders_pending', 'status', postgresql_where=text("status = 'PENDING'")),
        Index('idx_orders_active', 'status', postgresql_where=text("status IN ('PENDING', 'PARTIALLY_FILLED')")),
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, side={self.side}, quantity={self.quantity}, status={self.status})>"

class Execution(Base):
    """Order execution/fill table for transaction records"""
    __tablename__ = "executions"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Execution details
    execution_id = Column(String(100), unique=True, nullable=False, index=True)
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    side = Column(order_side_enum, nullable=False)
    
    # Timing
    executed_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    
    # Fees and commissions
    commission = Column(Numeric(20, 8), default=0)
    fees = Column(Numeric(20, 8), default=0)
    net_amount = Column(Numeric(20, 8), nullable=False)
    
    # Exchange information
    exchange = Column(String(20))
    venue = Column(String(20))
    
    # Relationships
    order = relationship("Order", back_populates="executions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name='positive_execution_quantity'),
        CheckConstraint("price > 0", name='positive_execution_price'),
        CheckConstraint("commission >= 0", name='non_negative_execution_commission'),
        CheckConstraint("fees >= 0", name='non_negative_execution_fees'),
        Index('idx_executions_order_executed', 'order_id', 'executed_at'),
        Index('idx_executions_executed_at', 'executed_at'),
        Index('idx_executions_price', 'price'),
    )
    
    def __repr__(self):
        return f"<Execution(id={self.id}, order_id={self.order_id}, quantity={self.quantity}, price={self.price})>"

class Position(Base):
    """Portfolio position tracking table"""
    __tablename__ = "positions"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign keys
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(PGUUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Position details
    quantity = Column(Numeric(20, 8), nullable=False, default=0)
    avg_cost = Column(Numeric(20, 8), nullable=False, default=0)
    market_value = Column(Numeric(20, 8), nullable=False, default=0)
    
    # P&L calculations
    unrealized_pnl = Column(Numeric(20, 8), nullable=False, default=0)
    realized_pnl = Column(Numeric(20, 8), nullable=False, default=0)
    day_pnl = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Risk metrics
    delta = Column(Numeric(10, 6), default=0)  # For options
    gamma = Column(Numeric(10, 6), default=0)  # For options
    theta = Column(Numeric(10, 6), default=0)  # For options
    vega = Column(Numeric(10, 6), default=0)   # For options
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False, index=True)
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")
    
    # Hybrid properties
    @hybrid_property
    def is_long(self):
        return self.quantity > 0
    
    @hybrid_property
    def is_short(self):
        return self.quantity < 0
    
    @hybrid_property
    def is_flat(self):
        return self.quantity == 0
    
    # Constraints
    __table_args__ = (
        CheckConstraint("avg_cost >= 0", name='non_negative_avg_cost'),
        CheckConstraint("market_value >= 0", name='non_negative_market_value'),
        # Unique constraint for account-instrument pairs
        UniqueConstraint('account_id', 'instrument_id', name='unique_account_instrument_position'),
        Index('idx_positions_account_updated', 'account_id', 'updated_at'),
        Index('idx_positions_instrument', 'instrument_id'),
        Index('idx_positions_quantity', 'quantity'),
        Index('idx_positions_market_value', 'market_value'),
        Index('idx_positions_pnl', 'unrealized_pnl', 'realized_pnl'),
        # Partial indexes for active positions
        Index('idx_positions_long', 'account_id', 'quantity', postgresql_where=text("quantity > 0")),
        Index('idx_positions_short', 'account_id', 'quantity', postgresql_where=text("quantity < 0")),
    )
    
    def __repr__(self):
        return f"<Position(account_id={self.account_id}, instrument_id={self.instrument_id}, quantity={self.quantity})>"

class Transaction(Base):
    """Financial transaction table for cash movements"""
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign keys
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(transaction_type_enum, nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    description = Column(Text)
    
    # Reference information
    reference_id = Column(String(100), index=True)  # External reference
    related_order_id = Column(PGUUID(as_uuid=True), ForeignKey("orders.id"))
    
    # Status
    status = Column(String(20), nullable=False, default='PENDING')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    settled_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    related_order = relationship("Order", foreign_keys=[related_order_id])
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount != 0", name='non_zero_amount'),
        CheckConstraint("currency IN ('USD', 'EUR', 'GBP', 'JPY', 'CAD')", name='valid_transaction_currency'),
        CheckConstraint("status IN ('PENDING', 'PROCESSED', 'SETTLED', 'CANCELLED', 'FAILED')", name='valid_transaction_status'),
        Index('idx_transactions_user_account', 'user_id', 'account_id'),
        Index('idx_transactions_type_status', 'transaction_type', 'status'),
        Index('idx_transactions_created_at', 'created_at'),
        Index('idx_transactions_processed_at', 'processed_at'),
        Index('idx_transactions_amount', 'amount'),
        Index('idx_transactions_reference', 'reference_id'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"

class AuditLog(Base):
    """Comprehensive audit log table for SOX compliance"""
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Foreign keys
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    # Audit details
    event_type = Column(String(50), nullable=False, index=True)
    event_description = Column(Text, nullable=False)
    table_name = Column(String(50), index=True)
    record_id = Column(PGUUID(as_uuid=True), index=True)
    
    # Before/After data for changes
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    
    # Session information
    session_id = Column(String(128), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Compliance fields
    compliance_tags = Column(JSONB)
    sox_relevant = Column(Boolean, default=False, nullable=False)
    retention_until = Column(DateTime(timezone=True), nullable=False)
    
    # Cryptographic integrity
    hash_value = Column(String(128), nullable=False)
    signature = Column(String(512))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("retention_until > created_at", name='valid_retention_period'),
        Index('idx_audit_logs_event_type', 'event_type'),
        Index('idx_audit_logs_table_record', 'table_name', 'record_id'),
        Index('idx_audit_logs_user_created', 'user_id', 'created_at'),
        Index('idx_audit_logs_sox_relevant', 'sox_relevant', postgresql_where=text("sox_relevant = true")),
        Index('idx_audit_logs_retention', 'retention_until'),
        Index('idx_audit_logs_session', 'session_id'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, created_at={self.created_at})>"

# Database triggers and functions for maintaining data integrity
audit_trigger_ddl = DDL("""
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, event_type, event_description, table_name, record_id, old_values, retention_until, hash_value, created_at)
        VALUES (
            current_setting('trading.current_user_id', true)::uuid,
            'DELETE',
            'Record deleted from ' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            OLD.id,
            to_jsonb(OLD),
            NOW() + INTERVAL '7 years',
            encode(digest(to_jsonb(OLD)::text, 'sha256'), 'hex'),
            NOW()
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, event_type, event_description, table_name, record_id, old_values, new_values, retention_until, hash_value, created_at)
        VALUES (
            current_setting('trading.current_user_id', true)::uuid,
            'UPDATE',
            'Record updated in ' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            NEW.id,
            to_jsonb(OLD),
            to_jsonb(NEW),
            NOW() + INTERVAL '7 years',
            encode(digest((to_jsonb(OLD)::text || to_jsonb(NEW)::text), 'sha256'), 'hex'),
            NOW()
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, event_type, event_description, table_name, record_id, new_values, retention_until, hash_value, created_at)
        VALUES (
            current_setting('trading.current_user_id', true)::uuid,
            'INSERT',
            'Record inserted into ' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            NEW.id,
            to_jsonb(NEW),
            NOW() + INTERVAL '7 years',
            encode(digest(to_jsonb(NEW)::text, 'sha256'), 'hex'),
            NOW()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

# Event listeners to create audit triggers
@event.listens_for(Base.metadata, "after_create")
def create_audit_triggers(target, connection, **kw):
    """Create audit triggers for all tables"""
    connection.execute(audit_trigger_ddl)
    
    # Create triggers for critical tables
    critical_tables = ['orders', 'executions', 'positions', 'transactions', 'accounts']
    for table in critical_tables:
        trigger_sql = f"""
        CREATE TRIGGER {table}_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON {table}
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        """
        connection.execute(text(trigger_sql))

# Validation functions
@event.listens_for(Order, 'before_insert')
@event.listens_for(Order, 'before_update')
def validate_order(mapper, connection, target):
    """Validate order before insert/update"""
    # Calculate remaining quantity
    target.remaining_quantity = target.quantity - target.filled_quantity
    
    # Calculate order value
    if target.price:
        target.order_value = target.quantity * target.price
    
    # Validate stop orders
    if target.order_type in ['STOP', 'STOP_LIMIT'] and not target.stop_price:
        raise ValueError("Stop orders require stop_price")
    
    # Validate limit orders
    if target.order_type in ['LIMIT', 'STOP_LIMIT'] and not target.price:
        raise ValueError("Limit orders require price")

@event.listens_for(Position, 'before_insert')
@event.listens_for(Position, 'before_update')
def calculate_position_pnl(mapper, connection, target):
    """Calculate P&L for positions"""
    if target.quantity != 0 and target.avg_cost > 0:
        # This would be calculated with current market price
        # For now, we'll use a placeholder calculation
        current_price = target.avg_cost * Decimal('1.05')  # 5% gain simulation
        target.market_value = abs(target.quantity) * current_price
        target.unrealized_pnl = target.quantity * (current_price - target.avg_cost)
    else:
        target.market_value = 0
        target.unrealized_pnl = 0