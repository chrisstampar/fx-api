"""
veFXN endpoints.

Read-only endpoints for veFXN locked information.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from app.models.responses import ErrorResponse
from app.services.sdk_service import SDKService
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
from fx_sdk.exceptions import ContractCallError
from typing import Dict, Any

router = APIRouter()


@router.get("/{address}/info", response_model=Dict[str, Any], tags=["vefxn"])
@limiter.limit("100/minute")
async def get_vefxn_info(
    request: Request,
    address: str = Path(..., description="User's Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get veFXN locked information.
    
    Returns veFXN balance and locked FXN information for the user.
    """
    try:
        info = sdk_service.get_vefxn_locked_info(address)
        return {
            "address": address,
            **info
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
                message=f"Failed to get veFXN info: {str(e)}"
            ).dict()
        )

