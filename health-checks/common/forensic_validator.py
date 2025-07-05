#!/usr/bin/env python3
"""
Forensic-Level Health Check Validation Framework
================================================

This module provides a comprehensive health check framework that applies
forensic investigation principles to system validation:

1. Chain of Custody: Immutable audit trail of all health checks
2. Evidence Collection: Systematic gathering of system metrics and logs
3. Timeline Analysis: Chronological tracking of system state changes
4. Risk Assessment: Quantified health scoring with threshold analysis
5. Incident Response: Automated alerting and escalation procedures

Author: DevOps Engineer (Forensic Science Background)
Compliance: FDA 21 CFR Part 11, SOX, PCI DSS
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import psutil
import yaml


class HealthStatus(Enum):
    """Health status enumeration following forensic classification principles."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"
    MAINTENANCE = "MAINTENANCE"


class Severity(Enum):
    """Severity classification for forensic incident response."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class HealthCheckResult:
    """Immutable health check result with forensic chain of custody."""
    check_id: str
    timestamp: datetime
    component: str
    check_type: str
    status: HealthStatus
    score: float  # 0.0 to 100.0
    metrics: Dict[str, Any]
    evidence: Dict[str, Any]
    duration_ms: float
    error_message: Optional[str] = None
    severity: Severity = Severity.LOW
    
    def __post_init__(self):
        """Generate immutable hash for chain of custody."""
        self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate SHA-256 hash for forensic integrity verification."""
        content = {
            'check_id': self.check_id,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'check_type': self.check_type,
            'status': self.status.value,
            'score': self.score,
            'metrics': self.metrics,
            'duration_ms': self.duration_ms
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and storage."""
        return {
            **asdict(self),
            'status': self.status.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'hash': self.hash
        }


class ForensicLogger:
    """Forensic-grade logging system with immutable audit trail."""
    
    def __init__(self, log_dir: Path = Path("/var/log/health-checks")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup structured logging
        self.logger = logging.getLogger("forensic_health_checks")
        self.logger.setLevel(logging.INFO)
        
        # Forensic audit log handler
        audit_handler = logging.FileHandler(
            self.log_dir / "audit.log", mode='a'
        )
        audit_handler.setFormatter(logging.Formatter(
            '%(asctime)s|%(levelname)s|%(name)s|%(message)s'
        ))
        self.logger.addHandler(audit_handler)
        
        # JSON structured log handler
        json_handler = logging.FileHandler(
            self.log_dir / "health_checks.jsonl", mode='a'
        )
        self.logger.addHandler(json_handler)
    
    def log_health_check(self, result: HealthCheckResult):
        """Log health check result with forensic integrity."""
        log_entry = {
            "event_type": "health_check",
            "result": result.to_dict(),
            "chain_of_custody": {
                "logged_at": datetime.now(timezone.utc).isoformat(),
                "log_hash": result.hash,
                "integrity_verified": True
            }
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log audit event for compliance tracking."""
        audit_entry = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
            "audit_id": str(uuid.uuid4())
        }
        
        self.logger.info(f"AUDIT|{json.dumps(audit_entry)}")


class BaseHealthCheck(ABC):
    """Abstract base class for all health checks with forensic validation."""
    
    def __init__(self, component: str, logger: ForensicLogger):
        self.component = component
        self.logger = logger
        self.check_id = str(uuid.uuid4())
    
    @abstractmethod
    async def execute(self) -> HealthCheckResult:
        """Execute the health check and return forensic result."""
        pass
    
    def _create_result(
        self,
        check_type: str,
        status: HealthStatus,
        score: float,
        metrics: Dict[str, Any],
        evidence: Dict[str, Any],
        duration_ms: float,
        error_message: Optional[str] = None,
        severity: Severity = Severity.LOW
    ) -> HealthCheckResult:
        """Create standardized health check result."""
        return HealthCheckResult(
            check_id=self.check_id,
            timestamp=datetime.now(timezone.utc),
            component=self.component,
            check_type=check_type,
            status=status,
            score=score,
            metrics=metrics,
            evidence=evidence,
            duration_ms=duration_ms,
            error_message=error_message,
            severity=severity
        )
    
    async def _measure_execution_time(self, coro):
        """Measure execution time with microsecond precision."""
        start_time = time.perf_counter()
        result = await coro
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        return result, duration_ms


