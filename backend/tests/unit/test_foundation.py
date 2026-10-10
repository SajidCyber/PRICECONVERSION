"""Unit Tests for Phase 1 Foundation: Settings, DB Session, Error Handlers, and Health."""

import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.core.database import SessionLocal, get_db
from app.core.exceptions import AppError, EntityNotFoundError, SSRFSecurityError
from app.main import app

client = TestClient(app)


def test_settings_initialization():
    """Verify settings loads properly and parses CORS origins."""
    settings = Settings(
        APP_NAME="Test E-Commerce Intelligence",
        CORS_ORIGINS="http://localhost:3000,http://localhost:8000",
    )
    assert settings.APP_NAME == "Test E-Commerce Intelligence"
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://localhost:8000" in settings.CORS_ORIGINS


def test_root_welcome_endpoint():
    """Verify root GET / endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome to" in data["message"]
    assert data["docs_url"] == "/api/v1/docs"
    assert data["health_url"] == "/api/v1/health"


def test_health_check_endpoint():
    """Verify /api/v1/health returns database connectivity status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["database_connected"] is True
    assert "version" in body["data"]
    assert "timestamp" in body["data"]


def test_custom_exception_handling():
    """Verify custom domain exceptions produce structured error envelopes."""

    @app.get("/api/v1/test-error-notfound")
    def trigger_not_found():
        raise EntityNotFoundError("Product", "prod_9999")

    @app.get("/api/v1/test-error-ssrf")
    def trigger_ssrf():
        raise SSRFSecurityError("http://169.254.169.254/latest/meta-data", "Private cloud metadata is restricted")

    # Test EntityNotFoundError
    resp1 = client.get("/api/v1/test-error-notfound")
    assert resp1.status_code == 404
    data1 = resp1.json()
    assert data1["success"] is False
    assert data1["error"]["code"] == "EntityNotFoundError"
    assert "prod_9999" in data1["error"]["message"]

    # Test SSRFSecurityError
    resp2 = client.get("/api/v1/test-error-ssrf")
    assert resp2.status_code == 403
    data2 = resp2.json()
    assert data2["success"] is False
    assert data2["error"]["code"] == "SSRFSecurityError"
    assert "SSRF Security Violation" in data2["error"]["message"]
