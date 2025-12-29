"""
Request models for API endpoints.

All requests use Pydantic models for validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class BroadcastTransactionRequest(BaseModel):
    """Request to broadcast a signed transaction."""
    rawTransaction: str = Field(..., description="Signed transaction in hex format (0x...)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rawTransaction": "0x02f8..."
            }
        }


class MintFTokenRequest(BaseModel):
    """Request to prepare minting fToken transaction."""
    market_address: str = Field(..., description="Market contract address")
    base_in: str = Field(..., description="Amount of base collateral (human-readable)")
    recipient: Optional[str] = Field(None, description="Recipient address (defaults to sender)")
    min_f_token_out: str = Field(default="0", description="Minimum fToken output (slippage protection)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "market_address": "0x1234567890123456789012345678901234567890",
                "base_in": "1.5",
                "recipient": "0x1234567890123456789012345678901234567890",
                "min_f_token_out": "1.4"
            }
        }


class MintXTokenRequest(BaseModel):
    """Request to prepare minting xToken transaction."""
    market_address: str = Field(..., description="Market contract address")
    base_in: str = Field(..., description="Amount of base collateral (human-readable)")
    recipient: Optional[str] = Field(None, description="Recipient address (defaults to sender)")
    min_x_token_out: str = Field(default="0", description="Minimum xToken output (slippage protection)")


class MintBothTokensRequest(BaseModel):
    """Request to prepare minting both tokens transaction."""
    market_address: str = Field(..., description="Market contract address")
    base_in: str = Field(..., description="Amount of base collateral (human-readable)")
    recipient: Optional[str] = Field(None, description="Recipient address (defaults to sender)")
    min_f_token_out: str = Field(default="0", description="Minimum fToken output")
    min_x_token_out: str = Field(default="0", description="Minimum xToken output")


class ApproveRequest(BaseModel):
    """Request to prepare token approval transaction."""
    token_address: str = Field(..., description="Token contract address")
    spender_address: str = Field(..., description="Spender address")
    amount: str = Field(..., description="Approval amount (human-readable, use 'max' for unlimited)")


class TransferRequest(BaseModel):
    """Request to prepare token transfer transaction."""
    token_address: str = Field(..., description="Token contract address")
    recipient_address: str = Field(..., description="Recipient address")
    amount: str = Field(..., description="Transfer amount (human-readable)")


# V1 Operations
class RebalancePoolDepositRequest(BaseModel):
    """Request to prepare rebalance pool deposit transaction."""
    amount: str = Field(..., description="Amount to deposit (human-readable)")
    recipient: Optional[str] = Field(None, description="Recipient address (defaults to sender)")


class RebalancePoolWithdrawRequest(BaseModel):
    """Request to prepare rebalance pool withdraw transaction."""
    claim_rewards: bool = Field(default=True, description="Whether to claim rewards when withdrawing")


# Savings & Stability Pool
class SavingsDepositRequest(BaseModel):
    """Request to prepare savings deposit transaction."""
    amount: str = Field(..., description="Amount of fxUSD to deposit (human-readable)")


class SavingsRedeemRequest(BaseModel):
    """Request to prepare savings redeem transaction."""
    amount: str = Field(..., description="Amount of fxSAVE to redeem (human-readable)")


class StabilityPoolDepositRequest(BaseModel):
    """Request to prepare stability pool deposit transaction."""
    amount: str = Field(..., description="Amount to deposit (human-readable)")


class StabilityPoolWithdrawRequest(BaseModel):
    """Request to prepare stability pool withdraw transaction."""
    amount: str = Field(..., description="Amount to withdraw (human-readable)")


# Vesting
class VestingClaimRequest(BaseModel):
    """Request to prepare vesting claim transaction."""
    # Token type comes from path parameter, no body needed


# Advanced Operations
class HarvestRequest(BaseModel):
    """Request to prepare harvest transaction."""
    # Pool address comes from path parameter, no body needed


class RequestBonusRequest(BaseModel):
    """Request to prepare reserve pool bonus request transaction."""
    token_address: str = Field(..., description="Token address")
    amount: str = Field(..., description="Amount to request (human-readable)")
    recipient: Optional[str] = Field(None, description="Recipient address (defaults to sender)")


# V2 Position Operations
class OperatePositionRequest(BaseModel):
    """Request to prepare position operate transaction."""
    pool_address: str = Field(..., description="Pool address")
    new_collateral: str = Field(..., description="New collateral amount (human-readable)")
    new_debt: str = Field(..., description="New debt amount (human-readable)")


class RebalancePositionRequest(BaseModel):
    """Request to prepare position rebalance transaction."""
    pool_address: str = Field(..., description="Pool address")
    receiver: Optional[str] = Field(None, description="Receiver address (defaults to sender)")


class LiquidatePositionRequest(BaseModel):
    """Request to prepare position liquidation transaction."""
    pool_address: str = Field(..., description="Pool address")
    receiver: Optional[str] = Field(None, description="Receiver address (defaults to sender)")


# Gauge Operations
class GaugeVoteRequest(BaseModel):
    """Request to prepare gauge vote transaction."""
    weight: str = Field(..., description="Vote weight (human-readable, 0-1 scale)")


class GaugeClaimRequest(BaseModel):
    """Request to prepare gauge claim rewards transaction."""
    token_address: Optional[str] = Field(None, description="Specific reward token (optional, claims all if not specified)")


# veFXN Operations
class VeFxnDepositRequest(BaseModel):
    """Request to prepare veFXN deposit transaction."""
    amount: str = Field(..., description="Amount of FXN to lock (human-readable)")
    unlock_time: int = Field(..., description="Unix timestamp for unlock time")


# Additional Minting
class MintViaTreasuryRequest(BaseModel):
    """Request to prepare mint via treasury transaction."""
    base_in: str = Field(..., description="Amount of base collateral (human-readable)")
    recipient: Optional[str] = Field(None, description="Recipient address")
    option: int = Field(default=0, description="Mint option (0: Both, 1: fToken, 2: xToken)")


class MintViaGatewayRequest(BaseModel):
    """Request to prepare mint via gateway transaction."""
    amount_eth: str = Field(..., description="Amount of ETH to send (human-readable)")
    min_token_out: str = Field(default="0", description="Minimum token output (slippage protection)")
    token_type: str = Field(..., description="Token type: 'f' or 'x'")


# Redeem Operations
class RedeemRequest(BaseModel):
    """Request to prepare redeem transaction."""
    market_address: str = Field(..., description="Market contract address")
    f_token_in: str = Field(default="0", description="Amount of fToken to redeem (human-readable)")
    x_token_in: str = Field(default="0", description="Amount of xToken to redeem (human-readable)")
    recipient: Optional[str] = Field(None, description="Recipient address (defaults to sender)")
    min_base_out: str = Field(default="0", description="Minimum base token output (slippage protection)")


class RedeemViaTreasuryRequest(BaseModel):
    """Request to prepare redeem via treasury transaction."""
    f_token_in: str = Field(default="0", description="Amount of fToken to redeem (human-readable)")
    x_token_in: str = Field(default="0", description="Amount of xToken to redeem (human-readable)")
    owner: Optional[str] = Field(None, description="Owner address (defaults to sender)")


# Additional V1 Operations
class RebalancePoolUnlockRequest(BaseModel):
    """Request to prepare rebalance pool unlock transaction."""
    amount: str = Field(..., description="Amount to unlock (human-readable)")


class RebalancePoolClaimRequest(BaseModel):
    """Request to prepare rebalance pool claim rewards transaction."""
    tokens: List[str] = Field(..., description="List of reward token addresses to claim")


# Advanced Operations
class SwapRequest(BaseModel):
    """Request to prepare swap transaction."""
    token_in: str = Field(..., description="Token address to swap from")
    amount_in: str = Field(..., description="Amount to swap (human-readable)")
    encoding: int = Field(..., description="Encoding for the converter")
    routes: List[int] = Field(..., description="List of routes for the swap")


class FlashLoanRequest(BaseModel):
    """Request to prepare flash loan transaction."""
    token_address: str = Field(..., description="Token address to borrow")
    amount: str = Field(..., description="Amount to borrow (human-readable)")
    receiver: str = Field(..., description="Receiver address (must implement flash loan callback)")
    data: Optional[str] = Field(default="0x", description="Additional data (hex string)")


# Gauge Operations
class ClaimAllGaugeRewardsRequest(BaseModel):
    """Request to prepare claim all gauge rewards transactions."""
    gauge_addresses: Optional[List[str]] = Field(None, description="List of gauge addresses (defaults to all configured gauges)")


# Batch Operations
class BatchBalancesRequest(BaseModel):
    """Request to fetch balances for multiple addresses."""
    addresses: List[str] = Field(..., description="List of Ethereum addresses (max 100)", min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "addresses": [
                    "0x1234567890123456789012345678901234567890",
                    "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12"
                ]
            }
        }


class BatchNavRequest(BaseModel):
    """Request to fetch NAV for multiple tokens."""
    tokens: List[str] = Field(..., description="List of token symbols (max 50)", min_length=1, max_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tokens": ["feth", "xeth", "xcvx"]
            }
        }
