"""
Tests for error handling and error messages.
"""

import pytest
from fastapi.testclient import TestClient


def test_404_error(client: TestClient):
    """Test 404 error handling."""
    response = client.get("/v1/nonexistent/endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] is True
    assert "HTTP_404" in data["code"]


def test_validation_error_format(client: TestClient):
    """Test validation error format."""
    # Invalid batch request
    response = client.post(
        "/v1/balances/batch",
        json={"addresses": "not_a_list"}
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] is True
    assert "VALIDATION_ERROR" in data["code"]
    assert "details" in data
    assert "summary" in data["details"]
    assert "help" in data["details"]


def test_invalid_address_error(client: TestClient):
    """Test error for invalid address."""
    response = client.get("/v1/balances/invalid_address")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] is True
    assert "INVALID_ADDRESS" in data["code"]
    assert "message" in data


def test_error_response_structure(client: TestClient):
    """Test that all error responses have consistent structure."""
    # Test various error scenarios
    error_endpoints = [
        ("/v1/balances/invalid", 400),
        ("/v1/nonexistent", 404),
    ]
    
    for endpoint, expected_status in error_endpoints:
        response = client.get(endpoint)
        assert response.status_code == expected_status
        data = response.json()
        assert "error" in data
        assert data["error"] is True
        assert "code" in data
        assert "message" in data


def test_rate_limit_headers(client: TestClient):
    """Test that rate limit headers are present."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    
    # Check for rate limit headers
    headers = response.headers
    assert "X-RateLimit-Limit-Minute" in headers or "X-RateLimit-Limit-Hour" in headers


def test_request_id_header(client: TestClient):
    """Test that request ID is in headers."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    
    # Request ID should be a valid UUID format
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36  # UUID format
    assert request_id.count("-") == 4


def test_process_time_header(client: TestClient):
    """Test that process time is in headers."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    
    # Process time should be a valid float
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0

