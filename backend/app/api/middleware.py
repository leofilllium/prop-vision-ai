"""
Request logging middleware for API analytics.

Records endpoint, method, status code, and response time for every request.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("propvision.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs API request details for analytics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request, measure response time, add rate limit headers."""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Add rate limit headers if set by dependency
        if hasattr(request.state, "rate_limit"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_remaining)
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_reset)

        # Log request details (skip health checks and docs)
        path = request.url.path
        if not path.endswith("/health") and not path.endswith("/docs"):
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "partner_id": getattr(request.state, "partner_id", None),
                },
            )

        return response
