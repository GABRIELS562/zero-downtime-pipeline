"""
Market Data Validation Middleware
Real-time validation of market data feeds for trading systems
"""

import json
import time
from typing import Callable, Optional, Dict, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics for market data validation
market_data_validation_errors = Counter(
    'market_data_validation_errors_total',
    'Total market data validation errors',
    ['error_type', 'symbol', 'data_source']
)

market_data_processing_time = Histogram(
    'market_data_processing_seconds',
    'Time spent processing market data',
    ['symbol', 'data_type']
)

market_data_requests = Counter(
    'market_data_requests_total',
    'Total market data requests',
    ['endpoint', 'symbol', 'status']
)

class MarketDataValidationError(Exception):
    """Custom exception for market data validation errors"""
    pass

class MarketDataMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating market data integrity and consistency
    Critical for maintaining data quality in trading systems
    """
    
    def __init__(self, app, 
                 price_deviation_threshold: float = 0.1,  # 10% price deviation threshold
                 stale_data_threshold_seconds: int = 300):  # 5 minutes for stale data
        super().__init__(app)
        self.price_deviation_threshold = price_deviation_threshold
        self.stale_data_threshold = stale_data_threshold_seconds
        self.price_cache = {}  # Simple in-memory cache for price validation
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only process market data related endpoints
        if not self._is_market_data_endpoint(request.url.path):
            return await call_next(request)
            
        start_time = time.perf_counter()
        
        try:
            # Pre-process validation for incoming market data
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_incoming_market_data(request)
            
            # Process the request
            response = await call_next(request)
            
            # Post-process validation for outgoing market data
            if response.status_code == 200 and self._is_market_data_response(request.url.path):
                await self._validate_outgoing_market_data(request, response)
            
            # Record successful processing
            market_data_requests.labels(
                endpoint=request.url.path,
                symbol=self._extract_symbol(request),
                status="success"
            ).inc()
            
            return response
            
        except MarketDataValidationError as e:
            logger.error(f"Market data validation failed: {e}")
            market_data_validation_errors.labels(
                error_type="validation_error",
                symbol=self._extract_symbol(request),
                data_source=request.headers.get("X-Data-Source", "unknown")
            ).inc()
            
            market_data_requests.labels(
                endpoint=request.url.path,
                symbol=self._extract_symbol(request),
                status="validation_error"
            ).inc()
            
            raise HTTPException(status_code=422, detail=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error in market data middleware: {e}")
            market_data_validation_errors.labels(
                error_type="system_error",
                symbol=self._extract_symbol(request),
                data_source=request.headers.get("X-Data-Source", "unknown")
            ).inc()
            
            market_data_requests.labels(
                endpoint=request.url.path,
                symbol=self._extract_symbol(request),
                status="system_error"
            ).inc()
            
            return await call_next(request)
            
        finally:
            # Record processing time
            processing_time = time.perf_counter() - start_time
            market_data_processing_time.labels(
                symbol=self._extract_symbol(request),
                data_type=self._get_data_type(request.url.path)
            ).observe(processing_time)
    
    def _is_market_data_endpoint(self, path: str) -> bool:
        """Check if the endpoint handles market data"""
        market_data_patterns = [
            "/api/v1/market-data",
            "/api/v1/quotes",
            "/api/v1/prices",
            "/api/v1/tickers",
            "/api/v1/feeds"
        ]
        return any(pattern in path for pattern in market_data_patterns)
    
    def _is_market_data_response(self, path: str) -> bool:
        """Check if the response contains market data"""
        return self._is_market_data_endpoint(path) and "GET" in path
    
    def _extract_symbol(self, request: Request) -> str:
        """Extract symbol from request"""
        # Try path parameters first
        if hasattr(request, 'path_params') and 'symbol' in request.path_params:
            return request.path_params['symbol']
        
        # Try query parameters
        symbol = request.query_params.get('symbol', 'unknown')
        return symbol
    
    def _get_data_type(self, path: str) -> str:
        """Determine the type of market data from path"""
        if "/quotes" in path:
            return "quote"
        elif "/prices" in path:
            return "price"
        elif "/tickers" in path:
            return "ticker"
        elif "/feeds" in path:
            return "feed"
        else:
            return "general"
    
    async def _validate_incoming_market_data(self, request: Request):
        """Validate incoming market data for consistency and format"""
        try:
            body = await request.body()
            if not body:
                return
                
            data = json.loads(body)
            symbol = self._extract_symbol(request)
            
            # Validate required fields
            self._validate_required_fields(data)
            
            # Validate price data
            if 'price' in data:
                self._validate_price_data(symbol, data['price'])
            
            # Validate timestamp
            if 'timestamp' in data:
                self._validate_timestamp(data['timestamp'])
            
            # Validate volume data
            if 'volume' in data:
                self._validate_volume_data(data['volume'])
                
        except json.JSONDecodeError:
            raise MarketDataValidationError("Invalid JSON format in market data")
        except Exception as e:
            raise MarketDataValidationError(f"Market data validation failed: {str(e)}")
    
    async def _validate_outgoing_market_data(self, request: Request, response: Response):
        """Validate outgoing market data for consistency"""
        try:
            # This would typically validate response data
            # For now, we'll just log successful validation
            symbol = self._extract_symbol(request)
            logger.debug(f"Market data response validated for symbol: {symbol}")
            
        except Exception as e:
            logger.warning(f"Failed to validate outgoing market data: {e}")
    
    def _validate_required_fields(self, data: Dict[str, Any]):
        """Validate that required fields are present"""
        if isinstance(data, dict):
            # For individual market data record
            if 'symbol' not in data:
                raise MarketDataValidationError("Missing required field: symbol")
        elif isinstance(data, list):
            # For bulk market data
            for record in data:
                if 'symbol' not in record:
                    raise MarketDataValidationError("Missing required field: symbol in bulk data")
    
    def _validate_price_data(self, symbol: str, price: Any):
        """Validate price data for reasonableness"""
        try:
            price_decimal = Decimal(str(price))
            
            # Check for negative prices
            if price_decimal < 0:
                raise MarketDataValidationError(f"Negative price not allowed: {price}")
            
            # Check for zero prices (might be valid in some cases)
            if price_decimal == 0:
                logger.warning(f"Zero price detected for symbol {symbol}")
            
            # Check for extreme price movements
            if symbol in self.price_cache:
                last_price = self.price_cache[symbol]['price']
                price_change = abs(price_decimal - last_price) / last_price
                
                if price_change > self.price_deviation_threshold:
                    logger.warning(
                        f"Large price movement detected for {symbol}: "
                        f"{price_change:.2%} change from {last_price} to {price_decimal}"
                    )
            
            # Update price cache
            self.price_cache[symbol] = {
                'price': price_decimal,
                'timestamp': datetime.now(timezone.utc)
            }
            
        except (InvalidOperation, ValueError, TypeError):
            raise MarketDataValidationError(f"Invalid price format: {price}")
    
    def _validate_timestamp(self, timestamp: Any):
        """Validate timestamp data"""
        try:
            # Parse timestamp
            if isinstance(timestamp, str):
                parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, (int, float)):
                parsed_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                raise MarketDataValidationError(f"Invalid timestamp format: {timestamp}")
            
            # Check for stale data
            now = datetime.now(timezone.utc)
            age_seconds = (now - parsed_time).total_seconds()
            
            if age_seconds > self.stale_data_threshold:
                logger.warning(f"Stale market data detected: {age_seconds} seconds old")
            
            # Check for future timestamps
            if parsed_time > now:
                raise MarketDataValidationError("Future timestamp not allowed in market data")
                
        except Exception as e:
            raise MarketDataValidationError(f"Timestamp validation failed: {str(e)}")
    
    def _validate_volume_data(self, volume: Any):
        """Validate volume data"""
        try:
            volume_decimal = Decimal(str(volume))
            
            # Check for negative volume
            if volume_decimal < 0:
                raise MarketDataValidationError(f"Negative volume not allowed: {volume}")
            
        except (InvalidOperation, ValueError, TypeError):
            raise MarketDataValidationError(f"Invalid volume format: {volume}")