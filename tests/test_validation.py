"""
Tests for input validation.
"""

import pytest
from fastapi.testclient import TestClient
from app.utils.validation import (
    is_valid_ethereum_address,
    validate_and_checksum_address,
    is_valid_amount,
    validate_amount,
    is_valid_hex_string,
    validate_hex_string
)


def test_address_validation_valid():
    """Test valid Ethereum address validation."""
    valid_addresses = [
        "0x1234567890123456789012345678901234567890",
        "0x0000000000000000000000000000000000000000",
        "0x9876543210987654321098765432109876543210"  # Valid address
    ]
    for addr in valid_addresses:
        assert is_valid_ethereum_address(addr) is True, f"Address {addr} should be valid"


def test_address_validation_invalid():
    """Test invalid Ethereum address validation."""
    invalid_addresses = [
        "invalid",
        "0x123",
        "1234567890123456789012345678901234567890",  # Missing 0x
        "0x1234567890123456789012345678901234567890G",  # Invalid character
        "",
        None
    ]
    for addr in invalid_addresses:
        if addr is not None:
            assert is_valid_ethereum_address(addr) is False


def test_address_checksumming():
    """Test address checksumming."""
    address = "0x1234567890123456789012345678901234567890"
    checksummed = validate_and_checksum_address(address)
    assert checksummed.startswith("0x")
    assert len(checksummed) == 42
    assert checksummed != address  # Should be checksummed


def test_amount_validation_valid():
    """Test valid amount validation."""
    valid_amounts = [
        "0",
        "1",
        "1.5",
        "1000.123456",
        "max",
        "0.0000000001"
    ]
    for amount in valid_amounts:
        assert is_valid_amount(amount) is True


def test_amount_validation_invalid():
    """Test invalid amount validation."""
    invalid_amounts = [
        "-1",
        "abc",
        "",
        None,
        "1.2.3"
    ]
    for amount in invalid_amounts:
        if amount is not None:
            assert is_valid_amount(amount) is False


def test_amount_validation_no_zero():
    """Test amount validation with zero not allowed."""
    assert is_valid_amount("0", allow_zero=False) is False
    assert is_valid_amount("1", allow_zero=False) is True


def test_amount_validation_max_decimals():
    """Test amount validation with max decimals."""
    assert is_valid_amount("1.123", max_decimals=2) is False
    assert is_valid_amount("1.12", max_decimals=2) is True


def test_hex_string_validation():
    """Test hex string validation."""
    assert is_valid_hex_string("0x123abc") is True
    assert is_valid_hex_string("123abc", prefix_required=False) is True
    assert is_valid_hex_string("123abc", prefix_required=True) is False
    assert is_valid_hex_string("0x123xyz") is False
    assert is_valid_hex_string("invalid") is False


def test_validation_error_messages(client: TestClient):
    """Test that validation errors return helpful messages."""
    # Invalid address
    response = client.get("/v1/balances/invalid")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "message" in data
    
    # Invalid batch request
    response = client.post(
        "/v1/balances/batch",
        json={"addresses": []}
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "details" in data
    assert "summary" in data["details"]

