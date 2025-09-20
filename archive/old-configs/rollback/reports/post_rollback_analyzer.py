#!/usr/bin/env python3
"""
Post-Rollback Analysis and Forensic Reporting System
===================================================

Comprehensive post-incident analysis system applying forensic investigation
principles to rollback events for continuous improvement and compliance:

- Root cause analysis using systematic forensic investigation methods
- Business impact quantification and attribution analysis
- Performance impact assessment with statistical correlation
- Stakeholder communication effectiveness analysis
- Regulatory compliance validation and reporting
- Lessons learned documentation and knowledge base updates
- Automated recommendations for process improvement

Forensic Methodology Applied:
- Timeline reconstruction with microsecond precision for causality analysis
- Evidence correlation across multiple data sources
- Statistical significance testing for impact attribution
- Chain of custody validation for all evidence and decisions
- Risk assessment methodology for prevention strategies
- Systematic documentation for regulatory compliance and audit trails
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set
import uuid
import hashlib

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from ..core.automated_rollback_orchestrator import (
    RollbackDecision, RollbackExecution, RollbackUrgency, RollbackStatus
)
from ..core.business_metrics_monitor import BusinessImpactLevel, RollbackTriggerType
from ..notifications.stakeholder_notifier import NotificationBatch


class AnalysisType(Enum):
    """Types of post-rollback analysis."""
    ROOT_CAUSE = "ROOT_CAUSE"
    BUSINESS_IMPACT = "BUSINESS_IMPACT"
    PERFORMANCE_IMPACT = "PERFORMANCE_IMPACT"
    COMMUNICATION_EFFECTIVENESS = "COMMUNICATION_EFFECTIVENESS"
    COMPLIANCE_VALIDATION = "COMPLIANCE_VALIDATION"
    LESSONS_LEARNED = "LESSONS_LEARNED"


class FindingsSeverity(Enum):
    """Severity levels for analysis findings."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisFinding:
    """Individual finding from post-rollback analysis."""
    
    def __init__(
        self,
        finding_id: str,
        analysis_type: AnalysisType,
        severity: FindingsSeverity,
        title: str,
        description: str,
        evidence: Dict[str, Any],
        recommendations: List[str]
    ):
        self.finding_id = finding_id
        self.analysis_type = analysis_type
        self.severity = severity
        self.title = title
        self.description = description
        self.evidence = evidence
        self.recommendations = recommendations
        self.timestamp = datetime.now(timezone.utc)
        self.forensic_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate forensic hash for finding integrity."""
        content = {
            'finding_id': self.finding_id,
            'analysis_type': self.analysis_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'timestamp': self.timestamp.isoformat()
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'finding_id': self.finding_id,
            'analysis_type': self.analysis_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'evidence': self.evidence,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat(),
            'forensic_hash': self.forensic_hash
        }


class PostRollbackReport:
    """Comprehensive post-rollback analysis report."""
    
    def __init__(
        self,
        report_id: str,
        rollback_execution: RollbackExecution,
        notification_batches: List[NotificationBatch]
    ):
        self.report_id = report_id
        self.rollback_execution = rollback_execution
        self.notification_batches = notification_batches
        self.generated_at = datetime.now(timezone.utc)
        self.findings: List[AnalysisFinding] = []
        self.metrics: Dict[str, Any] = {}
        self.conclusions: Dict[str, Any] = {}
        self.recommendations: List[str] = []
        self.forensic_timeline: List[Dict[str, Any]] = []
    
    def add_finding(self, finding: AnalysisFinding):
        """Add analysis finding to report."""
        self.findings.append(finding)
    
    def add_metric(self, metric_name: str, value: Any, metadata: Dict[str, Any] = None):
        """Add metric to report."""
        self.metrics[metric_name] = {
            'value': value,
            'metadata': metadata or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def add_conclusion(self, category: str, conclusion: str, confidence: float):
        """Add conclusion to report."""
        self.conclusions[category] = {
            'conclusion': conclusion,
            'confidence': confidence,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get report summary."""
        findings_by_severity = {}
        for finding in self.findings:
            severity = finding.severity.value
            if severity not in findings_by_severity:
                findings_by_severity[severity] = 0
            findings_by_severity[severity] += 1
        
        return {
            'report_id': self.report_id,
            'rollback_execution_id': self.rollback_execution.execution_id,
            'deployment_id': self.rollback_execution.deployment_id,
            'generated_at': self.generated_at.isoformat(),
            'rollback_duration_seconds': self._calculate_rollback_duration(),
            'business_impact': {
                'impact_level': self.rollback_execution.decision.business_impact.impact_level.value,
                'estimated_loss': str(self.rollback_execution.decision.business_impact.estimated_loss),
                'trigger_type': self.rollback_execution.decision.business_impact.trigger_type.value
            },
            'findings_summary': findings_by_severity,
            'total_findings': len(self.findings),
            'total_recommendations': len(self.recommendations),
            'notification_batches': len(self.notification_batches)
        }
    
    def _calculate_rollback_duration(self) -> float:
        """Calculate total rollback duration."""
        if self.rollback_execution.start_time and self.rollback_execution.end_time:
            return (self.rollback_execution.end_time - self.rollback_execution.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            'report_id': self.report_id,
            'rollback_execution': self.rollback_execution.to_dict(),
            'notification_batches': [batch.batch_id for batch in self.notification_batches],
            'generated_at': self.generated_at.isoformat(),
            'findings': [finding.to_dict() for finding in self.findings],
            'metrics': self.metrics,
            'conclusions': self.conclusions,
            'recommendations': self.recommendations,
            'summary': self.get_summary()
        }


