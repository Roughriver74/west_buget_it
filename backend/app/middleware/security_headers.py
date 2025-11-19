"""
Security Headers Middleware

This middleware adds security headers to all HTTP responses to protect against
common web vulnerabilities:

- HSTS (HTTP Strict Transport Security): Forces HTTPS connections
- CSP (Content Security Policy): Prevents XSS attacks
- X-Frame-Options: Prevents clickjacking attacks
- X-Content-Type-Options: Prevents MIME-type sniffing
- X-XSS-Protection: Additional XSS protection for older browsers
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Controls browser features

Based on OWASP security best practices.
"""

from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses

    This middleware is configurable based on environment (dev/prod) and can be
    customized for specific security requirements.
    """

    def __init__(self, app, is_production: bool = False, enable_hsts: bool = False):
        """
        Initialize security headers middleware

        Args:
            app: FastAPI application instance
            is_production: Whether running in production mode
            enable_hsts: Whether to enable HSTS (requires HTTPS)
        """
        super().__init__(app)
        self.is_production = is_production
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response with security headers added
        """
        # Process request
        response = await call_next(request)

        # Add security headers
        headers = self._get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value

        return response

    def _get_security_headers(self) -> dict:
        """
        Get security headers based on configuration

        Returns:
            Dictionary of security headers
        """
        headers = {}

        # HSTS (HTTP Strict Transport Security)
        # Only enable in production with HTTPS
        if self.enable_hsts and self.is_production:
            # max-age from settings (default: 1 year), includeSubDomains, preload
            headers["Strict-Transport-Security"] = f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains; preload"

        # CSP (Content Security Policy)
        # Restrictive policy for API - adjust for frontend if needed
        if self.is_production:
            # Production: Strict CSP
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # Development: Relaxed CSP for easier debugging
            headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' http://localhost:* ws://localhost:*; "
                "frame-ancestors 'none'"
            )

        # X-Frame-Options: Prevents clickjacking
        # DENY = Cannot be displayed in iframe at all
        # SAMEORIGIN would allow iframes from same origin
        headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevents MIME-type sniffing
        # Ensures browser respects Content-Type header
        headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Legacy XSS protection for older browsers
        # Modern browsers use CSP instead, but this doesn't hurt
        # 1; mode=block = Enable XSS filter and block page if attack detected
        headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Controls referrer information
        # strict-origin-when-cross-origin = Send full URL for same-origin,
        # origin only for cross-origin HTTPS, nothing for HTTP
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (formerly Feature-Policy)
        # Disable potentially dangerous browser features
        headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # X-Permitted-Cross-Domain-Policies
        # Restrict Adobe Flash and PDF cross-domain requests
        headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Cache-Control for sensitive data
        # Only set for production to prevent caching of sensitive data
        if self.is_production:
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            headers["Pragma"] = "no-cache"

        return headers


def create_security_headers_middleware(is_production: bool = False, enable_hsts: bool = False):
    """
    Factory function to create security headers middleware

    Args:
        is_production: Whether running in production mode
        enable_hsts: Whether to enable HSTS (requires HTTPS)

    Returns:
        SecurityHeadersMiddleware instance

    Example:
        app.add_middleware(
            create_security_headers_middleware(
                is_production=not settings.DEBUG,
                enable_hsts=True  # Only if using HTTPS
            )
        )
    """
    def middleware(app):
        return SecurityHeadersMiddleware(app, is_production=is_production, enable_hsts=enable_hsts)
    return middleware
