"""
Transaction endpoints.

Write operations that require signed transactions.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Query
from typing import Optional
from datetime import datetime
from app.models.responses import TransactionResponse, TransactionDataResponse, ErrorResponse, PreparedTransactionsResponse, TransactionStatusResponse
from app.utils.validation import validate_and_checksum_address, validate_amount, validate_hex_string
from app.services.tx_tracking_service import get_tx_tracker
from app.models.requests import (
    BroadcastTransactionRequest,
    MintFTokenRequest,
    MintXTokenRequest,
    MintBothTokensRequest,
    ApproveRequest,
    TransferRequest,
    RebalancePoolDepositRequest,
    RebalancePoolWithdrawRequest,
    RebalancePoolUnlockRequest,
    RebalancePoolClaimRequest,
    SavingsDepositRequest,
    SavingsRedeemRequest,
    StabilityPoolDepositRequest,
    StabilityPoolWithdrawRequest,
    HarvestRequest,
    RequestBonusRequest,
    OperatePositionRequest,
    RebalancePositionRequest,
    LiquidatePositionRequest,
    GaugeVoteRequest,
    GaugeClaimRequest,
    ClaimAllGaugeRewardsRequest,
    VeFxnDepositRequest,
    MintViaTreasuryRequest,
    MintViaGatewayRequest,
    RedeemRequest,
    RedeemViaTreasuryRequest,
    SwapRequest,
    FlashLoanRequest
)
from app.services.sdk_service import SDKService
from app.dependencies import get_sdk_service
from app.middleware.rate_limit import limiter
from fx_sdk.exceptions import ContractCallError, TransactionFailedError
from typing import Dict, Any, Optional

router = APIRouter()


@router.post("/broadcast", response_model=TransactionResponse, tags=["transactions"])
@limiter.limit("50/minute")  # Lower limit for write operations
async def broadcast_transaction(
    request: Request,
    broadcast_request: BroadcastTransactionRequest,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Broadcast a signed transaction to the network.
    
    The client must:
    1. Build the transaction (using SDK, web3.js, ethers.js, etc.)
    2. Sign it with their private key (offline)
    3. Send the raw signed transaction here
    
    **Security Note**: The API never handles private keys. All signing happens client-side.
    
    Example with ethers.js:
    ```javascript
    const tx = await contract.populateTransaction.mintFToken(amount, recipient, minOut);
    const signedTx = await wallet.signTransaction(tx);
    await fetch('/v1/transactions/broadcast', {
      method: 'POST',
      body: JSON.stringify({ rawTransaction: signedTx })
    });
    ```
    """
    # Validate hex string format
    try:
        broadcast_request.rawTransaction = validate_hex_string(
            broadcast_request.rawTransaction,
            prefix_required=True
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="INVALID_TRANSACTION_FORMAT",
                message=f"Invalid transaction format: {str(e)}"
            ).model_dump()
        )
    
    try:
        tx_hash = sdk_service.broadcast_signed_transaction(
            broadcast_request.rawTransaction
        )
        
        # Track the transaction
        tx_tracker = get_tx_tracker()
        tx_tracker.track_transaction(tx_hash)
        
        return TransactionResponse(
            success=True,
            transaction_hash=tx_hash,
            status="pending"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="INVALID_TRANSACTION",
                message=f"Invalid transaction format: {str(e)}"
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=True,
                code="BROADCAST_ERROR",
                message=f"Failed to broadcast transaction: {str(e)}"
            ).model_dump()
        )


@router.post("/mint/f-token/prepare", response_model=TransactionDataResponse, tags=["transactions"])
@limiter.limit("100/minute")
async def prepare_mint_f_token(
    request: Request,
    mint_request: MintFTokenRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    estimate_gas: bool = Query(False, description="Estimate gas for the transaction"),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction (required for gas estimation)")
):
    """
    Prepare unsigned transaction for minting fToken.
    
    Returns transaction data that can be signed by the client.
    The client should sign this transaction and send it to /transactions/broadcast.
    
    Set `estimate_gas=true` to get gas estimation (requires `from_address`).
    """
    # Validate from_address is provided if gas estimation is requested
    if estimate_gas and not from_address:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="MISSING_PARAMETER",
                message="from_address is required when estimate_gas=true"
            ).model_dump()
        )
    
    try:
        tx_data = sdk_service.build_mint_f_token_transaction(
            market_address=mint_request.market_address,
            base_in=mint_request.base_in,
            recipient=mint_request.recipient,
            min_f_token_out=mint_request.min_f_token_out
        )
        
        # Estimate gas if requested
        if estimate_gas:
            gas_estimation = sdk_service.estimate_transaction_gas(tx_data, from_address)
            tx_data.update(gas_estimation)
            gas_estimation = sdk_service.estimate_transaction_gas(tx_data, from_address)
            tx_data.update(gas_estimation)
        
        return TransactionDataResponse(**tx_data)
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
                message=f"Failed to prepare transaction: {str(e)}"
            ).model_dump()
        )


