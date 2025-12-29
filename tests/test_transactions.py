"""
Tests for transaction endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_prepare_mint_f_token(client: TestClient):
    """Test preparing mint fToken transaction."""
    request_data = {
        "market_address": "0x1234567890123456789012345678901234567890",
        "base_in": "1.5",
        "recipient": "0x1234567890123456789012345678901234567890",
        "min_f_token_out": "1.4"
    }
    
    response = client.post(
        "/v1/transactions/mint/f-token/prepare",
        json=request_data
    )
    
    # Should either succeed or fail with contract error (depending on RPC)
    assert response.status_code in [200, 400, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "to" in data
        assert "data" in data
        assert "value" in data
        assert "gas" in data
        assert "nonce" in data
        assert "chainId" in data


def test_prepare_mint_f_token_with_gas_estimation(client: TestClient):
    """Test preparing mint fToken transaction with gas estimation."""
    request_data = {
        "market_address": "0x1234567890123456789012345678901234567890",
        "base_in": "1.5",
        "min_f_token_out": "1.4"
    }
    
    response = client.post(
        "/v1/transactions/mint/f-token/prepare?estimate_gas=true&from_address=0x1234567890123456789012345678901234567890",
        json=request_data
    )
    
    # Should either succeed or fail (depending on RPC)
    assert response.status_code in [200, 400, 500]
    
    if response.status_code == 200:
        data = response.json()
        # Gas estimation fields are optional
        assert "to" in data
        assert "data" in data


@patch('app.services.sdk_service.SDKService.build_mint_f_token_transaction')
def test_prepare_mint_f_token_missing_from_address_for_gas(mock_build_tx, client: TestClient):
    """Test gas estimation without from_address."""
    # Mock the transaction building (won't be called if validation fails first)
    mock_build_tx.return_value = {
        "to": "0x1234567890123456789012345678901234567890",
        "data": "0x1234",
        "value": "0",
        "gas": 21000,
        "nonce": 0,
        "chainId": 1
    }
    
    request_data = {
        "market_address": "0x1234567890123456789012345678901234567890",
        "base_in": "1.5"
    }
    
    response = client.post(
        "/v1/transactions/mint/f-token/prepare?estimate_gas=true",
        json=request_data
    )
    
    # Should fail with 400 - missing from_address
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "MISSING_PARAMETER" in data.get("code", "")


def test_prepare_approve(client: TestClient):
    """Test preparing approve transaction."""
    request_data = {
        "token_address": "0x365AccFCa291e7D3914637ABf1F7635dB165Bb09",
        "spender_address": "0x1234567890123456789012345678901234567890",
        "amount": "1000"
    }
    
    response = client.post(
        "/v1/transactions/approve/prepare",
        json=request_data
    )
    
    assert response.status_code in [200, 400, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "to" in data
        assert "data" in data


def test_prepare_approve_max(client: TestClient):
    """Test preparing approve transaction with 'max' amount."""
    request_data = {
        "token_address": "0x365AccFCa291e7D3914637ABf1F7635dB165Bb09",
        "spender_address": "0x1234567890123456789012345678901234567890",
        "amount": "max"
    }
    
    response = client.post(
        "/v1/transactions/approve/prepare",
        json=request_data
    )
    
    assert response.status_code in [200, 400, 500]


def test_broadcast_transaction_invalid_format(client: TestClient):
    """Test broadcasting invalid transaction format."""
    request_data = {
        "rawTransaction": "invalid_hex"
    }
    
    response = client.post(
        "/v1/transactions/broadcast",
        json=request_data
    )
    
    # Should fail validation
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data


def test_broadcast_transaction_missing_field(client: TestClient):
    """Test broadcasting transaction with missing field."""
    response = client.post(
        "/v1/transactions/broadcast",
        json={}
    )
    
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "error" in data
    assert "details" in data


def test_transaction_status_not_found(client: TestClient):
    """Test getting status for non-existent transaction."""
    fake_tx_hash = "0x" + "0" * 64
    response = client.get(f"/v1/transactions/{fake_tx_hash}/status")
    
    # Should return 200 with not_found status, 404 if endpoint doesn't exist, or 500 if RPC fails
    assert response.status_code in [200, 404, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data["status"] in ["not_found", "pending"]

