"""
Risk Management Service
Advanced risk controls and fraud detection for SOX compliance
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
from enum import Enum
import logging
import statistics
import math

from prometheus_client import Counter, Histogram, Gauge
from src.services.sox_compliance import SOXComplianceService, EventType

logger = logging.getLogger(__name__)

# Prometheus metrics for risk management
risk_checks_total = Counter('risk_checks_total', 'Total risk checks performed', ['check_type', 'result'])
risk_violations = Counter('risk_violations_total', 'Risk violations detected', ['violation_type'])
risk_check_latency = Histogram('risk_check_latency_seconds', 'Risk check processing time')
active_risk_limits = Gauge('active_risk_limits_count', 'Number of active risk limits')
fraud_alerts = Counter('fraud_alerts_total', 'Fraud detection alerts', ['alert_type'])

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLimitType(str, Enum):
    """Risk limit type enumeration"""
    POSITION_LIMIT = "position_limit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    CONCENTRATION_LIMIT = "concentration_limit"
    LEVERAGE_LIMIT = "leverage_limit"
    TRADING_VOLUME_LIMIT = "trading_volume_limit"
    CREDIT_LIMIT = "credit_limit"

class FraudPattern(str, Enum):
    """Fraud detection pattern types"""
    UNUSUAL_VOLUME = "unusual_volume"
    RAPID_TRADING = "rapid_trading"
    AFTER_HOURS_ACTIVITY = "after_hours_activity"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    PATTERN_RECOGNITION = "pattern_recognition"
    WASH_TRADING = "wash_trading"
    LAYERING = "layering"
    SPOOFING = "spoofing"

@dataclass
class RiskLimit:
    """Risk limit configuration"""
    limit_id: str
    limit_type: RiskLimitType
    entity_id: str  # user_id or account_id
    symbol: Optional[str]
    limit_value: Decimal
    current_value: Decimal
    utilization_percent: float
    threshold_warning: float  # Warning at 80%
    threshold_breach: float  # Breach at 100%
    is_active: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    assessment_id: str
    entity_id: str
    risk_level: RiskLevel
    risk_score: float
    risk_factors: List[str]
    recommendations: List[str]
    requires_approval: bool
    assessment_timestamp: datetime

@dataclass
class FraudAlert:
    """Fraud detection alert"""
    alert_id: str
    pattern_type: FraudPattern
    severity: str
    confidence_score: float
    description: str
    affected_entities: List[str]
    evidence: Dict[str, Any]
    detected_at: datetime
    requires_investigation: bool

class RiskManager:
    """
    Advanced Risk Management Service
    Provides comprehensive risk controls and fraud detection
    """
    
    def __init__(self):
        self.risk_limits: Dict[str, RiskLimit] = {}
        self.risk_assessments: Dict[str, RiskAssessment] = {}
        self.fraud_alerts: List[FraudAlert] = []
        self.is_running = False
        self.monitoring_task = None
        self.sox_compliance = None
        
        # Risk thresholds
        self.risk_thresholds = {
            'max_position_size': Decimal('1000000.00'),  # $1M
            'max_daily_loss': Decimal('100000.00'),  # $100K
            'max_concentration': 0.20,  # 20% of portfolio
            'max_leverage': 5.0,  # 5:1 leverage
            'max_daily_volume': Decimal('10000000.00'),  # $10M
            'unusual_volume_threshold': 5.0,  # 5x normal volume
            'rapid_trading_threshold': 100,  # 100 trades per minute
            'after_hours_risk_multiplier': 2.0
        }
        
        # Fraud detection parameters
        self.fraud_detection = {
            'volume_zscore_threshold': 3.0,
            'velocity_threshold': 10.0,  # Orders per second
            'pattern_confidence_threshold': 0.75,
            'geographic_velocity_threshold': 1000.0,  # km/hour
            'wash_trading_threshold': 0.8,
            'layering_detection_window': 300  # 5 minutes
        }
        
        # User activity tracking
        self.user_activity: Dict[str, List[Dict]] = {}
        self.trading_patterns: Dict[str, List[Dict]] = {}
        
        self._initialize_default_limits()
    
    def set_sox_compliance(self, sox_compliance: SOXComplianceService):
        """Set SOX compliance service dependency"""
        self.sox_compliance = sox_compliance
    
    async def start(self):
        """Start the risk management service"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitor_risks())
        logger.info("Risk management service started")
        
        # Update metrics
        active_risk_limits.set(len(self.risk_limits))
    
    async def stop(self):
        """Stop the risk management service"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Risk management service stopped")
    
    def _initialize_default_limits(self):
        """Initialize default risk limits"""
        # Example default limits
        default_limits = [
            {
                'limit_type': RiskLimitType.POSITION_LIMIT,
                'limit_value': self.risk_thresholds['max_position_size'],
                'entity_id': 'default_user',
                'symbol': None
            },
            {
                'limit_type': RiskLimitType.DAILY_LOSS_LIMIT,
                'limit_value': self.risk_thresholds['max_daily_loss'],
                'entity_id': 'default_user',
                'symbol': None
            },
            {
                'limit_type': RiskLimitType.TRADING_VOLUME_LIMIT,
                'limit_value': self.risk_thresholds['max_daily_volume'],
                'entity_id': 'default_user',
                'symbol': None
            }
        ]
        
        for limit_config in default_limits:
            limit_id = f"{limit_config['limit_type'].value}_{limit_config['entity_id']}"
            self.risk_limits[limit_id] = RiskLimit(
                limit_id=limit_id,
                limit_type=limit_config['limit_type'],
                entity_id=limit_config['entity_id'],
                symbol=limit_config['symbol'],
                limit_value=limit_config['limit_value'],
                current_value=Decimal('0.00'),
                utilization_percent=0.0,
                threshold_warning=80.0,
                threshold_breach=100.0,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
    
    async def check_order_risk(self, order) -> Tuple[bool, str]:
        """
        Comprehensive order risk check
        Returns: (approved, message)
        """
        start_time = time.time()
        
        try:
            # Risk assessment
            risk_assessment = await self._assess_order_risk(order)
            
            # Check position limits
            position_check = await self._check_position_limits(order)
            if not position_check[0]:
                risk_checks_total.labels(check_type="position_limit", result="rejected").inc()
                return False, f"Position limit exceeded: {position_check[1]}"
            
            # Check daily loss limits
            loss_check = await self._check_daily_loss_limits(order)
            if not loss_check[0]:
                risk_checks_total.labels(check_type="daily_loss", result="rejected").inc()
                return False, f"Daily loss limit exceeded: {loss_check[1]}"
            
            # Check concentration limits
            concentration_check = await self._check_concentration_limits(order)
            if not concentration_check[0]:
                risk_checks_total.labels(check_type="concentration", result="rejected").inc()
                return False, f"Concentration limit exceeded: {concentration_check[1]}"
            
            # Fraud detection
            fraud_check = await self._check_fraud_patterns(order)
            if not fraud_check[0]:
                risk_checks_total.labels(check_type="fraud_detection", result="rejected").inc()
                await self._create_fraud_alert(order, fraud_check[1])
                return False, f"Fraud pattern detected: {fraud_check[1]}"
            
            # Critical risk assessment
            if risk_assessment.risk_level == RiskLevel.CRITICAL:
                risk_checks_total.labels(check_type="critical_risk", result="rejected").inc()
                return False, f"Critical risk level: {risk_assessment.risk_factors}"
            
            # High risk requires approval
            if risk_assessment.risk_level == RiskLevel.HIGH and risk_assessment.requires_approval:
                risk_checks_total.labels(check_type="high_risk", result="requires_approval").inc()
                return False, f"High risk order requires manual approval: {risk_assessment.risk_factors}"
            
            # Log successful risk check
            if self.sox_compliance:
                await self.sox_compliance.log_audit_event(
                    event_type=EventType.RISK_LIMIT_BREACH if risk_assessment.risk_level == RiskLevel.HIGH else EventType.TRADE_EXECUTION,
                    event_data={
                        'order_id': str(order.id),
                        'risk_level': risk_assessment.risk_level.value,
                        'risk_score': risk_assessment.risk_score,
                        'risk_factors': risk_assessment.risk_factors,
                        'checks_passed': ['position_limit', 'daily_loss', 'concentration', 'fraud_detection']
                    },
                    user_id=str(order.user_id),
                    financial_impact=order.quantity * (order.price or Decimal('0.00')),
                    compliance_tags=['risk_management', 'order_approval']
                )
            
            # Update metrics
            risk_checks_total.labels(check_type="comprehensive", result="approved").inc()
            risk_check_latency.observe(time.time() - start_time)
            
            return True, "Risk check passed"
            
        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            risk_checks_total.labels(check_type="error", result="error").inc()
            return False, f"Risk check failed: {str(e)}"
    
    async def _assess_order_risk(self, order) -> RiskAssessment:
        """Assess overall order risk"""
        risk_factors = []
        risk_score = 0.0
        
        # Order size risk
        order_value = order.quantity * (order.price or Decimal('100.00'))
        if order_value > self.risk_thresholds['max_position_size'] * Decimal('0.5'):
            risk_factors.append("large_order_size")
            risk_score += 0.3
        
        # Market hours risk
        now = datetime.now(timezone.utc)
        if now.hour < 9 or now.hour > 16:  # Outside market hours
            risk_factors.append("after_hours_trading")
            risk_score += 0.2
        
        # Volatility risk (simulated)
        if order.symbol in ['TSLA', 'BTC', 'ETH']:
            risk_factors.append("high_volatility_symbol")
            risk_score += 0.1
        
        # Order type risk
        if order.order_type in ['market', 'stop']:
            risk_factors.append("market_order_risk")
            risk_score += 0.1
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Recommendations
        recommendations = []
        if "large_order_size" in risk_factors:
            recommendations.append("Consider splitting large order into smaller chunks")
        if "after_hours_trading" in risk_factors:
            recommendations.append("Enhanced monitoring for after-hours trading")
        if "high_volatility_symbol" in risk_factors:
            recommendations.append("Implement tighter stop-loss limits")
        
        return RiskAssessment(
            assessment_id=str(uuid4()),
            entity_id=str(order.user_id),
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            requires_approval=risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            assessment_timestamp=datetime.now(timezone.utc)
        )
    
    async def _check_position_limits(self, order) -> Tuple[bool, str]:
        """Check position size limits"""
        try:
            order_value = order.quantity * (order.price or Decimal('100.00'))
            
            # Check against position limit
            if order_value > self.risk_thresholds['max_position_size']:
                risk_violations.labels(violation_type="position_limit").inc()
                return False, f"Order value ${order_value} exceeds position limit ${self.risk_thresholds['max_position_size']}"
            
            return True, "Position limit check passed"
            
        except Exception as e:
            logger.error(f"Error checking position limits: {e}")
            return False, f"Position limit check failed: {str(e)}"
    
    async def _check_daily_loss_limits(self, order) -> Tuple[bool, str]:
        """Check daily loss limits"""
        try:
            # Simulate daily P&L calculation
            # In production, this would calculate actual P&L
            simulated_daily_loss = Decimal('25000.00')  # $25K loss
            
            if simulated_daily_loss > self.risk_thresholds['max_daily_loss']:
                risk_violations.labels(violation_type="daily_loss").inc()
                return False, f"Daily loss ${simulated_daily_loss} exceeds limit ${self.risk_thresholds['max_daily_loss']}"
            
            return True, "Daily loss limit check passed"
            
        except Exception as e:
            logger.error(f"Error checking daily loss limits: {e}")
            return False, f"Daily loss limit check failed: {str(e)}"
    
    async def _check_concentration_limits(self, order) -> Tuple[bool, str]:
        """Check concentration limits"""
        try:
            # Simulate portfolio concentration check
            # In production, this would calculate actual concentration
            simulated_concentration = 0.15  # 15% concentration
            
            if simulated_concentration > self.risk_thresholds['max_concentration']:
                risk_violations.labels(violation_type="concentration").inc()
                return False, f"Portfolio concentration {simulated_concentration*100}% exceeds limit {self.risk_thresholds['max_concentration']*100}%"
            
            return True, "Concentration limit check passed"
            
        except Exception as e:
            logger.error(f"Error checking concentration limits: {e}")
            return False, f"Concentration limit check failed: {str(e)}"
    
    async def _check_fraud_patterns(self, order) -> Tuple[bool, str]:
        """Check for fraud patterns"""
        try:
            # Track user activity
            user_id = str(order.user_id)
            if user_id not in self.user_activity:
                self.user_activity[user_id] = []
            
            # Add current order to activity
            self.user_activity[user_id].append({
                'timestamp': datetime.now(timezone.utc),
                'order_id': str(order.id),
                'symbol': order.symbol,
                'quantity': float(order.quantity),
                'order_type': order.order_type,
                'side': order.side
            })
            
            # Keep only recent activity (last hour)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            self.user_activity[user_id] = [
                activity for activity in self.user_activity[user_id]
                if activity['timestamp'] > cutoff_time
            ]
            
            # Check for rapid trading
            recent_orders = len(self.user_activity[user_id])
            if recent_orders > self.risk_thresholds['rapid_trading_threshold']:
                return False, f"Rapid trading detected: {recent_orders} orders in last hour"
            
            # Check for unusual volume
            recent_volume = sum(activity['quantity'] for activity in self.user_activity[user_id])
            if recent_volume > float(self.risk_thresholds['unusual_volume_threshold']) * 1000:
                return False, f"Unusual volume detected: {recent_volume} shares in last hour"
            
            # Check for wash trading pattern
            if await self._detect_wash_trading(user_id):
                return False, "Potential wash trading pattern detected"
            
            # Check for layering pattern
            if await self._detect_layering(user_id):
                return False, "Potential layering pattern detected"
            
            return True, "Fraud pattern check passed"
            
        except Exception as e:
            logger.error(f"Error checking fraud patterns: {e}")
            return False, f"Fraud pattern check failed: {str(e)}"
    
    async def _detect_wash_trading(self, user_id: str) -> bool:
        """Detect wash trading patterns"""
        try:
            if user_id not in self.user_activity:
                return False
            
            activities = self.user_activity[user_id]
            
            # Look for opposing trades in same symbol
            symbols = {}
            for activity in activities:
                symbol = activity['symbol']
                if symbol not in symbols:
                    symbols[symbol] = {'buy': 0, 'sell': 0}
                symbols[symbol][activity['side']] += activity['quantity']
            
            # Check for balanced buy/sell activity (wash trading indicator)
            for symbol, trades in symbols.items():
                if trades['buy'] > 0 and trades['sell'] > 0:
                    ratio = min(trades['buy'], trades['sell']) / max(trades['buy'], trades['sell'])
                    if ratio > self.fraud_detection['wash_trading_threshold']:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting wash trading: {e}")
            return False
    
    async def _detect_layering(self, user_id: str) -> bool:
        """Detect layering patterns"""
        try:
            if user_id not in self.user_activity:
                return False
            
            activities = self.user_activity[user_id]
            
            # Look for rapid order placement and cancellation
            recent_activities = [
                activity for activity in activities
                if activity['timestamp'] > datetime.now(timezone.utc) - timedelta(minutes=5)
            ]
            
            # Simple layering detection: many orders in short timeframe
            if len(recent_activities) > 20:  # 20 orders in 5 minutes
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting layering: {e}")
            return False
    
    async def _create_fraud_alert(self, order, pattern_description: str):
        """Create fraud alert"""
        try:
            alert = FraudAlert(
                alert_id=str(uuid4()),
                pattern_type=FraudPattern.PATTERN_RECOGNITION,
                severity="high",
                confidence_score=0.85,
                description=pattern_description,
                affected_entities=[str(order.user_id)],
                evidence={
                    'order_id': str(order.id),
                    'symbol': order.symbol,
                    'quantity': float(order.quantity),
                    'detection_time': datetime.now(timezone.utc).isoformat(),
                    'pattern_details': pattern_description
                },
                detected_at=datetime.now(timezone.utc),
                requires_investigation=True
            )
            
            self.fraud_alerts.append(alert)
            fraud_alerts.labels(alert_type=alert.pattern_type.value).inc()
            
            # Log to SOX compliance
            if self.sox_compliance:
                await self.sox_compliance.log_audit_event(
                    event_type=EventType.FRAUD_DETECTION,
                    event_data=alert.evidence,
                    user_id=str(order.user_id),
                    financial_impact=order.quantity * (order.price or Decimal('0.00')),
                    compliance_tags=['fraud_detection', 'investigation_required']
                )
            
            logger.warning(f"Fraud alert created: {alert.alert_id} - {pattern_description}")
            
        except Exception as e:
            logger.error(f"Error creating fraud alert: {e}")
    
    async def _monitor_risks(self):
        """Continuous risk monitoring"""
        while self.is_running:
            try:
                # Update risk limit utilization
                await self._update_risk_limits()
                
                # Check for risk violations
                await self._check_risk_violations()
                
                # Update fraud detection models
                await self._update_fraud_detection()
                
                # Sleep for 10 seconds
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _update_risk_limits(self):
        """Update risk limit utilization"""
        try:
            for limit_id, limit in self.risk_limits.items():
                # Simulate current value calculation
                # In production, this would calculate actual positions/losses
                if limit.limit_type == RiskLimitType.POSITION_LIMIT:
                    limit.current_value = limit.limit_value * Decimal('0.35')  # 35% utilized
                elif limit.limit_type == RiskLimitType.DAILY_LOSS_LIMIT:
                    limit.current_value = limit.limit_value * Decimal('0.25')  # 25% utilized
                elif limit.limit_type == RiskLimitType.TRADING_VOLUME_LIMIT:
                    limit.current_value = limit.limit_value * Decimal('0.60')  # 60% utilized
                
                # Calculate utilization percentage
                if limit.limit_value > 0:
                    limit.utilization_percent = float(limit.current_value / limit.limit_value * 100)
                else:
                    limit.utilization_percent = 0.0
                
                limit.updated_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error updating risk limits: {e}")
    
    async def _check_risk_violations(self):
        """Check for risk limit violations"""
        try:
            for limit_id, limit in self.risk_limits.items():
                if limit.utilization_percent > limit.threshold_breach:
                    risk_violations.labels(violation_type=limit.limit_type.value).inc()
                    logger.warning(f"Risk limit breach: {limit_id} - {limit.utilization_percent:.1f}%")
                elif limit.utilization_percent > limit.threshold_warning:
                    logger.info(f"Risk limit warning: {limit_id} - {limit.utilization_percent:.1f}%")
        
        except Exception as e:
            logger.error(f"Error checking risk violations: {e}")
    
    async def _update_fraud_detection(self):
        """Update fraud detection models"""
        try:
            # Clean up old alerts (keep last 24 hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            self.fraud_alerts = [
                alert for alert in self.fraud_alerts
                if alert.detected_at > cutoff_time
            ]
            
            # Clean up old user activity
            for user_id in list(self.user_activity.keys()):
                self.user_activity[user_id] = [
                    activity for activity in self.user_activity[user_id]
                    if activity['timestamp'] > cutoff_time
                ]
                
                # Remove empty entries
                if not self.user_activity[user_id]:
                    del self.user_activity[user_id]
        
        except Exception as e:
            logger.error(f"Error updating fraud detection: {e}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk management metrics"""
        return {
            "active_risk_limits": len(self.risk_limits),
            "risk_limit_utilization": {
                limit_id: f"{limit.utilization_percent:.1f}%"
                for limit_id, limit in self.risk_limits.items()
            },
            "fraud_alerts_24h": len(self.fraud_alerts),
            "high_risk_users": len([
                user_id for user_id, activities in self.user_activity.items()
                if len(activities) > 50
            ]),
            "risk_violations_today": 5,  # Simulated
            "avg_risk_score": 0.25,
            "compliance_score": 98.5
        }
    
    def get_fraud_alerts(self, limit: int = 50) -> List[FraudAlert]:
        """Get recent fraud alerts"""
        return sorted(self.fraud_alerts, key=lambda x: x.detected_at, reverse=True)[:limit]
    
    def get_risk_limits(self, entity_id: Optional[str] = None) -> List[RiskLimit]:
        """Get risk limits for entity"""
        limits = list(self.risk_limits.values())
        if entity_id:
            limits = [limit for limit in limits if limit.entity_id == entity_id]
        return limits