@router.post("/mint/x-token/prepare", response_model=TransactionDataResponse, tags=["transactions"])
@limiter.limit("100/minute")
async def prepare_mint_x_token(
    request: Request,
    mint_request: MintXTokenRequest,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Prepare unsigned transaction for minting xToken.
    
    Returns transaction data that can be signed by the client.
    """
    try:
        tx_data = sdk_service.build_mint_x_token_transaction(
            market_address=mint_request.market_address,
            base_in=mint_request.base_in,
            recipient=mint_request.recipient,
            min_x_token_out=mint_request.min_x_token_out
        )
        return TransactionDataResponse(**tx_data)
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
                message=f"Failed to prepare transaction: {str(e)}"
            ).model_dump()
        )


@router.post("/mint/both/prepare", response_model=TransactionDataResponse, tags=["transactions"])
@limiter.limit("100/minute")
async def prepare_mint_both_tokens(
    request: Request,
    mint_request: MintBothTokensRequest,
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Prepare unsigned transaction for minting both fToken and xToken.
    
    Returns transaction data that can be signed by the client.
    """
    try:
        tx_data = sdk_service.build_mint_both_tokens_transaction(
            market_address=mint_request.market_address,
            base_in=mint_request.base_in,
            recipient=mint_request.recipient,
            min_f_token_out=mint_request.min_f_token_out,
            min_x_token_out=mint_request.min_x_token_out
        )
        return TransactionDataResponse(**tx_data)
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
                message=f"Failed to prepare transaction: {str(e)}"
            ).model_dump()
        )


@router.post("/approve/prepare", response_model=TransactionDataResponse, tags=["transactions"])
@limiter.limit("100/minute")
async def prepare_approve(
    request: Request,
    approve_request: ApproveRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """
    Prepare unsigned transaction for token approval.
    
    Returns transaction data that can be signed by the client.
    
    Note: The from_address should be provided by the client (via query param or header).
    This is the address that will sign the transaction.
    """
    try:
        tx_data = sdk_service.build_approve_transaction(
            token_address=approve_request.token_address,
            spender_address=approve_request.spender_address,
            amount=approve_request.amount,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
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
                message=f"Failed to prepare transaction: {str(e)}"
            ).model_dump()
        )


@router.post("/transfer/prepare", response_model=TransactionDataResponse, tags=["transactions"])
@limiter.limit("100/minute")
async def prepare_transfer(
    request: Request,
    transfer_request: TransferRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """
    Prepare unsigned transaction for token transfer.
    
    Returns transaction data that can be signed by the client.
    
    Note: The from_address should be provided by the client (via query param or header).
    This is the address that will sign the transaction.
    """
    try:
        tx_data = sdk_service.build_transfer_transaction(
            token_address=transfer_request.token_address,
            recipient_address=transfer_request.recipient_address,
            amount=transfer_request.amount,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
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
                message=f"Failed to prepare transaction: {str(e)}"
            ).model_dump()
        )

