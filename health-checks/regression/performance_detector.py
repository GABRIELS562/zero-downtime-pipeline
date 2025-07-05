#!/usr/bin/env python3
"""
Performance Regression Detection System
======================================

Real-time performance regression detection using forensic analysis techniques:
- Statistical baseline modeling with time-series analysis
- Anomaly detection using multiple detection algorithms
- Performance correlation analysis across system components
- Automated threshold adaptation based on historical patterns
- Forensic-level evidence collection for performance incidents

Forensic Methodology Applied:
- Baseline establishment using historical performance data
- Multi-dimensional correlation analysis for root cause identification
- Change point detection for identifying performance degradation events
- Evidence preservation for post-incident analysis
- Predictive modeling for proactive performance management
"""

import asyncio
import json
import math
import statistics
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
import numpy as np
import scipy.stats as stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ..common.forensic_validator import (
    BaseHealthCheck, HealthStatus, Severity, ForensicLogger, HealthCheckResult
)


class PerformanceBaseline(NamedTuple):
    """Performance baseline with statistical characteristics."""
    metric_name: str
    mean: float
    std_dev: float
    percentile_95: float
    percentile_99: float
    min_value: float
    max_value: float
    sample_count: int
    last_updated: datetime
    confidence_interval: Tuple[float, float]


class RegressionDetectionResult(NamedTuple):
    """Result of regression detection analysis."""
    is_regression: bool
    severity: Severity
    confidence: float
    detected_at: datetime
    baseline_value: float
    current_value: float
    deviation_percent: float
    detection_method: str
    evidence: Dict[str, Any]


