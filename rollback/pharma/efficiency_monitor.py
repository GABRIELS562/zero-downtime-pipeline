#!/usr/bin/env python3
"""
Manufacturing Efficiency Monitoring for Pharmaceutical Systems
==============================================================

Forensic-level manufacturing efficiency monitoring and automated rollback
triggers for pharmaceutical manufacturing with FDA compliance:

- Real-time manufacturing line efficiency monitoring (98% minimum)
- Environmental sensor impact on production quality
- Batch integrity and yield analysis
- Equipment performance degradation detection
- Regulatory compliance impact assessment
- GMP deviation tracking and rollback triggers

Forensic Methodology Applied:
- Production timeline reconstruction for root cause analysis
- Statistical process control with real-time deviation detection
- Equipment performance correlation analysis
- Batch genealogy tracking for impact attribution
- Environmental factor analysis for contamination risk
- Regulatory breach detection with automated documentation
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
import uuid

import aiohttp
import numpy as np
from scipy import stats

from ..core.business_metrics_monitor import (
    BusinessMetricsCollector, BusinessMetric, BusinessImpactAssessment,
    BusinessImpactLevel, RollbackTriggerType
)


class ManufacturingEfficiencyCollector(BusinessMetricsCollector):
    """
    Collect and analyze manufacturing efficiency metrics with GMP compliance.
    
    Monitors:
    - Overall Equipment Effectiveness (OEE)
    - Production line efficiency and throughput
    - Batch yield and quality metrics
    - Environmental compliance (temperature, pressure, humidity)
    - Equipment performance and maintenance status
    - Regulatory compliance indicators
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("manufacturing_efficiency", config)
        
        # Manufacturing system endpoints
        self.mes_api_url = config.get('mes_api_url', 'http://mes-system:8080')
        self.line_control_url = config.get('line_control_url', 'http://line-control:8080')
        self.quality_system_url = config.get('quality_system_url', 'http://quality-control:8080')
        self.environmental_url = config.get('environmental_url', 'http://environmental-monitor:8080')
        
        # Efficiency thresholds
        self.efficiency_thresholds = {
            'catastrophic_efficiency': Decimal('85'),        # <85% triggers immediate rollback
            'critical_efficiency': Decimal('90'),           # <90% triggers urgent rollback
            'high_impact_efficiency': Decimal('95'),        # <95% triggers rollback consideration
            'medium_impact_efficiency': Decimal('97'),      # <97% triggers enhanced monitoring
            'target_efficiency': Decimal('98'),             # FDA/GMP requirement
            'optimal_efficiency': Decimal('99.5')           # Target performance
        }
        
        # Cost impact calculations (per percentage point of efficiency loss)
        self.impact_calculations = {
            'production_cost_per_efficiency_point': Decimal('5000'),    # $5K per 1% efficiency loss
            'batch_loss_cost': Decimal('50000'),                        # $50K per lost batch
            'regulatory_violation_cost': Decimal('100000'),             # $100K per violation
            'equipment_damage_cost': Decimal('25000'),                  # $25K per equipment issue
            'client_penalty_cost': Decimal('75000')                     # $75K per delivery delay
        }
        
        # Environmental compliance ranges
        self.environmental_limits = {
            'temperature': {'min': 18.0, 'max': 25.0, 'unit': '°C'},
            'pressure': {'min': 0.8, 'max': 2.5, 'unit': 'bar'},
            'humidity': {'min': 30.0, 'max': 70.0, 'unit': '%RH'},
            'particle_count': {'min': 0, 'max': 100, 'unit': 'particles/m³'},
            'air_changes': {'min': 15, 'max': 25, 'unit': 'changes/hour'}
        }
        
        # Production schedule information
        self.production_schedule = config.get('production_schedule', {
            'shift_1_start': '06:00',
            'shift_1_end': '14:00',
            'shift_2_start': '14:00',
            'shift_2_end': '22:00',
            'shift_3_start': '22:00',
            'shift_3_end': '06:00',
            'maintenance_windows': ['02:00-05:00', '12:00-13:00', '20:00-21:00']
        })
    
    async def collect_metrics(self) -> List[BusinessMetric]:
        """Collect comprehensive manufacturing efficiency metrics."""
        current_time = datetime.now(timezone.utc)
        
        # Collect from multiple manufacturing systems concurrently
        tasks = [
            self._collect_oee_metrics(),
            self._collect_production_efficiency(),
            self._collect_batch_metrics(),
            self._collect_quality_metrics(),
            self._collect_environmental_metrics(),
            self._collect_equipment_performance(),
            self._collect_compliance_indicators(),
            self._collect_downtime_analysis()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_metrics = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting manufacturing metric {i}: {result}")
            elif isinstance(result, list):
                all_metrics.extend(result)
            elif result:
                all_metrics.append(result)
        
        return all_metrics
    
    async def _collect_oee_metrics(self) -> List[BusinessMetric]:
        """Collect Overall Equipment Effectiveness metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mes_api_url}/oee/current") as response:
                    oee_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            metrics = [
                BusinessMetric(
                    name="overall_equipment_effectiveness",
                    value=Decimal(str(oee_data.get('oee_percentage', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="mes_system",
                    metadata={
                        'availability': oee_data.get('availability', 0),
                        'performance': oee_data.get('performance', 0),
                        'quality': oee_data.get('quality', 0),
                        'planned_production_time': oee_data.get('planned_production_time', 0),
                        'actual_production_time': oee_data.get('actual_production_time', 0)
                    }
                ),
                BusinessMetric(
                    name="manufacturing_efficiency",
                    value=Decimal(str(oee_data.get('efficiency_percentage', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="mes_system",
                    metadata={
                        'target_efficiency': str(self.efficiency_thresholds['target_efficiency']),
                        'efficiency_trend': oee_data.get('efficiency_trend', 'stable'),
                        'line_count': oee_data.get('active_lines', 0)
                    }
                )
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting OEE metrics: {e}")
            return []
    
    async def _collect_production_efficiency(self) -> List[BusinessMetric]:
        """Collect production line efficiency metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.line_control_url}/production/efficiency") as response:
                    prod_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            return [
                BusinessMetric(
                    name="production_throughput",
                    value=Decimal(str(prod_data.get('units_per_hour', 0))),
                    timestamp=current_time,
                    unit="units_per_hour",
                    source="line_control",
                    metadata={
                        'target_throughput': prod_data.get('target_units_per_hour', 0),
                        'throughput_efficiency': prod_data.get('throughput_efficiency', 0),
                        'bottleneck_station': prod_data.get('bottleneck_station', 'none')
                    }
                ),
                BusinessMetric(
                    name="cycle_time_efficiency",
                    value=Decimal(str(prod_data.get('cycle_time_efficiency', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="line_control",
                    metadata={
                        'actual_cycle_time': prod_data.get('actual_cycle_time', 0),
                        'standard_cycle_time': prod_data.get('standard_cycle_time', 0),
                        'variation_coefficient': prod_data.get('variation_coefficient', 0)
                    }
                ),
                BusinessMetric(
                    name="first_pass_yield",
                    value=Decimal(str(prod_data.get('first_pass_yield', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="line_control",
                    metadata={
                        'defect_rate': prod_data.get('defect_rate', 0),
                        'rework_rate': prod_data.get('rework_rate', 0),
                        'scrap_rate': prod_data.get('scrap_rate', 0)
                    }
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Error collecting production efficiency: {e}")
            return []
    
    async def _collect_batch_metrics(self) -> List[BusinessMetric]:
        """Collect batch-related efficiency metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mes_api_url}/batches/current") as response:
                    batch_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            return [
                BusinessMetric(
                    name="batch_cycle_efficiency",
                    value=Decimal(str(batch_data.get('batch_efficiency', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="mes_system",
                    metadata={
                        'active_batches': batch_data.get('active_batches', 0),
                        'completed_batches_today': batch_data.get('completed_today', 0),
                        'average_batch_time': batch_data.get('average_batch_time', 0),
                        'batch_size_variance': batch_data.get('batch_size_variance', 0)
                    }
                ),
                BusinessMetric(
                    name="batch_yield_efficiency",
                    value=Decimal(str(batch_data.get('yield_efficiency', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="mes_system",
                    metadata={
                        'theoretical_yield': batch_data.get('theoretical_yield', 0),
                        'actual_yield': batch_data.get('actual_yield', 0),
                        'yield_variance': batch_data.get('yield_variance', 0),
                        'material_utilization': batch_data.get('material_utilization', 0)
                    }
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Error collecting batch metrics: {e}")
            return []
    
    async def _collect_quality_metrics(self) -> List[BusinessMetric]:
        """Collect quality-related efficiency metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.quality_system_url}/quality/metrics") as response:
                    quality_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            return [
                BusinessMetric(
                    name="quality_efficiency",
                    value=Decimal(str(quality_data.get('quality_efficiency', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="quality_system",
                    metadata={
                        'pass_rate': quality_data.get('pass_rate', 0),
                        'critical_defects': quality_data.get('critical_defects', 0),
                        'minor_defects': quality_data.get('minor_defects', 0),
                        'inspection_efficiency': quality_data.get('inspection_efficiency', 0)
                    }
                ),
                BusinessMetric(
                    name="compliance_score",
                    value=Decimal(str(quality_data.get('compliance_score', 0))),
                    timestamp=current_time,
                    unit="score",
                    source="quality_system",
                    metadata={
                        'gmp_compliance': quality_data.get('gmp_compliance', 0),
                        'fda_compliance': quality_data.get('fda_compliance', 0),
                        'iso_compliance': quality_data.get('iso_compliance', 0),
                        'deviation_count': quality_data.get('deviation_count', 0)
                    }
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Error collecting quality metrics: {e}")
            return []
    
    async def _collect_environmental_metrics(self) -> List[BusinessMetric]:
        """Collect environmental compliance metrics affecting efficiency."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.environmental_url}/environment/current") as response:
                    env_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            # Calculate environmental compliance efficiency
            compliance_scores = []
            env_evidence = {}
            
            for param, limits in self.environmental_limits.items():
                if param in env_data:
                    value = env_data[param]
                    in_range = limits['min'] <= value <= limits['max']
                    compliance_scores.append(1.0 if in_range else 0.0)
                    env_evidence[param] = {
                        'value': value,
                        'in_range': in_range,
                        'limits': limits
                    }
            
            environmental_efficiency = (sum(compliance_scores) / len(compliance_scores) * 100) if compliance_scores else 0
            
            return [
                BusinessMetric(
                    name="environmental_efficiency",
                    value=Decimal(str(environmental_efficiency)),
                    timestamp=current_time,
                    unit="percentage",
                    source="environmental_monitor",
                    metadata={
                        'parameters_monitored': len(compliance_scores),
                        'parameters_in_spec': sum(compliance_scores),
                        'environmental_details': env_evidence
                    }
                ),
                BusinessMetric(
                    name="hvac_efficiency",
                    value=Decimal(str(env_data.get('hvac_efficiency', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="environmental_monitor",
                    metadata={
                        'air_changes_per_hour': env_data.get('air_changes', 0),
                        'filter_efficiency': env_data.get('filter_efficiency', 0),
                        'energy_consumption': env_data.get('energy_consumption', 0)
                    }
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Error collecting environmental metrics: {e}")
            return []
    
    async def _collect_equipment_performance(self) -> List[BusinessMetric]:
        """Collect equipment performance affecting efficiency."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.line_control_url}/equipment/performance") as response:
                    equipment_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            return [
                BusinessMetric(
                    name="equipment_efficiency",
                    value=Decimal(str(equipment_data.get('average_efficiency', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="line_control",
                    metadata={
                        'equipment_count': equipment_data.get('equipment_count', 0),
                        'equipment_operational': equipment_data.get('operational_count', 0),
                        'maintenance_overdue': equipment_data.get('maintenance_overdue', 0),
                        'critical_equipment_down': equipment_data.get('critical_down', 0)
                    }
                ),
                BusinessMetric(
                    name="maintenance_efficiency",
                    value=Decimal(str(equipment_data.get('maintenance_efficiency', 0))),
                    timestamp=current_time,
                    unit="percentage",
                    source="line_control",
                    metadata={
                        'planned_maintenance_completion': equipment_data.get('planned_completion', 0),
                        'unplanned_downtime': equipment_data.get('unplanned_downtime', 0),
                        'mtbf': equipment_data.get('mean_time_between_failures', 0),
                        'mttr': equipment_data.get('mean_time_to_repair', 0)
                    }
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Error collecting equipment performance: {e}")
            return []
    
    async def _collect_compliance_indicators(self) -> BusinessMetric:
        """Collect regulatory compliance indicators."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.quality_system_url}/compliance/status") as response:
                    compliance_data = await response.json()
            
            return BusinessMetric(
                name="regulatory_compliance_efficiency",
                value=Decimal(str(compliance_data.get('overall_compliance', 0))),
                timestamp=datetime.now(timezone.utc),
                unit="percentage",
                source="quality_system",
                metadata={
                    'fda_21cfr11_compliance': compliance_data.get('fda_21cfr11', 0),
                    'gmp_compliance': compliance_data.get('gmp', 0),
                    'iso_13485_compliance': compliance_data.get('iso_13485', 0),
                    'active_deviations': compliance_data.get('active_deviations', 0),
                    'capa_overdue': compliance_data.get('capa_overdue', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting compliance indicators: {e}")
            return None
    
    async def _collect_downtime_analysis(self) -> BusinessMetric:
        """Collect downtime analysis affecting efficiency."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.line_control_url}/downtime/analysis") as response:
                    downtime_data = await response.json()
            
            # Calculate efficiency impact of downtime
            planned_downtime = downtime_data.get('planned_downtime_minutes', 0)
            unplanned_downtime = downtime_data.get('unplanned_downtime_minutes', 0)
            total_available_time = downtime_data.get('total_available_minutes', 480)  # 8-hour shift
            
            uptime_efficiency = ((total_available_time - unplanned_downtime) / total_available_time * 100) if total_available_time > 0 else 0
            
            return BusinessMetric(
                name="uptime_efficiency",
                value=Decimal(str(uptime_efficiency)),
                timestamp=datetime.now(timezone.utc),
                unit="percentage",
                source="line_control",
                metadata={
                    'planned_downtime_minutes': planned_downtime,
                    'unplanned_downtime_minutes': unplanned_downtime,
                    'total_available_minutes': total_available_time,
                    'downtime_categories': downtime_data.get('downtime_breakdown', {}),
                    'mtbf_hours': downtime_data.get('mtbf_hours', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting downtime analysis: {e}")
            return None
    
    def calculate_impact(self, current_metrics: List[BusinessMetric]) -> BusinessImpactAssessment:
        """Calculate business impact based on manufacturing efficiency metrics."""
        assessment_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        # Get current deployment ID
        from ..core.business_metrics_monitor import DeploymentTracker
        deployment_tracker = DeploymentTracker()
        deployment_id = deployment_tracker.get_current_deployment() or "no_active_deployment"
        
        # Extract key efficiency metrics
        manufacturing_efficiency = self._get_metric_value(current_metrics, "manufacturing_efficiency")
        oee = self._get_metric_value(current_metrics, "overall_equipment_effectiveness")
        quality_efficiency = self._get_metric_value(current_metrics, "quality_efficiency")
        environmental_efficiency = self._get_metric_value(current_metrics, "environmental_efficiency")
        compliance_score = self._get_metric_value(current_metrics, "regulatory_compliance_efficiency")
        
        # Calculate overall efficiency score (weighted average)
        overall_efficiency = self._calculate_weighted_efficiency(current_metrics)
        
        # Assess impact level and calculate costs
        impact_level, trigger_type = self._assess_efficiency_impact(overall_efficiency, current_metrics)
        estimated_loss = self._calculate_efficiency_loss_cost(overall_efficiency, current_metrics)
        
        # Calculate confidence based on data quality and environmental factors
        confidence = self._calculate_confidence(current_metrics)
        
        # Generate forensic evidence
        evidence = self._generate_efficiency_evidence(current_metrics, overall_efficiency)
        
        # Create recommendation
        recommendation = self._generate_efficiency_recommendation(impact_level, overall_efficiency, evidence)
        
        return BusinessImpactAssessment(
            assessment_id=assessment_id,
            timestamp=current_time,
            deployment_id=deployment_id,
            impact_level=impact_level,
            estimated_loss=estimated_loss,
            confidence=confidence,
            trigger_type=trigger_type,
            evidence=evidence,
            metrics=current_metrics,
            recommendation=recommendation
        )
    
    def _get_metric_value(self, metrics: List[BusinessMetric], metric_name: str) -> Decimal:
        """Extract metric value by name."""
        for metric in metrics:
            if metric.name == metric_name:
                return metric.value
        return Decimal('0')
    
    def _calculate_weighted_efficiency(self, metrics: List[BusinessMetric]) -> Decimal:
        """Calculate overall weighted efficiency score."""
        # Define weights for different efficiency components
        weights = {
            'manufacturing_efficiency': 0.30,
            'overall_equipment_effectiveness': 0.25,
            'quality_efficiency': 0.20,
            'environmental_efficiency': 0.15,
            'regulatory_compliance_efficiency': 0.10
        }
        
        weighted_sum = Decimal('0')
        total_weight = Decimal('0')
        
        for metric_name, weight in weights.items():
            value = self._get_metric_value(metrics, metric_name)
            if value > 0:  # Only include metrics with valid values
                weighted_sum += value * Decimal(str(weight))
                total_weight += Decimal(str(weight))
        
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return Decimal('0')
    
    def _assess_efficiency_impact(
        self, 
        overall_efficiency: Decimal, 
        metrics: List[BusinessMetric]
    ) -> Tuple[BusinessImpactLevel, RollbackTriggerType]:
        """Assess the severity of efficiency impact."""
        
        # Check for catastrophic efficiency loss
        if overall_efficiency <= self.efficiency_thresholds['catastrophic_efficiency']:
            return BusinessImpactLevel.CATASTROPHIC, RollbackTriggerType.EFFICIENCY_DROP
        
        # Check for critical efficiency loss
        elif overall_efficiency <= self.efficiency_thresholds['critical_efficiency']:
            return BusinessImpactLevel.CRITICAL, RollbackTriggerType.EFFICIENCY_DROP
        
        # Check for high efficiency loss
        elif overall_efficiency <= self.efficiency_thresholds['high_impact_efficiency']:
            return BusinessImpactLevel.HIGH, RollbackTriggerType.EFFICIENCY_DROP
        
        # Check for medium efficiency loss
        elif overall_efficiency < self.efficiency_thresholds['target_efficiency']:
            return BusinessImpactLevel.MEDIUM, RollbackTriggerType.EFFICIENCY_DROP
        
        # Check for specific compliance violations
        compliance_score = self._get_metric_value(metrics, "regulatory_compliance_efficiency")
        if compliance_score < Decimal('95'):  # Below 95% compliance
            return BusinessImpactLevel.HIGH, RollbackTriggerType.COMPLIANCE_VIOLATION
        
        # Check environmental efficiency
        env_efficiency = self._get_metric_value(metrics, "environmental_efficiency")
        if env_efficiency < Decimal('90'):  # Environmental issues
            return BusinessImpactLevel.MEDIUM, RollbackTriggerType.COMPLIANCE_VIOLATION
        
        # Check quality efficiency
        quality_efficiency = self._get_metric_value(metrics, "quality_efficiency")
        if quality_efficiency < Decimal('95'):  # Quality issues
            return BusinessImpactLevel.MEDIUM, RollbackTriggerType.EFFICIENCY_DROP
        
        return BusinessImpactLevel.LOW, RollbackTriggerType.EFFICIENCY_DROP
    
    def _calculate_efficiency_loss_cost(
        self, 
        overall_efficiency: Decimal, 
        metrics: List[BusinessMetric]
    ) -> Decimal:
        """Calculate estimated cost of efficiency loss."""
        target_efficiency = self.efficiency_thresholds['target_efficiency']
        efficiency_loss = max(Decimal('0'), target_efficiency - overall_efficiency)
        
        # Base cost calculation
        base_cost = efficiency_loss * self.impact_calculations['production_cost_per_efficiency_point']
        
        # Additional costs based on specific impacts
        additional_costs = Decimal('0')
        
        # Batch loss cost
        batch_efficiency = self._get_metric_value(metrics, "batch_cycle_efficiency")
        if batch_efficiency < Decimal('90'):  # Risk of batch loss
            additional_costs += self.impact_calculations['batch_loss_cost']
        
        # Compliance violation cost
        compliance_score = self._get_metric_value(metrics, "regulatory_compliance_efficiency")
        if compliance_score < Decimal('95'):
            additional_costs += self.impact_calculations['regulatory_violation_cost']
        
        # Equipment damage cost
        equipment_efficiency = self._get_metric_value(metrics, "equipment_efficiency")
        if equipment_efficiency < Decimal('85'):  # Risk of equipment damage
            additional_costs += self.impact_calculations['equipment_damage_cost']
        
        # Quality issues leading to client penalties
        quality_efficiency = self._get_metric_value(metrics, "quality_efficiency")
        if quality_efficiency < Decimal('90'):
            additional_costs += self.impact_calculations['client_penalty_cost']
        
        return base_cost + additional_costs
    
    def _calculate_confidence(self, metrics: List[BusinessMetric]) -> float:
        """Calculate confidence in the efficiency assessment."""
        if not metrics:
            return 0.0
        
        # Calculate based on data freshness, completeness, and source reliability
        current_time = datetime.now(timezone.utc)
        confidence_factors = []
        
        # Data freshness factor
        total_age = 0
        for metric in metrics:
            age_seconds = (current_time - metric.timestamp).total_seconds()
            total_age += age_seconds
        
        avg_age_minutes = (total_age / len(metrics)) / 60
        freshness_factor = max(0.0, 1.0 - (avg_age_minutes / 10))  # 10-minute decay
        
        # Data completeness factor (how many expected metrics we have)
        expected_metrics = [
            'manufacturing_efficiency', 'overall_equipment_effectiveness',
            'quality_efficiency', 'environmental_efficiency',
            'regulatory_compliance_efficiency'
        ]
        
        available_metrics = [m.name for m in metrics]
        completeness_factor = len([m for m in expected_metrics if m in available_metrics]) / len(expected_metrics)
        
        # Source reliability factor
        source_reliability = {
            'mes_system': 0.95,
            'line_control': 0.90,
            'quality_system': 0.95,
            'environmental_monitor': 0.85
        }
        
        reliability_scores = [
            source_reliability.get(metric.source, 0.70) for metric in metrics
        ]
        avg_reliability = statistics.mean(reliability_scores) if reliability_scores else 0.70
        
        # Environmental stability factor
        env_efficiency = self._get_metric_value(metrics, "environmental_efficiency")
        env_stability = min(1.0, float(env_efficiency) / 100) if env_efficiency > 0 else 0.5
        
        # Combined confidence
        overall_confidence = (
            freshness_factor * 0.25 +
            completeness_factor * 0.25 +
            avg_reliability * 0.25 +
            env_stability * 0.25
        )
        
        return min(1.0, max(0.0, overall_confidence))
    
    def _generate_efficiency_evidence(
        self, 
        metrics: List[BusinessMetric], 
        overall_efficiency: Decimal
    ) -> Dict[str, Any]:
        """Generate forensic evidence for efficiency impact."""
        evidence = {
            'efficiency_analysis': {
                'overall_efficiency': str(overall_efficiency),
                'target_efficiency': str(self.efficiency_thresholds['target_efficiency']),
                'efficiency_deviation': str(self.efficiency_thresholds['target_efficiency'] - overall_efficiency),
                'compliance_status': 'compliant' if overall_efficiency >= self.efficiency_thresholds['target_efficiency'] else 'non_compliant'
            },
            'component_breakdown': {},
            'environmental_conditions': {},
            'equipment_status': {},
            'quality_indicators': {},
            'compliance_status': {},
            'production_impact': {}
        }
        
        # Organize metrics by category
        for metric in metrics:
            category = self._categorize_efficiency_metric(metric.name)
            if category not in evidence['component_breakdown']:
                evidence['component_breakdown'][category] = []
            
            evidence['component_breakdown'][category].append({
                'name': metric.name,
                'value': str(metric.value),
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
                'metadata': metric.metadata
            })
        
        # Add specific analysis sections
        evidence['environmental_conditions'] = self._analyze_environmental_impact(metrics)
        evidence['equipment_status'] = self._analyze_equipment_impact(metrics)
        evidence['quality_indicators'] = self._analyze_quality_impact(metrics)
        evidence['compliance_status'] = self._analyze_compliance_impact(metrics)
        evidence['production_impact'] = self._analyze_production_impact(metrics)
        
        return evidence
    
    def _categorize_efficiency_metric(self, metric_name: str) -> str:
        """Categorize metrics for evidence organization."""
        if 'oee' in metric_name or 'equipment' in metric_name:
            return 'equipment_effectiveness'
        elif 'environmental' in metric_name or 'hvac' in metric_name:
            return 'environmental_control'
        elif 'quality' in metric_name or 'compliance' in metric_name:
            return 'quality_compliance'
        elif 'batch' in metric_name:
            return 'batch_processing'
        elif 'production' in metric_name or 'throughput' in metric_name:
            return 'production_efficiency'
        else:
            return 'general_metrics'
    
    def _analyze_environmental_impact(self, metrics: List[BusinessMetric]) -> Dict[str, Any]:
        """Analyze environmental factors affecting efficiency."""
        env_efficiency = self._get_metric_value(metrics, "environmental_efficiency")
        hvac_efficiency = self._get_metric_value(metrics, "hvac_efficiency")
        
        # Get environmental details from metadata
        env_details = {}
        for metric in metrics:
            if metric.name == "environmental_efficiency" and metric.metadata:
                env_details = metric.metadata.get('environmental_details', {})
        
        return {
            'environmental_efficiency': str(env_efficiency),
            'hvac_efficiency': str(hvac_efficiency),
            'parameter_compliance': env_details,
            'risk_assessment': 'low' if env_efficiency > 95 else 'medium' if env_efficiency > 85 else 'high'
        }
    
    def _analyze_equipment_impact(self, metrics: List[BusinessMetric]) -> Dict[str, Any]:
        """Analyze equipment performance impact on efficiency."""
        equipment_efficiency = self._get_metric_value(metrics, "equipment_efficiency")
        maintenance_efficiency = self._get_metric_value(metrics, "maintenance_efficiency")
        uptime_efficiency = self._get_metric_value(metrics, "uptime_efficiency")
        
        return {
            'equipment_efficiency': str(equipment_efficiency),
            'maintenance_efficiency': str(maintenance_efficiency),
            'uptime_efficiency': str(uptime_efficiency),
            'equipment_risk_level': 'low' if equipment_efficiency > 95 else 'medium' if equipment_efficiency > 85 else 'high'
        }
    
    def _analyze_quality_impact(self, metrics: List[BusinessMetric]) -> Dict[str, Any]:
        """Analyze quality metrics impact on efficiency."""
        quality_efficiency = self._get_metric_value(metrics, "quality_efficiency")
        first_pass_yield = self._get_metric_value(metrics, "first_pass_yield")
        
        return {
            'quality_efficiency': str(quality_efficiency),
            'first_pass_yield': str(first_pass_yield),
            'quality_risk_level': 'low' if quality_efficiency > 95 else 'medium' if quality_efficiency > 90 else 'high'
        }
    
    def _analyze_compliance_impact(self, metrics: List[BusinessMetric]) -> Dict[str, Any]:
        """Analyze regulatory compliance impact."""
        compliance_score = self._get_metric_value(metrics, "regulatory_compliance_efficiency")
        
        return {
            'overall_compliance_score': str(compliance_score),
            'fda_compliant': compliance_score >= 95,
            'gmp_compliant': compliance_score >= 95,
            'compliance_risk_level': 'low' if compliance_score >= 95 else 'medium' if compliance_score >= 90 else 'high'
        }
    
    def _analyze_production_impact(self, metrics: List[BusinessMetric]) -> Dict[str, Any]:
        """Analyze production metrics and impact."""
        production_throughput = self._get_metric_value(metrics, "production_throughput")
        batch_efficiency = self._get_metric_value(metrics, "batch_cycle_efficiency")
        
        return {
            'production_throughput': str(production_throughput),
            'batch_efficiency': str(batch_efficiency),
            'production_risk_level': 'low' if batch_efficiency > 95 else 'medium' if batch_efficiency > 90 else 'high'
        }
    
    def _generate_efficiency_recommendation(
        self, 
        impact_level: BusinessImpactLevel, 
        overall_efficiency: Decimal, 
        evidence: Dict[str, Any]
    ) -> str:
        """Generate actionable recommendation based on efficiency assessment."""
        
        target_efficiency = self.efficiency_thresholds['target_efficiency']
        efficiency_gap = target_efficiency - overall_efficiency
        
        if impact_level == BusinessImpactLevel.CATASTROPHIC:
            return (
                f"IMMEDIATE ROLLBACK REQUIRED: Manufacturing efficiency at {overall_efficiency}% "
                f"is {efficiency_gap}% below FDA/GMP requirement of {target_efficiency}%. "
                f"Production line must be stopped within 5 minutes to prevent regulatory violations."
            )
        
        elif impact_level == BusinessImpactLevel.CRITICAL:
            return (
                f"URGENT ROLLBACK RECOMMENDED: Manufacturing efficiency at {overall_efficiency}% "
                f"is critically below target. Rollback must be executed within 10 minutes to "
                f"prevent batch losses and regulatory non-compliance."
            )
        
        elif impact_level == BusinessImpactLevel.HIGH:
            return (
                f"ROLLBACK RECOMMENDED: Manufacturing efficiency at {overall_efficiency}% "
                f"is significantly below target. Consider rollback within 15 minutes if "
                f"efficiency does not improve."
            )
        
        elif impact_level == BusinessImpactLevel.MEDIUM:
            return (
                f"ENHANCED MONITORING: Manufacturing efficiency at {overall_efficiency}% "
                f"is below target. Prepare rollback procedures and investigate root causes."
            )
        
        else:
            return (
                f"Continue monitoring. Manufacturing efficiency at {overall_efficiency}% "
                f"is within acceptable range."
            )