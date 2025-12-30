"""
Balance endpoints.

All balance queries are read-only and don't require authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Body
from app.models.responses import BalanceResponse, AllBalancesResponse, ErrorResponse, BatchBalancesResponse
from app.models.requests import BatchBalancesRequest
from app.services.sdk_service import SDKService
from app.services.cache_service import get_cache_service
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
from app.utils.validation import validate_and_checksum_address
from fx_sdk.exceptions import ContractCallError
from typing import Dict, Tuple
import asyncio

router = APIRouter()
cache_service = get_cache_service()


@router.get("/{address}", response_model=AllBalancesResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_all_balances(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get all token balances for an address.
    
    Returns balances for all f(x) Protocol tokens including:
    - fxUSD, fETH, rUSD, btcUSD, cvxUSD, arUSD
    - xETH, xCVX, xWBTC, xeETH, xezETH, xstETH, xfrxETH
    - FXN, veFXN, fxSAVE, fxSP
    
    Results are cached for 30 seconds to improve performance.
    """
    # Validate and checksum address
    try:
        address = validate_and_checksum_address(address)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="INVALID_ADDRESS",
                message=str(e)
            ).model_dump()
        )
    
    # Check cache first
    cache_key = f"balances:all:{address.lower()}"
    cached_result = cache_service.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        result = sdk_service.get_all_balances(address, include_usd_value=True)
        response = AllBalancesResponse(
            address=address,
            balances=result["balances"],
            total_usd_value=result.get("total_usd_value")
        )
        # Only cache if we have complete data (including USD value)
        # This prevents caching incomplete responses that would cause inconsistent results
        total_usd = result.get("total_usd_value")
        if total_usd is not None:
            cache_service.set(cache_key, response, ttl=30)
        return response
    except ContractCallError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="CONTRACT_CALL_ERROR",
                message=str(e)
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get balances: {str(e)}"
            ).dict()
        )