class PerformanceRegressionDetector(BaseHealthCheck):
    """Advanced performance regression detection with forensic analysis."""
    
    def __init__(self, logger: ForensicLogger, config: Dict[str, Any]):
        super().__init__("regression.performance", logger)
        self.config = config
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Configuration parameters
        self.baseline_window_hours = config.get("baseline_window_hours", 24)
        self.regression_threshold_percent = config.get("regression_threshold_percent", 10.0)
        self.minimum_samples = config.get("minimum_samples", 50)
        self.confidence_threshold = config.get("confidence_threshold", 0.8)
    
    async def execute(self):
        """Execute performance regression detection."""
        start_time = time.perf_counter()
        
        try:
            # Collect current performance metrics
            current_metrics = await self._collect_performance_metrics()
            
            # Update baselines with historical data
            await self._update_baselines()
            
            # Detect regressions using multiple methods
            regression_results = []
            
            for metric_name, current_value in current_metrics.items():
                # Statistical regression detection
                stat_result = self._detect_statistical_regression(metric_name, current_value)
                if stat_result:
                    regression_results.append(stat_result)
                
                # Machine learning anomaly detection
                ml_result = await self._detect_ml_anomaly(metric_name, current_value)
                if ml_result:
                    regression_results.append(ml_result)
                
                # Change point detection
                change_result = self._detect_change_point(metric_name, current_value)
                if change_result:
                    regression_results.append(change_result)
                
                # Update performance history
                self.performance_history[metric_name].append({
                    "timestamp": datetime.now(timezone.utc),
                    "value": current_value
                })
            
            # Correlation analysis
            correlation_analysis = self._perform_correlation_analysis(current_metrics)
            
            # Root cause analysis
            root_cause_analysis = await self._perform_root_cause_analysis(regression_results)
            
            # Evidence collection
            evidence = {
                "current_metrics": current_metrics,
                "baselines": {name: baseline._asdict() for name, baseline in self.baselines.items()},
                "regression_detections": [result._asdict() for result in regression_results],
                "correlation_analysis": correlation_analysis,
                "root_cause_analysis": root_cause_analysis,
                "detection_metadata": {
                    "detection_timestamp": datetime.now(timezone.utc).isoformat(),
                    "baseline_window_hours": self.baseline_window_hours,
                    "detection_methods": ["statistical", "machine_learning", "change_point"]
                }
            }
            
            # Metrics for monitoring
            metrics = {
                "metrics_analyzed": len(current_metrics),
                "regressions_detected": len(regression_results),
                "critical_regressions": len([r for r in regression_results if r.severity == Severity.CRITICAL]),
                "high_severity_regressions": len([r for r in regression_results if r.severity == Severity.HIGH]),
                "average_confidence": statistics.mean([r.confidence for r in regression_results]) if regression_results else 0.0,
                "max_deviation_percent": max([r.deviation_percent for r in regression_results], default=0.0),
                "correlated_regressions": correlation_analysis["correlated_count"]
            }
            
            # Health scoring
            score, status, severity = self._calculate_regression_health_score(metrics, regression_results)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return self._create_result(
                check_type="performance_regression",
                status=status,
                score=score,
                metrics=metrics,
                evidence=evidence,
                duration_ms=duration_ms,
                severity=severity
            )
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return self._create_result(
                check_type="performance_regression",
                status=HealthStatus.CRITICAL,
                score=0.0,
                metrics={},
                evidence={"error": str(e)},
                duration_ms=duration_ms,
                error_message=str(e),
                severity=Severity.CRITICAL
            )
    
    async def _collect_performance_metrics(self) -> Dict[str, float]:
        """Collect current performance metrics from various sources."""
        metrics = {}
        
        # Collect from configured endpoints
        for endpoint_config in self.config.get("metric_endpoints", []):
            try:
                endpoint_metrics = await self._collect_from_endpoint(endpoint_config)
                metrics.update(endpoint_metrics)
            except Exception as e:
                self.logger.log_audit_event(
                    "metric_collection_failed",
                    {"endpoint": endpoint_config.get("name"), "error": str(e)}
                )
        
        # Add synthetic metrics for testing
        if self.config.get("include_synthetic", False):
            synthetic_metrics = self._generate_synthetic_metrics()
            metrics.update(synthetic_metrics)
        
        return metrics
    
    async def _collect_from_endpoint(self, endpoint_config: Dict[str, Any]) -> Dict[str, float]:
        """Collect metrics from a specific endpoint."""
        import aiohttp
        
        url = endpoint_config["url"]
        timeout = aiohttp.ClientTimeout(total=endpoint_config.get("timeout", 5))
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                data = await response.json()
                
                # Extract metrics based on configuration
                metrics = {}
                for metric_config in endpoint_config.get("metrics", []):
                    metric_name = metric_config["name"]
                    metric_path = metric_config["path"]
                    
                    # Navigate JSON path to extract value
                    value = self._extract_json_value(data, metric_path)
                    if value is not None:
                        metrics[f"{endpoint_config['name']}_{metric_name}"] = float(value)
                
                return metrics
    
    def _extract_json_value(self, data: Dict[str, Any], path: str) -> Optional[float]:
        """Extract value from JSON data using dot notation path."""
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            
            return float(current) if current is not None else None
        except (KeyError, ValueError, TypeError):
            return None
    
    def _generate_synthetic_metrics(self) -> Dict[str, float]:
        """Generate synthetic metrics for testing and demonstration."""
        import random
        
        base_time = time.time()
        
        # Simulate various performance metrics with some variability
        metrics = {
            "api_response_time_ms": 45.0 + random.gauss(0, 5),
            "database_query_time_ms": 12.3 + random.gauss(0, 2),
            "memory_usage_percent": 68.5 + random.gauss(0, 3),
            "cpu_usage_percent": 42.1 + random.gauss(0, 5),
            "throughput_requests_per_second": 1250 + random.gauss(0, 50),
            "error_rate_percent": 0.05 + max(0, random.gauss(0, 0.02))
        }
        
        # Introduce occasional performance regression for testing
        if random.random() < 0.1:  # 10% chance of regression
            regression_metric = random.choice(list(metrics.keys()))
            if "time_ms" in regression_metric or "usage_percent" in regression_metric:
                metrics[regression_metric] *= (1.0 + random.uniform(0.2, 0.5))  # 20-50% increase
            elif "requests_per_second" in regression_metric:
                metrics[regression_metric] *= (1.0 - random.uniform(0.2, 0.4))  # 20-40% decrease
        
        return metrics
    
    async def _update_baselines(self):
        """Update performance baselines using historical data."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.baseline_window_hours)
        
        for metric_name, history in self.performance_history.items():
            # Filter recent data for baseline calculation
            recent_data = [
                entry["value"] for entry in history
                if entry["timestamp"] > cutoff_time
            ]
            
            if len(recent_data) >= self.minimum_samples:
                # Calculate statistical baseline
                mean_val = statistics.mean(recent_data)
                std_dev = statistics.stdev(recent_data) if len(recent_data) > 1 else 0.0
                percentile_95 = np.percentile(recent_data, 95)
                percentile_99 = np.percentile(recent_data, 99)
                min_val = min(recent_data)
                max_val = max(recent_data)
                
                # Calculate confidence interval
                confidence_level = 0.95
                t_value = stats.t.ppf((1 + confidence_level) / 2, len(recent_data) - 1)
                margin_error = t_value * (std_dev / math.sqrt(len(recent_data)))
                confidence_interval = (mean_val - margin_error, mean_val + margin_error)
                
                # Update baseline
                self.baselines[metric_name] = PerformanceBaseline(
                    metric_name=metric_name,
                    mean=mean_val,
                    std_dev=std_dev,
                    percentile_95=percentile_95,
                    percentile_99=percentile_99,
                    min_value=min_val,
                    max_value=max_val,
                    sample_count=len(recent_data),
                    last_updated=datetime.now(timezone.utc),
                    confidence_interval=confidence_interval
                )
                
                # Update machine learning models
                await self._update_ml_models(metric_name, recent_data)
    
    async def _update_ml_models(self, metric_name: str, data: List[float]):
        """Update machine learning models for anomaly detection."""
        if len(data) < 20:  # Need minimum data for ML
            return
        
        # Prepare data for ML
        X = np.array(data).reshape(-1, 1)
        
        # Initialize or update scaler
        if metric_name not in self.scalers:
            self.scalers[metric_name] = StandardScaler()
        
        X_scaled = self.scalers[metric_name].fit_transform(X)
        
        # Initialize or update isolation forest
        if metric_name not in self.anomaly_detectors:
            self.anomaly_detectors[metric_name] = IsolationForest(
                contamination=0.05,  # Expect 5% outliers
                random_state=42
            )
        
        self.anomaly_detectors[metric_name].fit(X_scaled)
    
    def _detect_statistical_regression(self, metric_name: str, current_value: float) -> Optional[RegressionDetectionResult]:
        """Detect regression using statistical methods."""
        if metric_name not in self.baselines:
            return None
        
        baseline = self.baselines[metric_name]
        
        # Calculate z-score
        if baseline.std_dev > 0:
            z_score = abs(current_value - baseline.mean) / baseline.std_dev
        else:
            z_score = 0
        
        # Calculate percentage deviation
        if baseline.mean > 0:
            deviation_percent = abs(current_value - baseline.mean) / baseline.mean * 100
        else:
            deviation_percent = 0
        
        # Determine if this is a regression based on metric type
        is_regression = False
        severity = Severity.LOW
        
        # For time-based metrics (latency), higher is worse
        if "time_ms" in metric_name or "latency" in metric_name:
            if current_value > baseline.percentile_95:
                is_regression = True
                severity = Severity.HIGH if current_value > baseline.percentile_99 else Severity.MEDIUM
        
        # For usage metrics, higher might be worse
        elif "usage_percent" in metric_name or "utilization" in metric_name:
            if current_value > baseline.percentile_95:
                is_regression = True
                severity = Severity.HIGH if current_value > baseline.percentile_99 else Severity.MEDIUM
        
        # For throughput metrics, lower is worse
        elif "throughput" in metric_name or "requests_per_second" in metric_name:
            if current_value < baseline.mean - 2 * baseline.std_dev:
                is_regression = True
                severity = Severity.HIGH if current_value < baseline.mean - 3 * baseline.std_dev else Severity.MEDIUM
        
        # For error rates, higher is worse
        elif "error" in metric_name:
            if current_value > baseline.percentile_95:
                is_regression = True
                severity = Severity.CRITICAL if current_value > baseline.percentile_99 else Severity.HIGH
        
        # General threshold-based detection
        if not is_regression and deviation_percent > self.regression_threshold_percent:
            is_regression = True
            severity = Severity.MEDIUM
        
        if is_regression:
            confidence = min(z_score / 3.0, 1.0)  # Normalize z-score to confidence
            
            evidence = {
                "detection_method": "statistical",
                "z_score": z_score,
                "baseline_mean": baseline.mean,
                "baseline_std_dev": baseline.std_dev,
                "baseline_samples": baseline.sample_count,
                "percentile_95": baseline.percentile_95,
                "percentile_99": baseline.percentile_99,
                "confidence_interval": baseline.confidence_interval
            }
            
            return RegressionDetectionResult(
                is_regression=True,
                severity=severity,
                confidence=confidence,
                detected_at=datetime.now(timezone.utc),
                baseline_value=baseline.mean,
                current_value=current_value,
                deviation_percent=deviation_percent,
                detection_method="statistical",
                evidence=evidence
            )
        
        return None
    
    async def _detect_ml_anomaly(self, metric_name: str, current_value: float) -> Optional[RegressionDetectionResult]:
        """Detect anomalies using machine learning models."""
        if metric_name not in self.anomaly_detectors or metric_name not in self.scalers:
            return None
        
        try:
            # Scale the current value
            X = np.array([[current_value]])
            X_scaled = self.scalers[metric_name].transform(X)
            
            # Predict anomaly
            anomaly_score = self.anomaly_detectors[metric_name].decision_function(X_scaled)[0]
            is_anomaly = self.anomaly_detectors[metric_name].predict(X_scaled)[0] == -1
            
            if is_anomaly:
                # Convert anomaly score to confidence and severity
                confidence = min(abs(anomaly_score), 1.0)
                
                if confidence > 0.8:
                    severity = Severity.CRITICAL
                elif confidence > 0.6:
                    severity = Severity.HIGH
                else:
                    severity = Severity.MEDIUM
                
                baseline = self.baselines.get(metric_name)
                baseline_value = baseline.mean if baseline else 0.0
                deviation_percent = abs(current_value - baseline_value) / max(baseline_value, 1.0) * 100
                
                evidence = {
                    "detection_method": "machine_learning",
                    "anomaly_score": anomaly_score,
                    "model_type": "isolation_forest",
                    "scaled_value": X_scaled[0][0],
                }
                
                return RegressionDetectionResult(
                    is_regression=True,
                    severity=severity,
                    confidence=confidence,
                    detected_at=datetime.now(timezone.utc),
                    baseline_value=baseline_value,
                    current_value=current_value,
                    deviation_percent=deviation_percent,
                    detection_method="machine_learning",
                    evidence=evidence
                )
        
        except Exception as e:
            self.logger.log_audit_event(
                "ml_anomaly_detection_failed",
                {"metric": metric_name, "error": str(e)}
            )
        
        return None
    
    def _detect_change_point(self, metric_name: str, current_value: float) -> Optional[RegressionDetectionResult]:
        """Detect change points in performance metrics."""
        if metric_name not in self.performance_history:
            return None
        
        history = list(self.performance_history[metric_name])
        if len(history) < 20:  # Need sufficient history
            return None
        
        # Get recent values for change point detection
        recent_values = [entry["value"] for entry in history[-20:]]
        
        # Simple change point detection using sliding window
        window_size = 10
        if len(recent_values) >= window_size * 2:
            first_half = recent_values[:window_size]
            second_half = recent_values[window_size:]
            
            first_mean = statistics.mean(first_half)
            second_mean = statistics.mean(second_half)
            
            # Perform t-test to check for significant difference
            try:
                t_stat, p_value = stats.ttest_ind(first_half, second_half)
                
                # If p-value is small, there's a significant change
                if p_value < 0.05:
                    change_percent = abs(second_mean - first_mean) / max(first_mean, 1.0) * 100
                    
                    # Determine if this is a regression
                    is_regression = change_percent > self.regression_threshold_percent
                    
                    if is_regression:
                        confidence = 1.0 - p_value  # Higher confidence for lower p-value
                        severity = Severity.HIGH if change_percent > 25 else Severity.MEDIUM
                        
                        evidence = {
                            "detection_method": "change_point",
                            "t_statistic": t_stat,
                            "p_value": p_value,
                            "first_period_mean": first_mean,
                            "second_period_mean": second_mean,
                            "window_size": window_size
                        }
                        
                        return RegressionDetectionResult(
                            is_regression=True,
                            severity=severity,
                            confidence=confidence,
                            detected_at=datetime.now(timezone.utc),
                            baseline_value=first_mean,
                            current_value=current_value,
                            deviation_percent=change_percent,
                            detection_method="change_point",
                            evidence=evidence
                        )
            
            except Exception as e:
                self.logger.log_audit_event(
                    "change_point_detection_failed",
                    {"metric": metric_name, "error": str(e)}
                )
        
        return None
    
    def _perform_correlation_analysis(self, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Perform correlation analysis across metrics."""
        correlations = {}
        correlated_count = 0
        
        metric_names = list(current_metrics.keys())
        
        # Calculate correlations between metrics
        for i, metric1 in enumerate(metric_names):
            for metric2 in metric_names[i+1:]:
                if metric1 in self.performance_history and metric2 in self.performance_history:
                    history1 = [entry["value"] for entry in self.performance_history[metric1]]
                    history2 = [entry["value"] for entry in self.performance_history[metric2]]
                    
                    # Ensure same length
                    min_length = min(len(history1), len(history2))
                    if min_length > 10:
                        history1 = history1[-min_length:]
                        history2 = history2[-min_length:]
                        
                        # Calculate correlation
                        try:
                            correlation, p_value = stats.pearsonr(history1, history2)
                            
                            if abs(correlation) > 0.7 and p_value < 0.05:
                                correlations[f"{metric1}_vs_{metric2}"] = {
                                    "correlation": correlation,
                                    "p_value": p_value,
                                    "strength": "strong" if abs(correlation) > 0.8 else "moderate"
                                }
                                correlated_count += 1
                        
                        except Exception:
                            pass  # Skip if correlation calculation fails
        
        return {
            "correlations": correlations,
            "correlated_count": correlated_count,
            "total_pairs_analyzed": len(metric_names) * (len(metric_names) - 1) // 2
        }
    
    async def _perform_root_cause_analysis(self, regressions: List[RegressionDetectionResult]) -> Dict[str, Any]:
        """Perform root cause analysis for detected regressions."""
        if not regressions:
            return {"analysis": "no_regressions_detected"}
        
        # Group regressions by detection time proximity
        time_clusters = []
        for regression in regressions:
            placed = False
            for cluster in time_clusters:
                # If regression is within 5 minutes of cluster
                time_diff = abs((regression.detected_at - cluster[0].detected_at).total_seconds())
                if time_diff < 300:  # 5 minutes
                    cluster.append(regression)
                    placed = True
                    break
            
            if not placed:
                time_clusters.append([regression])
        
        # Analyze patterns
        patterns = []
        
        # Check for widespread impact
        if len(regressions) > 3:
            patterns.append({
                "pattern": "widespread_degradation",
                "description": "Multiple metrics degraded simultaneously",
                "affected_metrics": [r.detected_at for r in regressions],
                "likely_cause": "infrastructure_issue"
            })
        
        # Check for specific metric type issues
        latency_regressions = [r for r in regressions if "time_ms" in r.detection_method or "latency" in str(r.evidence)]
        if len(latency_regressions) >= 2:
            patterns.append({
                "pattern": "latency_degradation",
                "description": "Multiple latency metrics affected",
                "affected_count": len(latency_regressions),
                "likely_cause": "network_or_database_issue"
            })
        
        # Check for resource exhaustion patterns
        resource_regressions = [r for r in regressions if any(keyword in str(r.evidence).lower() 
                                                            for keyword in ["memory", "cpu", "disk"])]
        if len(resource_regressions) >= 2:
            patterns.append({
                "pattern": "resource_exhaustion",
                "description": "Resource utilization metrics affected",
                "affected_count": len(resource_regressions),
                "likely_cause": "capacity_issue"
            })
        
        return {
            "time_clusters": len(time_clusters),
            "patterns": patterns,
            "severity_distribution": {
                "critical": len([r for r in regressions if r.severity == Severity.CRITICAL]),
                "high": len([r for r in regressions if r.severity == Severity.HIGH]),
                "medium": len([r for r in regressions if r.severity == Severity.MEDIUM])
            },
            "detection_methods": list(set(r.detection_method for r in regressions))
        }
    
    def _calculate_regression_health_score(
        self, 
        metrics: Dict[str, float], 
        regressions: List[RegressionDetectionResult]
    ) -> Tuple[float, HealthStatus, Severity]:
        """Calculate health score based on regression detection results."""
        score = 100.0
        status = HealthStatus.HEALTHY
        severity = Severity.LOW
        
        if not regressions:
            return score, status, severity
        
        # Deduct points based on regression severity
        for regression in regressions:
            if regression.severity == Severity.CRITICAL:
                score -= 30
                status = HealthStatus.CRITICAL
                severity = Severity.CRITICAL
            elif regression.severity == Severity.HIGH:
                score -= 20
                status = HealthStatus.CRITICAL if status != HealthStatus.CRITICAL else status
                severity = max(severity, Severity.HIGH)
            elif regression.severity == Severity.MEDIUM:
                score -= 10
                status = HealthStatus.DEGRADED if status == HealthStatus.HEALTHY else status
                severity = max(severity, Severity.MEDIUM)
        
        # Additional penalty for multiple regressions
        if len(regressions) > 3:
            score -= 20
            status = HealthStatus.CRITICAL
            severity = Severity.CRITICAL
        
        # Consider average confidence
        if metrics["average_confidence"] > 0.8:
            # High confidence in detections, don't adjust score
            pass
        elif metrics["average_confidence"] > 0.6:
            # Medium confidence, reduce severity slightly
            score += 5
        else:
            # Low confidence, reduce severity more
            score += 10
            if status == HealthStatus.DEGRADED:
                status = HealthStatus.HEALTHY
                severity = Severity.LOW
        
        return max(score, 0.0), status, severity