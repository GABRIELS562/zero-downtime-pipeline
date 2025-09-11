"""
Database Manager Service
Handles database connections and initialization for pharmaceutical manufacturing system
"""

import logging
import sqlite3
import time
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.engine: Optional[create_engine] = None
        self.session_maker: Optional[sessionmaker] = None
        self.initialized = False
        self.start_time = time.time()
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            # Use environment variables or defaults for database connection
            database_url = os.getenv(
                "DATABASE_URL", 
                "sqlite:///./pharma_manufacturing.db"
            )
            
            logger.info(f"Initializing database connection to: {database_url.split('@')[-1] if '@' in database_url else database_url}")
            
            self.engine = create_engine(
                database_url,
                echo=os.getenv("DEBUG", "false").lower() == "true"
            )
            
            self.session_maker = sessionmaker(
                bind=self.engine,
                class_=Session,
                expire_on_commit=False
            )
            
            # Test connection
            with self.engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            
            self.initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't raise - allow app to start in degraded mode
            self.initialized = False
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.initialized:
            raise RuntimeError("Database not initialized")
        
        return self.session_maker()
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    async def check_health(self) -> bool:
        """Check database health - Returns boolean for readiness probe"""
        if not self.initialized:
            return False
        
        try:
            with self.engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def detailed_health_check(self) -> dict:
        """Detailed health check - Returns detailed status"""
        if not self.initialized:
            return {"healthy": False, "status": "unhealthy", "error": "Not initialized"}
        
        try:
            with self.engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            return {
                "healthy": True,
                "status": "healthy", 
                "database": "connected",
                "uptime_seconds": time.time() - self.start_time
            }
        except Exception as e:
            return {"healthy": False, "status": "unhealthy", "error": str(e)}