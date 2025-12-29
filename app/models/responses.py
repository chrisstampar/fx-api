"""
Response models for API endpoints.

All responses use Pydantic models for validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


class StatusResponse(BaseModel):
    """API status response."""
    status: str
    version: str
    environment: str
    rpc_connected: bool
    components: Optional[Dict[str, Any]] = Field(default=None, description="Component health status")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with component status."""
    status: str = Field(..., description="Overall service status (healthy, degraded, unhealthy)")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Health check timestamp")
    components: Dict[str, Any] = Field(..., description="Individual component health status")
    rpc_status: Dict[str, Any] = Field(..., description="RPC connection status for each endpoint")
    sdk_status: Dict[str, Any] = Field(..., description="SDK initialization status")


class BalanceResponse(BaseModel):
    """Single token balance response."""
    address: str
    token: str
    balance: str  # Decimal as string for JSON compatibility
    token_address: Optional[str] = None


class AllBalancesResponse(BaseModel):
    """All balances response."""
    address: str
    balances: Dict[str, str]  # token_name -> balance
    total_usd_value: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x1234567890123456789012345678901234567890",
                "balances": {
                    "fxusd": "1000.50",
                    "fxn": "500.25",
                    "feth": "10.75",
                    "xeth": "5.30"
                },
                "total_usd_value": "15234.56"
            }
        }


class ProtocolInfoResponse(BaseModel):
    """Protocol information response."""
    base_nav: str = Field(..., description="Base collateral NAV (stETH/wstETH) in USD")
    f_nav: str = Field(..., description="f-token NAV (fETH) - price of 1 fETH in USD")
    x_nav: str = Field(..., description="x-token NAV (xETH) - price of 1 xETH in USD")
    source: str = Field(default="treasury", description="Source of NAV data (treasury, v1_market, or v2_pool)")
    note: Optional[str] = Field(default=None, description="Additional information about the NAV values")
    
    class Config:
        json_schema_extra = {
            "example": {
                "base_nav": "2500.50",
                "f_nav": "2400.25",
                "x_nav": "2600.75",
                "source": "treasury",
                "note": "NAV calculated from stETH treasury"
            }
        }


class TokenNavResponse(BaseModel):
    """Token NAV response for specific tokens."""
    token: str = Field(..., description="Token name (e.g., 'feth', 'xeth', 'xcvx', 'xwbtc')")
    nav: str = Field(..., description="Net Asset Value - price of 1 token in USD")
    source: str = Field(..., description="Source of NAV data")
    note: Optional[str] = Field(default=None, description="Additional information")


class ErrorResponse(BaseModel):
    """Error response format."""
    error: bool = True
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class TransactionResponse(BaseModel):
    """Transaction submission response."""
    success: bool
    transaction_hash: str
    status: str  # "pending", "confirmed", "failed"
    gas_estimate: Optional[int] = None
    block_number: Optional[int] = None


# V2 Product Response Models
class V2PoolInfoResponse(BaseModel):
    """V2 Pool information response."""
    pool_address: str
    total_assets: str
    total_supply: str
    base_pool_address: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class V2PositionInfoResponse(BaseModel):
    """V2 Position information response."""
    position_id: int
    pool_address: str
    owner: str
    collateral: str
    debt: str
    collateral_ratio: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class V2PoolManagerInfoResponse(BaseModel):
    """V2 Pool Manager information response."""
    pool_address: str
    total_collateral: Optional[str] = None
    total_debt: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class V2ReservePoolInfoResponse(BaseModel):
    """V2 Reserve Pool information response."""
    pool_address: str
    total_reserves: Optional[str] = None
    bonus_ratio: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Convex Response Models
class ConvexVaultInfoResponse(BaseModel):
    """Convex vault information response."""
    vault_address: str
    pool_id: int
    pool_name: Optional[str] = None
    staked_balance: str
    staked_token: Optional[str] = None
    gauge_address: Optional[str] = None


class ConvexVaultRewardsResponse(BaseModel):
    """Convex vault rewards response."""
    vault_address: str
    pool_id: int
    rewards: Dict[str, str]  # token_address -> amount
    reward_tokens: List[str]  # List of reward token addresses


class ConvexPoolInfoResponse(BaseModel):
    """Convex pool information response."""
    pool_id: int
    pool_name: Optional[str] = None
    lp_token: Optional[str] = None
    gauge_address: Optional[str] = None
    tvl: Optional[str] = None
    reward_tokens: List[str] = []
    details: Optional[Dict[str, Any]] = None


class ConvexPoolsListResponse(BaseModel):
    """List of all Convex pools."""
    pools: Dict[int, Dict[str, Any]]  # pool_id -> pool_info
    total_pools: int
    page: Optional[int] = Field(None, description="Current page number")
    limit: Optional[int] = Field(None, description="Items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")


class ConvexUserVaultsResponse(BaseModel):
    """User's Convex vaults response."""
    address: str
    vaults: List[Dict[str, Any]]  # List of vault info
    total_vaults: int


