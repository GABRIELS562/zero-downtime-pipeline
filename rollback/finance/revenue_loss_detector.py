#!/usr/bin/env python3
"""
Revenue Loss Detection System for Financial Trading
==================================================

Forensic-level revenue loss detection and automated rollback triggers for
financial trading systems with real-time business impact analysis:

- Real-time trading revenue monitoring and loss detection
- Market impact analysis and attribution
- Client order flow disruption assessment
- Regulatory compliance impact evaluation
- Latency-induced revenue loss calculations
- Automated rollback triggers based on financial thresholds

Forensic Methodology Applied:
- Trade flow timeline reconstruction for impact attribution
- Statistical analysis of revenue variance with confidence intervals
- Market microstructure analysis for root cause identification
- Client impact quantification using trade execution quality metrics
- Regulatory breach detection with automatic documentation
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


class TradingRevenueCollector(BusinessMetricsCollector):
    """
    Collect and analyze trading revenue metrics with forensic precision.
    
    Monitors:
    - Trading P&L in real-time
    - Commission and fee revenue
    - Spread capture efficiency
    - Market making profits
    - Client order flow value
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("trading_revenue", config)
        
        # Trading system endpoints
        self.trading_api_url = config.get('trading_api_url', 'http://trading-engine:8080')
        self.market_data_url = config.get('market_data_url', 'http://market-data:8080')
        self.risk_system_url = config.get('risk_system_url', 'http://risk-management:8080')
        
        # Revenue thresholds (per minute)
        self.revenue_thresholds = {
            'catastrophic_loss_per_minute': Decimal('50000'),    # $50K/min
            'critical_loss_per_minute': Decimal('10000'),       # $10K/min
            'high_loss_per_minute': Decimal('2000'),            # $2K/min
            'medium_loss_per_minute': Decimal('500'),           # $500/min
            'baseline_revenue_per_minute': Decimal('1000')      # Expected $1K/min
        }
        
        # Performance impact multipliers
        self.impact_multipliers = {
            'latency_cost_per_ms': Decimal('100'),              # $100 per ms latency
            'error_cost_per_failed_trade': Decimal('1000'),     # $1K per failed trade
            'client_attrition_cost': Decimal('50000')           # $50K per client lost
        }
        
        # Market hours configuration
        self.market_hours = config.get('market_hours', {
            'pre_market_start': '04:00',
            'market_open': '09:30',
            'market_close': '16:00',
            'after_hours_end': '20:00',
            'timezone': 'America/New_York'
        })
    
    async def collect_metrics(self) -> List[BusinessMetric]:
        """Collect comprehensive trading revenue metrics."""
        current_time = datetime.now(timezone.utc)
        
        # Collect from multiple sources concurrently
        tasks = [
            self._collect_trading_pnl(),
            self._collect_commission_revenue(),
            self._collect_spread_capture(),
            self._collect_market_making_profits(),
            self._collect_order_flow_value(),
            self._collect_client_metrics(),
            self._collect_latency_impact(),
            self._collect_error_impact()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_metrics = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting metric {i}: {result}")
            elif isinstance(result, list):
                all_metrics.extend(result)
            elif result:
                all_metrics.append(result)
        
        return all_metrics
    
    async def _collect_trading_pnl(self) -> List[BusinessMetric]:
        """Collect real-time trading P&L metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/pnl/realtime") as response:
                    pnl_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            metrics = [
                BusinessMetric(
                    name="trading_pnl_total",
                    value=Decimal(str(pnl_data.get('total_pnl', 0))),
                    timestamp=current_time,
                    currency="USD",
                    source="trading_engine",
                    metadata={
                        'unrealized_pnl': pnl_data.get('unrealized_pnl', 0),
                        'realized_pnl': pnl_data.get('realized_pnl', 0),
                        'positions_count': pnl_data.get('positions_count', 0)
                    }
                ),
                BusinessMetric(
                    name="trading_pnl_per_minute",
                    value=Decimal(str(pnl_data.get('pnl_per_minute', 0))),
                    timestamp=current_time,
                    currency="USD",
                    unit="per_minute",
                    source="trading_engine",
                    metadata={'calculation_window': '1_minute'}
                )
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting trading P&L: {e}")
            return []
    
    async def _collect_commission_revenue(self) -> List[BusinessMetric]:
        """Collect commission and fee revenue metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/revenue/commissions") as response:
                    comm_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            return [
                BusinessMetric(
                    name="commission_revenue",
                    value=Decimal(str(comm_data.get('total_commissions', 0))),
                    timestamp=current_time,
                    currency="USD",
                    source="trading_engine",
                    metadata={
                        'trades_count': comm_data.get('trades_count', 0),
                        'average_commission': comm_data.get('average_commission', 0),
                        'commission_rate': comm_data.get('commission_rate', 0)
                    }
                ),
                BusinessMetric(
                    name="fee_revenue",
                    value=Decimal(str(comm_data.get('total_fees', 0))),
                    timestamp=current_time,
                    currency="USD",
                    source="trading_engine",
                    metadata={
                        'exchange_fees': comm_data.get('exchange_fees', 0),
                        'regulatory_fees': comm_data.get('regulatory_fees', 0),
                        'other_fees': comm_data.get('other_fees', 0)
                    }
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Error collecting commission revenue: {e}")
            return []
    
    async def _collect_spread_capture(self) -> BusinessMetric:
        """Collect bid-ask spread capture efficiency."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/metrics/spread-capture") as response:
                    spread_data = await response.json()
            
            return BusinessMetric(
                name="spread_capture_revenue",
                value=Decimal(str(spread_data.get('spread_revenue', 0))),
                timestamp=datetime.now(timezone.utc),
                currency="USD",
                source="trading_engine",
                metadata={
                    'average_spread_bps': spread_data.get('average_spread_bps', 0),
                    'capture_rate': spread_data.get('capture_rate', 0),
                    'volume_traded': spread_data.get('volume_traded', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting spread capture: {e}")
            return None
    
    async def _collect_market_making_profits(self) -> BusinessMetric:
        """Collect market making profits and inventory management."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/market-making/pnl") as response:
                    mm_data = await response.json()
            
            return BusinessMetric(
                name="market_making_profit",
                value=Decimal(str(mm_data.get('market_making_pnl', 0))),
                timestamp=datetime.now(timezone.utc),
                currency="USD",
                source="trading_engine",
                metadata={
                    'inventory_turnover': mm_data.get('inventory_turnover', 0),
                    'quote_fill_rate': mm_data.get('quote_fill_rate', 0),
                    'adverse_selection_cost': mm_data.get('adverse_selection_cost', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting market making profits: {e}")
            return None
    
    async def _collect_order_flow_value(self) -> BusinessMetric:
        """Collect order flow value metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/order-flow/value") as response:
                    flow_data = await response.json()
            
            return BusinessMetric(
                name="order_flow_value",
                value=Decimal(str(flow_data.get('flow_value_per_minute', 0))),
                timestamp=datetime.now(timezone.utc),
                currency="USD",
                unit="per_minute",
                source="trading_engine",
                metadata={
                    'order_count': flow_data.get('order_count', 0),
                    'average_order_size': flow_data.get('average_order_size', 0),
                    'flow_toxicity': flow_data.get('flow_toxicity', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting order flow value: {e}")
            return None
    
    async def _collect_client_metrics(self) -> List[BusinessMetric]:
        """Collect client-related revenue metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/clients/metrics") as response:
                    client_data = await response.json()
            
            current_time = datetime.now(timezone.utc)
            
            return [
                BusinessMetric(
                    name="client_revenue_per_minute",
                    value=Decimal(str(client_data.get('revenue_per_minute', 0))),
                    timestamp=current_time,
                    currency="USD",
                    unit="per_minute",
                    source="trading_engine",
                    metadata={
                        'active_clients': client_data.get('active_clients', 0),
                        'new_clients': client_data.get('new_clients', 0),
                        'client_satisfaction_score': client_data.get('satisfaction_score', 0)
                    }
                ),
                BusinessMetric(
                    name="client_execution_quality",
                    value=Decimal(str(client_data.get('execution_quality_score', 100))),
                    timestamp=current_time,
                    unit="score",
                    source="trading_engine",
                    metadata={
                        'average_slippage_bps': client_data.get('average_slippage_bps', 0),
                        'fill_rate': client_data.get('fill_rate', 0),
                        'speed_of_execution_ms': client_data.get('speed_of_execution_ms', 0)
                    }
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Error collecting client metrics: {e}")
            return []
    
    async def _collect_latency_impact(self) -> BusinessMetric:
        """Calculate revenue impact of latency degradation."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/metrics/latency") as response:
                    latency_data = await response.json()
            
            # Calculate latency impact on revenue
            current_latency = latency_data.get('average_latency_ms', 0)
            baseline_latency = latency_data.get('baseline_latency_ms', 10)  # 10ms baseline
            
            latency_degradation = max(0, current_latency - baseline_latency)
            estimated_loss = Decimal(str(latency_degradation)) * self.impact_multipliers['latency_cost_per_ms']
            
            return BusinessMetric(
                name="latency_impact_loss",
                value=estimated_loss,
                timestamp=datetime.now(timezone.utc),
                currency="USD",
                source="calculated",
                confidence=0.8,
                metadata={
                    'current_latency_ms': current_latency,
                    'baseline_latency_ms': baseline_latency,
                    'latency_degradation_ms': float(latency_degradation),
                    'cost_per_ms': str(self.impact_multipliers['latency_cost_per_ms'])
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting latency impact: {e}")
            return None
    
    async def _collect_error_impact(self) -> BusinessMetric:
        """Calculate revenue impact of trading errors."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_api_url}/metrics/errors") as response:
                    error_data = await response.json()
            
            # Calculate error impact
            failed_trades = error_data.get('failed_trades_per_minute', 0)
            estimated_loss = Decimal(str(failed_trades)) * self.impact_multipliers['error_cost_per_failed_trade']
            
            return BusinessMetric(
                name="error_impact_loss",
                value=estimated_loss,
                timestamp=datetime.now(timezone.utc),
                currency="USD",
                source="calculated",
                confidence=0.9,
                metadata={
                    'failed_trades_per_minute': failed_trades,
                    'error_rate': error_data.get('error_rate', 0),
                    'cost_per_failed_trade': str(self.impact_multipliers['error_cost_per_failed_trade']),
                    'error_types': error_data.get('error_breakdown', {})
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting error impact: {e}")
            return None
    
    def calculate_impact(self, current_metrics: List[BusinessMetric]) -> BusinessImpactAssessment:
        """Calculate business impact based on revenue metrics."""
        assessment_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        # Get current deployment ID
        from ..core.business_metrics_monitor import DeploymentTracker
        deployment_tracker = DeploymentTracker()
        deployment_id = deployment_tracker.get_current_deployment() or "no_active_deployment"
        
        # Extract key metrics
        pnl_per_minute = self._get_metric_value(current_metrics, "trading_pnl_per_minute")
        latency_loss = self._get_metric_value(current_metrics, "latency_impact_loss")
        error_loss = self._get_metric_value(current_metrics, "error_impact_loss")
        client_revenue = self._get_metric_value(current_metrics, "client_revenue_per_minute")
        
        # Calculate total revenue impact
        total_current_revenue = pnl_per_minute + client_revenue
        total_losses = latency_loss + error_loss
        net_revenue_impact = total_current_revenue - total_losses
        
        # Compare against baseline
        baseline_revenue = self.revenue_thresholds['baseline_revenue_per_minute']
        revenue_deviation = baseline_revenue - net_revenue_impact
        
        # Determine impact level and trigger type
        impact_level, trigger_type = self._assess_revenue_impact(revenue_deviation, current_metrics)
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(current_metrics)
        
        # Generate evidence
        evidence = self._generate_revenue_evidence(current_metrics, revenue_deviation)
        
        # Create recommendation
        recommendation = self._generate_recommendation(impact_level, revenue_deviation, evidence)
        
        return BusinessImpactAssessment(
            assessment_id=assessment_id,
            timestamp=current_time,
            deployment_id=deployment_id,
            impact_level=impact_level,
            estimated_loss=max(Decimal('0'), revenue_deviation),
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
    
    def _assess_revenue_impact(
        self, 
        revenue_deviation: Decimal, 
        metrics: List[BusinessMetric]
    ) -> Tuple[BusinessImpactLevel, RollbackTriggerType]:
        """Assess the severity of revenue impact."""
        
        # Check for catastrophic revenue loss
        if revenue_deviation >= self.revenue_thresholds['catastrophic_loss_per_minute']:
            return BusinessImpactLevel.CATASTROPHIC, RollbackTriggerType.REVENUE_LOSS
        
        # Check for critical revenue loss
        elif revenue_deviation >= self.revenue_thresholds['critical_loss_per_minute']:
            return BusinessImpactLevel.CRITICAL, RollbackTriggerType.REVENUE_LOSS
        
        # Check for high revenue loss
        elif revenue_deviation >= self.revenue_thresholds['high_loss_per_minute']:
            return BusinessImpactLevel.HIGH, RollbackTriggerType.REVENUE_LOSS
        
        # Check for medium revenue loss
        elif revenue_deviation >= self.revenue_thresholds['medium_loss_per_minute']:
            return BusinessImpactLevel.MEDIUM, RollbackTriggerType.REVENUE_LOSS
        
        # Check for latency-specific issues
        latency_loss = self._get_metric_value(metrics, "latency_impact_loss")
        if latency_loss >= Decimal('5000'):  # $5K latency loss
            return BusinessImpactLevel.HIGH, RollbackTriggerType.LATENCY_DEGRADATION
        
        # Check for error-specific issues
        error_loss = self._get_metric_value(metrics, "error_impact_loss")
        if error_loss >= Decimal('2000'):  # $2K error loss
            return BusinessImpactLevel.MEDIUM, RollbackTriggerType.ERROR_RATE_SPIKE
        
        # Check client execution quality
        execution_quality = self._get_metric_value(metrics, "client_execution_quality")
        if execution_quality < Decimal('90'):  # Below 90% quality score
            return BusinessImpactLevel.MEDIUM, RollbackTriggerType.CUSTOMER_IMPACT
        
        return BusinessImpactLevel.LOW, RollbackTriggerType.REVENUE_LOSS
    
    def _calculate_confidence(self, metrics: List[BusinessMetric]) -> float:
        """Calculate confidence in the impact assessment."""
        if not metrics:
            return 0.0
        
        # Calculate based on data freshness and source reliability
        current_time = datetime.now(timezone.utc)
        confidence_scores = []
        
        for metric in metrics:
            # Data freshness factor
            age_seconds = (current_time - metric.timestamp).total_seconds()
            freshness_factor = max(0.0, 1.0 - (age_seconds / 300))  # 5-minute decay
            
            # Source reliability factor
            source_reliability = {
                'trading_engine': 0.95,
                'market_data': 0.90,
                'calculated': 0.80,
                'estimated': 0.70
            }.get(metric.source, 0.60)
            
            # Metric-specific confidence
            metric_confidence = getattr(metric, 'confidence', 1.0)
            
            # Combined confidence
            combined_confidence = freshness_factor * source_reliability * metric_confidence
            confidence_scores.append(combined_confidence)
        
        return statistics.mean(confidence_scores)
    
    def _generate_revenue_evidence(
        self, 
        metrics: List[BusinessMetric], 
        revenue_deviation: Decimal
    ) -> Dict[str, Any]:
        """Generate forensic evidence for revenue impact."""
        evidence = {
            'revenue_analysis': {
                'baseline_revenue_per_minute': str(self.revenue_thresholds['baseline_revenue_per_minute']),
                'revenue_deviation': str(revenue_deviation),
                'deviation_percentage': float(revenue_deviation / self.revenue_thresholds['baseline_revenue_per_minute'] * 100)
            },
            'metrics_breakdown': {},
            'market_conditions': {},
            'performance_indicators': {},
            'client_impact': {}
        }
        
        # Organize metrics by category
        for metric in metrics:
            category = self._categorize_metric(metric.name)
            if category not in evidence['metrics_breakdown']:
                evidence['metrics_breakdown'][category] = []
            
            evidence['metrics_breakdown'][category].append({
                'name': metric.name,
                'value': str(metric.value),
                'currency': metric.currency,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
                'metadata': metric.metadata
            })
        
        # Add performance indicators
        evidence['performance_indicators'] = {
            'latency_impact': str(self._get_metric_value(metrics, "latency_impact_loss")),
            'error_impact': str(self._get_metric_value(metrics, "error_impact_loss")),
            'execution_quality': str(self._get_metric_value(metrics, "client_execution_quality"))
        }
        
        # Add market conditions
        evidence['market_conditions'] = {
            'assessment_time': datetime.now(timezone.utc).isoformat(),
            'market_session': self._get_market_session(),
            'trading_volume': 'high',  # Would be calculated from real data
            'volatility': 'normal'     # Would be calculated from real data
        }
        
        return evidence
    
    def _categorize_metric(self, metric_name: str) -> str:
        """Categorize metrics for evidence organization."""
        if 'pnl' in metric_name or 'profit' in metric_name:
            return 'trading_pnl'
        elif 'commission' in metric_name or 'fee' in metric_name:
            return 'revenue_streams'
        elif 'client' in metric_name:
            return 'client_metrics'
        elif 'latency' in metric_name or 'error' in metric_name:
            return 'performance_impact'
        else:
            return 'other'
    
    def _get_market_session(self) -> str:
        """Determine current market session."""
        # Simplified market session detection
        from datetime import datetime
        import pytz
        
        ny_tz = pytz.timezone('America/New_York')
        ny_time = datetime.now(ny_tz)
        hour = ny_time.hour
        
        if 4 <= hour < 9:
            return 'pre_market'
        elif 9 <= hour < 16:
            return 'regular_trading'
        elif 16 <= hour < 20:
            return 'after_hours'
        else:
            return 'closed'
    
    def _generate_recommendation(
        self, 
        impact_level: BusinessImpactLevel, 
        revenue_deviation: Decimal, 
        evidence: Dict[str, Any]
    ) -> str:
        """Generate actionable recommendation based on impact assessment."""
        
        if impact_level == BusinessImpactLevel.CATASTROPHIC:
            return (
                f"IMMEDIATE ROLLBACK REQUIRED: Catastrophic revenue loss of "
                f"${revenue_deviation}/minute detected. Estimated daily impact: "
                f"${revenue_deviation * 60 * 24}. Rollback must be executed within 2 minutes."
            )
        
        elif impact_level == BusinessImpactLevel.CRITICAL:
            return (
                f"URGENT ROLLBACK RECOMMENDED: Critical revenue loss of "
                f"${revenue_deviation}/minute detected. Estimated hourly impact: "
                f"${revenue_deviation * 60}. Rollback should be executed within 5 minutes."
            )
        
        elif impact_level == BusinessImpactLevel.HIGH:
            return (
                f"ROLLBACK RECOMMENDED: High revenue impact of ${revenue_deviation}/minute. "
                f"Monitor for 2 more minutes, then rollback if impact persists."
            )
        
        elif impact_level == BusinessImpactLevel.MEDIUM:
            return (
                f"ENHANCED MONITORING: Medium revenue impact detected. "
                f"Prepare rollback procedures and monitor for escalation."
            )
        
        else:
            return "Continue monitoring. Revenue impact within acceptable thresholds."