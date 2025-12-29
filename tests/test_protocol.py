"""
Tests for protocol information endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_get_protocol_nav(client: TestClient):
    """Test getting protocol NAV."""
    response = client.get("/v1/protocol/nav")
    assert response.status_code == 200
    data = response.json()
    assert "base_nav" in data
    assert "f_nav" in data
    assert "x_nav" in data
    assert "source" in data
    assert isinstance(data["base_nav"], str)
    assert isinstance(data["f_nav"], str)
    assert isinstance(data["x_nav"], str)


def test_get_token_nav_feth(client: TestClient):
    """Test getting fETH NAV."""
    response = client.get("/v1/protocol/nav/feth")
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "nav" in data
    assert "source" in data
    assert data["token"].lower() == "feth"


def test_get_token_nav_xeth(client: TestClient):
    """Test getting xETH NAV."""
    response = client.get("/v1/protocol/nav/xeth")
    assert response.status_code == 200
    data = response.json()
    assert data["token"].lower() == "xeth"


def test_get_token_nav_invalid(client: TestClient):
    """Test getting NAV for invalid token."""
    response = client.get("/v1/protocol/nav/invalid_token")
    # Should either return 200 with error note or 500
    assert response.status_code in [200, 500]


def test_batch_nav(client: TestClient):
    """Test batch NAV query."""
    tokens = ["feth", "xeth", "xcvx"]
    response = client.post(
        "/v1/protocol/nav/batch",
        json={"tokens": tokens}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert "cached" in data
    assert len(data["results"]) == len(tokens)
    
    # Check each token has results
    for token in tokens:
        assert token.lower() in [k.lower() for k in data["results"].keys()]


def test_batch_nav_empty_list(client: TestClient):
    """Test batch NAV with empty list."""
    response = client.post(
        "/v1/protocol/nav/batch",
        json={"tokens": []}
    )
    assert response.status_code == 422  # Validation error


@patch('app.services.sdk_service.SDKService.get_steth_price')
def test_get_steth_price(mock_get_price, client: TestClient):
    """Test getting stETH price."""
    # Mock stETH price
    mock_get_price.return_value = "3000.50"
    
    response = client.get("/v1/protocol/steth-price")
    assert response.status_code == 200
    data = response.json()
    assert "price" in data
    assert isinstance(data["price"], str)


@patch('app.services.sdk_service.SDKService.get_fxusd_total_supply')
def test_get_fxusd_supply(mock_get_supply, client: TestClient):
    """Test getting fxUSD total supply."""
    # Mock fxUSD supply
    mock_get_supply.return_value = "1000000.50"
    
    response = client.get("/v1/protocol/fxusd/supply")
    assert response.status_code == 200
    data = response.json()
    assert "total_supply" in data
    assert isinstance(data["total_supply"], str)

