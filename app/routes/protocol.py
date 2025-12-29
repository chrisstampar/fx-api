"""
Protocol information endpoints.

Read-only endpoints for protocol data.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Query, Body
from app.models.responses import (
    ProtocolInfoResponse,
    TokenNavResponse,
    ErrorResponse,
    ProtocolPoolInfoResponse,
    ProtocolMarketInfoResponse,
    ProtocolTreasuryInfoResponse,
    ProtocolPegKeeperInfoResponse,
    BatchNavResponse
)
from app.models.requests import BatchNavRequest
from typing import Any, Dict, List, Tuple
from app.services.sdk_service import SDKService
from app.services.cache_service import get_cache_service
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
import asyncio

router = APIRouter()
cache_service = get_cache_service()


@router.get("/nav", response_model=ProtocolInfoResponse, tags=["protocol"])
@limiter.limit("100/minute")
async def get_protocol_nav(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get protocol NAV (Net Asset Value) information.
    
    Returns base NAV, f-token NAV, and x-token NAV (for fETH/xETH).
    Results are cached for 5 minutes.
    """
    # Check cache first
    cache_key = "protocol:nav"
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        nav = sdk_service.get_protocol_nav()
        response = ProtocolInfoResponse(**nav)
        # Cache for 5 minutes
        cache_service.set(cache_key, response, ttl=300)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get protocol NAV: {str(e)}"
            ).model_dump()
        )


