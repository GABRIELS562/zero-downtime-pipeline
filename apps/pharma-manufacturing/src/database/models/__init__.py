"""
Pharmaceutical Manufacturing Database Models
FDA 21 CFR Part 11 compliant database models for pharmaceutical manufacturing operations
"""

from .base import (
    Base,
    BaseModel,
    TimestampMixin,
    StatusMixin,
    ApprovalMixin,
    TestResultMixin,
    BatchTrackingMixin,
    CalibrationMixin,
    DatabaseConstraints,
    DatabaseUtils,
    DatabaseIndexes
)

from .batch_models import (
    Product,
    Batch,
    BatchGenealogy,
    BatchStage,
    BatchStageEnvironment,
    BatchMaterial,
    BatchTestResult,
    BatchDeviation,
    Lot,
    BatchDocument
)

from .equipment_models import (
    EquipmentType,
    Equipment,
    EquipmentCalibration,
    EquipmentMaintenance,
    EquipmentValidation,
    SensorType,
    Sensor,
    SensorData,
    SensorCalibration,
    EquipmentUsageLog,
    EquipmentAlarm
)

from .material_models import (
    MaterialType,
    Material,
    Supplier,
    PurchaseOrder,
    MaterialReceipt,
    InventoryLot,
    InventoryTransaction,
    MaterialTestResult,
    MaterialTestDetail,
    MaterialReservation,
    MaterialDisposal
)

from .quality_control_models import (
    TestType,
    TestPlan,
    Laboratory,
    QualityTestResult,
    TestParameter,
    StabilityTestData,
    QualityInvestigation,
    QualityMetrics,
    QualityAlert,
    QualityTrend
)

from .environmental_monitoring_models import (
    MonitoringLocation,
    EnvironmentalParameter,
    EnvironmentalData,
    EnvironmentalExcursion,
    EnvironmentalCalibration,
    EnvironmentalReport,
    EnvironmentalAlert,
    EnvironmentalTrend
)

from .user_models import (
    UserRole,
    User,
    ElectronicSignature,
    UserSession,
    UserTraining,
    UserQualification,
    AccessLog
)

from .audit_models import (
    AuditTrail,
    SecurityEvent,
    ChangeLog,
    SystemEvent,
    BusinessEvent,
    AuditReport,
    AuditTrailArchive
)

from .deviation_models import (
    DeviationType,
    Deviation,
    DeviationInvestigation,
    CAPA,
    CAPAAction,
    CAPAMonitoring,
    DeviationTrend
)

# All model classes for easy import and registration
__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "TimestampMixin",
    "StatusMixin",
    "ApprovalMixin",
    "TestResultMixin",
    "BatchTrackingMixin",
    "CalibrationMixin",
    "DatabaseConstraints",
    "DatabaseUtils",
    "DatabaseIndexes",
    
    # Batch and lot tracking
    "Product",
    "Batch",
    "BatchGenealogy",
    "BatchStage",
    "BatchStageEnvironment",
    "BatchMaterial",
    "BatchTestResult",
    "BatchDeviation",
    "Lot",
    "BatchDocument",
    
    # Equipment and sensors
    "EquipmentType",
    "Equipment",
    "EquipmentCalibration",
    "EquipmentMaintenance",
    "EquipmentValidation",
    "SensorType",
    "Sensor",
    "SensorData",
    "SensorCalibration",
    "EquipmentUsageLog",
    "EquipmentAlarm",
    
    # Materials and inventory
    "MaterialType",
    "Material",
    "Supplier",
    "PurchaseOrder",
    "MaterialReceipt",
    "InventoryLot",
    "InventoryTransaction",
    "MaterialTestResult",
    "MaterialTestDetail",
    "MaterialReservation",
    "MaterialDisposal",
    
    # Quality control
    "TestType",
    "TestPlan",
    "Laboratory",
    "QualityTestResult",
    "TestParameter",
    "StabilityTestData",
    "QualityInvestigation",
    "QualityMetrics",
    "QualityAlert",
    "QualityTrend",
    
    # Environmental monitoring
    "MonitoringLocation",
    "EnvironmentalParameter",
    "EnvironmentalData",
    "EnvironmentalExcursion",
    "EnvironmentalCalibration",
    "EnvironmentalReport",
    "EnvironmentalAlert",
    "EnvironmentalTrend",
    
    # User management
    "UserRole",
    "User",
    "ElectronicSignature",
    "UserSession",
    "UserTraining",
    "UserQualification",
    "AccessLog",
    
    # Audit trail
    "AuditTrail",
    "SecurityEvent",
    "ChangeLog",
    "SystemEvent",
    "BusinessEvent",
    "AuditReport",
    "AuditTrailArchive",
    
    # Deviation and CAPA
    "DeviationType",
    "Deviation",
    "DeviationInvestigation",
    "CAPA",
    "CAPAAction",
    "CAPAMonitoring",
    "DeviationTrend",
]