# Curve Response Models
class CurvePoolInfoResponse(BaseModel):
    """Curve pool information response."""
    pool_address: str
    lp_token: Optional[str] = None
    gauge_address: Optional[str] = None
    virtual_price: Optional[str] = None
    balances: List[str] = []
    details: Optional[Dict[str, Any]] = None


class CurveGaugeBalanceResponse(BaseModel):
    """Curve gauge balance response."""
    gauge_address: str
    user_address: str
    staked_balance: str
    lp_token: Optional[str] = None


class CurveGaugeRewardsResponse(BaseModel):
    """Curve gauge rewards response."""
    gauge_address: str
    user_address: str
    rewards: Dict[str, str]  # token_address -> amount
    reward_tokens: List[str] = []


class CurvePoolsListResponse(BaseModel):
    """List of Curve pools."""
    pools: List[Dict[str, Any]]
    total_pools: int
    page: Optional[int] = Field(None, description="Current page number")
    limit: Optional[int] = Field(None, description="Items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")


# Protocol Info Response Models
class ProtocolPoolInfoResponse(BaseModel):
    """Pool manager information response."""
    pool_address: str
    collateral_capacity: Optional[str] = None
    collateral_balance: Optional[str] = None
    debt_capacity: Optional[str] = None
    debt_balance: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ProtocolMarketInfoResponse(BaseModel):
    """Market information response."""
    market_address: str
    collateral_ratio: Optional[str] = None
    total_collateral: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ProtocolTreasuryInfoResponse(BaseModel):
    """Treasury information response."""
    treasury_address: str
    details: Dict[str, Any]


class ProtocolV1InfoResponse(BaseModel):
    """V1 protocol information response."""
    nav: Optional[Dict[str, str]] = None
    collateral_ratio: Optional[str] = None
    rebalance_pools: Optional[List[str]] = None


class ProtocolPegKeeperInfoResponse(BaseModel):
    """Peg Keeper information response."""
    is_active: bool
    debt_ceiling: str
    total_debt: str
    details: Optional[Dict[str, Any]] = None


# Transaction Response Models
class TransactionResponse(BaseModel):
    """Transaction broadcast response."""
    success: bool
    transaction_hash: str
    status: str = Field(default="pending", description="Transaction status: pending, confirmed, failed")
    gas_estimate: Optional[int] = None
    block_number: Optional[int] = None


class TransactionDataResponse(BaseModel):
    """Unsigned transaction data response."""
    to: str
    data: str
    value: str
    gas: int
    gasPrice: Optional[str] = None
    maxFeePerGas: Optional[str] = None
    maxPriorityFeePerGas: Optional[str] = None
    nonce: int
    chainId: int
    estimated_gas: Optional[int] = Field(None, description="Estimated gas for the transaction (if estimation was requested)")
    estimated_gas_cost_wei: Optional[str] = Field(None, description="Estimated total gas cost in Wei (if estimation was requested)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "0x1234567890123456789012345678901234567890",
                "data": "0x095ea7b3000000000000000000000000...",
                "value": "0",
                "gas": 21000,
                "gasPrice": "20000000000",
                "maxFeePerGas": "30000000000",
                "maxPriorityFeePerGas": "2000000000",
                "nonce": 42,
                "chainId": 1,
                "estimated_gas": 65000,
                "estimated_gas_cost_wei": "1300000000000000"
            }
        }


class PreparedTransactionsResponse(BaseModel):
    """Response for multiple prepared transactions (e.g., claim all gauge rewards)."""
    transactions: List["TransactionDataResponse"]
    count: int


class BatchBalancesResponse(BaseModel):
    """Response for batch balance queries."""
    results: Dict[str, AllBalancesResponse] = Field(..., description="Address -> balances mapping")
    count: int = Field(..., description="Number of addresses queried")
    cached: int = Field(default=0, description="Number of results served from cache")


class BatchNavResponse(BaseModel):
    """Response for batch NAV queries."""
    results: Dict[str, TokenNavResponse] = Field(..., description="Token name -> NAV mapping")
    count: int = Field(..., description="Number of tokens queried")
    cached: int = Field(default=0, description="Number of results served from cache")


class TransactionStatusResponse(BaseModel):
    """Transaction status response."""
    transaction_hash: str = Field(..., description="Transaction hash")
    status: str = Field(..., description="Transaction status: pending, confirmed, failed, not_found")
    block_number: Optional[int] = Field(None, description="Block number where transaction was confirmed")
    confirmations: Optional[int] = Field(None, description="Number of confirmations")
    gas_used: Optional[int] = Field(None, description="Gas used by the transaction")
    effective_gas_price: Optional[str] = Field(None, description="Effective gas price in Wei")
    error: Optional[str] = Field(None, description="Error message if transaction failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_hash": "0x1234567890abcdef...",
                "status": "confirmed",
                "block_number": 19000000,
                "confirmations": 12,
                "gas_used": 21000,
                "effective_gas_price": "20000000000"
            }
        }
