"""
V2 Product endpoints.

Read-only endpoints for V2 pools, positions, and pool managers.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Query
from app.models.responses import (
    V2PoolInfoResponse,
    V2PositionInfoResponse,
    V2PoolManagerInfoResponse,
    V2ReservePoolInfoResponse,
    ErrorResponse
)
from app.services.sdk_service import SDKService
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
from fx_sdk.exceptions import ContractCallError

router = APIRouter()


@router.get("/pool", response_model=V2PoolInfoResponse, tags=["v2"])
@limiter.limit("100/minute")
async def get_v2_pool_info(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get V2 fxUSD Base Pool information.
    
    Returns pool details including total assets, total supply, and pool address.
    """
    try:
        pool_info = sdk_service.get_v2_pool_info()
        return V2PoolInfoResponse(**pool_info)
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
                message=f"Failed to get V2 pool info: {str(e)}"
            ).dict()
        )


@router.get("/position/{position_id}", response_model=V2PositionInfoResponse, tags=["v2"])
@limiter.limit("100/minute")
async def get_v2_position_info(
    request: Request,
    position_id: int = Path(..., description="V2 position ID"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get V2 position information.
    
    Returns position details including collateral, debt, collateral ratio, and owner.
    """
    try:
        position_info = sdk_service.get_v2_position_info(position_id)
        return V2PositionInfoResponse(**position_info)
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
                message=f"Failed to get V2 position info: {str(e)}"
            ).dict()
        )


@router.get("/pool-manager/{pool_address}", response_model=V2PoolManagerInfoResponse, tags=["v2"])
@limiter.limit("100/minute")
async def get_v2_pool_manager_info(
    request: Request,
    pool_address: str = Path(..., description="Pool manager contract address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get V2 pool manager information.
    
    Returns pool manager details including total collateral and total debt.
    """
    try:
        pool_info = sdk_service.get_v2_pool_manager_info(pool_address)
        return V2PoolManagerInfoResponse(**pool_info)
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
                message=f"Failed to get V2 pool manager info: {str(e)}"
            ).dict()
        )


@router.get("/reserve-pool/{token_address}", response_model=V2ReservePoolInfoResponse, tags=["v2"])
@limiter.limit("100/minute")
async def get_v2_reserve_pool_info(
    request: Request,
    token_address: str = Path(..., description="Token address for the reserve pool"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get V2 reserve pool information.
    
    Returns reserve pool details including bonus ratio for the specified token.
    """
    try:
        pool_info = sdk_service.get_v2_reserve_pool_info(token_address)
        return V2ReservePoolInfoResponse(**pool_info)
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
                message=f"Failed to get V2 reserve pool info: {str(e)}"
            ).dict()
        )

