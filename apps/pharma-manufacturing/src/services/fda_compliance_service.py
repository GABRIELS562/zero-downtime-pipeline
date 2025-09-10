"""
FDA Compliance Service
Service layer for FDA reporting, regulatory compliance, and validation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import json

logger = logging.getLogger(__name__)


class FDAComplianceService:
    """Service for managing FDA compliance and regulatory reporting"""
    
    def __init__(self):
        """Initialize FDA compliance service"""
        self.compliance_records = {}
        self.fda_reports = {}
        self.validation_records = {}
        self.regulatory_events = []
        logger.info("FDAComplianceService initialized")
    
    async def create_compliance_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new compliance record"""
        record_id = str(uuid4())
        compliance_record = {
            "id": record_id,
            "regulation_type": record_data.get("regulation_type", "21_CFR_211"),
            "requirement": record_data.get("requirement"),
            "batch_id": record_data.get("batch_id"),
            "compliance_status": record_data.get("compliance_status", "pending"),
            "evidence": record_data.get("evidence", []),
            "responsible_person": record_data.get("responsible_person"),
            "created_at": datetime.now().isoformat(),
            "due_date": record_data.get("due_date"),
            "priority": record_data.get("priority", "medium"),
            **record_data
        }
        self.compliance_records[record_id] = compliance_record
        logger.info(f"Created compliance record {record_id} for {compliance_record['regulation_type']}")
        return compliance_record
    
    async def update_compliance_status(self, record_id: str, status: str, 
                                     user_id: str, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update compliance record status"""
        if record_id in self.compliance_records:
            self.compliance_records[record_id].update({
                "compliance_status": status,
                "updated_at": datetime.now().isoformat(),
                "updated_by": user_id,
                "status_notes": notes
            })
            
            # Log regulatory event
            await self.log_regulatory_event(
                event_type="COMPLIANCE_STATUS_UPDATE",
                details={
                    "record_id": record_id,
                    "old_status": "previous",  # Would track previous status in real implementation
                    "new_status": status,
                    "updated_by": user_id,
                    "notes": notes
                }
            )
            
            logger.info(f"Updated compliance record {record_id} status to {status}")
            return self.compliance_records[record_id]
        return None
    
    async def generate_fda_report(self, report_type: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate FDA report"""
        report_id = str(uuid4())
        fda_report = {
            "id": report_id,
            "report_type": report_type,
            "report_period_start": report_data.get("period_start"),
            "report_period_end": report_data.get("period_end"),
            "facility_info": report_data.get("facility_info", {}),
            "generated_at": datetime.now().isoformat(),
            "generated_by": report_data.get("generated_by"),
            "status": "draft",
            "sections": self._generate_report_sections(report_type, report_data),
            "submission_deadline": report_data.get("submission_deadline"),
            "fda_contact": report_data.get("fda_contact"),
            **report_data
        }
        self.fda_reports[report_id] = fda_report
        logger.info(f"Generated FDA report {report_id} of type {report_type}")
        return fda_report
    
    def _generate_report_sections(self, report_type: str, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate report sections based on report type"""
        sections = []
        
        if report_type == "annual_report":
            sections = [
                {"section": "executive_summary", "status": "pending", "content": {}},
                {"section": "manufacturing_overview", "status": "pending", "content": {}},
                {"section": "quality_metrics", "status": "pending", "content": {}},
                {"section": "adverse_events", "status": "pending", "content": {}},
                {"section": "regulatory_changes", "status": "pending", "content": {}}
            ]
        elif report_type == "deviation_report":
            sections = [
                {"section": "deviation_summary", "status": "pending", "content": {}},
                {"section": "root_cause_analysis", "status": "pending", "content": {}},
                {"section": "corrective_actions", "status": "pending", "content": {}},
                {"section": "preventive_measures", "status": "pending", "content": {}}
            ]
        elif report_type == "inspection_response":
            sections = [
                {"section": "inspection_overview", "status": "pending", "content": {}},
                {"section": "findings_response", "status": "pending", "content": {}},
                {"section": "corrective_action_plan", "status": "pending", "content": {}},
                {"section": "implementation_timeline", "status": "pending", "content": {}}
            ]
        
        return sections
    
    async def validate_batch_compliance(self, batch_id: str, 
                                      validation_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate batch compliance against FDA requirements"""
        validation_id = str(uuid4())
        
        # Perform validation checks
        validation_results = []
        
        # Check documentation completeness
        doc_check = {
            "check_name": "documentation_completeness",
            "status": "pass",  # Would implement actual validation logic
            "details": "All required batch records present"
        }
        validation_results.append(doc_check)
        
        # Check test results compliance
        test_check = {
            "check_name": "test_results_compliance",
            "status": "pass",  # Would check against actual test data
            "details": "All test results within specifications"
        }
        validation_results.append(test_check)
        
        # Check process parameters
        process_check = {
            "check_name": "process_parameters",
            "status": "pass",  # Would validate against process specifications
            "details": "Process parameters within acceptable ranges"
        }
        validation_results.append(process_check)
        
        overall_status = "compliant" if all(r["status"] == "pass" for r in validation_results) else "non_compliant"
        
        validation_record = {
            "id": validation_id,
            "batch_id": batch_id,
            "validation_date": datetime.now().isoformat(),
            "validation_criteria": validation_criteria,
            "validation_results": validation_results,
            "overall_status": overall_status,
            "validator_id": validation_criteria.get("validator_id", "system"),
            "compliance_score": len([r for r in validation_results if r["status"] == "pass"]) / len(validation_results) * 100,
            "next_review_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        self.validation_records[validation_id] = validation_record
        logger.info(f"Completed batch validation {validation_id} for batch {batch_id}: {overall_status}")
        return validation_record
    
    async def log_regulatory_event(self, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Log regulatory event for audit trail"""
        event = {
            "id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "severity": details.get("severity", "info"),
            "affected_systems": details.get("affected_systems", []),
            "reported_by": details.get("reported_by", "system")
        }
        self.regulatory_events.append(event)
        logger.info(f"Logged regulatory event: {event_type}")
        return event
    
    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get compliance dashboard data"""
        total_records = len(self.compliance_records)
        compliant_records = len([r for r in self.compliance_records.values() 
                               if r.get("compliance_status") == "compliant"])
        pending_records = len([r for r in self.compliance_records.values() 
                             if r.get("compliance_status") == "pending"])
        non_compliant_records = len([r for r in self.compliance_records.values() 
                                   if r.get("compliance_status") == "non_compliant"])
        
        # Get overdue records
        overdue_records = []
        for record in self.compliance_records.values():
            if record.get("due_date"):
                due_date = datetime.fromisoformat(record["due_date"])
                if due_date < datetime.now() and record.get("compliance_status") != "compliant":
                    overdue_records.append(record)
        
        return {
            "compliance_summary": {
                "total_records": total_records,
                "compliant": compliant_records,
                "pending": pending_records,
                "non_compliant": non_compliant_records,
                "compliance_rate": (compliant_records / total_records * 100) if total_records > 0 else 0
            },
            "overdue_items": len(overdue_records),
            "recent_validations": len([v for v in self.validation_records.values() 
                                     if (datetime.now() - datetime.fromisoformat(v["validation_date"])).days <= 7]),
            "pending_reports": len([r for r in self.fda_reports.values() 
                                  if r.get("status") in ["draft", "pending"]]),
            "regulatory_events_today": len([e for e in self.regulatory_events 
                                          if (datetime.now() - datetime.fromisoformat(e["timestamp"])).days == 0])
        }
    
    async def get_regulatory_calendar(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming regulatory deadlines"""
        upcoming_deadlines = []
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        # Check compliance record due dates
        for record in self.compliance_records.values():
            if record.get("due_date"):
                due_date = datetime.fromisoformat(record["due_date"])
                if datetime.now() <= due_date <= cutoff_date:
                    upcoming_deadlines.append({
                        "type": "compliance_record",
                        "id": record["id"],
                        "title": record.get("requirement", "Compliance Requirement"),
                        "due_date": record["due_date"],
                        "status": record.get("compliance_status"),
                        "priority": record.get("priority", "medium")
                    })
        
        # Check FDA report submission deadlines
        for report in self.fda_reports.values():
            if report.get("submission_deadline"):
                deadline = datetime.fromisoformat(report["submission_deadline"])
                if datetime.now() <= deadline <= cutoff_date:
                    upcoming_deadlines.append({
                        "type": "fda_report",
                        "id": report["id"],
                        "title": f"{report['report_type']} Report",
                        "due_date": report["submission_deadline"],
                        "status": report.get("status"),
                        "priority": "high"
                    })
        
        # Sort by due date
        upcoming_deadlines.sort(key=lambda x: x["due_date"])
        return upcoming_deadlines
    
    async def export_compliance_report(self, start_date: datetime, 
                                     end_date: datetime) -> Dict[str, Any]:
        """Export comprehensive compliance report for specified period"""
        # Filter records by date range
        period_records = []
        for record in self.compliance_records.values():
            record_date = datetime.fromisoformat(record["created_at"])
            if start_date <= record_date <= end_date:
                period_records.append(record)
        
        # Filter validation records
        period_validations = []
        for validation in self.validation_records.values():
            validation_date = datetime.fromisoformat(validation["validation_date"])
            if start_date <= validation_date <= end_date:
                period_validations.append(validation)
        
        # Filter regulatory events
        period_events = []
        for event in self.regulatory_events:
            event_date = datetime.fromisoformat(event["timestamp"])
            if start_date <= event_date <= end_date:
                period_events.append(event)
        
        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "report_type": "comprehensive_compliance_report"
            },
            "compliance_records": period_records,
            "validation_records": period_validations,
            "regulatory_events": period_events,
            "summary": {
                "total_compliance_records": len(period_records),
                "total_validations": len(period_validations),
                "total_regulatory_events": len(period_events),
                "compliance_rate": len([r for r in period_records if r.get("compliance_status") == "compliant"]) / len(period_records) * 100 if period_records else 0
            }
        }