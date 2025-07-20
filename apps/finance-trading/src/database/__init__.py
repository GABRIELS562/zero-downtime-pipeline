"""
Database Package
Centralized database components for the trading system
"""

from .connection import (
    get_database_engine,
    get_database_session,
    get_db_session,
    database_manager,
    startup_database,
    shutdown_database,
    DatabaseManager,
    ConnectionPoolMonitor
)

from .models import (
    Base,
    User,
    Account,
    Instrument,
    MarketData,
    Order,
    Execution,
    Position,
    Transaction,
    AuditLog
)

from .schemas import (
    # User schemas
    UserCreate,
    UserUpdate,
    UserResponse,
    
    # Account schemas
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    
    # Instrument schemas
    InstrumentCreate,
    InstrumentUpdate,
    InstrumentResponse,
    
    # Market data schemas
    MarketDataCreate,
    MarketDataResponse,
    
    # Order schemas
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    
    # Execution schemas
    ExecutionCreate,
    ExecutionResponse,
    
    # Position schemas
    PositionResponse,
    
    # Transaction schemas
    TransactionCreate,
    TransactionResponse,
    
    # Audit log schemas
    AuditLogCreate,
    AuditLogResponse,
    
    # Portfolio schemas
    PortfolioSummary,
    PortfolioPosition,
    PortfolioResponse,
    
    # Enums
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    AccountType,
    AssetClass,
    TransactionType,
    
    # Utility schemas
    ErrorResponse,
    PaginationParams,
    PaginatedResponse
)

from .migrations import (
    MigrationManager,
    create_initial_migration,
    upgrade_to_latest,
    reset_database
)

__all__ = [
    # Connection management
    'get_database_engine',
    'get_database_session',
    'get_db_session',
    'database_manager',
    'startup_database',
    'shutdown_database',
    'DatabaseManager',
    'ConnectionPoolMonitor',
    
    # Models
    'Base',
    'User',
    'Account',
    'Instrument',
    'MarketData',
    'Order',
    'Execution',
    'Position',
    'Transaction',
    'AuditLog',
    
    # Schemas
    'UserCreate',
    'UserUpdate',
    'UserResponse',
    'AccountCreate',
    'AccountUpdate',
    'AccountResponse',
    'InstrumentCreate',
    'InstrumentUpdate',
    'InstrumentResponse',
    'MarketDataCreate',
    'MarketDataResponse',
    'OrderCreate',
    'OrderUpdate',
    'OrderResponse',
    'ExecutionCreate',
    'ExecutionResponse',
    'PositionResponse',
    'TransactionCreate',
    'TransactionResponse',
    'AuditLogCreate',
    'AuditLogResponse',
    'PortfolioSummary',
    'PortfolioPosition',
    'PortfolioResponse',
    'OrderSide',
    'OrderType',
    'OrderStatus',
    'TimeInForce',
    'AccountType',
    'AssetClass',
    'TransactionType',
    'ErrorResponse',
    'PaginationParams',
    'PaginatedResponse',
    
    # Migrations
    'MigrationManager',
    'create_initial_migration',
    'upgrade_to_latest',
    'reset_database'
]