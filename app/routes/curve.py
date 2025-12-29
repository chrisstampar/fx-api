"""
Curve Finance endpoints.

Read-only endpoints for Curve pools, gauges, and rewards.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Query
from app.models.responses import (
    CurvePoolInfoResponse,
    CurveGaugeBalanceResponse,
    CurveGaugeRewardsResponse,
    CurvePoolsListResponse,
    ErrorResponse
)
from app.services.sdk_service import SDKService
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
from fx_sdk.exceptions import ContractCallError

router = APIRouter()


@router.get("/pools", response_model=CurvePoolsListResponse, tags=["curve"])
@limiter.limit("100/minute")
async def get_curve_pools(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get all Curve pools from the registry with pagination.
    
    Returns information about all Curve pools including pool addresses, LP tokens, and gauge addresses.
    Supports pagination with `page` and `limit` query parameters.
    """
    try:
        all_pools = sdk_service.get_curve_pools()
        total_pools = len(all_pools)
        
        # Calculate pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_pools = all_pools[start_idx:end_idx]
        
        return CurvePoolsListResponse(
            pools=paginated_pools,
            total_pools=total_pools,
            page=page,
            limit=limit,
            total_pages=(total_pools + limit - 1) // limit if limit > 0 else 1
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get Curve pools: {str(e)}"
            ).dict()
        )


@router.get("/pool/{pool_address}", response_model=CurvePoolInfoResponse, tags=["curve"])
@limiter.limit("100/minute")
async def get_curve_pool_info(
    request: Request,
    pool_address: str = Path(..., description="Curve pool contract address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get information about a specific Curve pool.
    
    Returns pool details including LP token, virtual price, balances, and gauge address.
    """
    try:
        pool_info = sdk_service.get_curve_pool_info(pool_address)
        return CurvePoolInfoResponse(**pool_info)
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
                message=f"Failed to get Curve pool info: {str(e)}"
            ).dict()
        )


@router.get("/gauge/{gauge_address}/balance", response_model=CurveGaugeBalanceResponse, tags=["curve"])
@limiter.limit("100/minute")
async def get_curve_gauge_balance(
    request: Request,
    gauge_address: str = Path(..., description="Curve gauge contract address"),
    user_address: str = Query(..., description="User's Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get staked balance for a Curve gauge.
    
    Returns the amount of LP tokens staked in the gauge by the user.
    """
    try:
        balance_info = sdk_service.get_curve_gauge_balance(gauge_address, user_address)
        return CurveGaugeBalanceResponse(**balance_info)
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
                message=f"Failed to get Curve gauge balance: {str(e)}"
            ).dict()
        )


@router.get("/gauge/{gauge_address}/rewards", response_model=CurveGaugeRewardsResponse, tags=["curve"])
@limiter.limit("100/minute")
async def get_curve_gauge_rewards(
    request: Request,
    gauge_address: str = Path(..., description="Curve gauge contract address"),
    user_address: str = Query(..., description="User's Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get claimable rewards for a Curve gauge.
    
    Returns all claimable reward tokens and their amounts for the user.
    """
    try:
        rewards_info = sdk_service.get_curve_gauge_rewards(gauge_address, user_address)
        return CurveGaugeRewardsResponse(**rewards_info)
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
                message=f"Failed to get Curve gauge rewards: {str(e)}"
            ).dict()
        )