# Model registry for database operations
MODEL_REGISTRY = {
    # Batch and lot tracking
    "products": Product,
    "batches": Batch,
    "batch_genealogy": BatchGenealogy,
    "batch_stages": BatchStage,
    "batch_stage_environment": BatchStageEnvironment,
    "batch_materials": BatchMaterial,
    "batch_test_results": BatchTestResult,
    "batch_deviations": BatchDeviation,
    "lots": Lot,
    "batch_documents": BatchDocument,
    
    # Equipment and sensors
    "equipment_types": EquipmentType,
    "equipment": Equipment,
    "equipment_calibration": EquipmentCalibration,
    "equipment_maintenance": EquipmentMaintenance,
    "equipment_validation": EquipmentValidation,
    "sensor_types": SensorType,
    "sensors": Sensor,
    "sensor_data": SensorData,
    "sensor_calibration": SensorCalibration,
    "equipment_usage_log": EquipmentUsageLog,
    "equipment_alarms": EquipmentAlarm,
    
    # Materials and inventory
    "material_types": MaterialType,
    "materials": Material,
    "suppliers": Supplier,
    "purchase_orders": PurchaseOrder,
    "material_receipts": MaterialReceipt,
    "inventory_lots": InventoryLot,
    "inventory_transactions": InventoryTransaction,
    "material_test_results": MaterialTestResult,
    "material_test_details": MaterialTestDetail,
    "material_reservations": MaterialReservation,
    "material_disposals": MaterialDisposal,
    
    # Quality control
    "test_types": TestType,
    "test_plans": TestPlan,
    "laboratories": Laboratory,
    "quality_test_results": QualityTestResult,
    "test_parameters": TestParameter,
    "stability_test_data": StabilityTestData,
    "quality_investigations": QualityInvestigation,
    "quality_metrics": QualityMetrics,
    "quality_alerts": QualityAlert,
    "quality_trends": QualityTrend,
    
    # Environmental monitoring
    "monitoring_locations": MonitoringLocation,
    "environmental_parameters": EnvironmentalParameter,
    "environmental_data": EnvironmentalData,
    "environmental_excursions": EnvironmentalExcursion,
    "environmental_calibration": EnvironmentalCalibration,
    "environmental_reports": EnvironmentalReport,
    "environmental_alerts": EnvironmentalAlert,
    "environmental_trends": EnvironmentalTrend,
    
    # User management
    "user_roles": UserRole,
    "users": User,
    "electronic_signatures": ElectronicSignature,
    "user_sessions": UserSession,
    "user_training": UserTraining,
    "user_qualifications": UserQualification,
    "access_logs": AccessLog,
    
    # Audit trail
    "audit_trail": AuditTrail,
    "security_events": SecurityEvent,
    "change_logs": ChangeLog,
    "system_events": SystemEvent,
    "business_events": BusinessEvent,
    "audit_reports": AuditReport,
    "audit_trail_archive": AuditTrailArchive,
    
    # Deviation and CAPA
    "deviation_types": DeviationType,
    "deviations": Deviation,
    "deviation_investigations": DeviationInvestigation,
    "capa": CAPA,
    "capa_actions": CAPAAction,
    "capa_monitoring": CAPAMonitoring,
    "deviation_trends": DeviationTrend,
}

def get_model_by_table_name(table_name: str):
    """Get model class by table name"""
    return MODEL_REGISTRY.get(table_name)

def get_all_models():
    """Get all model classes"""
    return list(MODEL_REGISTRY.values())

def get_table_names():
    """Get all table names"""
    return list(MODEL_REGISTRY.keys())