"""
Health check and status endpoints.
"""

import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.models.responses import HealthResponse, StatusResponse, DetailedHealthResponse
from app.services.sdk_service import SDKService
from app.dependencies import get_sdk_service
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns basic health status of the API.
    """
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION
    )


@router.get("/status", response_model=StatusResponse, tags=["health"])
async def get_status(sdk_service: SDKService = Depends(get_sdk_service)):
    """
    Get detailed API status.
    
    Returns API version, environment, and RPC connection status.
    """
    # Check if RPC is connected
    rpc_connected = False
    rpc_status = {}
    
    try:
        if sdk_service.client:
            rpc_connected = sdk_service.client.w3.is_connected()
            # Test RPC with a simple call
            if rpc_connected:
                try:
                    block_number = sdk_service.client.w3.eth.block_number
                    rpc_status = {
                        "connected": True,
                        "current_block": block_number,
                        "endpoint": sdk_service.rpc_url
                    }
                except Exception as e:
                    rpc_status = {
                        "connected": False,
                        "error": str(e)
                    }
    except Exception as e:
        rpc_status = {
            "connected": False,
            "error": str(e)
        }
    
    # Check SDK status
    sdk_status = {
        "initialized": sdk_service.client is not None,
        "rpc_url": sdk_service.rpc_url,
        "fallback_urls": len(sdk_service.rpc_urls) - 1 if sdk_service.rpc_urls else 0
    }
    
    components = {
        "rpc": rpc_status,
        "sdk": sdk_status
    }
    
    return StatusResponse(
        status="operational" if rpc_connected else "degraded",
        version=settings.API_VERSION,
        environment=settings.API_ENV,
        rpc_connected=rpc_connected,
        components=components
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse, tags=["health"])
async def detailed_health_check(sdk_service: SDKService = Depends(get_sdk_service)):
    """
    Detailed health check endpoint.
    
    Returns comprehensive health status including:
    - RPC connectivity for all endpoints
    - SDK initialization status
    - Component-level health checks
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Test all RPC endpoints
    rpc_status = {}
    rpc_connected_count = 0
    
    for rpc_url in sdk_service.rpc_urls:
        try:
            # Create a temporary client to test this RPC
            from fx_sdk import ProtocolClient
            test_client = ProtocolClient(rpc_url=rpc_url)
            is_connected = test_client.w3.is_connected()
            
            if is_connected:
                try:
                    block_number = test_client.w3.eth.block_number
                    latency = time.time()
                    test_client.w3.eth.block_number  # Simple call to measure latency
                    latency = (time.time() - latency) * 1000  # Convert to ms
                    
                    rpc_status[rpc_url] = {
                        "status": "healthy",
                        "connected": True,
                        "current_block": block_number,
                        "latency_ms": round(latency, 2)
                    }
                    rpc_connected_count += 1
                except Exception as e:
                    rpc_status[rpc_url] = {
                        "status": "degraded",
                        "connected": True,
                        "error": str(e)
                    }
            else:
                rpc_status[rpc_url] = {
                    "status": "unhealthy",
                    "connected": False
                }
        except Exception as e:
            rpc_status[rpc_url] = {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    # SDK status
    sdk_status = {
        "initialized": sdk_service.client is not None,
        "primary_rpc": sdk_service.rpc_url,
        "fallback_rpcs": len(sdk_service.rpc_urls) - 1,
        "total_rpcs": len(sdk_service.rpc_urls)
    }
    
    if sdk_service.client:
        try:
            sdk_status["current_rpc_connected"] = sdk_service.client.w3.is_connected()
        except Exception:
            sdk_status["current_rpc_connected"] = False
    
    # Determine overall status
    if rpc_connected_count == 0:
        overall_status = "unhealthy"
    elif rpc_connected_count < len(sdk_service.rpc_urls):
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    components = {
        "api": {
            "status": "healthy",
            "version": settings.API_VERSION,
            "environment": settings.API_ENV
        },
        "rpc": {
            "status": "healthy" if rpc_connected_count > 0 else "unhealthy",
            "connected_count": rpc_connected_count,
            "total_count": len(sdk_service.rpc_urls),
            "endpoints": rpc_status
        },
        "sdk": {
            "status": "healthy" if sdk_status["initialized"] else "unhealthy",
            **sdk_status
        }
    }
    
    return DetailedHealthResponse(
        status=overall_status,
        version=settings.API_VERSION,
        timestamp=timestamp,
        components=components,
        rpc_status=rpc_status,
        sdk_status=sdk_status
    )


@router.get("/metrics", tags=["health"])
async def get_metrics(
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get API metrics.
    
    Returns basic metrics including:
    - Cache statistics
    - Transaction tracking statistics
    - Rate limit information
    """
    from app.services.cache_service import get_cache_service
    from app.services.tx_tracking_service import get_tx_tracker
    
    cache_service = get_cache_service()
    tx_tracker = get_tx_tracker()
    
    # Get cache stats
    cache_stats = cache_service.get_stats()
    
    # Get transaction tracking stats
    tx_stats = tx_tracker.get_stats()
    
    # Get RPC status
    rpc_connected = False
    try:
        if sdk_service.client:
            rpc_connected = sdk_service.client.w3.is_connected()
    except Exception:
        pass
    
    return {
        "cache": cache_stats,
        "transactions": tx_stats,
        "rpc": {
            "connected": rpc_connected,
            "endpoints": len(sdk_service.rpc_urls)
        },
        "rate_limits": {
            "per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "per_hour": settings.RATE_LIMIT_PER_HOUR,
            "per_day": settings.RATE_LIMIT_PER_DAY
        }
    }

