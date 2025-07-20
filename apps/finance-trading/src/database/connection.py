"""
Database Connection Management
High-performance connection pooling for PostgreSQL with SQLAlchemy
"""

import os
import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event, text
import logging

logger = logging.getLogger(__name__)

# Global database engine and session factory
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'trading_db'),
    'username': os.getenv('DB_USER', 'trading_user'),
    'password': os.getenv('DB_PASSWORD', 'trading_password'),
    'schema': os.getenv('DB_SCHEMA', 'public')
}

# Connection pool configuration
POOL_CONFIG = {
    'pool_size': int(os.getenv('DB_POOL_SIZE', '20')),
    'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '30')),
    'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
    'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
    'pool_pre_ping': os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true',
    'pool_reset_on_return': os.getenv('DB_POOL_RESET_ON_RETURN', 'commit')
}

# Performance configuration
PERFORMANCE_CONFIG = {
    'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',
    'echo_pool': os.getenv('DB_ECHO_POOL', 'false').lower() == 'true',
    'future': True,
    'query_cache_size': int(os.getenv('DB_QUERY_CACHE_SIZE', '1200')),
    'isolation_level': os.getenv('DB_ISOLATION_LEVEL', 'READ_COMMITTED')
}

def get_database_url() -> str:
    """Get database URL for connection"""
    return (
        f"postgresql+asyncpg://{DATABASE_CONFIG['username']}:"
        f"{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:"
        f"{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
    )

def get_sync_database_url() -> str:
    """Get synchronous database URL for migrations"""
    return (
        f"postgresql://{DATABASE_CONFIG['username']}:"
        f"{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:"
        f"{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
    )

async def create_database_engine() -> AsyncEngine:
    """Create database engine with optimized connection pool"""
    database_url = get_database_url()
    
    # Create engine with connection pooling
    engine = create_async_engine(
        database_url,
        # Pool configuration
        poolclass=QueuePool,
        pool_size=POOL_CONFIG['pool_size'],
        max_overflow=POOL_CONFIG['max_overflow'],
        pool_timeout=POOL_CONFIG['pool_timeout'],
        pool_recycle=POOL_CONFIG['pool_recycle'],
        pool_pre_ping=POOL_CONFIG['pool_pre_ping'],
        pool_reset_on_return=POOL_CONFIG['pool_reset_on_return'],
        
        # Performance configuration
        echo=PERFORMANCE_CONFIG['echo'],
        echo_pool=PERFORMANCE_CONFIG['echo_pool'],
        future=PERFORMANCE_CONFIG['future'],
        query_cache_size=PERFORMANCE_CONFIG['query_cache_size'],
        
        # Connection arguments
        connect_args={
            'server_settings': {
                'application_name': 'finance_trading_app',
                'statement_timeout': '30000',  # 30 second timeout
                'idle_in_transaction_session_timeout': '60000',  # 1 minute timeout
                'tcp_keepalives_idle': '300',  # 5 minutes
                'tcp_keepalives_interval': '30',  # 30 seconds
                'tcp_keepalives_count': '3'
            },
            'command_timeout': 30,
            'prepared_statement_cache_size': 100
        }
    )
    
    # Set up event listeners for connection optimization
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set connection-level configuration"""
        pass
    
    @event.listens_for(engine.sync_engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """Configure connection on checkout"""
        logger.debug(f"Connection checked out: {id(dbapi_connection)}")
    
    @event.listens_for(engine.sync_engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        """Handle connection checkin"""
        logger.debug(f"Connection checked in: {id(dbapi_connection)}")
    
    return engine

async def get_database_engine() -> AsyncEngine:
    """Get or create database engine"""
    global _engine
    
    if _engine is None:
        _engine = await create_database_engine()
        logger.info("Database engine created")
    
    return _engine

async def get_session_factory() -> async_sessionmaker:
    """Get or create session factory"""
    global _session_factory
    
    if _session_factory is None:
        engine = await get_database_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        logger.info("Session factory created")
    
    return _session_factory

@asynccontextmanager
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup"""
    session_factory = await get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections"""
        if self._initialized:
            return
        
        self.engine = await create_database_engine()
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        # Test connection
        await self.health_check()
        
        self._initialized = True
        logger.info("Database manager initialized")
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            self._initialized = False
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """Get connection pool information"""
        if not self.engine:
            return {}
        
        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }

# Global database manager instance
database_manager = DatabaseManager()

# Convenience functions
async def init_database():
    """Initialize database connections"""
    await database_manager.initialize()

async def close_database():
    """Close database connections"""
    await database_manager.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (convenience function)"""
    async with database_manager.get_session() as session:
        yield session

async def execute_query(query: str, params: dict = None) -> any:
    """Execute raw SQL query"""
    async with get_db_session() as session:
        result = await session.execute(text(query), params or {})
        return result

async def execute_transaction(queries: list) -> bool:
    """Execute multiple queries in a transaction"""
    async with get_db_session() as session:
        try:
            for query, params in queries:
                await session.execute(text(query), params or {})
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Transaction failed: {e}")
            return False

# Connection pool monitoring
class ConnectionPoolMonitor:
    """Monitor connection pool health and performance"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
        self.monitoring_active = False
        self.monitoring_task = None
    
    async def start_monitoring(self, interval: int = 60):
        """Start connection pool monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info("Connection pool monitoring started")
    
    async def stop_monitoring(self):
        """Stop connection pool monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Connection pool monitoring stopped")
    
    async def _monitor_loop(self, interval: int):
        """Monitor loop for connection pool"""
        while self.monitoring_active:
            try:
                info = await self.db_manager.get_connection_info()
                if info:
                    pool_utilization = (info['checked_out'] / info['pool_size']) * 100
                    
                    logger.info(
                        f"Connection pool status: "
                        f"Size={info['pool_size']}, "
                        f"In use={info['checked_out']}, "
                        f"Available={info['checked_in']}, "
                        f"Utilization={pool_utilization:.1f}%"
                    )
                    
                    # Alert if pool utilization is high
                    if pool_utilization > 80:
                        logger.warning(f"High connection pool utilization: {pool_utilization:.1f}%")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in connection pool monitoring: {e}")
                await asyncio.sleep(interval)

# Create global pool monitor
pool_monitor = ConnectionPoolMonitor(database_manager)

# Startup and shutdown handlers
async def startup_database():
    """Database startup handler"""
    await init_database()
    await pool_monitor.start_monitoring()

async def shutdown_database():
    """Database shutdown handler"""
    await pool_monitor.stop_monitoring()
    await close_database()