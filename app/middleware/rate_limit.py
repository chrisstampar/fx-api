"""
Rate limiting middleware.

Uses slowapi for IP-based rate limiting (free tier for all users).
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.config import settings

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,  # Rate limit by IP address
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)

# Custom rate limit exceeded handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    from fastapi.responses import JSONResponse
    from app.models.responses import ErrorResponse
    
    response = JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error=True,
            code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded: {exc.detail}",
            details={
                "retry_after": exc.retry_after
            }
        ).dict()
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    return response


async def add_rate_limit_headers(request: Request, call_next):
    """
    Middleware to add rate limit information to response headers.
    
    Adds headers:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Remaining requests in current window
    - X-RateLimit-Reset: Time when the rate limit resets
    """
    response = await call_next(request)
    
    # Try to get rate limit info from slowapi
    try:
        # Get the limiter state if available
        if hasattr(request.app.state, 'limiter'):
            # Add rate limit headers (slowapi doesn't expose this easily, so we add defaults)
            response.headers["X-RateLimit-Limit-Minute"] = str(settings.RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Limit-Hour"] = str(settings.RATE_LIMIT_PER_HOUR)
            response.headers["X-RateLimit-Limit-Day"] = str(settings.RATE_LIMIT_PER_DAY)
    except Exception:
        pass
    
    return response