# V1 Operations
@router.post("/v1/rebalance-pool/{pool_address}/deposit/prepare", response_model=TransactionDataResponse, tags=["transactions", "v1"])
@limiter.limit("100/minute")
async def prepare_rebalance_pool_deposit(
    request: Request,
    pool_address: str,
    deposit_request: RebalancePoolDepositRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for depositing to V1 rebalance pool."""
    try:
        tx_data = sdk_service.build_rebalance_pool_deposit_transaction(
            pool_address=pool_address,
            amount=deposit_request.amount,
            recipient=deposit_request.recipient,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/v1/rebalance-pool/{pool_address}/withdraw/prepare", response_model=TransactionDataResponse, tags=["transactions", "v1"])
@limiter.limit("100/minute")
async def prepare_rebalance_pool_withdraw(
    request: Request,
    pool_address: str,
    withdraw_request: RebalancePoolWithdrawRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for withdrawing from V1 rebalance pool."""
    try:
        tx_data = sdk_service.build_rebalance_pool_withdraw_transaction(
            pool_address=pool_address,
            claim_rewards=withdraw_request.claim_rewards,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Savings & Stability Pool
@router.post("/savings/deposit/prepare", response_model=TransactionDataResponse, tags=["transactions", "savings"])
@limiter.limit("100/minute")
async def prepare_savings_deposit(
    request: Request,
    deposit_request: SavingsDepositRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for depositing to fxSAVE."""
    try:
        tx_data = sdk_service.build_savings_deposit_transaction(
            amount=deposit_request.amount,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/savings/redeem/prepare", response_model=TransactionDataResponse, tags=["transactions", "savings"])
@limiter.limit("100/minute")
async def prepare_savings_redeem(
    request: Request,
    redeem_request: SavingsRedeemRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for redeeming fxSAVE."""
    try:
        tx_data = sdk_service.build_savings_redeem_transaction(
            amount=redeem_request.amount,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/stability-pool/deposit/prepare", response_model=TransactionDataResponse, tags=["transactions", "stability-pool"])
@limiter.limit("100/minute")
async def prepare_stability_pool_deposit(
    request: Request,
    deposit_request: StabilityPoolDepositRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for depositing to stability pool."""
    try:
        tx_data = sdk_service.build_stability_pool_deposit_transaction(
            amount=deposit_request.amount,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/stability-pool/withdraw/prepare", response_model=TransactionDataResponse, tags=["transactions", "stability-pool"])
@limiter.limit("100/minute")
async def prepare_stability_pool_withdraw(
    request: Request,
    withdraw_request: StabilityPoolWithdrawRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for withdrawing from stability pool."""
    try:
        tx_data = sdk_service.build_stability_pool_withdraw_transaction(
            amount=withdraw_request.amount,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Vesting
@router.post("/vesting/{token_type}/claim/prepare", response_model=TransactionDataResponse, tags=["transactions", "vesting"])
@limiter.limit("100/minute")
async def prepare_vesting_claim(
    request: Request,
    token_type: str,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for claiming vesting rewards."""
    try:
        tx_data = sdk_service.build_vesting_claim_transaction(
            token_type=token_type,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Advanced Operations
@router.post("/pool-manager/{pool_address}/harvest/prepare", response_model=TransactionDataResponse, tags=["transactions", "advanced"])
@limiter.limit("100/minute")
async def prepare_harvest(
    request: Request,
    pool_address: str,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for harvesting pool manager rewards."""
    try:
        tx_data = sdk_service.build_harvest_transaction(
            pool_address=pool_address,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/reserve-pool/request-bonus/prepare", response_model=TransactionDataResponse, tags=["transactions", "advanced"])
@limiter.limit("100/minute")
async def prepare_request_bonus(
    request: Request,
    bonus_request: RequestBonusRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for requesting reserve pool bonus."""
    try:
        tx_data = sdk_service.build_request_bonus_transaction(
            token_address=bonus_request.token_address,
            amount=bonus_request.amount,
            recipient=bonus_request.recipient,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# V2 Position Operations
@router.post("/v2/position/{position_id}/operate/prepare", response_model=TransactionDataResponse, tags=["transactions", "v2"])
@limiter.limit("100/minute")
async def prepare_operate_position(
    request: Request,
    position_id: int,
    operate_request: OperatePositionRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for operating a V2 position."""
    try:
        tx_data = sdk_service.build_operate_position_transaction(
            pool_address=operate_request.pool_address,
            position_id=position_id,
            new_collateral=operate_request.new_collateral,
            new_debt=operate_request.new_debt,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/v2/position/{position_id}/rebalance/prepare", response_model=TransactionDataResponse, tags=["transactions", "v2"])
@limiter.limit("100/minute")
async def prepare_rebalance_position(
    request: Request,
    position_id: int,
    rebalance_request: RebalancePositionRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for rebalancing a V2 position."""
    try:
        tx_data = sdk_service.build_rebalance_position_transaction(
            pool_address=rebalance_request.pool_address,
            position_id=position_id,
            receiver=rebalance_request.receiver,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/v2/position/{position_id}/liquidate/prepare", response_model=TransactionDataResponse, tags=["transactions", "v2"])
@limiter.limit("100/minute")
async def prepare_liquidate_position(
    request: Request,
    position_id: int,
    liquidate_request: LiquidatePositionRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for liquidating a V2 position."""
    try:
        tx_data = sdk_service.build_liquidate_position_transaction(
            pool_address=liquidate_request.pool_address,
            position_id=position_id,
            receiver=liquidate_request.receiver,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Gauge Operations
@router.post("/gauges/{gauge_address}/vote/prepare", response_model=TransactionDataResponse, tags=["transactions", "gauges"])
@limiter.limit("100/minute")
async def prepare_gauge_vote(
    request: Request,
    gauge_address: str,
    vote_request: GaugeVoteRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for voting on gauge weight."""
    try:
        tx_data = sdk_service.build_gauge_vote_transaction(
            gauge_address=gauge_address,
            weight=vote_request.weight,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/gauges/{gauge_address}/claim/prepare", response_model=TransactionDataResponse, tags=["transactions", "gauges"])
@limiter.limit("100/minute")
async def prepare_gauge_claim(
    request: Request,
    gauge_address: str,
    claim_request: GaugeClaimRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for claiming gauge rewards."""
    try:
        tx_data = sdk_service.build_gauge_claim_transaction(
            gauge_address=gauge_address,
            token_address=claim_request.token_address,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# veFXN Operations
@router.post("/vefxn/deposit/prepare", response_model=TransactionDataResponse, tags=["transactions", "vefxn"])
@limiter.limit("100/minute")
async def prepare_vefxn_deposit(
    request: Request,
    deposit_request: VeFxnDepositRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for depositing to veFXN."""
    try:
        tx_data = sdk_service.build_vefxn_deposit_transaction(
            amount=deposit_request.amount,
            unlock_time=deposit_request.unlock_time,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Additional Minting
@router.post("/mint/treasury/prepare", response_model=TransactionDataResponse, tags=["transactions", "minting"])
@limiter.limit("100/minute")
async def prepare_mint_via_treasury(
    request: Request,
    mint_request: MintViaTreasuryRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for minting via treasury."""
    try:
        tx_data = sdk_service.build_mint_via_treasury_transaction(
            base_in=mint_request.base_in,
            recipient=mint_request.recipient,
            option=mint_request.option,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/mint/gateway/prepare", response_model=TransactionDataResponse, tags=["transactions", "minting"])
@limiter.limit("100/minute")
async def prepare_mint_via_gateway(
    request: Request,
    mint_request: MintViaGatewayRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction"),
):
    """Prepare unsigned transaction for minting via gateway."""
    try:
        tx_data = sdk_service.build_mint_via_gateway_transaction(
            amount_eth=mint_request.amount_eth,
            min_token_out=mint_request.min_token_out,
            token_type=mint_request.token_type,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())

# Redeem Operations
@router.post("/redeem/prepare", response_model=TransactionDataResponse, tags=["transactions", "minting"])
@limiter.limit("100/minute")
async def prepare_redeem(
    request: Request,
    redeem_request: RedeemRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for redeeming tokens."""
    try:
        tx_data = sdk_service.build_redeem_transaction(
            market_address=redeem_request.market_address,
            f_token_in=redeem_request.f_token_in,
            x_token_in=redeem_request.x_token_in,
            recipient=redeem_request.recipient,
            min_base_out=redeem_request.min_base_out,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/redeem/treasury/prepare", response_model=TransactionDataResponse, tags=["transactions", "minting"])
@limiter.limit("100/minute")
async def prepare_redeem_via_treasury(
    request: Request,
    redeem_request: RedeemViaTreasuryRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for redeeming via treasury."""
    try:
        tx_data = sdk_service.build_redeem_via_treasury_transaction(
            f_token_in=redeem_request.f_token_in,
            x_token_in=redeem_request.x_token_in,
            owner=redeem_request.owner,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Additional V1 Operations
@router.post("/v1/rebalance-pool/{pool_address}/unlock/prepare", response_model=TransactionDataResponse, tags=["transactions", "v1"])
@limiter.limit("100/minute")
async def prepare_rebalance_pool_unlock(
    request: Request,
    pool_address: str,
    unlock_request: RebalancePoolUnlockRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for unlocking rebalance pool assets."""
    try:
        tx_data = sdk_service.build_rebalance_pool_unlock_transaction(
            pool_address=pool_address,
            amount=unlock_request.amount,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/v1/rebalance-pool/{pool_address}/claim/prepare", response_model=TransactionDataResponse, tags=["transactions", "v1"])
@limiter.limit("100/minute")
async def prepare_rebalance_pool_claim(
    request: Request,
    pool_address: str,
    claim_request: RebalancePoolClaimRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for claiming rebalance pool rewards."""
    try:
        tx_data = sdk_service.build_rebalance_pool_claim_transaction(
            pool_address=pool_address,
            tokens=claim_request.tokens,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Additional Advanced Operations
@router.post("/swap/prepare", response_model=TransactionDataResponse, tags=["transactions", "advanced"])
@limiter.limit("100/minute")
async def prepare_swap(
    request: Request,
    swap_request: SwapRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for swapping tokens."""
    try:
        tx_data = sdk_service.build_swap_transaction(
            token_in=swap_request.token_in,
            amount_in=swap_request.amount_in,
            encoding=swap_request.encoding,
            routes=swap_request.routes,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/flash-loan/prepare", response_model=TransactionDataResponse, tags=["transactions", "advanced"])
@limiter.limit("100/minute")
async def prepare_flash_loan(
    request: Request,
    flash_loan_request: FlashLoanRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for flash loan."""
    try:
        tx_data = sdk_service.build_flash_loan_transaction(
            token_address=flash_loan_request.token_address,
            amount=flash_loan_request.amount,
            receiver=flash_loan_request.receiver,
            data=flash_loan_request.data,
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


@router.post("/treasury/harvest/prepare", response_model=TransactionDataResponse, tags=["transactions", "advanced"])
@limiter.limit("100/minute")
async def prepare_harvest_treasury(
    request: Request,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transaction for harvesting treasury rewards."""
    try:
        tx_data = sdk_service.build_harvest_treasury_transaction(
            from_address=from_address
        )
        return TransactionDataResponse(**tx_data)
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transaction: {str(e)}").dict())


# Additional Gauge Operations
@router.post("/gauges/claim-all/prepare", response_model=PreparedTransactionsResponse, tags=["transactions", "gauges"])
@limiter.limit("100/minute")
async def prepare_claim_all_gauge_rewards(
    request: Request,
    claim_all_request: ClaimAllGaugeRewardsRequest,
    sdk_service: SDKService = Depends(get_sdk_service),
    from_address: Optional[str] = Query(None, description="Address that will sign the transaction")
):
    """Prepare unsigned transactions for claiming all gauge rewards."""
    try:
        tx_data_list = sdk_service.build_claim_all_gauge_rewards_transactions(
            gauge_addresses=claim_all_request.gauge_addresses,
            from_address=from_address
        )
        
        transactions = [TransactionDataResponse(**tx) for tx in tx_data_list]
        return PreparedTransactionsResponse(
            transactions=transactions,
            count=len(transactions)
        )
    except ContractCallError as e:
        raise HTTPException(status_code=400, detail=ErrorResponse(error=True, code="CONTRACT_CALL_ERROR", message=str(e)).dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=ErrorResponse(error=True, code="INTERNAL_ERROR", message=f"Failed to prepare transactions: {str(e)}").model_dump())


@router.get("/{tx_hash}/status", response_model=TransactionStatusResponse, tags=["transactions"])
@limiter.limit("100/minute")
async def get_transaction_status(
    request: Request,
    tx_hash: str = Path(..., description="Transaction hash"),
    sdk_service: SDKService = Depends(get_sdk_service)
):
    """
    Get the status of a broadcasted transaction.
    
    Returns transaction status including:
    - Current status (pending, confirmed, failed, not_found)
    - Block number (if confirmed)
    - Confirmations count
    - Gas used (if confirmed)
    - Error message (if failed)
    """
    # Validate transaction hash format
    try:
        tx_hash = validate_hex_string(tx_hash, prefix_required=True)
        if len(tx_hash) != 66:  # 0x + 64 hex chars
            raise ValueError("Transaction hash must be 64 hex characters")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=True,
                code="INVALID_TRANSACTION_HASH",
                message=f"Invalid transaction hash format: {str(e)}"
            ).model_dump()
        )
    
    # Get transaction from tracker
    tx_tracker = get_tx_tracker()
    tracked_tx = tx_tracker.get_transaction(tx_hash)
    
    if tracked_tx:
        # Return tracked transaction status
        return TransactionStatusResponse(**tracked_tx)
    
    # If not tracked, try to get from blockchain
    try:
        if sdk_service.client:
            tx_receipt = sdk_service.client.w3.eth.get_transaction_receipt(tx_hash)
            tx = sdk_service.client.w3.eth.get_transaction(tx_hash)
            current_block = sdk_service.client.w3.eth.block_number
            
            status = "confirmed" if tx_receipt.status == 1 else "failed"
            confirmations = max(0, current_block - tx_receipt.blockNumber) if tx_receipt.blockNumber else 0
            
            return TransactionStatusResponse(
                transaction_hash=tx_hash,
                status=status,
                block_number=tx_receipt.blockNumber,
                confirmations=confirmations,
                gas_used=tx_receipt.gasUsed,
                effective_gas_price=str(tx_receipt.effectiveGasPrice) if hasattr(tx_receipt, 'effectiveGasPrice') else None,
                error=None if status == "confirmed" else "Transaction reverted"
            )
    except Exception:
        # Transaction not found or error querying
        return TransactionStatusResponse(
            transaction_hash=tx_hash,
            status="not_found",
            block_number=None,
            confirmations=None,
            gas_used=None,
            effective_gas_price=None,
            error=None
        )

