"""
Database Manager Service
Handles database connections and initialization for pharmaceutical manufacturing system
"""

import logging
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.engine: Optional[create_async_engine] = None
        self.session_maker: Optional[sessionmaker] = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            # Use environment variables or defaults for database connection
            database_url = os.getenv(
                "DATABASE_URL", 
                "sqlite+aiosqlite:///./pharma_manufacturing.db"
            )
            
            logger.info(f"Initializing database connection to: {database_url.split('@')[-1] if '@' in database_url else database_url}")
            
            self.engine = create_async_engine(
                database_url,
                echo=os.getenv("DEBUG", "false").lower() == "true"
            )
            
            self.session_maker = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            self.initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't raise - allow app to start in degraded mode
            self.initialized = False
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.initialized:
            raise RuntimeError("Database not initialized")
        
        return self.session_maker()
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    async def health_check(self) -> dict:
        """Check database health"""
        if not self.initialized:
            return {"status": "unhealthy", "error": "Not initialized"}
        
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}