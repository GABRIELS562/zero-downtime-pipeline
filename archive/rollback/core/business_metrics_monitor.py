#!/usr/bin/env python3
"""
Business Metrics Monitoring Framework
=====================================

Forensic-level business impact monitoring for automated rollback decisions:
- Real-time business metric collection and analysis
- Statistical anomaly detection with confidence intervals
- Risk assessment using forensic investigation principles
- Evidence-based rollback trigger mechanisms
- Chain of custody for all business impact decisions

Forensic Methodology Applied:
- Evidence collection from multiple business data sources
- Timeline reconstruction of business impact events
- Statistical significance testing for impact validation
- Risk quantification using actuarial analysis methods
- Incident response procedures based on business criticality
"""

import asyncio
import json
import logging
import statistics
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, asdict
import hashlib
import uuid

import aiohttp
import numpy as np
from scipy import stats


class BusinessImpactLevel(Enum):
    """Business impact severity levels for forensic classification."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    CATASTROPHIC = "CATASTROPHIC"


class RollbackTriggerType(Enum):
    """Types of rollback triggers based on forensic analysis."""
    REVENUE_LOSS = "REVENUE_LOSS"
    EFFICIENCY_DROP = "EFFICIENCY_DROP"
    ERROR_RATE_SPIKE = "ERROR_RATE_SPIKE"
    LATENCY_DEGRADATION = "LATENCY_DEGRADATION"
    COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"
    CUSTOMER_IMPACT = "CUSTOMER_IMPACT"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"


@dataclass
class BusinessMetric:
    """Business metric with forensic metadata."""
    name: str
    value: Decimal
    timestamp: datetime
    currency: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate forensic hash for data integrity."""
        content = {
            'name': self.name,
            'value': str(self.value),
            'timestamp': self.timestamp.isoformat(),
            'currency': self.currency,
            'unit': self.unit,
            'source': self.source
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


@dataclass
class BusinessImpactAssessment:
    """Forensic assessment of business impact."""
    assessment_id: str
    timestamp: datetime
    deployment_id: str
    impact_level: BusinessImpactLevel
    estimated_loss: Decimal
    confidence: float
    trigger_type: RollbackTriggerType
    evidence: Dict[str, Any]
    metrics: List[BusinessMetric]
    recommendation: str
    
    def __post_init__(self):
        self.forensic_hash = self._generate_forensic_hash()
    
    def _generate_forensic_hash(self) -> str:
        """Generate forensic hash for assessment integrity."""
        content = {
            'assessment_id': self.assessment_id,
            'timestamp': self.timestamp.isoformat(),
            'deployment_id': self.deployment_id,
            'impact_level': self.impact_level.value,
            'estimated_loss': str(self.estimated_loss),
            'trigger_type': self.trigger_type.value,
            'metrics_count': len(self.metrics)
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


class BusinessMetricsCollector(ABC):
    """Abstract base class for business metrics collection."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"business_metrics.{name}")
        self.baseline_metrics: Dict[str, List[BusinessMetric]] = {}
    
    @abstractmethod
    async def collect_metrics(self) -> List[BusinessMetric]:
        """Collect business metrics from data sources."""
        pass
    
    @abstractmethod
    def calculate_impact(self, current_metrics: List[BusinessMetric]) -> BusinessImpactAssessment:
        """Calculate business impact based on current vs baseline metrics."""
        pass
    
    async def establish_baseline(self, hours_back: int = 24) -> Dict[str, Any]:
        """Establish baseline metrics for comparison."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        baseline_data = await self._collect_historical_metrics(start_time, end_time)
        
        baseline_summary = {}
        for metric_name, metrics in baseline_data.items():
            if metrics:
                values = [float(m.value) for m in metrics]
                baseline_summary[metric_name] = {
                    'mean': statistics.mean(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
                    'median': statistics.median(values),
                    'p95': np.percentile(values, 95),
                    'p99': np.percentile(values, 99),
                    'sample_count': len(values),
                    'min_value': min(values),
                    'max_value': max(values)
                }
        
        self.baseline_metrics = baseline_data
        return baseline_summary
    
    async def _collect_historical_metrics(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, List[BusinessMetric]]:
        """Collect historical metrics for baseline establishment."""
        # Implementation would depend on specific data sources
        # This is a template for subclasses to implement
        return {}
    
    def _calculate_statistical_significance(
        self, 
        baseline_values: List[float], 
        current_values: List[float]
    ) -> Tuple[float, float]:
        """Calculate statistical significance of change."""
        if len(baseline_values) < 2 or len(current_values) < 2:
            return 0.0, 1.0
        
        try:
            t_stat, p_value = stats.ttest_ind(baseline_values, current_values)
            return float(t_stat), float(p_value)
        except Exception:
            return 0.0, 1.0
    
    def _quantify_business_impact(
        self,
        metric_name: str,
        baseline_value: float,
        current_value: float,
        impact_per_unit: Decimal
    ) -> Tuple[Decimal, BusinessImpactLevel]:
        """Quantify business impact in monetary terms."""
        if baseline_value == 0:
            return Decimal('0'), BusinessImpactLevel.NONE
        
        percentage_change = abs(current_value - baseline_value) / baseline_value * 100
        estimated_loss = abs(Decimal(str(current_value - baseline_value)) * impact_per_unit)
        
        # Classify impact level
        if percentage_change >= 50 or estimated_loss >= Decimal('1000000'):  # $1M+
            impact_level = BusinessImpactLevel.CATASTROPHIC
        elif percentage_change >= 25 or estimated_loss >= Decimal('100000'):  # $100K+
            impact_level = BusinessImpactLevel.CRITICAL
        elif percentage_change >= 10 or estimated_loss >= Decimal('10000'):   # $10K+
            impact_level = BusinessImpactLevel.HIGH
        elif percentage_change >= 5 or estimated_loss >= Decimal('1000'):    # $1K+
            impact_level = BusinessImpactLevel.MEDIUM
        elif percentage_change >= 1 or estimated_loss >= Decimal('100'):     # $100+
            impact_level = BusinessImpactLevel.LOW
        else:
            impact_level = BusinessImpactLevel.NONE
        
        return estimated_loss, impact_level


class BusinessMetricsMonitor:
    """
    Main business metrics monitoring system with forensic capabilities.
    
    Coordinates multiple collectors and performs impact analysis using
    forensic investigation principles.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("business_metrics_monitor")
        self.collectors: Dict[str, BusinessMetricsCollector] = {}
        self.deployment_tracker = DeploymentTracker()
        self.impact_assessments: List[BusinessImpactAssessment] = []
        
        # Configure thresholds
        self.rollback_thresholds = config.get('rollback_thresholds', {
            'revenue_loss_threshold': Decimal('10000'),      # $10K
            'efficiency_drop_threshold': 5.0,               # 5%
            'error_rate_threshold': 2.0,                    # 2%
            'latency_threshold_ms': 100,                    # 100ms
            'confidence_threshold': 0.8                     # 80% confidence
        })
        
        # Monitoring intervals
        self.monitoring_interval = config.get('monitoring_interval_seconds', 60)
        self.baseline_update_interval = config.get('baseline_update_hours', 6)
    
    def register_collector(self, collector: BusinessMetricsCollector):
        """Register a business metrics collector."""
        self.collectors[collector.name] = collector
        self.logger.info(f"Registered collector: {collector.name}")
    
    async def start_monitoring(self):
        """Start continuous business metrics monitoring."""
        self.logger.info("Starting business metrics monitoring...")
        
        # Establish baselines for all collectors
        for collector in self.collectors.values():
            await collector.establish_baseline()
        
        # Start monitoring loop
        while True:
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(30)  # Brief pause before retrying
    
    async def _monitoring_cycle(self):
        """Execute one cycle of business metrics monitoring."""
        cycle_start = datetime.now(timezone.utc)
        
        # Collect metrics from all collectors
        all_assessments = []
        
        for collector_name, collector in self.collectors.items():
            try:
                # Collect current metrics
                current_metrics = await collector.collect_metrics()
                
                # Perform impact assessment
                impact_assessment = collector.calculate_impact(current_metrics)
                all_assessments.append(impact_assessment)
                
                # Log forensic evidence
                self._log_forensic_evidence(collector_name, impact_assessment)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics from {collector_name}: {e}")
        
        # Analyze overall business impact
        overall_impact = await self._analyze_overall_impact(all_assessments)
        
        # Check rollback triggers
        rollback_decision = await self._evaluate_rollback_triggers(overall_impact, all_assessments)
        
        # Store assessments
        self.impact_assessments.extend(all_assessments)
        
        # Log monitoring cycle completion
        cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        self.logger.info(
            f"Monitoring cycle completed in {cycle_duration:.2f}s - "
            f"Overall impact: {overall_impact['impact_level']} - "
            f"Rollback recommended: {rollback_decision['rollback_recommended']}"
        )
        
        return {
            'cycle_start': cycle_start,
            'overall_impact': overall_impact,
            'rollback_decision': rollback_decision,
            'assessments': all_assessments
        }
    
    def _log_forensic_evidence(self, collector_name: str, assessment: BusinessImpactAssessment):
        """Log forensic evidence for audit trail."""
        evidence_entry = {
            'timestamp': assessment.timestamp.isoformat(),
            'collector': collector_name,
            'assessment_id': assessment.assessment_id,
            'deployment_id': assessment.deployment_id,
            'impact_level': assessment.impact_level.value,
            'estimated_loss': str(assessment.estimated_loss),
            'confidence': assessment.confidence,
            'trigger_type': assessment.trigger_type.value,
            'forensic_hash': assessment.forensic_hash,
            'evidence_summary': {
                'metrics_analyzed': len(assessment.metrics),
                'primary_indicators': list(assessment.evidence.keys())[:5],
                'recommendation': assessment.recommendation
            }
        }
        
        self.logger.info(f"FORENSIC_EVIDENCE|{json.dumps(evidence_entry)}")
    
    async def _analyze_overall_impact(self, assessments: List[BusinessImpactAssessment]) -> Dict[str, Any]:
        """Analyze overall business impact across all collectors."""
        if not assessments:
            return {
                'impact_level': BusinessImpactLevel.NONE.value,
                'total_estimated_loss': Decimal('0'),
                'confidence': 0.0,
                'affected_systems': 0
            }
        
        # Calculate total estimated loss
        total_loss = sum(assessment.estimated_loss for assessment in assessments)
        
        # Determine highest impact level
        impact_levels = [assessment.impact_level for assessment in assessments]
        highest_impact = max(impact_levels, key=lambda x: list(BusinessImpactLevel).index(x))
        
        # Calculate weighted confidence
        weighted_confidence = sum(
            assessment.confidence * float(assessment.estimated_loss)
            for assessment in assessments
        ) / max(float(total_loss), 1.0)
        
        # Count affected systems
        affected_systems = len([a for a in assessments if a.impact_level != BusinessImpactLevel.NONE])
        
        return {
            'impact_level': highest_impact.value,
            'total_estimated_loss': total_loss,
            'confidence': weighted_confidence,
            'affected_systems': affected_systems,
            'assessments_count': len(assessments)
        }
    
    async def _evaluate_rollback_triggers(
        self, 
        overall_impact: Dict[str, Any], 
        assessments: List[BusinessImpactAssessment]
    ) -> Dict[str, Any]:
        """Evaluate whether rollback should be triggered based on business impact."""
        rollback_recommended = False
        rollback_urgency = "none"
        rollback_reasons = []
        
        # Check revenue loss threshold
        if overall_impact['total_estimated_loss'] >= self.rollback_thresholds['revenue_loss_threshold']:
            rollback_recommended = True
            rollback_urgency = "immediate"
            rollback_reasons.append(
                f"Revenue loss ${overall_impact['total_estimated_loss']} "
                f"exceeds threshold ${self.rollback_thresholds['revenue_loss_threshold']}"
            )
        
        # Check impact level
        if overall_impact['impact_level'] in ['CRITICAL', 'CATASTROPHIC']:
            rollback_recommended = True
            rollback_urgency = "immediate" if overall_impact['impact_level'] == 'CATASTROPHIC' else "urgent"
            rollback_reasons.append(f"Business impact level: {overall_impact['impact_level']}")
        
        # Check confidence threshold
        if (overall_impact['confidence'] >= self.rollback_thresholds['confidence_threshold'] and
            overall_impact['affected_systems'] >= 2):
            rollback_recommended = True
            rollback_urgency = "urgent" if rollback_urgency == "none" else rollback_urgency
            rollback_reasons.append(
                f"High confidence ({overall_impact['confidence']:.2f}) "
                f"with multiple affected systems ({overall_impact['affected_systems']})"
            )
        
        # Check specific trigger types
        critical_triggers = [
            RollbackTriggerType.COMPLIANCE_VIOLATION,
            RollbackTriggerType.SECURITY_INCIDENT
        ]
        
        for assessment in assessments:
            if assessment.trigger_type in critical_triggers:
                rollback_recommended = True
                rollback_urgency = "immediate"
                rollback_reasons.append(f"Critical trigger: {assessment.trigger_type.value}")
        
        # Generate rollback decision
        rollback_decision = {
            'rollback_recommended': rollback_recommended,
            'urgency': rollback_urgency,
            'reasons': rollback_reasons,
            'confidence': overall_impact['confidence'],
            'decision_timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_hash': self._generate_decision_hash(rollback_recommended, rollback_reasons, overall_impact)
        }
        
        return rollback_decision
    
    def _generate_decision_hash(
        self, 
        rollback_recommended: bool, 
        reasons: List[str], 
        impact: Dict[str, Any]
    ) -> str:
        """Generate forensic hash for rollback decision."""
        content = {
            'rollback_recommended': rollback_recommended,
            'reasons': sorted(reasons),
            'impact_level': impact['impact_level'],
            'total_estimated_loss': str(impact['total_estimated_loss']),
            'confidence': impact['confidence']
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    
    async def get_current_impact_assessment(self) -> Dict[str, Any]:
        """Get current business impact assessment."""
        recent_assessments = [
            a for a in self.impact_assessments
            if (datetime.now(timezone.utc) - a.timestamp).seconds <= self.monitoring_interval * 2
        ]
        
        if not recent_assessments:
            return {
                'status': 'no_recent_data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        overall_impact = await self._analyze_overall_impact(recent_assessments)
        rollback_decision = await self._evaluate_rollback_triggers(overall_impact, recent_assessments)
        
        return {
            'status': 'active',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_impact': overall_impact,
            'rollback_decision': rollback_decision,
            'recent_assessments_count': len(recent_assessments)
        }


class DeploymentTracker:
    """Track deployment events for correlation with business impact."""
    
    def __init__(self):
        self.active_deployments: Dict[str, Dict[str, Any]] = {}
        self.deployment_history: List[Dict[str, Any]] = []
    
    def start_deployment(self, deployment_id: str, metadata: Dict[str, Any]):
        """Record start of a deployment."""
        deployment_info = {
            'deployment_id': deployment_id,
            'start_time': datetime.now(timezone.utc),
            'metadata': metadata,
            'status': 'active'
        }
        
        self.active_deployments[deployment_id] = deployment_info
        self.deployment_history.append(deployment_info.copy())
    
    def end_deployment(self, deployment_id: str, status: str = 'completed'):
        """Record end of a deployment."""
        if deployment_id in self.active_deployments:
            self.active_deployments[deployment_id]['end_time'] = datetime.now(timezone.utc)
            self.active_deployments[deployment_id]['status'] = status
            del self.active_deployments[deployment_id]
    
    def get_current_deployment(self) -> Optional[str]:
        """Get the most recent active deployment ID."""
        if not self.active_deployments:
            return None
        
        # Return the most recently started deployment
        latest_deployment = max(
            self.active_deployments.values(),
            key=lambda x: x['start_time']
        )
        return latest_deployment['deployment_id']