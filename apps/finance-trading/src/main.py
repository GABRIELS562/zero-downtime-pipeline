#!/usr/bin/env python3
"""
Finance Trading Application - Main Entry Point
Zero-Downtime Pipeline Portfolio Project

This application demonstrates a sophisticated trading system with:
- Real-time market data processing
- Order management and execution
- Risk management and compliance
- Health checks and metrics for DevOps pipeline
- SOX compliance and audit trails
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from prometheus_client import make_asgi_app
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.health import health_router
from src.api.trading import trading_router
from src.api.metrics import metrics_router
from middleware.latency_monitor import LatencyMiddleware
from middleware.market_data_validator import MarketDataMiddleware
from middleware.compliance_logger import ComplianceMiddleware
from services.market_data_service import MarketDataService
from services.order_processor import OrderProcessor
from services.risk_manager import RiskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/trading-app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global services
market_data_service = None
order_processor = None
risk_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global market_data_service, order_processor, risk_manager
    
    logger.info("Starting Finance Trading Application...")
    
    # Initialize services
    market_data_service = MarketDataService()
    order_processor = OrderProcessor()
    risk_manager = RiskManager()
    
    # Start background tasks
    await market_data_service.start()
    await order_processor.start()
    await risk_manager.start()
    
    logger.info("Finance Trading Application started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Finance Trading Application...")
    await market_data_service.stop()
    await order_processor.stop()
    await risk_manager.stop()
    logger.info("Finance Trading Application stopped")

# Create FastAPI application
app = FastAPI(
    title="Finance Trading System",
    description="High-performance trading system with forensic DevOps integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LatencyMiddleware)
app.add_middleware(MarketDataMiddleware)
app.add_middleware(ComplianceMiddleware)

# Include routers
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(trading_router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["metrics"])

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Finance Trading System",
        "version": "1.0.0",
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "build_id": os.getenv("BUILD_ID", "local"),
        "git_commit": os.getenv("GIT_COMMIT", "unknown")
    }

@app.get("/info")
async def info():
    """System information endpoint"""
    return {
        "application": {
            "name": "Finance Trading System",
            "version": "1.0.0",
            "description": "High-performance trading system for zero-downtime deployments"
        },
        "build": {
            "id": os.getenv("BUILD_ID", "local"),
            "timestamp": os.getenv("BUILD_TIMESTAMP", "unknown"),
            "git_commit": os.getenv("GIT_COMMIT", "unknown")
        },
        "environment": {
            "name": os.getenv("ENVIRONMENT", "development"),
            "region": os.getenv("AWS_REGION", "us-east-1")
        },
        "compliance": {
            "sox_enabled": True,
            "audit_logging": True,
            "encryption": True
        }
    }

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    workers = int(os.getenv("WORKERS", "1"))
    
    logger.info(f"Starting Finance Trading Application on {host}:{port}")
    
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
        reload=False
    )