@router.get("/{address}/fxusd", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_fxusd_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get fxUSD balance for an address."""
    try:
        result = sdk_service.get_balance(address, "fxusd")
        return BalanceResponse(
            address=address,
            token="fxusd",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get fxUSD balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/fxn", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_fxn_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get FXN balance for an address."""
    try:
        result = sdk_service.get_balance(address, "fxn")
        return BalanceResponse(
            address=address,
            token="fxn",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get FXN balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/feth", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_feth_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get fETH balance for an address."""
    try:
        result = sdk_service.get_balance(address, "feth")
        return BalanceResponse(
            address=address,
            token="feth",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get fETH balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/xeth", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_xeth_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get xETH balance for an address."""
    try:
        result = sdk_service.get_balance(address, "xeth")
        return BalanceResponse(
            address=address,
            token="xeth",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get xETH balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/xcvx", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_xcvx_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get xCVX balance for an address."""
    try:
        result = sdk_service.get_balance(address, "xcvx")
        return BalanceResponse(
            address=address,
            token="xcvx",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get xCVX balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/xwbtc", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_xwbtc_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get xWBTC balance for an address."""
    try:
        result = sdk_service.get_balance(address, "xwbtc")
        return BalanceResponse(
            address=address,
            token="xwbtc",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get xWBTC balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/xeeth", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_xeeth_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get xeETH balance for an address."""
    try:
        result = sdk_service.get_balance(address, "xeeth")
        return BalanceResponse(
            address=address,
            token="xeeth",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get xeETH balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/xezeth", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_xezeth_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get xezETH balance for an address."""
    try:
        result = sdk_service.get_balance(address, "xezeth")
        return BalanceResponse(
            address=address,
            token="xezeth",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get xezETH balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/xsteth", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_xsteth_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get xstETH balance for an address."""
    try:
        result = sdk_service.get_balance(address, "xsteth")
        return BalanceResponse(
            address=address,
            token="xsteth",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get xstETH balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/xfrxeth", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_xfrxeth_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get xfrxETH balance for an address."""
    try:
        result = sdk_service.get_balance(address, "xfrxeth")
        return BalanceResponse(
            address=address,
            token="xfrxeth",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get xfrxETH balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/vefxn", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_vefxn_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get veFXN balance for an address."""
    try:
        result = sdk_service.get_balance(address, "vefxn")
        return BalanceResponse(
            address=address,
            token="vefxn",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get veFXN balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/fxsave", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_fxsave_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get fxSAVE balance for an address."""
    try:
        result = sdk_service.get_balance(address, "fxsave")
        return BalanceResponse(
            address=address,
            token="fxsave",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get fxSAVE balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/fxsp", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_fxsp_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get fxSP balance for an address."""
    try:
        result = sdk_service.get_balance(address, "fxsp")
        return BalanceResponse(
            address=address,
            token="fxsp",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get fxSP balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/rusd", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_rusd_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get rUSD balance for an address."""
    try:
        result = sdk_service.get_balance(address, "rusd")
        return BalanceResponse(
            address=address,
            token="rusd",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get rUSD balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/arusd", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_arusd_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get arUSD balance for an address."""
    try:
        result = sdk_service.get_balance(address, "arusd")
        return BalanceResponse(
            address=address,
            token="arusd",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get arUSD balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/btcusd", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_btcusd_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get btcUSD balance for an address."""
    try:
        result = sdk_service.get_balance(address, "btcusd")
        return BalanceResponse(
            address=address,
            token="btcusd",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get btcUSD balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/cvxusd", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_cvxusd_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get cvxUSD balance for an address."""
    try:
        result = sdk_service.get_balance(address, "cvxusd")
        return BalanceResponse(
            address=address,
            token="cvxusd",
            balance=result["balance"],
            token_address=result["token_address"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get cvxUSD balance: {str(e)}"
            ).dict()
        )


@router.get("/{address}/token/{token_address}", response_model=BalanceResponse, tags=["balances"])
@limiter.limit("100/minute")
async def get_token_balance(
    request: Request,
    address: str = Path(..., description="Ethereum address"),
    token_address: str = Path(..., description="Token contract address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """Get balance for any ERC-20 token by contract address."""
    try:
        balance = sdk_service.get_token_balance_by_address(address, token_address)
        return BalanceResponse(
            address=address,
            token="custom",
            balance=balance["balance"],
            token_address=token_address
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get token balance: {str(e)}"
            ).dict()
        )


@router.post("/batch", response_model=BatchBalancesResponse, tags=["balances"])
@limiter.limit("50/minute")  # Lower limit for batch operations
async def get_batch_balances(
    request: Request,
    batch_request: BatchBalancesRequest = Body(...),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get balances for multiple addresses in a single request.
    
    This endpoint is more efficient than making individual requests
    for each address. Results are cached for 30 seconds.
    
    Maximum 100 addresses per request.
    """
    results: Dict[str, AllBalancesResponse] = {}
    cached_count = 0
    
    # Process addresses in parallel
    async def get_balance_for_address(addr: str) -> Tuple[str, AllBalancesResponse]:
        cache_key = f"balances:all:{addr.lower()}"
        cached_result = cache_service.get(cache_key)
        
        if cached_result is not None:
            return (addr, cached_result)
        
        try:
            result = sdk_service.get_all_balances(addr, include_usd_value=True)
            response = AllBalancesResponse(
                address=addr,
                balances=result["balances"],
                total_usd_value=result.get("total_usd_value")
            )
            # Cache for 30 seconds
            cache_service.set(cache_key, response, ttl=30)
            return (addr, response)
        except Exception as e:
            # Return error response for this address
            error_response = AllBalancesResponse(
                address=addr,
                balances={},
                total_usd_value=None
            )
            return (addr, error_response)
    
    # Fetch all balances concurrently
    tasks = [get_balance_for_address(addr) for addr in batch_request.addresses]
    fetched_results = await asyncio.gather(*tasks)
    
    # Count cached results
    for addr in batch_request.addresses:
        cache_key = f"balances:all:{addr.lower()}"
        if cache_service.get(cache_key) is not None:
            cached_count += 1
    
    # Build results dictionary
    for addr, response in fetched_results:
        results[addr] = response
    
    return BatchBalancesResponse(
        results=results,
        count=len(results),
        cached=cached_count
    )

