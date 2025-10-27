"""
HTTPS Redirect Middleware

This middleware enforces HTTPS in production by redirecting all HTTP requests
to HTTPS. This should only be enabled when:
1. Running in production (DEBUG=False)
2. Behind a proper TLS/SSL termination (e.g., nginx, load balancer)
3. SSL certificates are properly configured

For development, this should be disabled to allow HTTP connections.
"""

from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response
from starlette.datastructures import URL


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS

    This middleware checks the request scheme and redirects to HTTPS if needed.
    It handles both direct connections and connections behind proxies that set
    X-Forwarded-Proto header.
    """

    def __init__(self, app, enabled: bool = False):
        """
        Initialize HTTPS redirect middleware

        Args:
            app: FastAPI application instance
            enabled: Whether to enable HTTPS redirection (default: False)
        """
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check request scheme and redirect to HTTPS if needed

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response (redirect to HTTPS or normal response)
        """
        # Skip if not enabled
        if not self.enabled:
            return await call_next(request)

        # Check for HTTPS
        # Consider both direct connection and proxy headers
        is_https = self._is_https_request(request)

        # Redirect to HTTPS if not already
        if not is_https:
            return self._redirect_to_https(request)

        # Continue with request
        return await call_next(request)

    def _is_https_request(self, request: Request) -> bool:
        """
        Check if request is already using HTTPS

        Checks both the request URL scheme and X-Forwarded-Proto header
        (for requests behind a proxy/load balancer)

        Args:
            request: HTTP request

        Returns:
            True if HTTPS, False otherwise
        """
        # Check direct connection scheme
        if request.url.scheme == "https":
            return True

        # Check X-Forwarded-Proto header (for proxies/load balancers)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        if forwarded_proto == "https":
            return True

        # Check X-Forwarded-Ssl header (alternative)
        forwarded_ssl = request.headers.get("X-Forwarded-Ssl", "").lower()
        if forwarded_ssl == "on":
            return True

        return False

    def _redirect_to_https(self, request: Request) -> RedirectResponse:
        """
        Redirect HTTP request to HTTPS

        Args:
            request: HTTP request

        Returns:
            Redirect response to HTTPS URL
        """
        # Build HTTPS URL
        url = URL(str(request.url))
        https_url = url.replace(scheme="https")

        # Return permanent redirect (301)
        return RedirectResponse(
            url=str(https_url),
            status_code=301  # Permanent redirect
        )


def create_https_redirect_middleware(enabled: bool = False):
    """
    Factory function to create HTTPS redirect middleware

    Args:
        enabled: Whether to enable HTTPS redirection

    Returns:
        HTTPSRedirectMiddleware instance

    Example:
        # Enable in production only
        app.add_middleware(
            create_https_redirect_middleware(
                enabled=not settings.DEBUG  # Only in production
            )
        )

    Note:
        - Only enable this in production with proper SSL/TLS setup
        - Ensure your reverse proxy/load balancer sets X-Forwarded-Proto
        - Test thoroughly before deploying to production
        - Consider using HSTS header (Strict-Transport-Security) as well
    """
    def middleware(app):
        return HTTPSRedirectMiddleware(app, enabled=enabled)
    return middleware
