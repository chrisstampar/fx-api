"""
Convex Finance endpoints.

Read-only endpoints for Convex vaults, pools, and rewards.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Query
from app.models.responses import (
    ConvexVaultInfoResponse,
    ConvexVaultRewardsResponse,
    ConvexPoolInfoResponse,
    ConvexPoolsListResponse,
    ConvexUserVaultsResponse,
    ErrorResponse
)
from app.services.sdk_service import SDKService
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
from fx_sdk.exceptions import ContractCallError

router = APIRouter()


@router.get("/pools", response_model=ConvexPoolsListResponse, tags=["convex"])
@limiter.limit("100/minute")
async def get_all_convex_pools(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get all Convex pools with pagination.
    
    Returns information about all Convex pools including pool IDs, names, TVL, and reward tokens.
    Supports pagination with `page` and `limit` query parameters.
    """
    try:
        all_pools = sdk_service.get_all_convex_pools()
        total_pools = len(all_pools)
        
        # Convert dict to list for pagination
        pools_list = list(all_pools.items())
        
        # Calculate pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = pools_list[start_idx:end_idx]
        
        # Convert back to dict
        paginated_pools = {pool_id: pool_info for pool_id, pool_info in paginated_items}
        
        return ConvexPoolsListResponse(
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
                message=f"Failed to get Convex pools: {str(e)}"
            ).model_dump()
        )


@router.get("/pool/{pool_id}", response_model=ConvexPoolInfoResponse, tags=["convex"])
@limiter.limit("100/minute")
async def get_convex_pool_info(
    request: Request,
    pool_id: int = Path(..., description="Convex pool ID"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get information about a specific Convex pool.
    
    Returns pool details including TVL, reward tokens, gauge address, and LP token.
    """
    try:
        pool_info = sdk_service.get_convex_pool_info(pool_id)
        return ConvexPoolInfoResponse(**pool_info)
    except ContractCallError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="CONTRACT_CALL_ERROR",
                message=str(e)
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get Convex pool info: {str(e)}"
            ).model_dump()
        )


@router.get("/vaults/{address}", response_model=ConvexUserVaultsResponse, tags=["convex"])
@limiter.limit("100/minute")
async def get_user_convex_vaults(
    request: Request,
    address: str = Path(..., description="User's Ethereum address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get all Convex vaults for a user address.
    
    Returns a list of all Convex vaults the user has created, including vault addresses and pool IDs.
    """
    try:
        vaults = sdk_service.get_user_convex_vaults(address)
        return ConvexUserVaultsResponse(
            address=address,
            vaults=vaults,
            total_vaults=len(vaults)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get user Convex vaults: {str(e)}"
            ).model_dump()
        )


@router.get("/vault/{vault_address}", response_model=ConvexVaultInfoResponse, tags=["convex"])
@limiter.limit("100/minute")
async def get_convex_vault_info(
    request: Request,
    vault_address: str = Path(..., description="Convex vault address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get information about a specific Convex vault.
    
    Returns vault details including pool ID, staked balance, and gauge address.
    """
    try:
        vault_info = sdk_service.get_convex_vault_info(vault_address)
        return ConvexVaultInfoResponse(**vault_info)
    except ContractCallError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="CONTRACT_CALL_ERROR",
                message=str(e)
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get Convex vault info: {str(e)}"
            ).model_dump()
        )


@router.get("/vault/{vault_address}/balance", response_model=ConvexVaultInfoResponse, tags=["convex"])
@limiter.limit("100/minute")
async def get_convex_vault_balance(
    request: Request,
    vault_address: str = Path(..., description="Convex vault address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get staked balance for a Convex vault.
    
    Returns the amount of LP tokens staked in the vault.
    """
    try:
        balance_info = sdk_service.get_convex_vault_balance(vault_address)
        return ConvexVaultInfoResponse(**balance_info)
    except ContractCallError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="CONTRACT_CALL_ERROR",
                message=str(e)
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get Convex vault balance: {str(e)}"
            ).model_dump()
        )


@router.get("/vault/{vault_address}/rewards", response_model=ConvexVaultRewardsResponse, tags=["convex"])
@limiter.limit("100/minute")
async def get_convex_vault_rewards(
    request: Request,
    vault_address: str = Path(..., description="Convex vault address"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get claimable rewards for a Convex vault.
    
    Returns all claimable reward tokens and their amounts.
    """
    try:
        rewards_info = sdk_service.get_convex_vault_rewards(vault_address)
        return ConvexVaultRewardsResponse(**rewards_info)
    except ContractCallError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="CONTRACT_CALL_ERROR",
                message=str(e)
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="INTERNAL_ERROR",
                message=f"Failed to get Convex vault rewards: {str(e)}"
            ).model_dump()
        )

