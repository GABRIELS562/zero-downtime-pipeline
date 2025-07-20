"""
Latency Monitoring Middleware
Ultra-low latency tracking for high-frequency trading
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Histogram, Counter
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics for latency monitoring
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

ultra_low_latency_violations = Counter(
    'ultra_low_latency_violations_total',
    'Requests that exceeded ultra-low latency threshold',
    ['endpoint', 'threshold_ms']
)

class LatencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring request latency with ultra-low latency alerting
    Critical for high-frequency trading systems
    """
    
    def __init__(self, app, ultra_low_latency_threshold_ms: float = 50.0):
        super().__init__(app)
        self.ultra_low_latency_threshold = ultra_low_latency_threshold_ms / 1000.0  # Convert to seconds
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Record start time with high precision
        start_time = time.perf_counter()
        
        # Extract request information
        method = request.method
        path = request.url.path
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.perf_counter() - start_time
        duration_ms = duration * 1000
        
        # Record metrics
        status_code = str(response.status_code)
        
        request_duration.labels(
            method=method,
            endpoint=path,
            status_code=status_code
        ).observe(duration)
        
        request_count.labels(
            method=method,
            endpoint=path,
            status_code=status_code
        ).inc()
        
        # Check ultra-low latency violations
        if duration > self.ultra_low_latency_threshold:
            ultra_low_latency_violations.labels(
                endpoint=path,
                threshold_ms=str(self.ultra_low_latency_threshold * 1000)
            ).inc()
            
            # Log critical latency violations
            if duration > (self.ultra_low_latency_threshold * 2):  # Double threshold
                logger.warning(
                    f"Critical latency violation: {path} took {duration_ms:.2f}ms "
                    f"(threshold: {self.ultra_low_latency_threshold * 1000:.2f}ms)"
                )
        
        # Add latency headers for debugging
        response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "unknown")
        
        # Add performance classification header
        if duration < self.ultra_low_latency_threshold * 0.5:
            response.headers["X-Performance-Class"] = "excellent"
        elif duration < self.ultra_low_latency_threshold:
            response.headers["X-Performance-Class"] = "good"
        elif duration < self.ultra_low_latency_threshold * 2:
            response.headers["X-Performance-Class"] = "degraded"
        else:
            response.headers["X-Performance-Class"] = "critical"
        
        return response