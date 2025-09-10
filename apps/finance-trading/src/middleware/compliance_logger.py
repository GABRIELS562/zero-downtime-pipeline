"""
Compliance Logging Middleware
Automatic SOX compliance logging for all financial transactions
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional
from uuid import uuid4
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.services.sox_compliance import SOXComplianceService, EventType

logger = logging.getLogger(__name__)

class ComplianceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic SOX compliance logging
    Logs all financial transactions with chain of custody
    """
    
    def __init__(self, app, sox_compliance_service: Optional[SOXComplianceService] = None):
        super().__init__(app)
        self.sox_compliance = sox_compliance_service or SOXComplianceService()
        self.session_tracking: Dict[str, Dict[str, Any]] = {}
        
        # Define financial endpoints that require compliance logging
        self.financial_endpoints = {
            '/api/v1/trading/orders': EventType.ORDER_CREATION,
            '/api/v1/trading/orders/{order_id}': EventType.ORDER_MODIFICATION,
            '/api/v1/trading/portfolio': EventType.POSITION_CHANGE,
            '/api/v1/trading/market-data': EventType.TRADE_EXECUTION,
            '/compliance/log-event': EventType.REGULATORY_REPORT
        }
        
        # Sensitive data fields that should be logged
        self.sensitive_fields = {
            'quantity', 'price', 'stop_price', 'balance', 'available_balance',
            'total_value', 'positions_value', 'total_pnl', 'financial_impact'
        }
        
        # HTTP methods that require compliance logging
        self.logged_methods = {'POST', 'PUT', 'PATCH', 'DELETE'}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with compliance logging"""
        start_time = time.time()
        
        # Generate request ID for tracing
        request_id = str(uuid4())
        
        # Extract session information
        session_info = self._extract_session_info(request)
        
        # Check if this endpoint requires compliance logging
        requires_logging = self._requires_compliance_logging(request)
        
        # Log pre-request information
        if requires_logging:
            await self._log_request_start(request, request_id, session_info)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Log post-request information
            if requires_logging:
                await self._log_request_completion(
                    request, response, request_id, session_info, start_time
                )
            
            return response
            
        except Exception as e:
            # Log error information
            if requires_logging:
                await self._log_request_error(request, e, request_id, session_info)
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
    
    def _extract_session_info(self, request: Request) -> Dict[str, Any]:
        """Extract session information from request"""
        return {
            'ip_address': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'session_id': request.headers.get('x-session-id') or str(uuid4()),
            'user_id': request.headers.get('x-user-id'),
            'request_id': request.headers.get('x-request-id') or str(uuid4()),
            'correlation_id': request.headers.get('x-correlation-id'),
            'authorization': bool(request.headers.get('authorization')),
            'content_type': request.headers.get('content-type'),
            'accept': request.headers.get('accept')
        }
    
    def _requires_compliance_logging(self, request: Request) -> bool:
        """Determine if request requires compliance logging"""
        # Check if it's a financial endpoint
        path = request.url.path
        method = request.method
        
        # Log all financial endpoints
        if any(endpoint in path for endpoint in self.financial_endpoints.keys()):
            return True
        
        # Log all state-changing operations
        if method in self.logged_methods:
            return True
        
        # Log all authenticated requests to sensitive endpoints
        if request.headers.get('authorization') and any(
            sensitive in path for sensitive in ['trading', 'portfolio', 'orders', 'compliance']
        ):
            return True
        
        return False
    
    async def _log_request_start(
        self, 
        request: Request, 
        request_id: str, 
        session_info: Dict[str, Any]
    ):
        """Log request start for compliance"""
        try:
            # Extract request body if present
            request_body = await self._extract_request_body(request)
            
            # Determine event type
            event_type = self._determine_event_type(request)
            
            # Create event data
            event_data = {
                'request_id': request_id,
                'http_method': request.method,
                'endpoint': request.url.path,
                'query_params': dict(request.query_params),
                'request_body': request_body,
                'request_size': len(str(request_body)) if request_body else 0,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'request_start',
                'headers': dict(request.headers),
                'compliance_required': True
            }
            
            # Calculate financial impact if applicable
            financial_impact = self._calculate_financial_impact(request_body)
            
            # Log to SOX compliance
            await self.sox_compliance.log_audit_event(
                event_type=event_type,
                event_data=event_data,
                user_id=session_info['user_id'],
                session_id=session_info['session_id'],
                ip_address=session_info['ip_address'],
                user_agent=session_info['user_agent'],
                financial_impact=financial_impact,
                compliance_tags=['middleware_logged', 'request_start', 'financial_transaction']
            )
            
            logger.info(f"Compliance request logged: {request_id} - {request.method} {request.url.path}")
            
        except Exception as e:
            logger.error(f"Error logging request start: {e}")
    
    async def _log_request_completion(
        self,
        request: Request,
        response: Response,
        request_id: str,
        session_info: Dict[str, Any],
        start_time: float
    ):
        """Log request completion for compliance"""
        try:
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Extract response body if needed
            response_body = await self._extract_response_body(response)
            
            # Determine event type
            event_type = self._determine_event_type(request)
            
            # Create event data
            event_data = {
                'request_id': request_id,
                'http_method': request.method,
                'endpoint': request.url.path,
                'status_code': response.status_code,
                'response_body': response_body,
                'response_size': len(str(response_body)) if response_body else 0,
                'processing_time_ms': round(processing_time * 1000, 2),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'request_completion',
                'success': 200 <= response.status_code < 300,
                'compliance_verified': True
            }
            
            # Calculate financial impact from response
            financial_impact = self._calculate_financial_impact(response_body)
            
            # Log to SOX compliance
            await self.sox_compliance.log_audit_event(
                event_type=event_type,
                event_data=event_data,
                user_id=session_info['user_id'],
                session_id=session_info['session_id'],
                ip_address=session_info['ip_address'],
                user_agent=session_info['user_agent'],
                financial_impact=financial_impact,
                compliance_tags=['middleware_logged', 'request_completion', 'financial_transaction']
            )
            
            logger.info(f"Compliance response logged: {request_id} - {response.status_code} ({processing_time*1000:.2f}ms)")
            
        except Exception as e:
            logger.error(f"Error logging request completion: {e}")
    
    async def _log_request_error(
        self,
        request: Request,
        error: Exception,
        request_id: str,
        session_info: Dict[str, Any]
    ):
        """Log request error for compliance"""
        try:
            # Create error event data
            event_data = {
                'request_id': request_id,
                'http_method': request.method,
                'endpoint': request.url.path,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'request_error',
                'compliance_concern': True,
                'requires_investigation': True
            }
            
            # Log to SOX compliance
            await self.sox_compliance.log_audit_event(
                event_type=EventType.FRAUD_DETECTION,  # Errors might indicate fraud
                event_data=event_data,
                user_id=session_info['user_id'],
                session_id=session_info['session_id'],
                ip_address=session_info['ip_address'],
                user_agent=session_info['user_agent'],
                compliance_tags=['middleware_logged', 'request_error', 'investigation_required']
            )
            
            logger.error(f"Compliance error logged: {request_id} - {type(error).__name__}: {error}")
            
        except Exception as e:
            logger.error(f"Error logging request error: {e}")
    
    async def _extract_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract request body for logging"""
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                # Handle JSON requests
                if request.headers.get('content-type', '').startswith('application/json'):
                    body = await request.body()
                    if body:
                        import json
                        return json.loads(body.decode())
                
                # Handle form data
                elif request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded'):
                    form_data = await request.form()
                    return dict(form_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting request body: {e}")
            return {'error': 'Unable to extract request body'}
    
    async def _extract_response_body(self, response: Response) -> Optional[Dict[str, Any]]:
        """Extract response body for logging"""
        try:
            # Only log response bodies for financial endpoints
            if hasattr(response, 'body') and response.body:
                if response.headers.get('content-type', '').startswith('application/json'):
                    import json
                    return json.loads(response.body.decode())
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting response body: {e}")
            return {'error': 'Unable to extract response body'}
    
    def _determine_event_type(self, request: Request) -> EventType:
        """Determine SOX event type based on request"""
        path = request.url.path
        method = request.method
        
        # Map endpoints to event types
        if '/orders' in path:
            if method == 'POST':
                return EventType.ORDER_CREATION
            elif method in ['PUT', 'PATCH']:
                return EventType.ORDER_MODIFICATION
            elif method == 'DELETE':
                return EventType.ORDER_CANCELLATION
            else:
                return EventType.TRADE_EXECUTION
        
        elif '/portfolio' in path:
            return EventType.POSITION_CHANGE
        
        elif '/market-data' in path:
            return EventType.TRADE_EXECUTION
        
        elif '/compliance' in path:
            return EventType.REGULATORY_REPORT
        
        elif '/login' in path:
            return EventType.USER_LOGIN
        
        elif '/logout' in path:
            return EventType.USER_LOGOUT
        
        else:
            return EventType.TRADE_EXECUTION
    
    def _calculate_financial_impact(self, data: Optional[Dict[str, Any]]) -> Optional[float]:
        """Calculate financial impact from request/response data"""
        if not data:
            return None
        
        try:
            # Look for financial values in the data
            financial_impact = 0.0
            
            # Check for order-related financial impact
            if 'quantity' in data and 'price' in data:
                quantity = float(data['quantity'])
                price = float(data['price'])
                financial_impact = quantity * price
            
            # Check for portfolio-related financial impact
            elif 'total_value' in data:
                financial_impact = float(data['total_value'])
            
            # Check for P&L impact
            elif 'total_pnl' in data:
                financial_impact = abs(float(data['total_pnl']))
            
            # Check for balance changes
            elif 'balance' in data:
                financial_impact = float(data['balance'])
            
            return financial_impact if financial_impact > 0 else None
            
        except (ValueError, TypeError, KeyError):
            return None
    
    def _contains_sensitive_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains sensitive financial information"""
        if not data:
            return False
        
        # Check for sensitive field names
        for field in self.sensitive_fields:
            if field in data:
                return True
        
        # Check for nested sensitive data
        for value in data.values():
            if isinstance(value, dict) and self._contains_sensitive_data(value):
                return True
        
        return False
    
    async def track_user_session(self, user_id: str, session_id: str, action: str):
        """Track user session for compliance"""
        try:
            # Update session tracking
            if user_id not in self.session_tracking:
                self.session_tracking[user_id] = {}
            
            self.session_tracking[user_id][session_id] = {
                'last_activity': datetime.now(timezone.utc),
                'action_count': self.session_tracking[user_id].get(session_id, {}).get('action_count', 0) + 1,
                'last_action': action
            }
            
            # Log session activity
            await self.sox_compliance.track_user_activity(
                user_id=user_id,
                activity_type=action,
                activity_details={
                    'session_id': session_id,
                    'action': action,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                session_id=session_id,
                ip_address="middleware_tracked",
                user_agent="system_tracking"
            )
            
        except Exception as e:
            logger.error(f"Error tracking user session: {e}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics for monitoring"""
        try:
            active_sessions = 0
            total_actions = 0
            
            for user_sessions in self.session_tracking.values():
                for session_data in user_sessions.values():
                    # Consider session active if activity within last hour
                    if (datetime.now(timezone.utc) - session_data['last_activity']).total_seconds() < 3600:
                        active_sessions += 1
                    total_actions += session_data['action_count']
            
            return {
                'active_sessions': active_sessions,
                'total_tracked_users': len(self.session_tracking),
                'total_actions_logged': total_actions,
                'last_update': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {
                'error': 'Unable to retrieve session statistics',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }