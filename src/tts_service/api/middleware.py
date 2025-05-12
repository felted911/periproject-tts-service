# API middleware
import time
import uuid
from typing import Callable, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..infrastructure import get_logger

logger = get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.
        
        Args:
            request: Request object
            call_next: Next middleware in the chain
            
        Returns:
            Response object
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
            },
        )
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            duration_ms = round((time.time() - start_time) * 1000)
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log exception
            duration_ms = round((time.time() - start_time) * 1000)
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                },
            )
            raise
