"""
Tests for balance endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_get_all_balances(client: TestClient, sample_address):
    """Test getting all balances for an address."""
    response = client.get(f"/v1/balances/{sample_address}")
    assert response.status_code == 200
    data = response.json()
    assert "address" in data
    assert "balances" in data
    assert isinstance(data["balances"], dict)
    assert data["address"].lower() == sample_address.lower()
    
    # Check response headers
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


def test_get_all_balances_invalid_address(client: TestClient):
    """Test getting balances with invalid address."""
    response = client.get("/v1/balances/invalid_address")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] is True
    assert "INVALID_ADDRESS" in data["code"]


def test_get_fxusd_balance(client: TestClient, sample_address):
    """Test getting fxUSD balance."""
    response = client.get(f"/v1/balances/{sample_address}/fxusd")
    assert response.status_code == 200
    data = response.json()
    assert "address" in data
    assert "token" in data
    assert "balance" in data
    assert data["token"] == "fxusd"
    assert "token_address" in data


def test_get_fxn_balance(client: TestClient, sample_address):
    """Test getting FXN balance."""
    response = client.get(f"/v1/balances/{sample_address}/fxn")
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "fxn"
    assert "balance" in data


def test_get_feth_balance(client: TestClient, sample_address):
    """Test getting fETH balance."""
    response = client.get(f"/v1/balances/{sample_address}/feth")
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "feth"


def test_get_xeth_balance(client: TestClient, sample_address):
    """Test getting xETH balance."""
    response = client.get(f"/v1/balances/{sample_address}/xeth")
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "xeth"


def test_batch_balances(client: TestClient, sample_address):
    """Test batch balance query."""
    addresses = [
        sample_address,
        "0x9876543210987654321098765432109876543210"
    ]
    
    response = client.post(
        "/v1/balances/batch",
        json={"addresses": addresses}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert "cached" in data
    assert len(data["results"]) == len(addresses)
    
    # Check each address has results
    for addr in addresses:
        assert addr.lower() in [k.lower() for k in data["results"].keys()]


def test_batch_balances_empty_list(client: TestClient):
    """Test batch balance with empty list."""
    response = client.post(
        "/v1/balances/batch",
        json={"addresses": []}
    )
    assert response.status_code == 422  # Validation error


def test_batch_balances_too_many(client: TestClient):
    """Test batch balance with too many addresses."""
    addresses = [f"0x{'0' * 40}"] * 101  # 101 addresses (max is 100)
    response = client.post(
        "/v1/balances/batch",
        json={"addresses": addresses}
    )
    assert response.status_code == 422  # Validation error


def test_get_token_balance_by_address(client: TestClient, sample_address):
    """Test getting balance for custom token address."""
    token_address = "0x365AccFCa291e7D3914637ABf1F7635dB165Bb09"  # FXN token
    response = client.get(f"/v1/balances/{sample_address}/token/{token_address}")
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert "token_address" in data
    assert data["token_address"].lower() == token_address.lower()

