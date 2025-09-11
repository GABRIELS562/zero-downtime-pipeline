"""
Database Manager Service
Handles database connections and initialization for pharmaceutical manufacturing system
FULLY SYNCHRONOUS - Fixed for production deployment
"""

import logging
import time
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations - Fully Synchronous"""
    
    def __init__(self):
        # Use synchronous SQLite
        database_url = os.getenv("DATABASE_URL", "sqlite:///app/pharma.db")
        logger.info(f"Initializing database: {database_url}")
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.initialized = False
        self.start_time = time.time()
        
        # Initialize immediately
        self.initialize_sync()
    
    def initialize_sync(self):
        """Initialize database connection synchronously"""
        try:
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.initialized = True
            logger.info("Database connection initialized successfully (sync)")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't raise - allow app to start in degraded mode
            self.initialized = False
    
    async def initialize(self):
        """Async wrapper for compatibility"""
        self.initialize_sync()
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.initialized:
            logger.warning("Database not initialized, attempting to reinitialize")
            self.initialize_sync()
            
        return self.SessionLocal()
    
    def check_health(self) -> dict:
        """Check database health synchronously"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def detailed_health_check(self) -> dict:
        """Detailed health check - Returns detailed status"""
        health_status = self.check_health()
        if health_status['status'] == 'healthy':
            return {
                "healthy": True,
                "status": "healthy", 
                "database": "connected",
                "uptime_seconds": time.time() - self.start_time
            }
        else:
            return {
                "healthy": False, 
                "status": "unhealthy", 
                "error": health_status.get('error', 'Unknown error')
            }
    
    async def close(self):
        """Close database connections"""
        self.close_sync()
            
    def close_sync(self):
        """Close database connections synchronously"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed (sync)")