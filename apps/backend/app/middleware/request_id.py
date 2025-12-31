"""
Request ID middleware for tracking requests across logs
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import request_id_var

logger = __import__('logging').getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request_id to all requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or get request ID from header
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Add request_id to request state
        request.state.request_id = request_id
        
        # Set request_id in context variable (thread-safe and async-safe)
        # The filter in logging.py will pick this up automatically
        token = request_id_var.set(request_id)
        
        try:
            response = await call_next(request)
            # Add request_id to response header
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Reset context (filter will still work but return 'unknown' if no context)
            request_id_var.reset(token)



