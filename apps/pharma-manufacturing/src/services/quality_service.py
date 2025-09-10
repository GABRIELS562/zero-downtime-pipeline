"""
Quality Service
Service layer for quality control checks, test results, and batch approval
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class QualityService:
    """Service for managing pharmaceutical quality control operations"""
    
    def __init__(self):
        """Initialize quality service"""
        self.quality_checks = {}
        self.test_results = {}
        self.batch_approvals = {}
        logger.info("QualityService initialized")
    
    async def create_quality_check(self, check_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new quality control check"""
        check_id = str(uuid4())
        quality_check = {
            "id": check_id,
            "batch_id": check_data.get("batch_id"),
            "check_type": check_data.get("check_type", "general"),
            "parameters": check_data.get("parameters", []),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "created_by": check_data.get("created_by", "system"),
            "priority": check_data.get("priority", "normal"),
            **check_data
        }
        self.quality_checks[check_id] = quality_check
        logger.info(f"Created quality check {check_id} for batch {quality_check['batch_id']}")
        return quality_check
    
    async def get_quality_check(self, check_id: str) -> Optional[Dict[str, Any]]:
        """Get quality check by ID"""
        return self.quality_checks.get(check_id)
    
    async def update_quality_check_status(self, check_id: str, status: str, 
                                         user_id: str, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update quality check status"""
        if check_id in self.quality_checks:
            self.quality_checks[check_id].update({
                "status": status,
                "updated_at": datetime.now().isoformat(),
                "updated_by": user_id,
                "notes": notes
            })
            logger.info(f"Updated quality check {check_id} status to {status}")
            return self.quality_checks[check_id]
        return None
    
    async def record_test_result(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record test results for quality control"""
        result_id = str(uuid4())
        test_result = {
            "id": result_id,
            "batch_id": test_data.get("batch_id"),
            "test_type": test_data.get("test_type"),
            "parameter": test_data.get("parameter"),
            "measured_value": test_data.get("measured_value"),
            "expected_range": test_data.get("expected_range"),
            "unit": test_data.get("unit"),
            "pass_fail": test_data.get("pass_fail", "pending"),
            "test_method": test_data.get("test_method"),
            "equipment_id": test_data.get("equipment_id"),
            "operator_id": test_data.get("operator_id"),
            "timestamp": datetime.now().isoformat(),
            "notes": test_data.get("notes"),
            **test_data
        }
        self.test_results[result_id] = test_result
        logger.info(f"Recorded test result {result_id} for batch {test_result['batch_id']}")
        return test_result
    
    async def get_test_results_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        """Get all test results for a specific batch"""
        return [result for result in self.test_results.values() 
                if result.get("batch_id") == batch_id]
    
    async def get_failed_tests(self, batch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get failed test results, optionally filtered by batch"""
        failed_tests = [result for result in self.test_results.values() 
                       if result.get("pass_fail") == "fail"]
        
        if batch_id:
            failed_tests = [test for test in failed_tests 
                          if test.get("batch_id") == batch_id]
        
        return failed_tests
    
    async def approve_batch(self, batch_id: str, approver_id: str, 
                           approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve batch for release after quality checks"""
        approval_id = str(uuid4())
        
        # Check if all required tests are passed
        batch_tests = await self.get_test_results_by_batch(batch_id)
        failed_tests = [test for test in batch_tests if test.get("pass_fail") == "fail"]
        
        approval_status = "approved" if not failed_tests else "rejected"
        
        batch_approval = {
            "id": approval_id,
            "batch_id": batch_id,
            "status": approval_status,
            "approver_id": approver_id,
            "approval_date": datetime.now().isoformat(),
            "comments": approval_data.get("comments", ""),
            "failed_tests_count": len(failed_tests),
            "total_tests_count": len(batch_tests),
            "approval_criteria_met": not failed_tests,
            "expiry_date": approval_data.get("expiry_date"),
            "storage_conditions": approval_data.get("storage_conditions"),
            **approval_data
        }
        
        self.batch_approvals[approval_id] = batch_approval
        logger.info(f"Batch {batch_id} {approval_status} by {approver_id}")
        return batch_approval
    
    async def get_batch_approval_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get approval status for a batch"""
        for approval in self.batch_approvals.values():
            if approval.get("batch_id") == batch_id:
                return approval
        return None
    
    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get batches pending quality approval"""
        # Find batches with completed tests but no approval
        approved_batches = {approval["batch_id"] for approval in self.batch_approvals.values()}
        
        batches_with_tests = {}
        for result in self.test_results.values():
            batch_id = result.get("batch_id")
            if batch_id not in batches_with_tests:
                batches_with_tests[batch_id] = []
            batches_with_tests[batch_id].append(result)
        
        pending_batches = []
        for batch_id, tests in batches_with_tests.items():
            if batch_id not in approved_batches:
                # Check if all tests are completed
                pending_tests = [test for test in tests if test.get("pass_fail") == "pending"]
                if not pending_tests:  # All tests completed
                    pending_batches.append({
                        "batch_id": batch_id,
                        "total_tests": len(tests),
                        "failed_tests": len([t for t in tests if t.get("pass_fail") == "fail"]),
                        "last_test_date": max(test["timestamp"] for test in tests)
                    })
        
        return pending_batches
    
    async def get_quality_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get quality metrics for reporting"""
        # Filter results by date range
        period_results = []
        for result in self.test_results.values():
            result_date = datetime.fromisoformat(result["timestamp"])
            if start_date <= result_date <= end_date:
                period_results.append(result)
        
        total_tests = len(period_results)
        passed_tests = len([r for r in period_results if r.get("pass_fail") == "pass"])
        failed_tests = len([r for r in period_results if r.get("pass_fail") == "fail"])
        
        # Filter approvals by date range
        period_approvals = []
        for approval in self.batch_approvals.values():
            approval_date = datetime.fromisoformat(approval["approval_date"])
            if start_date <= approval_date <= end_date:
                period_approvals.append(approval)
        
        approved_batches = len([a for a in period_approvals if a.get("status") == "approved"])
        rejected_batches = len([a for a in period_approvals if a.get("status") == "rejected"])
        
        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "test_metrics": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "batch_metrics": {
                "total_batches_reviewed": len(period_approvals),
                "approved_batches": approved_batches,
                "rejected_batches": rejected_batches,
                "approval_rate": (approved_batches / len(period_approvals) * 100) if period_approvals else 0
            }
        }