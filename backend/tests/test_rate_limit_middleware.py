import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.middleware.rate_limit import create_rate_limiter


def _client(per_minute: int = 2, per_hour: int = 10) -> TestClient:
    """Build isolated app with rate limiter for testing."""
    app = FastAPI()
    app.add_middleware(create_rate_limiter(per_minute, per_hour))

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return TestClient(app)


def test_rate_limit_blocks_after_threshold():
    client = _client(per_minute=2, per_hour=100)

    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200

    with pytest.raises(HTTPException) as exc:
        client.get("/ping")

    assert exc.value.status_code == 429
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "Rate limit exceeded"
    assert "retry_after" in detail


def test_health_endpoints_bypass_rate_limit():
    client = _client(per_minute=1, per_hour=1)

    # Health endpoints should not increment counters or be blocked
    for path in ["/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"]:
        response = client.get(path)
        # docs/redoc/openapi may not be mounted, allow 404 but not 429
        assert response.status_code != 429
