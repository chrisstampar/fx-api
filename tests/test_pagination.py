"""
Tests for pagination functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@patch('app.services.sdk_service.SDKService.get_all_convex_pools')
def test_convex_pools_pagination(mock_get_pools, client: TestClient):
    """Test pagination for Convex pools."""
    # Mock Convex pools data
    mock_pools = {
        1: {"name": "Pool 1", "tvl": "1000000"},
        2: {"name": "Pool 2", "tvl": "2000000"},
        3: {"name": "Pool 3", "tvl": "3000000"},
        4: {"name": "Pool 4", "tvl": "4000000"},
        5: {"name": "Pool 5", "tvl": "5000000"},
        6: {"name": "Pool 6", "tvl": "6000000"},
        7: {"name": "Pool 7", "tvl": "7000000"},
        8: {"name": "Pool 8", "tvl": "8000000"},
        9: {"name": "Pool 9", "tvl": "9000000"},
        10: {"name": "Pool 10", "tvl": "10000000"},
        11: {"name": "Pool 11", "tvl": "11000000"},
        12: {"name": "Pool 12", "tvl": "12000000"},
    }
    mock_get_pools.return_value = mock_pools
    
    # First page
    response1 = client.get("/v1/convex/pools?page=1&limit=10")
    assert response1.status_code == 200
    data1 = response1.json()
    assert "pools" in data1
    assert "total_pools" in data1
    assert "page" in data1
    assert "limit" in data1
    assert "total_pages" in data1
    assert data1["page"] == 1
    assert data1["limit"] == 10
    
    # Second page
    response2 = client.get("/v1/convex/pools?page=2&limit=10")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["page"] == 2
    
    # Different pages should have different results (if enough pools)
    if data1["total_pools"] > 10:
        assert data1["pools"] != data2["pools"]


@patch('app.services.sdk_service.SDKService.get_all_convex_pools')
def test_convex_pools_pagination_defaults(mock_get_pools, client: TestClient):
    """Test Convex pools pagination with default values."""
    # Mock Convex pools data
    mock_pools = {
        1: {"name": "Pool 1", "tvl": "1000000"},
        2: {"name": "Pool 2", "tvl": "2000000"},
    }
    mock_get_pools.return_value = mock_pools
    
    response = client.get("/v1/convex/pools")
    assert response.status_code == 200
    data = response.json()
    assert "page" in data
    assert "limit" in data
    assert data["page"] == 1
    assert data["limit"] == 50  # Default limit


def test_convex_pools_pagination_invalid_page(client: TestClient):
    """Test pagination with invalid page number."""
    response = client.get("/v1/convex/pools?page=0")
    assert response.status_code == 422  # Validation error


def test_convex_pools_pagination_max_limit(client: TestClient):
    """Test pagination with limit exceeding maximum."""
    response = client.get("/v1/convex/pools?limit=200")  # Max is 100
    assert response.status_code == 422  # Validation error


def test_curve_pools_pagination(client: TestClient):
    """Test pagination for Curve pools."""
    response = client.get("/v1/curve/pools?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "pools" in data
    assert "total_pools" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data
    assert data["page"] == 1
    assert data["limit"] == 10


def test_curve_pools_pagination_defaults(client: TestClient):
    """Test Curve pools pagination with default values."""
    response = client.get("/v1/curve/pools")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 50  # Default limit