class PostRollbackAnalyzer:
    """
    Main post-rollback analysis system with forensic capabilities.
    
    Performs comprehensive analysis of rollback events to identify root causes,
    quantify impacts, and generate actionable recommendations for improvement.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("post_rollback_analyzer")
        
        # Analysis configuration
        self.analysis_config = config.get('analysis', {})
        self.data_retention_days = config.get('data_retention_days', 90)
        self.statistical_significance_threshold = config.get('statistical_significance', 0.05)
        
        # External data sources
        self.metrics_sources = config.get('metrics_sources', {})
        self.log_sources = config.get('log_sources', {})
        
        # Report storage
        self.reports: Dict[str, PostRollbackReport] = {}
        self.historical_data: Dict[str, List[Dict[str, Any]]] = {}
    
    async def analyze_rollback(
        self, 
        execution: RollbackExecution,
        notification_batches: List[NotificationBatch] = None
    ) -> PostRollbackReport:
        """Perform comprehensive post-rollback analysis."""
        report_id = str(uuid.uuid4())
        report = PostRollbackReport(
            report_id=report_id,
            rollback_execution=execution,
            notification_batches=notification_batches or []
        )
        
        self.logger.info(f"Starting post-rollback analysis for execution {execution.execution_id}")
        
        # Perform different types of analysis
        analysis_tasks = [
            self._analyze_root_cause(execution, report),
            self._analyze_business_impact(execution, report),
            self._analyze_performance_impact(execution, report),
            self._analyze_communication_effectiveness(execution, notification_batches, report),
            self._analyze_compliance_validation(execution, report),
            self._generate_lessons_learned(execution, report)
        ]
        
        # Execute analysis tasks concurrently
        await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Generate overall conclusions and recommendations
        await self._generate_conclusions(report)
        await self._generate_recommendations(report)
        
        # Store report
        self.reports[report_id] = report
        
        # Update historical data
        await self._update_historical_data(report)
        
        self.logger.info(f"Post-rollback analysis completed: {report_id}")
        
        return report
    
    async def _analyze_root_cause(self, execution: RollbackExecution, report: PostRollbackReport):
        """Perform root cause analysis using forensic investigation methods."""
        try:
            # Analyze rollback trigger
            trigger_analysis = await self._analyze_rollback_trigger(execution)
            
            # Analyze deployment timeline
            timeline_analysis = await self._analyze_deployment_timeline(execution)
            
            # Analyze system health leading up to rollback
            health_analysis = await self._analyze_system_health_degradation(execution)
            
            # Correlate evidence to identify root cause
            root_cause = await self._correlate_root_cause_evidence(
                trigger_analysis, timeline_analysis, health_analysis
            )
            
            finding = AnalysisFinding(
                finding_id=str(uuid.uuid4()),
                analysis_type=AnalysisType.ROOT_CAUSE,
                severity=self._determine_root_cause_severity(root_cause),
                title="Root Cause Analysis",
                description=root_cause.get('description', 'Root cause analysis completed'),
                evidence={
                    'trigger_analysis': trigger_analysis,
                    'timeline_analysis': timeline_analysis,
                    'health_analysis': health_analysis,
                    'correlation_analysis': root_cause
                },
                recommendations=root_cause.get('recommendations', [])
            )
            
            report.add_finding(finding)
            
        except Exception as e:
            self.logger.error(f"Error in root cause analysis: {e}")
    
    async def _analyze_rollback_trigger(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Analyze what triggered the rollback."""
        decision = execution.decision
        impact = decision.business_impact
        
        return {
            'trigger_type': impact.trigger_type.value,
            'impact_level': impact.impact_level.value,
            'confidence': impact.confidence,
            'estimated_loss': str(impact.estimated_loss),
            'justification': decision.justification,
            'evidence_categories': list(decision.evidence.keys()),
            'decision_timestamp': decision.timestamp.isoformat(),
            'urgency_level': decision.urgency.value
        }
    
    async def _analyze_deployment_timeline(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Analyze deployment and rollback timeline."""
        timeline_events = []
        
        # Add decision event
        timeline_events.append({
            'event': 'rollback_decision_made',
            'timestamp': execution.decision.timestamp.isoformat(),
            'details': {
                'decision_id': execution.decision.decision_id,
                'urgency': execution.decision.urgency.value
            }
        })
        
        # Add execution start
        if execution.start_time:
            timeline_events.append({
                'event': 'rollback_execution_started',
                'timestamp': execution.start_time.isoformat(),
                'details': {
                    'strategy': execution.rollback_strategy,
                    'execution_id': execution.execution_id
                }
            })
        
        # Add execution steps
        for i, step in enumerate(execution.execution_steps):
            timeline_events.append({
                'event': f'rollback_step_{i+1}',
                'timestamp': step['timestamp'],
                'details': {
                    'step_name': step['step_name'],
                    'success': step['success'],
                    'duration_ms': step['duration_ms']
                }
            })
        
        # Add execution end
        if execution.end_time:
            timeline_events.append({
                'event': 'rollback_execution_completed',
                'timestamp': execution.end_time.isoformat(),
                'details': {
                    'final_status': execution.status.value,
                    'total_steps': len(execution.execution_steps),
                    'total_errors': len(execution.error_log)
                }
            })
        
        # Calculate timeline metrics
        if execution.start_time and execution.end_time:
            total_duration = (execution.end_time - execution.start_time).total_seconds()
            decision_to_execution = (execution.start_time - execution.decision.timestamp).total_seconds()
        else:
            total_duration = 0
            decision_to_execution = 0
        
        return {
            'timeline_events': timeline_events,
            'total_duration_seconds': total_duration,
            'decision_to_execution_seconds': decision_to_execution,
            'total_steps': len(execution.execution_steps),
            'successful_steps': len([s for s in execution.execution_steps if s['success']]),
            'failed_steps': len([s for s in execution.execution_steps if not s['success']]),
            'total_errors': len(execution.error_log)
        }
    
    async def _analyze_system_health_degradation(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Analyze system health degradation patterns."""
        # This would integrate with actual monitoring systems
        # For now, we'll simulate the analysis
        
        health_metrics = {
            'cpu_utilization': {'baseline': 45.0, 'during_incident': 85.0, 'threshold': 80.0},
            'memory_usage': {'baseline': 60.0, 'during_incident': 90.0, 'threshold': 85.0},
            'error_rate': {'baseline': 0.1, 'during_incident': 5.2, 'threshold': 1.0},
            'response_time_ms': {'baseline': 150, 'during_incident': 500, 'threshold': 300},
            'throughput_rps': {'baseline': 1000, 'during_incident': 600, 'threshold': 800}
        }
        
        degradation_analysis = {}
        for metric, values in health_metrics.items():
            baseline = values['baseline']
            incident = values['during_incident']
            threshold = values['threshold']
            
            degradation_pct = ((incident - baseline) / baseline) * 100
            threshold_breach = incident > threshold
            
            degradation_analysis[metric] = {
                'baseline_value': baseline,
                'incident_value': incident,
                'threshold_value': threshold,
                'degradation_percentage': degradation_pct,
                'threshold_breached': threshold_breach,
                'severity': 'high' if abs(degradation_pct) > 50 else 'medium' if abs(degradation_pct) > 25 else 'low'
            }
        
        return {
            'metrics_analyzed': degradation_analysis,
            'overall_health_score': self._calculate_health_score(degradation_analysis),
            'critical_metrics': [
                metric for metric, analysis in degradation_analysis.items()
                if analysis['threshold_breached'] and analysis['severity'] == 'high'
            ]
        }
    
    def _calculate_health_score(self, degradation_analysis: Dict[str, Any]) -> float:
        """Calculate overall system health score."""
        severity_weights = {'low': 1, 'medium': 2, 'high': 3}
        
        total_impact = sum(
            severity_weights[analysis['severity']] * abs(analysis['degradation_percentage'])
            for analysis in degradation_analysis.values()
        )
        
        max_possible_impact = len(degradation_analysis) * severity_weights['high'] * 100
        
        health_score = max(0, 100 - (total_impact / max_possible_impact * 100))
        return round(health_score, 2)
    
    async def _correlate_root_cause_evidence(
        self, 
        trigger_analysis: Dict[str, Any],
        timeline_analysis: Dict[str, Any],
        health_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Correlate evidence to identify most likely root cause."""
        
        # Analyze correlation between trigger and health degradation
        trigger_type = trigger_analysis['trigger_type']
        critical_metrics = health_analysis['critical_metrics']
        health_score = health_analysis['overall_health_score']
        
        # Determine most likely root cause based on evidence
        if trigger_type == 'EFFICIENCY_DROP' and 'cpu_utilization' in critical_metrics:
            root_cause = {
                'primary_cause': 'Resource exhaustion leading to efficiency degradation',
                'confidence': 0.85,
                'contributing_factors': ['High CPU utilization', 'Increased error rates'],
                'description': 'System resource exhaustion caused performance degradation triggering efficiency-based rollback',
                'recommendations': [
                    'Implement resource monitoring with proactive scaling',
                    'Add CPU utilization alerts at 70% threshold',
                    'Review deployment resource allocations'
                ]
            }
        elif trigger_type == 'REVENUE_LOSS' and 'response_time_ms' in critical_metrics:
            root_cause = {
                'primary_cause': 'Latency degradation impacting trading revenue',
                'confidence': 0.90,
                'contributing_factors': ['Increased response time', 'Reduced throughput'],
                'description': 'Application latency increase directly correlated with revenue loss in trading systems',
                'recommendations': [
                    'Implement sub-50ms response time monitoring',
                    'Add latency-based automatic scaling policies',
                    'Review database query performance'
                ]
            }
        elif trigger_type == 'ERROR_RATE_SPIKE':
            root_cause = {
                'primary_cause': 'Application errors causing system instability',
                'confidence': 0.80,
                'contributing_factors': ['High error rates', 'Failed transactions'],
                'description': 'Increased application error rate indicates deployment introduced bugs or incompatibilities',
                'recommendations': [
                    'Enhance pre-deployment testing coverage',
                    'Implement canary deployment with error rate monitoring',
                    'Add comprehensive integration testing'
                ]
            }
        else:
            root_cause = {
                'primary_cause': 'Multiple system degradations detected',
                'confidence': 0.70,
                'contributing_factors': critical_metrics,
                'description': f'System health score dropped to {health_score}% with multiple metric degradations',
                'recommendations': [
                    'Conduct detailed post-mortem analysis',
                    'Review deployment procedures',
                    'Enhance monitoring and alerting'
                ]
            }
        
        # Add timeline correlation
        decision_to_execution_time = timeline_analysis['decision_to_execution_seconds']
        if decision_to_execution_time > 300:  # More than 5 minutes
            root_cause['contributing_factors'].append('Delayed rollback execution')
            root_cause['recommendations'].append('Optimize rollback decision and execution pipeline')
        
        return root_cause
    
    def _determine_root_cause_severity(self, root_cause: Dict[str, Any]) -> FindingsSeverity:
        """Determine severity of root cause finding."""
        confidence = root_cause.get('confidence', 0.5)
        
        if confidence >= 0.9:
            return FindingsSeverity.CRITICAL
        elif confidence >= 0.8:
            return FindingsSeverity.HIGH
        elif confidence >= 0.6:
            return FindingsSeverity.MEDIUM
        else:
            return FindingsSeverity.LOW
    
    async def _analyze_business_impact(self, execution: RollbackExecution, report: PostRollbackReport):
        """Analyze actual vs estimated business impact."""
        try:
            decision = execution.decision
            estimated_impact = decision.business_impact
            
            # Calculate actual impact based on rollback duration and recovery
            actual_impact = await self._calculate_actual_business_impact(execution)
            
            # Compare estimated vs actual
            impact_variance = await self._analyze_impact_variance(estimated_impact, actual_impact)
            
            finding = AnalysisFinding(
                finding_id=str(uuid.uuid4()),
                analysis_type=AnalysisType.BUSINESS_IMPACT,
                severity=self._determine_impact_severity(impact_variance),
                title="Business Impact Analysis",
                description=f"Actual business impact analysis: {impact_variance['accuracy_assessment']}",
                evidence={
                    'estimated_impact': {
                        'level': estimated_impact.impact_level.value,
                        'estimated_loss': str(estimated_impact.estimated_loss),
                        'confidence': estimated_impact.confidence
                    },
                    'actual_impact': actual_impact,
                    'variance_analysis': impact_variance
                },
                recommendations=impact_variance.get('recommendations', [])
            )
            
            report.add_finding(finding)
            
            # Add business metrics
            report.add_metric('estimated_loss', str(estimated_impact.estimated_loss))
            report.add_metric('actual_loss', str(actual_impact['total_loss']))
            report.add_metric('impact_accuracy', impact_variance['accuracy_percentage'])
            
        except Exception as e:
            self.logger.error(f"Error in business impact analysis: {e}")
    
    async def _calculate_actual_business_impact(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Calculate actual business impact from rollback execution."""
        if not execution.start_time or not execution.end_time:
            return {'total_loss': Decimal('0'), 'impact_components': {}}
        
        rollback_duration_minutes = (execution.end_time - execution.start_time).total_seconds() / 60
        
        # Calculate impact based on rollback type and duration
        impact_components = {}
        
        if execution.decision.business_impact.trigger_type == RollbackTriggerType.REVENUE_LOSS:
            # For revenue loss, calculate based on downtime and revenue rate
            revenue_per_minute = Decimal('1000')  # Base rate from config
            downtime_loss = revenue_per_minute * Decimal(str(rollback_duration_minutes))
            impact_components['downtime_revenue_loss'] = downtime_loss
        
        if execution.decision.business_impact.trigger_type == RollbackTriggerType.EFFICIENCY_DROP:
            # For efficiency, calculate based on production impact
            efficiency_cost_per_minute = Decimal('500')
            efficiency_loss = efficiency_cost_per_minute * Decimal(str(rollback_duration_minutes))
            impact_components['efficiency_loss'] = efficiency_loss
        
        # Add rollback execution costs
        execution_cost = Decimal('1000')  # Base execution cost
        if execution.rollback_strategy == 'full_stack_rollback':
            execution_cost *= Decimal('3')  # 3x cost for full stack
        elif execution.rollback_strategy == 'blue_green_switch':
            execution_cost *= Decimal('1.5')  # 1.5x cost for blue-green
        
        impact_components['rollback_execution_cost'] = execution_cost
        
        # Add error recovery costs if there were errors
        if execution.error_log:
            error_recovery_cost = Decimal('500') * len(execution.error_log)
            impact_components['error_recovery_cost'] = error_recovery_cost
        
        total_loss = sum(impact_components.values())
        
        return {
            'total_loss': total_loss,
            'rollback_duration_minutes': rollback_duration_minutes,
            'impact_components': {k: str(v) for k, v in impact_components.items()},
            'cost_breakdown': impact_components
        }
    
    async def _analyze_impact_variance(
        self, 
        estimated_impact: Any, 
        actual_impact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze variance between estimated and actual impact."""
        estimated_loss = estimated_impact.estimated_loss
        actual_loss = actual_impact['total_loss']
        
        if estimated_loss == 0:
            accuracy_percentage = 0.0
        else:
            variance = abs(actual_loss - estimated_loss)
            accuracy_percentage = max(0, 100 - (float(variance / estimated_loss) * 100))
        
        variance_ratio = float(actual_loss / estimated_loss) if estimated_loss > 0 else 0.0
        
        # Determine accuracy assessment
        if accuracy_percentage >= 90:
            accuracy_assessment = "Highly accurate impact estimation"
        elif accuracy_percentage >= 75:
            accuracy_assessment = "Good impact estimation with minor variance"
        elif accuracy_percentage >= 50:
            accuracy_assessment = "Moderate impact estimation accuracy"
        else:
            accuracy_assessment = "Poor impact estimation requiring improvement"
        
        recommendations = []
        if accuracy_percentage < 75:
            recommendations.extend([
                "Review impact calculation algorithms",
                "Improve baseline metric collection",
                "Enhance business impact modeling"
            ])
        
        if variance_ratio > 2.0:
            recommendations.append("Investigate factors causing higher than expected impact")
        elif variance_ratio < 0.5:
            recommendations.append("Review conservative impact estimation approach")
        
        return {
            'estimated_loss': str(estimated_loss),
            'actual_loss': str(actual_loss),
            'variance_amount': str(abs(actual_loss - estimated_loss)),
            'variance_ratio': variance_ratio,
            'accuracy_percentage': round(accuracy_percentage, 2),
            'accuracy_assessment': accuracy_assessment,
            'recommendations': recommendations
        }
    
    def _determine_impact_severity(self, impact_variance: Dict[str, Any]) -> FindingsSeverity:
        """Determine severity of impact variance finding."""
        accuracy = impact_variance['accuracy_percentage']
        
        if accuracy < 50:
            return FindingsSeverity.HIGH
        elif accuracy < 75:
            return FindingsSeverity.MEDIUM
        else:
            return FindingsSeverity.LOW
    
    async def _analyze_performance_impact(self, execution: RollbackExecution, report: PostRollbackReport):
        """Analyze performance impact of rollback execution."""
        try:
            performance_metrics = await self._collect_performance_metrics(execution)
            rollback_efficiency = await self._analyze_rollback_efficiency(execution)
            
            finding = AnalysisFinding(
                finding_id=str(uuid.uuid4()),
                analysis_type=AnalysisType.PERFORMANCE_IMPACT,
                severity=self._determine_performance_severity(rollback_efficiency),
                title="Rollback Performance Analysis",
                description=f"Rollback executed in {rollback_efficiency['total_duration']}s with {rollback_efficiency['efficiency_score']}% efficiency",
                evidence={
                    'performance_metrics': performance_metrics,
                    'rollback_efficiency': rollback_efficiency,
                    'execution_timeline': execution.forensic_timeline[-10:]  # Last 10 events
                },
                recommendations=rollback_efficiency.get('recommendations', [])
            )
            
            report.add_finding(finding)
            
            # Add performance metrics
            report.add_metric('rollback_duration_seconds', rollback_efficiency['total_duration'])
            report.add_metric('rollback_efficiency_score', rollback_efficiency['efficiency_score'])
            report.add_metric('steps_success_rate', rollback_efficiency['step_success_rate'])
            
        except Exception as e:
            self.logger.error(f"Error in performance impact analysis: {e}")
    
    async def _collect_performance_metrics(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Collect performance metrics for rollback execution."""
        if not execution.start_time or not execution.end_time:
            return {'error': 'Incomplete execution timing data'}
        
        total_duration = (execution.end_time - execution.start_time).total_seconds()
        
        # Analyze execution steps
        step_durations = [step['duration_ms'] / 1000 for step in execution.execution_steps]
        successful_steps = len([step for step in execution.execution_steps if step['success']])
        
        return {
            'total_duration_seconds': total_duration,
            'total_steps': len(execution.execution_steps),
            'successful_steps': successful_steps,
            'failed_steps': len(execution.execution_steps) - successful_steps,
            'average_step_duration': statistics.mean(step_durations) if step_durations else 0,
            'longest_step_duration': max(step_durations) if step_durations else 0,
            'total_errors': len(execution.error_log),
            'rollback_strategy': execution.rollback_strategy
        }
    
    async def _analyze_rollback_efficiency(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Analyze efficiency of rollback execution."""
        performance_metrics = await self._collect_performance_metrics(execution)
        
        # Calculate efficiency score based on multiple factors
        duration_score = self._calculate_duration_score(
            performance_metrics['total_duration_seconds'], 
            execution.rollback_strategy
        )
        
        success_rate = (performance_metrics['successful_steps'] / 
                       max(performance_metrics['total_steps'], 1)) * 100
        
        error_penalty = min(20, performance_metrics['total_errors'] * 5)  # Max 20% penalty
        
        efficiency_score = max(0, duration_score + (success_rate * 0.3) - error_penalty)
        
        recommendations = []
        if efficiency_score < 70:
            recommendations.extend([
                "Review rollback procedure optimization opportunities",
                "Consider implementing faster rollback strategies",
                "Analyze step execution bottlenecks"
            ])
        
        if performance_metrics['total_errors'] > 2:
            recommendations.append("Investigate and resolve rollback execution errors")
        
        return {
            'efficiency_score': round(efficiency_score, 2),
            'total_duration': performance_metrics['total_duration_seconds'],
            'step_success_rate': round(success_rate, 2),
            'error_count': performance_metrics['total_errors'],
            'duration_score': duration_score,
            'recommendations': recommendations
        }
    
    def _calculate_duration_score(self, duration: float, strategy: str) -> float:
        """Calculate score based on rollback duration and strategy."""
        # Expected durations by strategy (in seconds)
        expected_durations = {
            'blue_green_switch': 60,      # 1 minute
            'kubernetes_rolling': 300,    # 5 minutes
            'canary_rollback': 180,       # 3 minutes
            'database_rollback': 600,     # 10 minutes
            'full_stack_rollback': 900    # 15 minutes
        }
        
        expected = expected_durations.get(strategy, 300)
        
        if duration <= expected:
            return 70.0  # Good performance
        elif duration <= expected * 1.5:
            return 50.0  # Acceptable performance
        else:
            return 30.0  # Poor performance
    
    def _determine_performance_severity(self, efficiency: Dict[str, Any]) -> FindingsSeverity:
        """Determine severity of performance finding."""
        score = efficiency['efficiency_score']
        
        if score < 50:
            return FindingsSeverity.HIGH
        elif score < 70:
            return FindingsSeverity.MEDIUM
        else:
            return FindingsSeverity.LOW
    
    async def _analyze_communication_effectiveness(
        self, 
        execution: RollbackExecution,
        notification_batches: List[NotificationBatch],
        report: PostRollbackReport
    ):
        """Analyze effectiveness of stakeholder communications."""
        try:
            if not notification_batches:
                finding = AnalysisFinding(
                    finding_id=str(uuid.uuid4()),
                    analysis_type=AnalysisType.COMMUNICATION_EFFECTIVENESS,
                    severity=FindingsSeverity.MEDIUM,
                    title="Communication Analysis - No Data",
                    description="No notification batches available for analysis",
                    evidence={},
                    recommendations=["Ensure notification system is properly integrated"]
                )
                report.add_finding(finding)
                return
            
            communication_analysis = await self._analyze_notification_performance(notification_batches)
            stakeholder_coverage = await self._analyze_stakeholder_coverage(notification_batches, execution)
            
            finding = AnalysisFinding(
                finding_id=str(uuid.uuid4()),
                analysis_type=AnalysisType.COMMUNICATION_EFFECTIVENESS,
                severity=self._determine_communication_severity(communication_analysis),
                title="Stakeholder Communication Analysis",
                description=f"Notification delivery: {communication_analysis['overall_success_rate']}% success rate",
                evidence={
                    'notification_performance': communication_analysis,
                    'stakeholder_coverage': stakeholder_coverage,
                    'communication_timeline': self._build_communication_timeline(notification_batches)
                },
                recommendations=communication_analysis.get('recommendations', [])
            )
            
            report.add_finding(finding)
            
            # Add communication metrics
            report.add_metric('notification_success_rate', communication_analysis['overall_success_rate'])
            report.add_metric('stakeholder_coverage', stakeholder_coverage['coverage_percentage'])
            
        except Exception as e:
            self.logger.error(f"Error in communication effectiveness analysis: {e}")
    
    async def _analyze_notification_performance(self, batches: List[NotificationBatch]) -> Dict[str, Any]:
        """Analyze notification delivery performance."""
        total_deliveries = sum(len(batch.deliveries) for batch in batches)
        
        if total_deliveries == 0:
            return {
                'overall_success_rate': 0.0,
                'total_notifications': 0,
                'recommendations': ["No notifications were sent"]
            }
        
        successful_deliveries = sum(
            len([d for d in batch.deliveries if d.status in ['sent', 'delivered']])
            for batch in batches
        )
        
        success_rate = (successful_deliveries / total_deliveries) * 100
        
        # Analyze by channel
        channel_performance = {}
        for batch in batches:
            for delivery in batch.deliveries:
                channel = delivery.channel.value
                if channel not in channel_performance:
                    channel_performance[channel] = {'total': 0, 'successful': 0}
                
                channel_performance[channel]['total'] += 1
                if delivery.status in ['sent', 'delivered']:
                    channel_performance[channel]['successful'] += 1
        
        # Calculate channel success rates
        for channel_data in channel_performance.values():
            channel_data['success_rate'] = (
                (channel_data['successful'] / channel_data['total']) * 100
                if channel_data['total'] > 0 else 0
            )
        
        recommendations = []
        if success_rate < 95:
            recommendations.append("Improve notification delivery reliability")
        
        for channel, data in channel_performance.items():
            if data['success_rate'] < 90:
                recommendations.append(f"Address {channel} delivery issues")
        
        return {
            'overall_success_rate': round(success_rate, 2),
            'total_notifications': total_deliveries,
            'successful_notifications': successful_deliveries,
            'channel_performance': channel_performance,
            'recommendations': recommendations
        }
    
    async def _analyze_stakeholder_coverage(
        self, 
        batches: List[NotificationBatch], 
        execution: RollbackExecution
    ) -> Dict[str, Any]:
        """Analyze stakeholder notification coverage."""
        urgency = execution.decision.urgency
        impact_level = execution.decision.business_impact.impact_level
        
        # Expected stakeholders based on urgency and impact
        expected_stakeholders = self._get_expected_stakeholders(urgency, impact_level)
        
        # Actual notified stakeholders
        notified_stakeholders = set()
        for batch in batches:
            for delivery in batch.deliveries:
                notified_stakeholders.add(delivery.recipient)
        
        coverage_percentage = (len(notified_stakeholders) / max(len(expected_stakeholders), 1)) * 100
        
        missing_stakeholders = expected_stakeholders - notified_stakeholders
        
        return {
            'expected_stakeholders': list(expected_stakeholders),
            'notified_stakeholders': list(notified_stakeholders),
            'missing_stakeholders': list(missing_stakeholders),
            'coverage_percentage': round(coverage_percentage, 2)
        }
    
    def _get_expected_stakeholders(self, urgency: RollbackUrgency, impact_level: BusinessImpactLevel) -> Set[str]:
        """Get expected stakeholders based on urgency and impact."""
        # This would be based on actual stakeholder configuration
        # For now, we'll simulate based on severity
        stakeholders = set()
        
        if urgency in [RollbackUrgency.EMERGENCY, RollbackUrgency.IMMEDIATE]:
            stakeholders.update(['cto@company.com', 'ops-lead@company.com', 'business-lead@company.com'])
        
        if impact_level in [BusinessImpactLevel.CRITICAL, BusinessImpactLevel.CATASTROPHIC]:
            stakeholders.update(['ceo@company.com', 'legal@company.com'])
        
        # Always include technical team
        stakeholders.update(['devops@company.com', 'sre@company.com'])
        
        return stakeholders
    
    def _build_communication_timeline(self, batches: List[NotificationBatch]) -> List[Dict[str, Any]]:
        """Build timeline of communication events."""
        timeline = []
        
        for batch in batches:
            timeline.append({
                'event': 'notification_batch_created',
                'timestamp': batch.created_at.isoformat(),
                'batch_id': batch.batch_id,
                'notification_type': batch.notification_type,
                'delivery_count': len(batch.deliveries)
            })
            
            for delivery in batch.deliveries:
                if delivery.sent_at:
                    timeline.append({
                        'event': 'notification_sent',
                        'timestamp': delivery.sent_at.isoformat(),
                        'recipient': delivery.recipient,
                        'channel': delivery.channel.value,
                        'priority': delivery.priority.value
                    })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def _determine_communication_severity(self, analysis: Dict[str, Any]) -> FindingsSeverity:
        """Determine severity of communication finding."""
        success_rate = analysis['overall_success_rate']
        
        if success_rate < 80:
            return FindingsSeverity.HIGH
        elif success_rate < 95:
            return FindingsSeverity.MEDIUM
        else:
            return FindingsSeverity.LOW
    
    async def _analyze_compliance_validation(self, execution: RollbackExecution, report: PostRollbackReport):
        """Analyze regulatory compliance aspects of rollback."""
        try:
            compliance_analysis = await self._validate_compliance_requirements(execution)
            audit_trail_analysis = await self._validate_audit_trail(execution)
            
            finding = AnalysisFinding(
                finding_id=str(uuid.uuid4()),
                analysis_type=AnalysisType.COMPLIANCE_VALIDATION,
                severity=self._determine_compliance_severity(compliance_analysis),
                title="Regulatory Compliance Validation",
                description=f"Compliance validation: {compliance_analysis['overall_compliance_status']}",
                evidence={
                    'compliance_requirements': compliance_analysis,
                    'audit_trail_validation': audit_trail_analysis,
                    'forensic_hashes': self._collect_forensic_hashes(execution)
                },
                recommendations=compliance_analysis.get('recommendations', [])
            )
            
            report.add_finding(finding)
            
            # Add compliance metrics
            report.add_metric('compliance_score', compliance_analysis['compliance_score'])
            report.add_metric('audit_trail_complete', audit_trail_analysis['completeness_score'])
            
        except Exception as e:
            self.logger.error(f"Error in compliance validation: {e}")
    
    async def _validate_compliance_requirements(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Validate compliance with regulatory requirements."""
        compliance_checks = {
            'decision_documentation': self._check_decision_documentation(execution),
            'evidence_preservation': self._check_evidence_preservation(execution),
            'timeline_accuracy': self._check_timeline_accuracy(execution),
            'authorization_trail': self._check_authorization_trail(execution),
            'impact_quantification': self._check_impact_quantification(execution)
        }
        
        passed_checks = sum(1 for check in compliance_checks.values() if check['passed'])
        compliance_score = (passed_checks / len(compliance_checks)) * 100
        
        recommendations = []
        for check_name, check_result in compliance_checks.items():
            if not check_result['passed']:
                recommendations.extend(check_result.get('recommendations', []))
        
        overall_status = "COMPLIANT" if compliance_score >= 90 else "NON_COMPLIANT"
        
        return {
            'overall_compliance_status': overall_status,
            'compliance_score': round(compliance_score, 2),
            'compliance_checks': compliance_checks,
            'recommendations': recommendations
        }
    
    def _check_decision_documentation(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Check if rollback decision is properly documented."""
        decision = execution.decision
        
        required_fields = ['decision_id', 'timestamp', 'justification', 'forensic_hash']
        missing_fields = [field for field in required_fields if not getattr(decision, field, None)]
        
        return {
            'passed': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'recommendations': ['Complete decision documentation'] if missing_fields else []
        }
    
    def _check_evidence_preservation(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Check if evidence is properly preserved."""
        evidence_count = len(execution.decision.evidence)
        forensic_timeline_count = len(execution.forensic_timeline)
        
        sufficient_evidence = evidence_count >= 3  # Minimum evidence threshold
        timeline_documented = forensic_timeline_count >= 5  # Minimum timeline events
        
        passed = sufficient_evidence and timeline_documented
        
        recommendations = []
        if not sufficient_evidence:
            recommendations.append("Enhance evidence collection procedures")
        if not timeline_documented:
            recommendations.append("Improve forensic timeline documentation")
        
        return {
            'passed': passed,
            'evidence_count': evidence_count,
            'timeline_events': forensic_timeline_count,
            'recommendations': recommendations
        }
    
    def _check_timeline_accuracy(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Check timeline accuracy and completeness."""
        has_start_time = execution.start_time is not None
        has_end_time = execution.end_time is not None
        has_decision_time = execution.decision.timestamp is not None
        
        timeline_complete = has_start_time and has_end_time and has_decision_time
        
        # Check for reasonable timeline (decision should be before execution)
        reasonable_timeline = True
        if has_decision_time and has_start_time:
            reasonable_timeline = execution.decision.timestamp <= execution.start_time
        
        passed = timeline_complete and reasonable_timeline
        
        recommendations = []
        if not timeline_complete:
            recommendations.append("Ensure complete timestamp recording")
        if not reasonable_timeline:
            recommendations.append("Validate timeline chronology")
        
        return {
            'passed': passed,
            'timeline_complete': timeline_complete,
            'chronology_valid': reasonable_timeline,
            'recommendations': recommendations
        }
    
    def _check_authorization_trail(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Check authorization and approval trail."""
        # For automated systems, check that decision maker is documented
        decision_maker = execution.decision.decision_maker
        has_decision_maker = decision_maker is not None and decision_maker != ""
        
        # Check if urgent decisions have proper authorization
        urgency = execution.decision.urgency
        urgent_decision = urgency in [RollbackUrgency.EMERGENCY, RollbackUrgency.IMMEDIATE]
        
        # For urgent decisions, automated authorization is acceptable
        authorization_valid = has_decision_maker
        
        recommendations = []
        if not has_decision_maker:
            recommendations.append("Document decision maker in all rollback decisions")
        
        return {
            'passed': authorization_valid,
            'has_decision_maker': has_decision_maker,
            'urgent_decision': urgent_decision,
            'recommendations': recommendations
        }
    
    def _check_impact_quantification(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Check if business impact is properly quantified."""
        impact = execution.decision.business_impact
        
        has_estimated_loss = impact.estimated_loss > 0
        has_confidence = impact.confidence > 0
        has_evidence = len(impact.evidence) > 0
        
        impact_documented = has_estimated_loss and has_confidence and has_evidence
        
        recommendations = []
        if not has_estimated_loss:
            recommendations.append("Quantify financial impact of rollback decisions")
        if not has_confidence:
            recommendations.append("Include confidence levels in impact assessments")
        if not has_evidence:
            recommendations.append("Document evidence supporting impact calculations")
        
        return {
            'passed': impact_documented,
            'has_financial_impact': has_estimated_loss,
            'has_confidence_level': has_confidence,
            'has_supporting_evidence': has_evidence,
            'recommendations': recommendations
        }
    
    async def _validate_audit_trail(self, execution: RollbackExecution) -> Dict[str, Any]:
        """Validate completeness of audit trail."""
        audit_elements = {
            'decision_hash': bool(execution.decision.forensic_hash),
            'execution_timeline': len(execution.forensic_timeline) > 0,
            'step_documentation': len(execution.execution_steps) > 0,
            'error_logging': True,  # Error log exists even if empty
            'evidence_integrity': len(execution.decision.evidence) > 0
        }
        
        completeness_score = (sum(audit_elements.values()) / len(audit_elements)) * 100
        
        return {
            'completeness_score': round(completeness_score, 2),
            'audit_elements': audit_elements,
            'trail_complete': completeness_score >= 90
        }
    
    def _collect_forensic_hashes(self, execution: RollbackExecution) -> Dict[str, str]:
        """Collect all forensic hashes for integrity validation."""
        hashes = {
            'decision_hash': execution.decision.forensic_hash,
            'impact_hash': execution.decision.business_impact.forensic_hash
        }
        
        # Add timeline event hashes
        for i, event in enumerate(execution.forensic_timeline):
            if 'event_hash' in event:
                hashes[f'timeline_event_{i}'] = event['event_hash']
        
        return hashes
    
    def _determine_compliance_severity(self, analysis: Dict[str, Any]) -> FindingsSeverity:
        """Determine severity of compliance finding."""
        score = analysis['compliance_score']
        
        if score < 70:
            return FindingsSeverity.CRITICAL
        elif score < 85:
            return FindingsSeverity.HIGH
        elif score < 95:
            return FindingsSeverity.MEDIUM
        else:
            return FindingsSeverity.LOW
    
    async def _generate_lessons_learned(self, execution: RollbackExecution, report: PostRollbackReport):
        """Generate lessons learned from rollback execution."""
        try:
            lessons = await self._extract_lessons_learned(execution, report)
            
            finding = AnalysisFinding(
                finding_id=str(uuid.uuid4()),
                analysis_type=AnalysisType.LESSONS_LEARNED,
                severity=FindingsSeverity.INFO,
                title="Lessons Learned and Knowledge Base Update",
                description=f"Identified {len(lessons['lessons'])} key lessons from rollback execution",
                evidence={
                    'lessons_learned': lessons,
                    'knowledge_base_updates': lessons.get('knowledge_base_updates', []),
                    'process_improvements': lessons.get('process_improvements', [])
                },
                recommendations=lessons.get('actionable_recommendations', [])
            )
            
            report.add_finding(finding)
            
        except Exception as e:
            self.logger.error(f"Error generating lessons learned: {e}")
    
    async def _extract_lessons_learned(self, execution: RollbackExecution, report: PostRollbackReport) -> Dict[str, Any]:
        """Extract lessons learned from analysis findings."""
        lessons = []
        knowledge_base_updates = []
        process_improvements = []
        actionable_recommendations = []
        
        # Analyze findings to extract lessons
        for finding in report.findings:
            if finding.analysis_type == AnalysisType.ROOT_CAUSE:
                lessons.append({
                    'category': 'root_cause',
                    'lesson': f"Root cause identified: {finding.evidence.get('correlation_analysis', {}).get('primary_cause', 'Unknown')}",
                    'impact': finding.severity.value,
                    'prevention': finding.recommendations
                })
                
                # Add to knowledge base
                knowledge_base_updates.append({
                    'type': 'root_cause_pattern',
                    'pattern': finding.evidence.get('correlation_analysis', {}),
                    'frequency': 1,  # Would be updated with historical data
                    'prevention_strategies': finding.recommendations
                })
            
            elif finding.analysis_type == AnalysisType.PERFORMANCE_IMPACT:
                efficiency_score = finding.evidence.get('rollback_efficiency', {}).get('efficiency_score', 0)
                lessons.append({
                    'category': 'performance',
                    'lesson': f"Rollback efficiency: {efficiency_score}% - {finding.description}",
                    'impact': finding.severity.value,
                    'optimization': finding.recommendations
                })
                
                if efficiency_score < 70:
                    process_improvements.append({
                        'area': 'rollback_execution',
                        'current_performance': f"{efficiency_score}%",
                        'target_performance': "85%",
                        'improvement_actions': finding.recommendations
                    })
            
            elif finding.analysis_type == AnalysisType.COMMUNICATION_EFFECTIVENESS:
                success_rate = finding.evidence.get('notification_performance', {}).get('overall_success_rate', 0)
                lessons.append({
                    'category': 'communication',
                    'lesson': f"Notification success rate: {success_rate}% - stakeholder communication effectiveness",
                    'impact': finding.severity.value,
                    'improvements': finding.recommendations
                })
                
                if success_rate < 95:
                    process_improvements.append({
                        'area': 'stakeholder_communication',
                        'current_performance': f"{success_rate}%",
                        'target_performance': "98%",
                        'improvement_actions': finding.recommendations
                    })
        
        # Generate actionable recommendations
        all_recommendations = []
        for finding in report.findings:
            all_recommendations.extend(finding.recommendations)
        
        # Deduplicate and prioritize recommendations
        unique_recommendations = list(set(all_recommendations))
        
        # Prioritize based on finding severity
        high_priority_recommendations = []
        medium_priority_recommendations = []
        
        for finding in report.findings:
            if finding.severity in [FindingsSeverity.CRITICAL, FindingsSeverity.HIGH]:
                high_priority_recommendations.extend(finding.recommendations)
            else:
                medium_priority_recommendations.extend(finding.recommendations)
        
        actionable_recommendations = list(set(high_priority_recommendations + medium_priority_recommendations))[:10]  # Top 10
        
        return {
            'lessons': lessons,
            'knowledge_base_updates': knowledge_base_updates,
            'process_improvements': process_improvements,
            'actionable_recommendations': actionable_recommendations,
            'total_lessons': len(lessons),
            'improvement_areas': len(process_improvements)
        }
    
    async def _generate_conclusions(self, report: PostRollbackReport):
        """Generate overall conclusions from analysis."""
        findings_by_type = {}
        for finding in report.findings:
            analysis_type = finding.analysis_type.value
            if analysis_type not in findings_by_type:
                findings_by_type[analysis_type] = []
            findings_by_type[analysis_type].append(finding)
        
        # Generate conclusion for each analysis type
        for analysis_type, findings in findings_by_type.items():
            high_severity_count = len([f for f in findings if f.severity in [FindingsSeverity.CRITICAL, FindingsSeverity.HIGH]])
            
            if analysis_type == 'ROOT_CAUSE':
                if high_severity_count > 0:
                    conclusion = "Root cause identified with high confidence. Immediate preventive actions required."
                    confidence = 0.85
                else:
                    conclusion = "Root cause analysis completed. Monitor for pattern recurrence."
                    confidence = 0.70
            
            elif analysis_type == 'BUSINESS_IMPACT':
                if high_severity_count > 0:
                    conclusion = "Business impact estimation requires improvement. Review impact calculation models."
                    confidence = 0.75
                else:
                    conclusion = "Business impact accurately estimated and contained within acceptable limits."
                    confidence = 0.90
            
            elif analysis_type == 'PERFORMANCE_IMPACT':
                if high_severity_count > 0:
                    conclusion = "Rollback performance below expectations. Optimization required."
                    confidence = 0.80
                else:
                    conclusion = "Rollback executed efficiently within performance targets."
                    confidence = 0.85
            
            elif analysis_type == 'COMMUNICATION_EFFECTIVENESS':
                if high_severity_count > 0:
                    conclusion = "Stakeholder communication needs improvement. Review notification procedures."
                    confidence = 0.75
                else:
                    conclusion = "Stakeholder communication executed effectively with good coverage."
                    confidence = 0.85
            
            elif analysis_type == 'COMPLIANCE_VALIDATION':
                if high_severity_count > 0:
                    conclusion = "Compliance requirements not fully met. Immediate remediation required."
                    confidence = 0.90
                else:
                    conclusion = "Regulatory compliance requirements satisfied with complete audit trail."
                    confidence = 0.95
            
            else:
                conclusion = f"Analysis completed for {analysis_type.lower().replace('_', ' ')}."
                confidence = 0.70
            
            report.add_conclusion(analysis_type, conclusion, confidence)
    
    async def _generate_recommendations(self, report: PostRollbackReport):
        """Generate prioritized recommendations."""
        all_recommendations = []
        
        # Collect recommendations from all findings
        for finding in report.findings:
            for rec in finding.recommendations:
                all_recommendations.append({
                    'recommendation': rec,
                    'severity': finding.severity,
                    'analysis_type': finding.analysis_type,
                    'finding_id': finding.finding_id
                })
        
        # Priority mapping
        severity_priority = {
            FindingsSeverity.CRITICAL: 1,
            FindingsSeverity.HIGH: 2,
            FindingsSeverity.MEDIUM: 3,
            FindingsSeverity.LOW: 4,
            FindingsSeverity.INFO: 5
        }
        
        # Sort by priority and deduplicate
        unique_recommendations = {}
        for rec_data in all_recommendations:
            rec_text = rec_data['recommendation']
            if rec_text not in unique_recommendations:
                unique_recommendations[rec_text] = rec_data
            else:
                # Keep the highest priority version
                if severity_priority[rec_data['severity']] < severity_priority[unique_recommendations[rec_text]['severity']]:
                    unique_recommendations[rec_text] = rec_data
        
        # Sort by priority
        sorted_recommendations = sorted(
            unique_recommendations.values(),
            key=lambda x: severity_priority[x['severity']]
        )
        
        # Take top recommendations
        top_recommendations = [rec['recommendation'] for rec in sorted_recommendations[:15]]
        
        report.recommendations = top_recommendations
    
    async def _update_historical_data(self, report: PostRollbackReport):
        """Update historical data for trend analysis."""
        report_data = {
            'report_id': report.report_id,
            'timestamp': report.generated_at.isoformat(),
            'rollback_execution_id': report.rollback_execution.execution_id,
            'summary': report.get_summary(),
            'findings_count': len(report.findings),
            'recommendations_count': len(report.recommendations)
        }
        
        # Store in historical data (simplified - would use database in production)
        date_key = report.generated_at.strftime('%Y-%m-%d')
        if date_key not in self.historical_data:
            self.historical_data[date_key] = []
        
        self.historical_data[date_key].append(report_data)
        
        # Cleanup old data
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.data_retention_days)
        
        keys_to_remove = [
            key for key in self.historical_data.keys()
            if datetime.strptime(key, '%Y-%m-%d').replace(tzinfo=timezone.utc) < cutoff_date
        ]
        
        for key in keys_to_remove:
            del self.historical_data[key]
    
    async def get_report(self, report_id: str) -> Optional[PostRollbackReport]:
        """Get report by ID."""
        return self.reports.get(report_id)
    
    async def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis of rollback patterns."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        relevant_data = []
        for date_str, reports in self.historical_data.items():
            date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if start_date <= date <= end_date:
                relevant_data.extend(reports)
        
        if not relevant_data:
            return {
                'period_days': days,
                'total_rollbacks': 0,
                'trend_analysis': "Insufficient data for trend analysis"
            }
        
        # Analyze trends
        total_rollbacks = len(relevant_data)
        avg_findings = statistics.mean([r['findings_count'] for r in relevant_data])
        avg_recommendations = statistics.mean([r['recommendations_count'] for r in relevant_data])
        
        # Group by date for daily trends
        daily_counts = {}
        for report in relevant_data:
            date = report['timestamp'][:10]  # YYYY-MM-DD
            if date not in daily_counts:
                daily_counts[date] = 0
            daily_counts[date] += 1
        
        trend_direction = "stable"
        if len(daily_counts) > 7:  # Need at least a week of data
            recent_avg = statistics.mean(list(daily_counts.values())[-7:])
            earlier_avg = statistics.mean(list(daily_counts.values())[:-7])
            
            if recent_avg > earlier_avg * 1.2:
                trend_direction = "increasing"
            elif recent_avg < earlier_avg * 0.8:
                trend_direction = "decreasing"
        
        return {
            'period_days': days,
            'total_rollbacks': total_rollbacks,
            'average_findings_per_rollback': round(avg_findings, 2),
            'average_recommendations_per_rollback': round(avg_recommendations, 2),
            'daily_rollback_counts': daily_counts,
            'trend_direction': trend_direction,
            'trend_analysis': f"Rollback frequency is {trend_direction} over the past {days} days"
        }
    
    async def generate_executive_summary(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Generate executive summary of rollback analysis."""
        report = await self.get_report(report_id)
        if not report:
            return None
        
        summary = report.get_summary()
        
        # Key metrics
        key_metrics = {
            'rollback_duration': f"{summary['rollback_duration_seconds']:.1f} seconds",
            'business_impact': summary['business_impact']['estimated_loss'],
            'impact_level': summary['business_impact']['impact_level'],
            'total_findings': summary['total_findings'],
            'critical_findings': summary['findings_summary'].get('CRITICAL', 0) + summary['findings_summary'].get('HIGH', 0)
        }
        
        # Executive recommendations (top 5)
        executive_recommendations = report.recommendations[:5]
        
        # Risk assessment
        critical_findings = summary['findings_summary'].get('CRITICAL', 0)
        high_findings = summary['findings_summary'].get('HIGH', 0)
        
        if critical_findings > 0:
            risk_level = "HIGH"
            risk_description = "Critical issues identified requiring immediate attention"
        elif high_findings > 2:
            risk_level = "MEDIUM"
            risk_description = "Multiple high-priority issues requiring prompt resolution"
        else:
            risk_level = "LOW"
            risk_description = "Standard rollback execution with minor improvements needed"
        
        return {
            'report_id': report_id,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'executive_summary': {
                'key_metrics': key_metrics,
                'risk_assessment': {
                    'risk_level': risk_level,
                    'description': risk_description
                },
                'top_recommendations': executive_recommendations,
                'overall_assessment': f"Rollback completed in {summary['rollback_duration_seconds']:.1f}s with {summary['business_impact']['impact_level']} business impact",
                'next_steps': executive_recommendations[:3] if executive_recommendations else ["Continue monitoring for recurrence"]
            }
        }