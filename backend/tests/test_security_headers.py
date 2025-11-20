import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import create_security_headers_middleware
from app.core.config import settings


def _create_app_with_security(is_production: bool, enable_hsts: bool = False) -> TestClient:
    app = FastAPI()
    app.add_middleware(
        create_security_headers_middleware(
            is_production=is_production,
            enable_hsts=enable_hsts,
        )
    )

    @app.get("/ping")
    def ping():
        return {"status": "ok"}

    return TestClient(app)


def test_security_headers_dev_profile():
    """Development mode should set relaxed CSP and skip HSTS/cache headers."""
    client = _create_app_with_security(is_production=False, enable_hsts=True)

    response = client.get("/ping")

    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy", "")
    assert "unsafe-inline" in csp  # relaxed for dev
    assert "Strict-Transport-Security" not in response.headers
    assert "Cache-Control" not in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_security_headers_prod_with_hsts():
    """Production mode should include HSTS and strict CSP."""
    client = _create_app_with_security(is_production=True, enable_hsts=True)

    response = client.get("/ping")

    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy", "")
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    hsts = response.headers.get("Strict-Transport-Security", "")
    assert f"max-age={settings.HSTS_MAX_AGE}" in hsts
    assert response.headers.get("Cache-Control") == "no-store, no-cache, must-revalidate, private"
    assert response.headers.get("Pragma") == "no-cache"