@router.get("/nav/{token}", response_model=TokenNavResponse, tags=["protocol"])
@limiter.limit("100/minute")
async def get_token_nav(
    request: Request,
    token: str = Path(..., description="Token name (e.g., 'feth', 'xeth', 'xcvx', 'xwbtc', 'xeeth', 'xezeth', 'xsteth', 'xfrxeth')"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get NAV (Net Asset Value) for a specific token.
    
    Results are cached for 5 minutes.
    
    Supported tokens:
    - fETH: f-token NAV
    - xETH, xCVX, xWBTC, xeETH, xezETH, xstETH, xfrxETH: x-token NAVs
    """
    # Check cache first
    cache_key = f"protocol:nav:{token.lower()}"
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        nav_info = sdk_service.get_token_nav(token)
        response = TokenNavResponse(**nav_info)
        # Cache for 5 minutes
        cache_service.set(cache_key, response, ttl=300)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get {token} NAV: {str(e)}"
            ).model_dump()
        )


@router.get("/pool-info/{pool_address}", response_model=ProtocolPoolInfoResponse, tags=["protocol"])
@limiter.limit("100/minute")
async def get_pool_info(
    request: Request,
    pool_address: str = Path(..., description="Pool manager contract address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get pool manager information.
    
    Returns pool details including collateral and debt capacity/balance.
    """
    try:
        pool_info = sdk_service.get_pool_manager_info(pool_address)
        return ProtocolPoolInfoResponse(**pool_info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get pool info: {str(e)}"
            ).model_dump()
        )


@router.get("/market-info/{market_address}", response_model=ProtocolMarketInfoResponse, tags=["protocol"])
@limiter.limit("100/minute")
async def get_market_info(
    request: Request,
    market_address: str = Path(..., description="Market contract address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get market information.
    
    Returns market details including collateral ratio and total collateral.
    """
    try:
        market_info = sdk_service.get_market_info(market_address)
        return ProtocolMarketInfoResponse(**market_info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get market info: {str(e)}"
            ).model_dump()
        )


@router.get("/treasury-info", response_model=ProtocolTreasuryInfoResponse, tags=["protocol"])
@limiter.limit("100/minute")
async def get_treasury_info(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get stETH treasury information.
    
    Returns treasury details including NAV and other metrics.
    """
    try:
        treasury_info = sdk_service.get_treasury_info()
        return ProtocolTreasuryInfoResponse(**treasury_info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get treasury info: {str(e)}"
            ).model_dump()
        )


@router.get("/v1/nav", response_model=ProtocolInfoResponse, tags=["protocol"])
@limiter.limit("100/minute")
async def get_v1_nav(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get V1 NAV (Net Asset Value) information.
    
    Returns fETH and xETH NAV values from V1 market.
    """
    try:
        nav_info = sdk_service.get_v1_nav()
        return ProtocolInfoResponse(**nav_info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get V1 NAV: {str(e)}"
            ).model_dump()
        )


@router.get("/v1/collateral-ratio", response_model=Dict[str, str], tags=["protocol"])
@limiter.limit("100/minute")
async def get_v1_collateral_ratio(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get V1 collateral ratio.
    
    Returns the current collateral ratio of the V1 market.
    """
    try:
        ratio = sdk_service.get_v1_collateral_ratio()
        return {"collateral_ratio": str(ratio)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get V1 collateral ratio: {str(e)}"
            ).model_dump()
        )


@router.get("/v1/rebalance-pools", response_model=Dict[str, List[str]], tags=["protocol"])
@limiter.limit("100/minute")
async def get_v1_rebalance_pools(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get all registered V1 rebalance pools.
    
    Returns a list of rebalance pool addresses.
    """
    try:
        pools = sdk_service.get_v1_rebalance_pools()
        return {"rebalance_pools": pools}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get V1 rebalance pools: {str(e)}"
            ).model_dump()
        )


@router.get("/v1/rebalance-pool/{pool_address}/balances/{address}", response_model=Dict[str, Any], tags=["protocol"])
@limiter.limit("100/minute")
async def get_rebalance_pool_balances(
    request: Request,
    pool_address: str = Path(..., description="Rebalance pool contract address"),
    address: str = Path(..., description="User's Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get rebalance pool balances for a user address.
    
    Returns balances and unlocked amounts for the user in the rebalance pool.
    """
    try:
        balances = sdk_service.get_rebalance_pool_balances(pool_address, address)
        return balances
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get rebalance pool balances: {str(e)}"
            ).model_dump()
        )


@router.get("/steth-price", response_model=Dict[str, str], tags=["protocol"])
@limiter.limit("100/minute")
async def get_steth_price(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get stETH price.
    
    Returns the current stETH price in USD.
    """
    try:
        price = sdk_service.get_steth_price()
        return {"price": str(price)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get stETH price: {str(e)}"
            ).model_dump()
        )


@router.get("/fxusd/supply", response_model=Dict[str, str], tags=["protocol"])
@limiter.limit("100/minute")
async def get_fxusd_supply(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get fxUSD total supply.
    
    Returns the total supply of fxUSD tokens.
    """
    try:
        supply = sdk_service.get_fxusd_total_supply()
        return {"total_supply": str(supply)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get fxUSD supply: {str(e)}"
            ).model_dump()
        )


@router.get("/peg-keeper", response_model=ProtocolPegKeeperInfoResponse, tags=["protocol"])
@limiter.limit("100/minute")
async def get_peg_keeper_info(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get peg keeper information.
    
    Returns peg keeper status including active state, debt ceiling, and total debt.
    """
    try:
        peg_info = sdk_service.get_peg_keeper_info()
        return ProtocolPegKeeperInfoResponse(**peg_info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get peg keeper info: {str(e)}"
            ).model_dump()
        )


@router.post("/nav/batch", response_model=BatchNavResponse, tags=["protocol"])
@limiter.limit("50/minute")  # Lower limit for batch operations
async def get_batch_nav(
    request: Request,
    batch_request: BatchNavRequest = Body(...),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get NAV for multiple tokens in a single request.
    
    This endpoint is more efficient than making individual requests
    for each token. Results are cached for 5 minutes.
    
    Maximum 20 tokens per request.
    """
    results: Dict[str, TokenNavResponse] = {}
    cached_count = 0
    
    # Process tokens in parallel
    async def get_nav_for_token(token_name: str) -> Tuple[str, TokenNavResponse]:
        cache_key = f"protocol:nav:{token_name.lower()}"
        cached_result = cache_service.get(cache_key)
        
        if cached_result is not None:
            return (token_name, cached_result)
        
        try:
            nav_info = sdk_service.get_token_nav(token_name)
            response = TokenNavResponse(**nav_info)
            # Cache for 5 minutes
            cache_service.set(cache_key, response, ttl=300)
            return (token_name, response)
        except Exception as e:
            # Return error response for this token
            error_response = TokenNavResponse(
                token=token_name,
                nav="0",
                source="error",
                note=f"Failed to get NAV: {str(e)}"
            )
            return (token_name, error_response)
    
    # Fetch all NAVs concurrently
    tasks = [get_nav_for_token(token) for token in batch_request.tokens]
    fetched_results = await asyncio.gather(*tasks)
    
    # Count cached results
    for token in batch_request.tokens:
        cache_key = f"protocol:nav:{token.lower()}"
        if cache_service.get(cache_key) is not None:
            cached_count += 1
    
    # Build results dictionary
    for token, response in fetched_results:
        results[token] = response
    
    return BatchNavResponse(
        results=results,
        count=len(results),
        cached=cached_count
    )

