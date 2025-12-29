"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "v1"
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


def test_health_check_root(client: TestClient):
    """Test root health check endpoint (convenience route)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "v1"


def test_status_endpoint(client: TestClient):
    """Test status endpoint."""
    response = client.get("/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "rpc_connected" in data
    assert "components" in data


def test_detailed_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "components" in data
    assert "rpc_status" in data
    assert "sdk_status" in data
    
    # Check component structure
    assert "api" in data["components"]
    assert "rpc" in data["components"]
    assert "sdk" in data["components"]


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint."""
    response = client.get("/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cache" in data
    assert "transactions" in data
    assert "rpc" in data
    assert "rate_limits" in data
    
    # Check cache stats structure
    assert "size" in data["cache"]
    assert "hits" in data["cache"]
    assert "misses" in data["cache"]
    
    # Check rate limits
    assert "per_minute" in data["rate_limits"]
    assert "per_hour" in data["rate_limits"]
    assert "per_day" in data["rate_limits"]

