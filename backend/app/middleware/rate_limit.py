"""
Rate limiting middleware for API protection
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import log_warning


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent API abuse

    Implements a sliding window rate limiter that tracks requests per IP address.
    Default limits: 100 requests per minute, 1000 requests per hour
    """

    def __init__(self, app, requests_per_minute: int = 100, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Store: {ip: [(timestamp1, timestamp2, ...)]}
        self.request_times: Dict[str, list] = defaultdict(list)

        # Cleanup interval in seconds (clean up old entries every 5 minutes)
        self.cleanup_interval = 300
        self.last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies"""
        # Check X-Forwarded-For header (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory bloat"""
        current_time = time.time()

        # Only cleanup periodically
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        hour_ago = current_time - 3600

        # Remove old timestamps and empty IP entries
        ips_to_remove = []
        for ip, timestamps in self.request_times.items():
            # Keep only timestamps from last hour
            self.request_times[ip] = [t for t in timestamps if t > hour_ago]

            # Mark empty entries for removal
            if not self.request_times[ip]:
                ips_to_remove.append(ip)

        # Remove empty entries
        for ip in ips_to_remove:
            del self.request_times[ip]

        self.last_cleanup = current_time

    def _is_rate_limited(self, ip: str) -> Tuple[bool, str]:
        """
        Check if IP has exceeded rate limits

        Returns:
            (is_limited, reason)
        """
        current_time = time.time()
        timestamps = self.request_times[ip]

        # Count requests in last minute
        minute_ago = current_time - 60
        requests_last_minute = sum(1 for t in timestamps if t > minute_ago)

        if requests_last_minute >= self.requests_per_minute:
            return True, f"Rate limit exceeded: {requests_last_minute} requests in last minute (max {self.requests_per_minute})"

        # Count requests in last hour
        hour_ago = current_time - 3600
        requests_last_hour = sum(1 for t in timestamps if t > hour_ago)

        if requests_last_hour >= self.requests_per_hour:
            return True, f"Rate limit exceeded: {requests_last_hour} requests in last hour (max {self.requests_per_hour})"

        return False, ""

    def _get_retry_after(self, ip: str) -> int:
        """Calculate seconds until rate limit resets"""
        current_time = time.time()
        timestamps = self.request_times[ip]

        if not timestamps:
            return 0

        # Find oldest timestamp in the last minute
        minute_ago = current_time - 60
        minute_timestamps = [t for t in timestamps if t > minute_ago]

        if len(minute_timestamps) >= self.requests_per_minute:
            # Rate limited by minute - return seconds until oldest request expires
            oldest_in_minute = min(minute_timestamps)
            return int(60 - (current_time - oldest_in_minute)) + 1

        # Rate limited by hour - return seconds until we're under the limit
        hour_ago = current_time - 3600
        hour_timestamps = [t for t in timestamps if t > hour_ago]

        if len(hour_timestamps) >= self.requests_per_hour:
            oldest_in_hour = min(hour_timestamps)
            return int(3600 - (current_time - oldest_in_hour)) + 1

        return 0

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting for health check and static files
        if request.url.path in ["/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Periodic cleanup
        self._cleanup_old_requests()

        # Check rate limit
        is_limited, reason = self._is_rate_limited(client_ip)

        if is_limited:
            retry_after = self._get_retry_after(client_ip)
            log_warning(f"Rate limit exceeded for IP {client_ip}: {reason}", "RateLimit")

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": reason,
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        # Record this request
        current_time = time.time()
        self.request_times[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        minute_ago = current_time - 60
        requests_last_minute = sum(1 for t in self.request_times[client_ip] if t > minute_ago)

        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.requests_per_minute - requests_last_minute))
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)

        return response


# Default rate limiter instance
def create_rate_limiter(
    requests_per_minute: int = 100,
    requests_per_hour: int = 1000
) -> RateLimitMiddleware:
    """
    Create a rate limiter middleware instance

    Args:
        requests_per_minute: Maximum requests per minute per IP
        requests_per_hour: Maximum requests per hour per IP

    Returns:
        RateLimitMiddleware instance
    """
    def _middleware_factory(app):
        return RateLimitMiddleware(app, requests_per_minute, requests_per_hour)

    return _middleware_factory
