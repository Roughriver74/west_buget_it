"""
Rate limiting middleware for API protection with Redis support
"""
import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import log_warning, log_info
from app.core.config import settings

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent API abuse

    Supports two backends:
    1. Redis (distributed) - for production with multiple servers
    2. In-memory (local) - for development or single server

    Default limits: 100 requests per minute, 1000 requests per hour
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = None,
        requests_per_hour: int = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_DEFAULT_REQUESTS_PER_MINUTE
        self.requests_per_hour = requests_per_hour or settings.RATE_LIMIT_DEFAULT_REQUESTS_PER_HOUR

        # Initialize Redis if enabled and available
        self.use_redis = settings.USE_REDIS and REDIS_AVAILABLE
        self.redis_client: Optional[redis.Redis] = None

        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True,
                    socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                )
                # Test connection
                self.redis_client.ping()
                log_info(f"Rate limiting using Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}", "RateLimit")
            except Exception as e:
                log_warning(f"Failed to connect to Redis, falling back to in-memory: {e}", "RateLimit")
                self.use_redis = False
                self.redis_client = None

        # In-memory storage (fallback or when Redis not enabled)
        if not self.use_redis:
            log_info("Rate limiting using in-memory storage (not distributed)", "RateLimit")
            self.request_times: Dict[str, list] = defaultdict(list)
            self.cleanup_interval = settings.RATE_LIMIT_CLEANUP_INTERVAL
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

    # ========== REDIS BACKEND ==========

    def _is_rate_limited_redis(self, ip: str) -> Tuple[bool, str]:
        """Check rate limit using Redis backend"""
        current_time = int(time.time())

        # Keys for minute and hour windows
        minute_key = f"ratelimit:{ip}:minute:{current_time // 60}"
        hour_key = f"ratelimit:{ip}:hour:{current_time // 3600}"

        try:
            # Increment counters (atomic operations)
            minute_count = self.redis_client.incr(minute_key)
            hour_count = self.redis_client.incr(hour_key)

            # Set expiration on first increment (TTL)
            if minute_count == 1:
                self.redis_client.expire(minute_key, settings.REDIS_MINUTE_WINDOW_TTL)
            if hour_count == 1:
                self.redis_client.expire(hour_key, settings.REDIS_HOUR_WINDOW_TTL)

            # Check limits
            if minute_count > self.requests_per_minute:
                return True, f"Rate limit exceeded: {minute_count} requests in last minute (max {self.requests_per_minute})"

            if hour_count > self.requests_per_hour:
                return True, f"Rate limit exceeded: {hour_count} requests in last hour (max {self.requests_per_hour})"

            return False, ""

        except Exception as e:
            log_warning(f"Redis error in rate limiting: {e}, allowing request", "RateLimit")
            # Fail open - allow request on Redis errors
            return False, ""

    def _get_retry_after_redis(self, ip: str) -> int:
        """Calculate seconds until rate limit resets (Redis backend)"""
        current_time = int(time.time())

        minute_key = f"ratelimit:{ip}:minute:{current_time // 60}"
        hour_key = f"ratelimit:{ip}:hour:{current_time // 3600}"

        try:
            minute_count = int(self.redis_client.get(minute_key) or 0)
            hour_count = int(self.redis_client.get(hour_key) or 0)

            # If minute limit exceeded, return seconds until next minute
            if minute_count >= self.requests_per_minute:
                return 60 - (current_time % 60)

            # If hour limit exceeded, return seconds until next hour
            if hour_count >= self.requests_per_hour:
                return 3600 - (current_time % 3600)

            return 0
        except Exception:
            return 60  # Default retry after 1 minute on error

    # ========== IN-MEMORY BACKEND ==========

    def _cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory bloat (in-memory backend)"""
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

    def _is_rate_limited_memory(self, ip: str) -> Tuple[bool, str]:
        """Check rate limit using in-memory backend"""
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

    def _get_retry_after_memory(self, ip: str) -> int:
        """Calculate seconds until rate limit resets (in-memory backend)"""
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

    # ========== UNIFIED INTERFACE ==========

    def _is_rate_limited(self, ip: str) -> Tuple[bool, str]:
        """Check if IP has exceeded rate limits (unified interface)"""
        if self.use_redis:
            return self._is_rate_limited_redis(ip)
        else:
            return self._is_rate_limited_memory(ip)

    def _get_retry_after(self, ip: str) -> int:
        """Calculate seconds until rate limit resets (unified interface)"""
        if self.use_redis:
            return self._get_retry_after_redis(ip)
        else:
            return self._get_retry_after_memory(ip)

    def _record_request(self, ip: str):
        """Record this request (backend-specific)"""
        if self.use_redis:
            # Already recorded in _is_rate_limited_redis (incr operations)
            pass
        else:
            # In-memory: append timestamp
            current_time = time.time()
            self.request_times[ip].append(current_time)

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting for health check and static files
        if request.url.path in ["/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Periodic cleanup (in-memory only)
        if not self.use_redis:
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
        self._record_request(client_ip)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response (best effort for in-memory)
        if not self.use_redis:
            current_time = time.time()
            minute_ago = current_time - 60
            requests_last_minute = sum(1 for t in self.request_times[client_ip] if t > minute_ago)

            response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.requests_per_minute - requests_last_minute))
            response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)

        return response


# Factory function
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
