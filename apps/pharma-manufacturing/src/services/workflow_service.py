"""
Manufacturing Workflow Service
Manages pharmaceutical manufacturing workflows and processes
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStage(Enum):
    """Manufacturing workflow stages"""
    MATERIAL_PREP = "material_preparation"
    MIXING = "mixing"
    GRANULATION = "granulation"
    DRYING = "drying"
    COMPRESSION = "compression"
    COATING = "coating"
    QUALITY_CHECK = "quality_check"
    PACKAGING = "packaging"
    FINAL_INSPECTION = "final_inspection"

@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    stage: WorkflowStage
    name: str
    description: str
    duration_minutes: int
    equipment_required: List[str]
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ManufacturingWorkflow:
    """Complete manufacturing workflow"""
    workflow_id: str
    batch_number: str
    product_name: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = "system"

class WorkflowService:
    """Service for managing manufacturing workflows"""
    
    def __init__(self):
        self.workflows: Dict[str, ManufacturingWorkflow] = {}
        self._initialize_sample_workflows()
        logger.info("Workflow Service initialized")
    
    def _initialize_sample_workflows(self):
        """Initialize sample workflows"""
        # Create a sample tablet manufacturing workflow
        workflow_id = str(uuid4())
        steps = [
            WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage.MATERIAL_PREP,
                name="Material Preparation",
                description="Weigh and prepare raw materials",
                duration_minutes=60,
                equipment_required=["Scale", "Container"],
                status=WorkflowStatus.COMPLETED
            ),
            WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage.MIXING,
                name="Dry Mixing",
                description="Mix active ingredients with excipients",
                duration_minutes=45,
                equipment_required=["MIXER-001"],
                status=WorkflowStatus.IN_PROGRESS
            ),
            WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage.GRANULATION,
                name="Wet Granulation",
                description="Form granules using binding solution",
                duration_minutes=90,
                equipment_required=["Granulator"],
                status=WorkflowStatus.PENDING
            ),
            WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage.COMPRESSION,
                name="Tablet Compression",
                description="Compress granules into tablets",
                duration_minutes=120,
                equipment_required=["TABLET-PRESS-001"],
                status=WorkflowStatus.PENDING
            ),
            WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage.COATING,
                name="Film Coating",
                description="Apply protective coating to tablets",
                duration_minutes=180,
                equipment_required=["COATING-PAN-001"],
                status=WorkflowStatus.PENDING
            ),
            WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage.QUALITY_CHECK,
                name="Quality Control",
                description="Test samples for quality compliance",
                duration_minutes=60,
                equipment_required=["Lab Equipment"],
                status=WorkflowStatus.PENDING
            ),
            WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage.PACKAGING,
                name="Primary Packaging",
                description="Package tablets in bottles/blisters",
                duration_minutes=90,
                equipment_required=["PACKAGING-001"],
                status=WorkflowStatus.PENDING
            )
        ]
        
        workflow = ManufacturingWorkflow(
            workflow_id=workflow_id,
            batch_number="BATCH-2024-001",
            product_name="Acetaminophen 500mg Tablets",
            status=WorkflowStatus.IN_PROGRESS,
            steps=steps,
            created_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        
        self.workflows[workflow_id] = workflow
    
    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows"""
        return [self._workflow_to_dict(w) for w in self.workflows.values()]
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get specific workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        return self._workflow_to_dict(workflow)
    
    async def create_workflow(self, batch_number: str, product_name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create new manufacturing workflow"""
        workflow_id = str(uuid4())
        
        workflow_steps = []
        for step_data in steps:
            workflow_steps.append(WorkflowStep(
                step_id=str(uuid4()),
                stage=WorkflowStage(step_data.get('stage', WorkflowStage.MATERIAL_PREP.value)),
                name=step_data.get('name', 'Unnamed Step'),
                description=step_data.get('description', ''),
                duration_minutes=step_data.get('duration_minutes', 60),
                equipment_required=step_data.get('equipment_required', []),
                status=WorkflowStatus.PENDING
            ))
        
        workflow = ManufacturingWorkflow(
            workflow_id=workflow_id,
            batch_number=batch_number,
            product_name=product_name,
            status=WorkflowStatus.DRAFT,
            steps=workflow_steps,
            created_at=datetime.now(timezone.utc)
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow {workflow_id} for batch {batch_number}")
        
        return self._workflow_to_dict(workflow)
    
    async def start_workflow(self, workflow_id: str) -> bool:
        """Start a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        workflow.status = WorkflowStatus.IN_PROGRESS
        workflow.started_at = datetime.now(timezone.utc)
        
        # Start first step
        if workflow.steps:
            workflow.steps[0].status = WorkflowStatus.IN_PROGRESS
            workflow.steps[0].started_at = datetime.now(timezone.utc)
        
        logger.info(f"Started workflow {workflow_id}")
        return True
    
    async def advance_workflow(self, workflow_id: str) -> bool:
        """Advance workflow to next step"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        # Find current step
        current_step = None
        current_index = -1
        for i, step in enumerate(workflow.steps):
            if step.status == WorkflowStatus.IN_PROGRESS:
                current_step = step
                current_index = i
                break
        
        if current_step:
            # Complete current step
            current_step.status = WorkflowStatus.COMPLETED
            current_step.completed_at = datetime.now(timezone.utc)
            
            # Start next step if available
            if current_index + 1 < len(workflow.steps):
                next_step = workflow.steps[current_index + 1]
                next_step.status = WorkflowStatus.IN_PROGRESS
                next_step.started_at = datetime.now(timezone.utc)
            else:
                # Workflow completed
                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.now(timezone.utc)
        
        logger.info(f"Advanced workflow {workflow_id}")
        return True
    
    async def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        active = [w for w in self.workflows.values() if w.status == WorkflowStatus.IN_PROGRESS]
        return [self._workflow_to_dict(w) for w in active]
    
    def _workflow_to_dict(self, workflow: ManufacturingWorkflow) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "workflow_id": workflow.workflow_id,
            "batch_number": workflow.batch_number,
            "product_name": workflow.product_name,
            "status": workflow.status.value,
            "steps": [
                {
                    "step_id": step.step_id,
                    "stage": step.stage.value,
                    "name": step.name,
                    "description": step.description,
                    "duration_minutes": step.duration_minutes,
                    "equipment_required": step.equipment_required,
                    "status": step.status.value,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None
                }
                for step in workflow.steps
            ],
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "created_by": workflow.created_by,
            "progress_percentage": self._calculate_progress(workflow)
        }
    
    def _calculate_progress(self, workflow: ManufacturingWorkflow) -> float:
        """Calculate workflow progress percentage"""
        if not workflow.steps:
            return 0.0
        
        completed = sum(1 for step in workflow.steps if step.status == WorkflowStatus.COMPLETED)
        return (completed / len(workflow.steps)) * 100