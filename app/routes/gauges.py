"""
Gauge and governance endpoints.

Read-only endpoints for gauge weights, rewards, and balances.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Query
from app.models.responses import ErrorResponse
from app.services.sdk_service import SDKService
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
from fx_sdk.exceptions import ContractCallError
from typing import Dict, Any, List

router = APIRouter()


@router.get("/{gauge_address}/weight", response_model=Dict[str, str], tags=["gauges"])
@limiter.limit("100/minute")
async def get_gauge_weight(
    request: Request,
    gauge_address: str = Path(..., description="Gauge contract address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get gauge weight.
    
    Returns the current weight of the gauge.
    """
    try:
        weight = sdk_service.get_gauge_weight(gauge_address)
        return {"gauge_address": gauge_address, "weight": str(weight)}
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
                message=f"Failed to get gauge weight: {str(e)}"
            ).dict()
        )


@router.get("/{gauge_address}/relative-weight", response_model=Dict[str, str], tags=["gauges"])
@limiter.limit("100/minute")
async def get_gauge_relative_weight(
    request: Request,
    gauge_address: str = Path(..., description="Gauge contract address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get gauge relative weight.
    
    Returns the relative weight of the gauge (as a percentage of total).
    """
    try:
        relative_weight = sdk_service.get_gauge_relative_weight(gauge_address)
        return {"gauge_address": gauge_address, "relative_weight": str(relative_weight)}
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
                message=f"Failed to get gauge relative weight: {str(e)}"
            ).dict()
        )


@router.get("/{gauge_address}/rewards/{address}", response_model=Dict[str, Any], tags=["gauges"])
@limiter.limit("100/minute")
async def get_gauge_rewards(
    request: Request,
    gauge_address: str = Path(..., description="Gauge contract address"),
    address: str = Path(..., description="User's Ethereum address"),
    token_address: str = Query(..., description="Reward token address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get claimable rewards for a gauge.
    
    Returns the claimable amount of a specific reward token for the user.
    """
    try:
        rewards = sdk_service.get_claimable_rewards(gauge_address, token_address, address)
        return {
            "gauge_address": gauge_address,
            "user_address": address,
            "token_address": token_address,
            "claimable_rewards": str(rewards)
        }
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
                message=f"Failed to get gauge rewards: {str(e)}"
            ).dict()
        )


@router.get("/{address}/all", response_model=Dict[str, Any], tags=["gauges"])
@limiter.limit("100/minute")
async def get_all_gauge_balances(
    request: Request,
    address: str = Path(..., description="User's Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get all gauge balances for an address.
    
    Returns balances across all gauges for the user.
    """
    try:
        balances = sdk_service.get_all_gauge_balances(address)
        return {
            "address": address,
            "gauge_balances": balances
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get all gauge balances: {str(e)}"
            ).dict()
        )

