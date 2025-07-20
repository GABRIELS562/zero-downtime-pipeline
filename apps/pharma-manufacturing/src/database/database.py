"""
Database Configuration and Connection Management
Real-time monitoring optimized database setup for pharmaceutical manufacturing
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import threading
import time
from datetime import datetime, timezone, timedelta

from .models import Base, AuditTrail, SystemEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://pharma_user:pharma_pass@localhost:5432/pharma_manufacturing"
        )
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "30"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        self.pool_pre_ping = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
        
        # Real-time monitoring settings
        self.monitoring_enabled = os.getenv("DB_MONITORING_ENABLED", "true").lower() == "true"
        self.slow_query_threshold = float(os.getenv("DB_SLOW_QUERY_THRESHOLD", "1.0"))
        self.connection_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))
        
        # FDA compliance settings
        self.audit_all_queries = os.getenv("DB_AUDIT_ALL_QUERIES", "false").lower() == "true"
        self.data_integrity_checks = os.getenv("DB_DATA_INTEGRITY_CHECKS", "true").lower() == "true"
        
        # Performance settings
        self.statement_timeout = int(os.getenv("DB_STATEMENT_TIMEOUT", "300"))  # 5 minutes
        self.idle_in_transaction_session_timeout = int(os.getenv("DB_IDLE_TIMEOUT", "600"))  # 10 minutes

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self._connection_pool_stats = {}
        self._query_stats = {}
        self._lock = threading.Lock()
        
    def initialize(self):
        """Initialize database engine and session factory"""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                connect_args={
                    "connect_timeout": self.config.connection_timeout,
                    "options": f"-c statement_timeout={self.config.statement_timeout}s "
                              f"-c idle_in_transaction_session_timeout={self.config.idle_in_transaction_session_timeout}s"
                },
                echo=False,  # Set to True for SQL debugging
                future=True
            )
            
            # Set up session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Register event listeners
            self._setup_event_listeners()
            
            logger.info(f"Database initialized successfully with pool size: {self.config.pool_size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring"""
        if not self.config.monitoring_enabled:
            return
        
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Handle new database connections"""
            connection_record.info['connect_time'] = time.time()
            logger.debug(f"New database connection established: {id(dbapi_connection)}")
        
        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout from pool"""
            with self._lock:
                self._connection_pool_stats['checkouts'] = self._connection_pool_stats.get('checkouts', 0) + 1
                connection_record.info['checkout_time'] = time.time()
        
        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Handle connection checkin to pool"""
            with self._lock:
                self._connection_pool_stats['checkins'] = self._connection_pool_stats.get('checkins', 0) + 1
                if 'checkout_time' in connection_record.info:
                    usage_time = time.time() - connection_record.info['checkout_time']
                    self._connection_pool_stats['avg_usage_time'] = (
                        self._connection_pool_stats.get('avg_usage_time', 0) * 0.9 + usage_time * 0.1
                    )
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Monitor query execution start"""
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Monitor query execution completion"""
            if hasattr(context, '_query_start_time'):
                execution_time = time.time() - context._query_start_time
                
                # Log slow queries
                if execution_time > self.config.slow_query_threshold:
                    logger.warning(f"Slow query detected ({execution_time:.2f}s): {statement[:100]}...")
                
                # Update query statistics
                with self._lock:
                    self._query_stats['total_queries'] = self._query_stats.get('total_queries', 0) + 1
                    self._query_stats['total_time'] = self._query_stats.get('total_time', 0) + execution_time
                    self._query_stats['avg_time'] = (
                        self._query_stats['total_time'] / self._query_stats['total_queries']
                    )
                    
                    if execution_time > self.config.slow_query_threshold:
                        self._query_stats['slow_queries'] = self._query_stats.get('slow_queries', 0) + 1
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {str(e)}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_session_factory(self) -> sessionmaker:
        """Get session factory for dependency injection"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.session_factory
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            with self.get_session() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1"))
                result.fetchone()
                
                # Get connection pool status
                pool_status = {
                    "size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "total_connections": self.engine.pool.size() + self.engine.pool.overflow()
                }
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pool_status": pool_status,
                    "connection_stats": self._connection_pool_stats.copy(),
                    "query_stats": self._query_stats.copy()
                }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        with self._lock:
            return {
                "connection_pool": {
                    "size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "total_connections": self.engine.pool.size() + self.engine.pool.overflow(),
                    "utilization": (self.engine.pool.checkedout() / self.engine.pool.size()) * 100
                },
                "connection_stats": self._connection_pool_stats.copy(),
                "query_stats": self._query_stats.copy(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def optimize_for_real_time(self, session: Session):
        """Optimize database session for real-time monitoring"""
        # Set session-level optimizations
        session.execute(text("SET synchronous_commit = OFF"))  # Faster writes
        session.execute(text("SET wal_writer_delay = 10ms"))   # Faster WAL writes
        session.execute(text("SET commit_delay = 0"))          # No commit delays
        
        # Enable parallel query execution for large datasets
        session.execute(text("SET max_parallel_workers_per_gather = 4"))
        session.execute(text("SET parallel_tuple_cost = 0.1"))
        
        # Optimize for monitoring queries
        session.execute(text("SET random_page_cost = 1.1"))    # SSD optimization
        session.execute(text("SET seq_page_cost = 1.0"))       # Sequential scan cost
        
    def cleanup_expired_sessions(self):
        """Clean up expired user sessions and audit records"""
        try:
            with self.get_session() as session:
                # Clean up expired sessions
                expired_time = datetime.now(timezone.utc) - timedelta(hours=24)
                
                from .models import UserSession
                expired_sessions = session.query(UserSession).filter(
                    UserSession.last_activity < expired_time,
                    UserSession.session_status == "active"
                ).update({"session_status": "expired"})
                
                logger.info(f"Cleaned up {expired_sessions} expired sessions")
                
                # Archive old audit records (older than 1 year)
                archive_time = datetime.now(timezone.utc) - timedelta(days=365)
                
                from .models import AuditTrail, AuditTrailArchive
                old_audits = session.query(AuditTrail).filter(
                    AuditTrail.timestamp < archive_time
                ).all()
                
                for audit in old_audits:
                    # Create archive record
                    archive = AuditTrailArchive(
                        original_audit_id=audit.audit_id,
                        archive_date=datetime.now(timezone.utc),
                        archive_reason="routine",
                        archived_data=audit.to_dict(),
                        retention_period_years=7,
                        storage_location="database",
                        storage_medium="database"
                    )
                    session.add(archive)
                    session.delete(audit)
                
                logger.info(f"Archived {len(old_audits)} old audit records")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Dependency injection for database sessions"""
    return db_manager.get_session()

def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager

def init_database(config: Optional[DatabaseConfig] = None):
    """Initialize database with configuration"""
    global db_manager
    if config:
        db_manager = DatabaseManager(config)
    db_manager.initialize()
    return db_manager

# Real-time monitoring specific functions
def get_real_time_session():
    """Get optimized session for real-time monitoring"""
    session = db_manager.get_session_factory()()
    db_manager.optimize_for_real_time(session)
    return session

@contextmanager
def get_monitoring_session():
    """Context manager for real-time monitoring sessions"""
    session = get_real_time_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Real-time monitoring session error: {str(e)}")
        raise
    finally:
        session.close()

# Database health monitoring
def monitor_database_health():
    """Monitor database health and performance"""
    return db_manager.health_check()

def get_database_metrics():
    """Get database performance metrics"""
    return db_manager.get_performance_metrics()

# Audit trail helpers
def create_audit_record(session: Session, event_type: str, table_name: str, 
                       record_id: str, user_id: str, action: str, 
                       old_values: Dict = None, new_values: Dict = None):
    """Create audit trail record"""
    audit = AuditTrail(
        event_type=event_type,
        event_category="data",
        event_description=f"{action} on {table_name}",
        table_name=table_name,
        record_id=record_id,
        user_id=user_id,
        user_name="system",  # Should be populated with actual user
        user_role="system",
        action=action,
        action_status="success",
        old_values=old_values,
        new_values=new_values,
        ip_address="127.0.0.1",  # Should be populated with actual IP
        user_agent="system",
        session_id="system",
        created_by=user_id,
        modified_by=user_id
    )
    session.add(audit)
    return audit

# Connection pooling monitoring
def get_connection_pool_stats():
    """Get connection pool statistics"""
    if not db_manager.engine:
        return {"error": "Database not initialized"}
    
    return {
        "size": db_manager.engine.pool.size(),
        "checked_in": db_manager.engine.pool.checkedin(),
        "checked_out": db_manager.engine.pool.checkedout(),
        "overflow": db_manager.engine.pool.overflow(),
        "total_connections": db_manager.engine.pool.size() + db_manager.engine.pool.overflow(),
        "utilization_percent": (db_manager.engine.pool.checkedout() / db_manager.engine.pool.size()) * 100
    }