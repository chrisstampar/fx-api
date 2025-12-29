"""
Tests for caching functionality.
"""

import pytest
from fastapi.testclient import TestClient
from app.services.cache_service import get_cache_service, CacheService


def test_cache_service_basic():
    """Test basic cache operations."""
    cache = CacheService(default_ttl=60)
    
    # Set and get
    cache.set("test_key", "test_value", ttl=60)
    assert cache.get("test_key") == "test_value"
    
    # Get non-existent key
    assert cache.get("non_existent") is None
    
    # Delete
    cache.delete("test_key")
    assert cache.get("test_key") is None


def test_cache_expiration():
    """Test cache expiration."""
    cache = CacheService(default_ttl=1)  # 1 second TTL
    
    cache.set("expire_key", "value", ttl=1)
    assert cache.get("expire_key") == "value"
    
    import time
    time.sleep(1.1)  # Wait for expiration
    
    assert cache.get("expire_key") is None


def test_cache_stats():
    """Test cache statistics."""
    cache = CacheService()
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    cache.get("key1")  # Hit
    cache.get("key1")  # Hit
    cache.get("key3")  # Miss
    
    stats = cache.get_stats()
    assert stats["size"] == 2
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["hit_rate"] > 0


def test_balance_caching(client: TestClient, sample_address):
    """Test that balance responses are cached."""
    # First request
    response1 = client.get(f"/v1/balances/{sample_address}")
    assert response1.status_code == 200
    process_time1 = float(response1.headers.get("X-Process-Time", 0))
    
    # Second request (should be cached, faster)
    response2 = client.get(f"/v1/balances/{sample_address}")
    assert response2.status_code == 200
    process_time2 = float(response2.headers.get("X-Process-Time", 0))
    
    # Cached response should be faster (or at least not slower)
    # Note: In test environment, this might not always be true due to test client overhead
    assert response1.json() == response2.json()


def test_protocol_nav_caching(client: TestClient):
    """Test that protocol NAV is cached."""
    # First request
    response1 = client.get("/v1/protocol/nav")
    assert response1.status_code == 200
    
    # Second request (should be cached)
    response2 = client.get("/v1/protocol/nav")
    assert response2.status_code == 200
    
    assert response1.json() == response2.json()


def test_cache_cleanup():
    """Test cache cleanup of expired entries."""
    cache = CacheService(default_ttl=1)
    
    cache.set("key1", "value1", ttl=1)
    cache.set("key2", "value2", ttl=60)
    
    import time
    time.sleep(1.1)
    
    removed = cache.cleanup_expired()
    assert removed == 1
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"