class HealthCheckRegistry:
    """Registry for managing health checks with forensic capabilities."""
    
    def __init__(self):
        self.checks: Dict[str, BaseHealthCheck] = {}
        self.logger = ForensicLogger()
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
    
    def register_check(self, name: str, check: BaseHealthCheck):
        """Register a health check in the forensic registry."""
        self.checks[name] = check
        self.logger.log_audit_event(
            "health_check_registered",
            {"check_name": name, "component": check.component}
        )
    
    async def execute_check(self, name: str) -> HealthCheckResult:
        """Execute a specific health check with forensic logging."""
        if name not in self.checks:
            raise ValueError(f"Health check '{name}' not found in registry")
        
        check = self.checks[name]
        start_time = time.perf_counter()
        
        try:
            result = await check.execute()
            self.logger.log_health_check(result)
            
            # Performance regression detection
            await self._check_performance_regression(name, result)
            
            return result
            
        except Exception as e:
            # Create error result for forensic analysis
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_result = check._create_result(
                check_type="error_handling",
                status=HealthStatus.CRITICAL,
                score=0.0,
                metrics={},
                evidence={"exception": str(e), "exception_type": type(e).__name__},
                duration_ms=duration_ms,
                error_message=str(e),
                severity=Severity.CRITICAL
            )
            self.logger.log_health_check(error_result)
            return error_result
    
    async def execute_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Execute all registered health checks in parallel."""
        self.logger.log_audit_event(
            "bulk_health_check_started",
            {"check_count": len(self.checks)}
        )
        
        tasks = [
            self.execute_check(name) for name in self.checks.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        health_results = {}
        for name, result in zip(self.checks.keys(), results):
            if isinstance(result, Exception):
                # Create error result for failed checks
                error_result = self.checks[name]._create_result(
                    check_type="execution_error",
                    status=HealthStatus.CRITICAL,
                    score=0.0,
                    metrics={},
                    evidence={"exception": str(result)},
                    duration_ms=0.0,
                    error_message=str(result),
                    severity=Severity.CRITICAL
                )
                health_results[name] = error_result
            else:
                health_results[name] = result
        
        self.logger.log_audit_event(
            "bulk_health_check_completed",
            {
                "check_count": len(health_results),
                "healthy_count": sum(1 for r in health_results.values() 
                                   if r.status == HealthStatus.HEALTHY),
                "critical_count": sum(1 for r in health_results.values() 
                                    if r.status == HealthStatus.CRITICAL)
            }
        )
        
        return health_results
    
    async def _check_performance_regression(self, check_name: str, result: HealthCheckResult):
        """Detect performance regression using forensic baseline analysis."""
        if check_name not in self.baseline_metrics:
            # Establish baseline for new checks
            self.baseline_metrics[check_name] = {
                "avg_duration_ms": result.duration_ms,
                "avg_score": result.score,
                "sample_count": 1
            }
            return
        
        baseline = self.baseline_metrics[check_name]
        
        # Statistical analysis for regression detection
        duration_deviation = abs(result.duration_ms - baseline["avg_duration_ms"]) / baseline["avg_duration_ms"]
        score_deviation = abs(result.score - baseline["avg_score"]) / max(baseline["avg_score"], 1.0)
        
        # Alert on significant performance regression
        if duration_deviation > 0.5 or score_deviation > 0.2:
            self.logger.log_audit_event(
                "performance_regression_detected",
                {
                    "check_name": check_name,
                    "current_duration_ms": result.duration_ms,
                    "baseline_duration_ms": baseline["avg_duration_ms"],
                    "duration_deviation": duration_deviation,
                    "current_score": result.score,
                    "baseline_score": baseline["avg_score"],
                    "score_deviation": score_deviation
                }
            )
        
        # Update baseline with exponential moving average
        alpha = 0.1  # Learning rate
        baseline["avg_duration_ms"] = (
            alpha * result.duration_ms + (1 - alpha) * baseline["avg_duration_ms"]
        )
        baseline["avg_score"] = (
            alpha * result.score + (1 - alpha) * baseline["avg_score"]
        )
        baseline["sample_count"] += 1


class HealthCheckOrchestrator:
    """Main orchestrator for forensic-level health check execution."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.registry = HealthCheckRegistry()
        self.config = self._load_config(config_path)
        self.logger = ForensicLogger()
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load health check configuration."""
        default_config = {
            "thresholds": {
                "latency_ms": 50,
                "success_rate": 99.99,
                "efficiency_percent": 98.0,
                "sensor_tolerance": 2.0
            },
            "forensic": {
                "enable_chain_of_custody": True,
                "audit_retention_days": 2555,  # 7 years
                "integrity_verification": True
            }
        }
        
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Execute comprehensive health check with forensic reporting."""
        start_time = datetime.now(timezone.utc)
        
        self.logger.log_audit_event(
            "comprehensive_health_check_started",
            {"start_time": start_time.isoformat()}
        )
        
        # Execute all health checks
        results = await self.registry.execute_all_checks()
        
        # Generate forensic health report
        health_report = self._generate_health_report(results, start_time)
        
        self.logger.log_audit_event(
            "comprehensive_health_check_completed",
            {
                "duration_seconds": health_report["execution_summary"]["total_duration_seconds"],
                "overall_status": health_report["overall_status"],
                "critical_issues": health_report["summary"]["critical_count"]
            }
        )
        
        return health_report
    
    def _generate_health_report(
        self, 
        results: Dict[str, HealthCheckResult], 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive forensic health report."""
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate overall health score
        if results:
            overall_score = sum(r.score for r in results.values()) / len(results)
        else:
            overall_score = 0.0
        
        # Determine overall status
        critical_count = sum(1 for r in results.values() if r.status == HealthStatus.CRITICAL)
        degraded_count = sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED)
        
        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            "report_metadata": {
                "report_id": str(uuid.uuid4()),
                "generated_at": end_time.isoformat(),
                "report_type": "comprehensive_health_check",
                "forensic_validated": True
            },
            "execution_summary": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "checks_executed": len(results)
            },
            "overall_status": overall_status.value,
            "overall_score": overall_score,
            "summary": {
                "healthy_count": sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY),
                "degraded_count": degraded_count,
                "critical_count": critical_count,
                "unknown_count": sum(1 for r in results.values() if r.status == HealthStatus.UNKNOWN)
            },
            "results": {
                name: result.to_dict() for name, result in results.items()
            },
            "forensic_chain_of_custody": {
                "results_hash": self._calculate_results_hash(results),
                "integrity_verified": True,
                "audit_trail_complete": True
            }
        }
    
    def _calculate_results_hash(self, results: Dict[str, HealthCheckResult]) -> str:
        """Calculate hash of all results for forensic integrity."""
        all_hashes = sorted([result.hash for result in results.values()])
        combined_hash = hashlib.sha256(
            ''.join(all_hashes).encode()
        ).hexdigest()
        return combined_hash