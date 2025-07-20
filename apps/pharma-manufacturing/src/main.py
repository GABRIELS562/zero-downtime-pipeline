"""
Pharmaceutical Manufacturing Monitoring System
FastAPI application for GMP-compliant manufacturing operations
"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from datetime import datetime

# Import API routers
from api.batch_tracking import router as batch_router
from api.equipment_monitoring import router as equipment_router
from api.inventory_management import router as inventory_router
from api.quality_control import router as quality_router
from api.manufacturing_workflow import router as workflow_router
from api.environmental_monitoring import router as environmental_router
from api.health import router as health_router
from api.alerts import router as alerts_router

# Import middleware
from middleware.gmp_compliance_logger import GMPComplianceMiddleware
from middleware.fda_validation import FDAValidationMiddleware
from middleware.audit_trail import AuditTrailMiddleware

# Import services
from services.database_manager import DatabaseManager
from services.alert_manager import AlertManager
from services.equipment_simulator import EquipmentSimulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/pharma-manufacturing.log')
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🏭 Starting Pharmaceutical Manufacturing Monitoring System")
    
    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Initialize alert manager
    alert_manager = AlertManager()
    await alert_manager.initialize()
    
    # Start equipment simulator for demo purposes
    equipment_simulator = EquipmentSimulator()
    await equipment_simulator.start()
    
    logger.info("✅ All systems initialized successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down Pharmaceutical Manufacturing System")
    await equipment_simulator.stop()
    await alert_manager.shutdown()
    await db_manager.close()

# Create FastAPI application
app = FastAPI(
    title="Pharmaceutical Manufacturing Monitoring System",
    description="GMP-compliant manufacturing monitoring with FDA validation capabilities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware for GMP compliance
app.add_middleware(GMPComplianceMiddleware)
app.add_middleware(FDAValidationMiddleware)
app.add_middleware(AuditTrailMiddleware)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with audit logging"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with audit logging"""
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
    )

# Include API routers
app.include_router(
    health_router,
    prefix="/api/v1/health",
    tags=["Health & Status"]
)

app.include_router(
    batch_router,
    prefix="/api/v1/batches",
    tags=["Batch Tracking"]
)

app.include_router(
    equipment_router,
    prefix="/api/v1/equipment",
    tags=["Equipment Monitoring"]
)

app.include_router(
    inventory_router,
    prefix="/api/v1/inventory",
    tags=["Inventory Management"]
)

app.include_router(
    quality_router,
    prefix="/api/v1/quality",
    tags=["Quality Control"]
)

app.include_router(
    workflow_router,
    prefix="/api/v1/workflow",
    tags=["Manufacturing Workflow"]
)

app.include_router(
    environmental_router,
    prefix="/api/v1/environmental",
    tags=["Environmental Monitoring"]
)

app.include_router(
    alerts_router,
    prefix="/api/v1/alerts",
    tags=["Alert Management"]
)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system information"""
    return {
        "system": "Pharmaceutical Manufacturing Monitoring System",
        "version": "1.0.0",
        "status": "operational",
        "compliance": "GMP/FDA",
        "timestamp": datetime.utcnow().isoformat(),
        "documentation": "/api/docs"
    }

@app.get("/api/v1/system/info", tags=["System Information"])
async def system_info():
    """Get comprehensive system information"""
    return {
        "application": {
            "name": "Pharmaceutical Manufacturing Monitoring System",
            "version": "1.0.0",
            "environment": "production"
        },
        "compliance": {
            "gmp_enabled": True,
            "fda_validation": True,
            "audit_trail": True,
            "data_integrity": True
        },
        "monitoring": {
            "equipment_sensors": True,
            "environmental_conditions": True,
            "batch_tracking": True,
            "quality_control": True
        },
        "capabilities": {
            "real_time_alerts": True,
            "zero_downtime_health": True,
            "regulatory_reporting": True,
            "equipment_integration": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )