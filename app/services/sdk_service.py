"""
SDK Service wrapper.

Wraps the fx-sdk ProtocolClient to provide a service layer
for the API endpoints.
"""

import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal

from fx_sdk import ProtocolClient
from fx_sdk import constants as fx_constants
from fx_sdk.exceptions import (
    FXProtocolError,
    ContractCallError,
    TransactionFailedError,
    InsufficientBalanceError
)

logger = logging.getLogger(__name__)


class SDKService:
    """
    Service wrapper around the fx-sdk ProtocolClient.
    
    Handles RPC fallback logic and provides a clean interface
    for the API endpoints.
    """
    
    def __init__(self, rpc_url: str, rpc_urls: Optional[List[str]] = None):
        """
        Initialize the SDK service.
        
        Args:
            rpc_url: Primary RPC URL
            rpc_urls: List of RPC URLs for fallback (optional)
        """
        self.rpc_url = rpc_url
        self.rpc_urls = rpc_urls or [rpc_url]
        self.client: Optional[ProtocolClient] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the ProtocolClient with the primary RPC URL."""
        try:
            self.client = ProtocolClient(rpc_url=self.rpc_url)
            logger.info(f"SDK client initialized with RPC: {self.rpc_url}")
        except Exception as e:
            logger.error(f"Failed to initialize SDK client: {e}")
            raise
    
    def _try_with_fallback(self, func, *args, **kwargs):
        """
        Try executing a function with fallback RPC URLs.
        
        If the primary RPC fails, tries other RPCs in the list.
        Tracks which RPC was used for monitoring.
        """
        last_error = None
        attempted_rpcs = []
        
        for idx, rpc_url in enumerate(self.rpc_urls):
            try:
                # Reinitialize client with new RPC if needed
                if self.client is None or self.client.w3.provider.endpoint_uri != rpc_url:
                    logger.info(f"Switching to RPC {idx + 1}/{len(self.rpc_urls)}: {rpc_url}")
                    self.client = ProtocolClient(rpc_url=rpc_url)
                
                # Test connection before using
                if not self.client.w3.is_connected():
                    raise FXProtocolError(f"RPC {rpc_url} is not connected")
                
                result = func(*args, **kwargs)
                
                # Log successful RPC usage (only if not primary)
                if idx > 0:
                    logger.info(f"Successfully used fallback RPC {idx + 1}/{len(self.rpc_urls)}: {rpc_url}")
                
                return result
            except Exception as e:
                last_error = e
                attempted_rpcs.append(rpc_url)
                logger.warning(f"RPC {idx + 1}/{len(self.rpc_urls)} ({rpc_url}) failed: {e}, trying next...")
                continue
        
        # All RPCs failed
        error_msg = f"All {len(self.rpc_urls)} RPC endpoints failed. Attempted: {', '.join(attempted_rpcs)}. Last error: {last_error}"
        logger.error(error_msg)
        raise ContractCallError(error_msg)
    
    # Balance methods
    def get_all_balances(self, address: str, include_usd_value: bool = True) -> Dict[str, any]:
        """
        Get all token balances for an address.
        
        Args:
            address: Ethereum address
            include_usd_value: Whether to calculate total USD value
            
        Returns:
            Dictionary with 'balances' and optionally 'total_usd_value'
        """
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            balances = self.client.get_all_balances(address)
            # Convert Decimal values to strings for JSON serialization
            balances_dict = {token: str(balance) for token, balance in balances.items()}
            
            result = {"balances": balances_dict}
            
            # Calculate total USD value if requested
            if include_usd_value:
                try:
                    from app.services.price_service import PriceService
                    price_service = PriceService(self.client)
                    total_usd = price_service.calculate_total_usd_value(balances_dict)
                    result["total_usd_value"] = str(total_usd)
                except Exception as e:
                    logger.warning(f"Failed to calculate USD value: {e}")
                    result["total_usd_value"] = None
            
            return result
        except Exception as e:
            logger.error(f"Failed to get balances for {address}: {e}")
            raise
    
    def get_balance(self, address: str, token_name: str) -> str:
        """
        Get balance for a specific token.
        
        Args:
            address: Ethereum address
            token_name: Token name (e.g., 'fxusd', 'fxn', 'feth')
            
        Returns:
            Balance as string
        """
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            # Map token names to SDK methods and addresses
            token_method_map = {
                "fxusd": ("get_fxusd_balance", fx_constants.FXUSD),
                "fxn": ("get_fxn_balance", fx_constants.FXN),
                "feth": ("get_feth_balance", fx_constants.FETH),
                "rusd": ("get_rusd_balance", fx_constants.RUSD),
                "arusd": ("get_arusd_balance", fx_constants.ARUSD),
                "btcusd": ("get_btcusd_balance", fx_constants.BTCUSD),
                "cvxusd": ("get_cvxusd_balance", fx_constants.CVXUSD),
                "xeth": ("get_xeth_balance", fx_constants.XETH),
                "xcvx": ("get_xcvx_balance", fx_constants.XCVX),
                "xwbtc": ("get_xwbtc_balance", fx_constants.XWBTC),
                "xeeth": ("get_xeeth_balance", fx_constants.XEETH),
                "xezeth": ("get_xezeth_balance", fx_constants.XEZETH),
                "xsteth": ("get_xsteth_balance", fx_constants.XSTETH),
                "xfrxeth": ("get_xfrxeth_balance", fx_constants.XFRXETH),
                "fxsave": ("get_fxsave_balance", fx_constants.SAVING_FXUSD),  # SAVING_FXUSD is the fxSAVE token
                "fxsp": ("get_fxsp_balance", fx_constants.FXSP),
                "vefxn": ("get_vefxn_balance", fx_constants.VEFXN),
                "cvxfxn": ("get_cvxfxn_balance", fx_constants.CVXFXN_TOKEN),
            }
            
            token_name_lower = token_name.lower()
            if token_name_lower not in token_method_map:
                raise FXProtocolError(f"Unsupported token: {token_name}. Supported tokens: {', '.join(token_method_map.keys())}")
            
            # Get the method and token address
            method_name, token_address = token_method_map[token_name_lower]
            method = getattr(self.client, method_name)
            balance = method(account_address=address)
            
            # Return balance and token address
            return {
                "balance": str(balance),
                "token_address": token_address
            }
        except Exception as e:
            logger.error(f"Failed to get {token_name} balance for {address}: {e}")
            raise
    
    def get_token_balance_by_address(self, address: str, token_address: str) -> Dict[str, str]:
        """
        Get balance for any ERC-20 token by contract address.
        
        Args:
            address: Ethereum address
            token_address: Token contract address
            
        Returns:
            Dictionary with balance and token_address
        """
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            balance = self.client.get_token_balance(token_address, account_address=address)
            return {
                "balance": str(balance),
                "token_address": token_address
            }
        except Exception as e:
            logger.error(f"Failed to get token balance for {address}: {e}")
            raise
    
    # Protocol info methods (examples - will expand)
    def get_protocol_nav(self) -> Dict[str, str]:
        """Get protocol NAV information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            # Try to get V2 pool info first (most reliable)
            try:
                v2_info = self.client.get_v2_pool_info()
                return {
                    "base_nav": str(v2_info.get("base_nav", "0")),
                    "f_nav": str(v2_info.get("f_nav", "0")),
                    "x_nav": str(v2_info.get("x_nav", "0")),
                    "source": "v2_pool",
                    "note": "V2 fxUSD Base Pool NAV values. f_nav represents fETH price, x_nav represents xETH price."
                }
            except Exception:
                # Fallback to treasury NAV if V2 not available
                try:
                    treasury_nav = self.client.get_treasury_nav()
                    return {
                        "base_nav": str(treasury_nav.get("base_nav", "0")),
                        "f_nav": str(treasury_nav.get("f_nav", "0")),
                        "x_nav": str(treasury_nav.get("x_nav", "0")),
                        "source": "treasury",
                        "note": "Treasury NAV values. base_nav is stETH/wstETH collateral value, f_nav is fETH price (1 fETH = f_nav USD), x_nav is xETH price (1 xETH = x_nav USD)."
                    }
                except Exception:
                    # Last resort: try V1 NAV (may not be available)
                    nav = self.client.get_v1_nav()
                    # V1 returns fETH_NAV and xETH_NAV, map to f_nav and x_nav
                    return {
                        "base_nav": "0",  # V1 doesn't have base_nav
                        "f_nav": str(nav.get("fETH_NAV", "0")),
                        "x_nav": str(nav.get("xETH_NAV", "0")),
                        "source": "v1_market",
                        "note": "V1 Market NAV values. f_nav is fETH price, x_nav is xETH price. base_nav not available for V1."
                    }
        except Exception as e:
            logger.error(f"Failed to get protocol NAV: {e}")
            raise
    
    def get_token_nav(self, token_name: str) -> Dict[str, str]:
        """
        Get NAV for a specific token.
        
        Args:
            token_name: Token name (e.g., 'feth', 'xeth', 'xcvx', 'xwbtc')
            
        Returns:
            Dictionary with nav, source, and note
        """
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        token_lower = token_name.lower()
        
        try:
            # Get treasury NAV (contains base_nav, f_nav, x_nav)
            treasury_nav = self.client.get_treasury_nav()
            
            # Map tokens to NAV values
            nav_mapping = {
                "feth": ("f_nav", "fETH price (1 fETH = f_nav USD)"),
                "xeth": ("x_nav", "xETH price (1 xETH = x_nav USD)"),
                "xcvx": ("x_nav", "xCVX price (uses x-token NAV, typically ~xETH NAV)"),
                "xwbtc": ("x_nav", "xWBTC price (uses x-token NAV, typically ~xETH NAV)"),
                "xeeth": ("x_nav", "xeETH price (uses x-token NAV, typically ~xETH NAV)"),
                "xezeth": ("x_nav", "xezETH price (uses x-token NAV, typically ~xETH NAV)"),
                "xsteth": ("x_nav", "xstETH price (uses x-token NAV, typically ~xETH NAV)"),
                "xfrxeth": ("x_nav", "xfrxETH price (uses x-token NAV, typically ~xETH NAV)"),
            }
            
            if token_lower not in nav_mapping:
                raise FXProtocolError(
                    f"Unsupported token for NAV: {token_name}. "
                    f"Supported tokens: {', '.join(nav_mapping.keys())}"
                )
            
            nav_key, description = nav_mapping[token_lower]
            nav_value = treasury_nav.get(nav_key, Decimal("0"))
            
            return {
                "token": token_name,
                "nav": str(nav_value),
                "source": "treasury",
                "note": description
            }
        except Exception as e:
            logger.error(f"Failed to get {token_name} NAV: {e}")
            raise
    
    # V2 Product methods
    def get_v2_pool_info(self) -> Dict[str, Any]:
        """Get V2 pool information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pool_info = self.client.get_v2_pool_info()
            # Convert Decimal values to strings
            return {
                "pool_address": pool_info.get("base_pool_address", ""),
                "base_pool_address": pool_info.get("base_pool_address"),
                "total_assets": str(pool_info.get("total_assets", Decimal("0"))),
                "total_supply": str(pool_info.get("total_supply", Decimal("0"))),
                "details": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in pool_info.items()
                    if k not in ["base_pool_address", "total_assets", "total_supply"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get V2 pool info: {e}")
            raise
    
    def get_v2_position_info(self, position_id: int) -> Dict[str, Any]:
        """Get V2 position information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            position_info = self.client.get_position_info(position_id)
            # Convert Decimal values to strings
            return {
                "position_id": position_id,
                "pool_address": position_info.get("pool_address", ""),
                "owner": position_info.get("owner", ""),
                "collateral": str(position_info.get("collateral", Decimal("0"))),
                "debt": str(position_info.get("debt", Decimal("0"))),
                "collateral_ratio": str(position_info.get("collateral_ratio", Decimal("0"))) if position_info.get("collateral_ratio") else None,
                "details": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in position_info.items()
                    if k not in ["pool_address", "owner", "collateral", "debt", "collateral_ratio"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get V2 position info: {e}")
            raise
    
    def get_v2_pool_manager_info(self, pool_address: str) -> Dict[str, Any]:
        """Get V2 pool manager information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pool_info = self.client.get_pool_manager_info(pool_address)
            # Convert Decimal values to strings
            return {
                "pool_address": pool_address,
                "total_collateral": str(pool_info.get("total_collateral", Decimal("0"))) if pool_info.get("total_collateral") else None,
                "total_debt": str(pool_info.get("total_debt", Decimal("0"))) if pool_info.get("total_debt") else None,
                "details": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in pool_info.items()
                    if k not in ["total_collateral", "total_debt"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get V2 pool manager info: {e}")
            raise
    
    def get_v2_reserve_pool_info(self, token_address: str) -> Dict[str, Any]:
        """Get V2 reserve pool information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            bonus_ratio = self.client.get_reserve_pool_bonus_ratio(token_address)
            # Note: get_reserve_pool_bonus_ratio only returns the bonus ratio
            # We might need additional methods for full reserve pool info
            return {
                "pool_address": token_address,  # Using token address as pool identifier
                "bonus_ratio": str(bonus_ratio),
                "details": {}
            }
        except Exception as e:
            logger.error(f"Failed to get V2 reserve pool info: {e}")
            raise
    
    # Additional Protocol Info methods
    def get_pool_manager_info(self, pool_address: str) -> Dict[str, Any]:
        """Get pool manager information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pool_info = self.client.get_pool_manager_info(pool_address)
            # Convert Decimal values to strings
            return {
                "pool_address": pool_address,
                "collateral_capacity": str(pool_info.get("collateral_capacity", Decimal("0"))) if pool_info.get("collateral_capacity") else None,
                "collateral_balance": str(pool_info.get("collateral_balance", Decimal("0"))) if pool_info.get("collateral_balance") else None,
                "debt_capacity": str(pool_info.get("debt_capacity", Decimal("0"))) if pool_info.get("debt_capacity") else None,
                "debt_balance": str(pool_info.get("debt_balance", Decimal("0"))) if pool_info.get("debt_balance") else None,
                "details": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in pool_info.items()
                    if k not in ["collateral_capacity", "collateral_balance", "debt_capacity", "debt_balance"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get pool manager info: {e}")
            raise
    
    def get_market_info(self, market_address: str) -> Dict[str, Any]:
        """Get market information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            market_info = self.client.get_market_info(market_address)
            # Convert Decimal values to strings
            return {
                "market_address": market_address,
                "collateral_ratio": str(market_info.get("collateral_ratio", Decimal("0"))) if market_info.get("collateral_ratio") else None,
                "total_collateral": str(market_info.get("total_collateral", Decimal("0"))) if market_info.get("total_collateral") else None,
                "details": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in market_info.items()
                    if k not in ["collateral_ratio", "total_collateral"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get market info: {e}")
            raise
    
    def get_treasury_info(self) -> Dict[str, Any]:
        """Get stETH treasury information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            treasury_info = self.client.get_steth_treasury_info()
            # Convert Decimal values to strings
            # Treasury info doesn't have a treasury_address field, use a constant or extract from contract
            from fx_sdk import constants as fx_constants
            return {
                "treasury_address": fx_constants.STETH_TREASURY_PROXY if hasattr(fx_constants, 'STETH_TREASURY_PROXY') else "",
                "details": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in treasury_info.items()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get treasury info: {e}")
            raise
    
    def get_v1_nav(self) -> Dict[str, str]:
        """Get V1 NAV information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            nav = self.client.get_v1_nav()
            return {
                "base_nav": "0",  # V1 doesn't have base_nav
                "f_nav": str(nav.get("fETH_NAV", Decimal("0"))),
                "x_nav": str(nav.get("xETH_NAV", Decimal("0"))),
                "source": "v1_market",
                "note": "V1 Market NAV values. f_nav is fETH price, x_nav is xETH price. base_nav not available for V1."
            }
        except Exception as e:
            logger.error(f"Failed to get V1 NAV: {e}")
            raise
    
    def get_v1_collateral_ratio(self) -> Decimal:
        """Get V1 collateral ratio."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            ratio = self.client.get_v1_collateral_ratio()
            return ratio
        except Exception as e:
            logger.error(f"Failed to get V1 collateral ratio: {e}")
            raise
    
    def get_v1_rebalance_pools(self) -> List[str]:
        """Get all registered V1 rebalance pools."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pools = self.client.get_v1_rebalance_pools()
            return pools
        except Exception as e:
            logger.error(f"Failed to get V1 rebalance pools: {e}")
            raise
    
    def get_rebalance_pool_balances(self, pool_address: str, address: str) -> Dict[str, Any]:
        """Get rebalance pool balances for a user."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            balances = self.client.get_v1_rebalance_pool_balances(pool_address, account_address=address)
            # Convert Decimal values to strings
            return {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in balances.items()
            }
        except Exception as e:
            logger.error(f"Failed to get rebalance pool balances: {e}")
            raise
    
    def get_steth_price(self) -> Decimal:
        """Get stETH price."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            price = self.client.get_steth_price()
            return price
        except Exception as e:
            logger.error(f"Failed to get stETH price: {e}")
            raise
    
    def get_fxusd_total_supply(self) -> Decimal:
        """Get fxUSD total supply."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            supply = self.client.get_fxusd_total_supply()
            return supply
        except Exception as e:
            logger.error(f"Failed to get fxUSD total supply: {e}")
            raise
    
    def get_peg_keeper_info(self) -> Dict[str, Any]:
        """Get peg keeper information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            peg_info = self.client.get_peg_keeper_info()
            # Convert Decimal values to strings
            return {
                "is_active": peg_info.get("is_active", False),
                "debt_ceiling": str(peg_info.get("debt_ceiling", Decimal("0"))),
                "total_debt": str(peg_info.get("total_debt", Decimal("0"))),
                "details": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in peg_info.items()
                    if k not in ["is_active", "debt_ceiling", "total_debt"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get peg keeper info: {e}")
            raise
    
    # Gauge methods
    def get_gauge_weight(self, gauge_address: str) -> Decimal:
        """Get gauge weight."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            weight = self.client.get_gauge_weight(gauge_address)
            return weight
        except Exception as e:
            logger.error(f"Failed to get gauge weight: {e}")
            raise
    
    def get_gauge_relative_weight(self, gauge_address: str) -> Decimal:
        """Get gauge relative weight."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            relative_weight = self.client.get_gauge_relative_weight(gauge_address)
            return relative_weight
        except Exception as e:
            logger.error(f"Failed to get gauge relative weight: {e}")
            raise
    
    def get_claimable_rewards(self, gauge_address: str, token_address: str, user_address: str) -> Decimal:
        """Get claimable rewards for a gauge."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            rewards = self.client.get_claimable_rewards(
                gauge_address=gauge_address,
                token_address=token_address,
                account_address=user_address
            )
            return rewards
        except Exception as e:
            logger.error(f"Failed to get claimable rewards: {e}")
            raise
    
    def get_all_gauge_balances(self, address: str) -> Dict[str, Any]:
        """Get all gauge balances for an address."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            balances = self.client.get_all_gauge_balances(account_address=address)
            # Convert Decimal values to strings
            return {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in balances.items()
            }
        except Exception as e:
            logger.error(f"Failed to get all gauge balances: {e}")
            raise
    
    # Transaction methods
    def broadcast_signed_transaction(self, raw_transaction: str) -> str:
        """
        Broadcast a signed transaction to the network.
        
        Args:
            raw_transaction: Hex-encoded signed transaction (0x...)
            
        Returns:
            Transaction hash
        """
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            # Remove '0x' prefix if present
            if raw_transaction.startswith('0x'):
                raw_tx_bytes = bytes.fromhex(raw_transaction[2:])
            else:
                raw_tx_bytes = bytes.fromhex(raw_transaction)
            
            # Broadcast using Web3
            tx_hash = self.client.w3.eth.send_raw_transaction(raw_tx_bytes)
            return tx_hash.hex()
        except ValueError as e:
            raise FXProtocolError(f"Invalid transaction format: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to broadcast transaction: {e}")
            raise FXProtocolError(f"Failed to broadcast transaction: {str(e)}")
    
    def estimate_transaction_gas(self, tx_data: Dict[str, Any], from_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Estimate gas for a transaction.
        
        Args:
            tx_data: Transaction data dictionary
            from_address: Address that will send the transaction (optional)
            
        Returns:
            Dictionary with estimated_gas and estimated_gas_cost_wei
        """
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            # Build transaction dict for estimation
            tx_dict = {
                "to": tx_data.get("to"),
                "data": tx_data.get("data"),
                "value": int(tx_data.get("value", "0"), 16) if isinstance(tx_data.get("value"), str) and tx_data["value"].startswith("0x") else int(tx_data.get("value", 0)),
            }
            
            if from_address:
                tx_dict["from"] = from_address
            
            # Estimate gas
            estimated_gas = self.client.w3.eth.estimate_gas(tx_dict)
            
            # Get current gas price
            try:
                gas_price = self.client.w3.eth.gas_price
                estimated_cost = estimated_gas * gas_price
            except Exception:
                # Fallback if gas price unavailable
                gas_price = None
                estimated_cost = None
            
            return {
                "estimated_gas": estimated_gas,
                "estimated_gas_cost_wei": str(estimated_cost) if estimated_cost else None
            }
        except Exception as e:
            logger.warning(f"Failed to estimate gas: {e}")
            return {
                "estimated_gas": None,
                "estimated_gas_cost_wei": None
            }
    
    def build_mint_f_token_transaction(
        self,
        market_address: str,
        base_in: str,
        recipient: Optional[str] = None,
        min_f_token_out: str = "0"
    ) -> Dict[str, Any]:
        """Build unsigned transaction for minting fToken."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_mint_f_token_transaction(
                market_address=market_address,
                base_in=base_in,
                recipient=recipient,
                min_f_token_out=min_f_token_out
            )
            # Convert values to strings for JSON
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build mint fToken transaction: {e}")
            raise
    
    def build_mint_x_token_transaction(
        self,
        market_address: str,
        base_in: str,
        recipient: Optional[str] = None,
        min_x_token_out: str = "0"
    ) -> Dict[str, Any]:
        """Build unsigned transaction for minting xToken."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_mint_x_token_transaction(
                market_address=market_address,
                base_in=base_in,
                recipient=recipient,
                min_x_token_out=min_x_token_out
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build mint xToken transaction: {e}")
            raise
    
    def build_mint_both_tokens_transaction(
        self,
        market_address: str,
        base_in: str,
        recipient: Optional[str] = None,
        min_f_token_out: str = "0",
        min_x_token_out: str = "0"
    ) -> Dict[str, Any]:
        """Build unsigned transaction for minting both tokens."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_mint_both_tokens_transaction(
                market_address=market_address,
                base_in=base_in,
                recipient=recipient,
                min_f_token_out=min_f_token_out,
                min_x_token_out=min_x_token_out
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build mint both tokens transaction: {e}")
            raise
    
    def build_approve_transaction(
        self,
        token_address: str,
        spender_address: str,
        amount: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for token approval."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_approve_transaction(
                token_address=token_address,
                spender_address=spender_address,
                amount=amount,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build approve transaction: {e}")
            raise
    
    def build_transfer_transaction(
        self,
        token_address: str,
        recipient_address: str,
        amount: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for token transfer."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_transfer_transaction(
                token_address=token_address,
                recipient_address=recipient_address,
                amount=amount,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build transfer transaction: {e}")
            raise
    
    # V1 Operations
    def build_rebalance_pool_deposit_transaction(
        self,
        pool_address: str,
        amount: str,
        recipient: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for depositing to V1 rebalance pool."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_rebalance_pool_deposit_transaction(
                pool_address=pool_address,
                amount=amount,
                recipient=recipient,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build rebalance pool deposit transaction: {e}")
            raise
    
    def build_rebalance_pool_withdraw_transaction(
        self,
        pool_address: str,
        claim_rewards: bool = True,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for withdrawing from V1 rebalance pool."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_rebalance_pool_withdraw_transaction(
                pool_address=pool_address,
                claim_rewards=claim_rewards,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build rebalance pool withdraw transaction: {e}")
            raise
    
    # Savings & Stability Pool
    def build_savings_deposit_transaction(
        self,
        amount: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for depositing to fxSAVE."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_savings_deposit_transaction(
                amount=amount,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build savings deposit transaction: {e}")
            raise
    
    def build_savings_redeem_transaction(
        self,
        amount: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for redeeming fxSAVE."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_savings_redeem_transaction(
                amount=amount,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build savings redeem transaction: {e}")
            raise
    
    def build_stability_pool_deposit_transaction(
        self,
        amount: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for depositing to stability pool."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_stability_pool_deposit_transaction(
                amount=amount,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build stability pool deposit transaction: {e}")
            raise
    
    def build_stability_pool_withdraw_transaction(
        self,
        amount: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for withdrawing from stability pool."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_stability_pool_withdraw_transaction(
                amount=amount,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build stability pool withdraw transaction: {e}")
            raise
    
    # Vesting
    def build_vesting_claim_transaction(
        self,
        token_type: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for claiming vesting rewards."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_vesting_claim_transaction(
                token_type=token_type,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build vesting claim transaction: {e}")
            raise
    
    # Advanced Operations
    def build_harvest_transaction(
        self,
        pool_address: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for harvesting pool manager rewards."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_harvest_pool_manager_transaction(
                pool_address=pool_address,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build harvest transaction: {e}")
            raise
    
    def build_request_bonus_transaction(
        self,
        token_address: str,
        amount: str,
        recipient: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for requesting reserve pool bonus."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_request_bonus_transaction(
                token_address=token_address,
                amount=amount,
                recipient=recipient,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build request bonus transaction: {e}")
            raise
    
    # V2 Position Operations
    def build_operate_position_transaction(
        self,
        pool_address: str,
        position_id: int,
        new_collateral: str,
        new_debt: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for operating a V2 position."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_operate_position_transaction(
                pool_address=pool_address,
                position_id=position_id,
                new_collateral=new_collateral,
                new_debt=new_debt,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build operate position transaction: {e}")
            raise
    
    def build_rebalance_position_transaction(
        self,
        pool_address: str,
        position_id: int,
        receiver: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for rebalancing a V2 position."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_rebalance_position_transaction(
                pool_address=pool_address,
                position_id=position_id,
                receiver=receiver,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build rebalance position transaction: {e}")
            raise
    
    def build_liquidate_position_transaction(
        self,
        pool_address: str,
        position_id: int,
        receiver: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for liquidating a V2 position."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_liquidate_position_transaction(
                pool_address=pool_address,
                position_id=position_id,
                receiver=receiver,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build liquidate position transaction: {e}")
            raise
    
    # Gauge Operations
    def build_gauge_vote_transaction(
        self,
        gauge_address: str,
        weight: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for voting on gauge weight."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_gauge_vote_transaction(
                gauge_address=gauge_address,
                weight=weight,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build gauge vote transaction: {e}")
            raise
    
    def build_gauge_claim_transaction(
        self,
        gauge_address: str,
        token_address: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for claiming gauge rewards."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_gauge_claim_transaction(
                gauge_address=gauge_address,
                token_address=token_address,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build gauge claim transaction: {e}")
            raise
    
    # veFXN Operations
    def build_vefxn_deposit_transaction(
        self,
        amount: str,
        unlock_time: int,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for depositing to veFXN."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_vefxn_deposit_transaction(
                amount=amount,
                unlock_time=unlock_time,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build veFXN deposit transaction: {e}")
            raise
    
    # Additional Minting
    def build_mint_via_treasury_transaction(
        self,
        base_in: str,
        recipient: Optional[str] = None,
        option: int = 0,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for minting via treasury."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_mint_via_treasury_transaction(
                base_in=base_in,
                recipient=recipient,
                option=option,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build mint via treasury transaction: {e}")
            raise
    
    def build_mint_via_gateway_transaction(
        self,
        amount_eth: str,
        min_token_out: str = "0",
        token_type: str = "f",
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for minting via gateway."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_mint_via_gateway_transaction(
                amount_eth=amount_eth,
                min_token_out=min_token_out,
                token_type=token_type,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build mint via gateway transaction: {e}")
            raise
    
    # Redeem Operations
    def build_redeem_transaction(
        self,
        market_address: str,
        f_token_in: str = "0",
        x_token_in: str = "0",
        recipient: Optional[str] = None,
        min_base_out: str = "0",
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for redeeming tokens."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_redeem_transaction(
                market_address=market_address,
                f_token_in=f_token_in,
                x_token_in=x_token_in,
                recipient=recipient,
                min_base_out=min_base_out,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build redeem transaction: {e}")
            raise
    
    def build_redeem_via_treasury_transaction(
        self,
        f_token_in: str = "0",
        x_token_in: str = "0",
        owner: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for redeeming via treasury."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_redeem_via_treasury_transaction(
                f_token_in=f_token_in,
                x_token_in=x_token_in,
                owner=owner,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build redeem via treasury transaction: {e}")
            raise
    
    # Additional V1 Operations
    def build_rebalance_pool_unlock_transaction(
        self,
        pool_address: str,
        amount: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for unlocking rebalance pool assets."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_rebalance_pool_unlock_transaction(
                pool_address=pool_address,
                amount=amount,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build rebalance pool unlock transaction: {e}")
            raise
    
    def build_rebalance_pool_claim_transaction(
        self,
        pool_address: str,
        tokens: List[str],
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for claiming rebalance pool rewards."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_rebalance_pool_claim_transaction(
                pool_address=pool_address,
                tokens=tokens,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build rebalance pool claim transaction: {e}")
            raise
    
    # Additional Advanced Operations
    def build_swap_transaction(
        self,
        token_in: str,
        amount_in: str,
        encoding: int,
        routes: List[int],
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for swapping tokens."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_swap_transaction(
                token_in=token_in,
                amount_in=amount_in,
                encoding=encoding,
                routes=routes,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build swap transaction: {e}")
            raise
    
    def build_flash_loan_transaction(
        self,
        token_address: str,
        amount: str,
        receiver: str,
        data: str = "0x",
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for flash loan."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            # Convert hex string to bytes
            data_bytes = bytes.fromhex(data[2:]) if data.startswith("0x") else bytes.fromhex(data) if data else b""
            
            tx_data = self.client.build_flash_loan_transaction(
                token_address=token_address,
                amount=amount,
                receiver=receiver,
                data=data_bytes,
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build flash loan transaction: {e}")
            raise
    
    def build_harvest_treasury_transaction(
        self,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build unsigned transaction for harvesting treasury rewards."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data = self.client.build_harvest_treasury_transaction(
                from_address=from_address
            )
            return {
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": str(tx_data.get("value", 0)),
                "gas": tx_data["gas"],
                "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                "nonce": tx_data["nonce"],
                "chainId": tx_data["chainId"]
            }
        except Exception as e:
            logger.error(f"Failed to build harvest treasury transaction: {e}")
            raise
    
    def build_claim_all_gauge_rewards_transactions(
        self,
        gauge_addresses: Optional[List[str]] = None,
        from_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Build unsigned transactions for claiming all gauge rewards."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            tx_data_list = self.client.build_claim_all_gauge_rewards_transaction(
                gauge_addresses=gauge_addresses,
                from_address=from_address
            )
            
            # Convert each transaction to API format
            result = []
            for tx_data in tx_data_list:
                result.append({
                    "to": tx_data["to"],
                    "data": tx_data["data"],
                    "value": str(tx_data.get("value", 0)),
                    "gas": tx_data["gas"],
                    "gasPrice": str(tx_data.get("gasPrice", 0)) if tx_data.get("gasPrice") else None,
                    "maxFeePerGas": str(tx_data.get("maxFeePerGas", 0)) if tx_data.get("maxFeePerGas") else None,
                    "maxPriorityFeePerGas": str(tx_data.get("maxPriorityFeePerGas", 0)) if tx_data.get("maxPriorityFeePerGas") else None,
                    "nonce": tx_data["nonce"],
                    "chainId": tx_data["chainId"]
                })
            return result
        except Exception as e:
            logger.error(f"Failed to build claim all gauge rewards transactions: {e}")
            raise
    
    # veFXN methods
    def get_vefxn_locked_info(self, address: str) -> Dict[str, Any]:
        """Get veFXN locked information."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            info = self.client.get_vefxn_locked_info(account_address=address)
            # Convert Decimal values to strings
            return {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in info.items()
            }
        except Exception as e:
            logger.error(f"Failed to get veFXN locked info: {e}")
            raise
    
    # Convex methods
    def get_all_convex_pools(self) -> Dict[int, Dict[str, Any]]:
        """Get all Convex pools."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pools = self.client.get_all_convex_pools()
            # Convert Decimal values to strings
            result = {}
            for pool_id, pool_info in pools.items():
                result[pool_id] = {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in pool_info.items()
                }
            return result
        except Exception as e:
            logger.error(f"Failed to get all Convex pools: {e}")
            raise
    
    def get_convex_pool_info(self, pool_id: int) -> Dict[str, Any]:
        """Get information about a specific Convex pool."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pool_info = self.client.get_convex_pool_info(pool_id=pool_id)
            # Convert Decimal values to strings
            return {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in pool_info.items()
            }
        except Exception as e:
            logger.error(f"Failed to get Convex pool info: {e}")
            raise
    
    def get_user_convex_vaults(self, address: str) -> List[Dict[str, Any]]:
        """Get all Convex vaults for a user address."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            vaults = self.client.get_all_user_vaults(user_address=address)
            # Convert Decimal values to strings
            result = []
            for vault in vaults:
                result.append({
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in vault.items()
                })
            return result
        except Exception as e:
            logger.error(f"Failed to get user Convex vaults: {e}")
            raise
    
    def get_convex_vault_info(self, vault_address: str) -> Dict[str, Any]:
        """Get information about a specific Convex vault."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            vault_info = self.client.get_convex_vault_info(vault_address)
            # Convert Decimal values to strings
            return {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in vault_info.items()
            }
        except Exception as e:
            logger.error(f"Failed to get Convex vault info: {e}")
            raise
    
    def get_convex_vault_balance(self, vault_address: str) -> Dict[str, Any]:
        """Get staked balance for a Convex vault."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            balance = self.client.get_convex_vault_balance(vault_address=vault_address)
            vault_info = self.client.get_convex_vault_info(vault_address)
            
            return {
                "vault_address": vault_address,
                "pool_id": vault_info.get("pid", 0),
                "staked_balance": str(balance),
                "gauge_address": vault_info.get("gaugeAddress"),
                "staked_token": vault_info.get("stakingToken")
            }
        except Exception as e:
            logger.error(f"Failed to get Convex vault balance: {e}")
            raise
    
    def get_convex_vault_rewards(self, vault_address: str) -> Dict[str, Any]:
        """Get claimable rewards for a Convex vault."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            rewards = self.client.get_convex_vault_rewards(vault_address=vault_address)
            vault_info = self.client.get_convex_vault_info(vault_address)
            
            # Convert rewards amounts to strings
            rewards_dict = {
                token: str(amount) if isinstance(amount, Decimal) else amount
                for token, amount in rewards.get("amounts", {}).items()
            }
            
            return {
                "vault_address": vault_address,
                "pool_id": vault_info.get("pid", 0),
                "rewards": rewards_dict,
                "reward_tokens": list(rewards_dict.keys())
            }
        except Exception as e:
            logger.error(f"Failed to get Convex vault rewards: {e}")
            raise
    
    # Curve methods
    def get_curve_pools(self) -> List[Dict[str, Any]]:
        """Get all Curve pools from the registry."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pools = self.client.get_curve_pools_from_registry()
            # Convert Decimal values to strings
            result = []
            for pool_address, pool_info in pools.items():
                result.append({
                    "pool_address": pool_address,
                    **{
                        k: str(v) if isinstance(v, Decimal) else v
                        for k, v in pool_info.items()
                    }
                })
            return result
        except Exception as e:
            logger.error(f"Failed to get Curve pools: {e}")
            raise
    
    def get_curve_pool_info(self, pool_address: str) -> Dict[str, Any]:
        """Get information about a specific Curve pool."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            pool_info = self.client.get_curve_pool_info(pool_address)
            # Convert Decimal values to strings
            result = {
                "pool_address": pool_address,
                **{
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in pool_info.items()
                }
            }
            
            # Get gauge address if available
            try:
                gauge_address = self.client.get_curve_gauge_from_pool(pool_address)
                if gauge_address:
                    result["gauge_address"] = gauge_address
            except Exception:
                pass
            
            return result
        except Exception as e:
            logger.error(f"Failed to get Curve pool info: {e}")
            raise
    
    def get_curve_gauge_balance(self, gauge_address: str, user_address: str) -> Dict[str, Any]:
        """Get staked balance for a Curve gauge."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            balance = self.client.get_curve_gauge_balance(gauge_address, user_address=user_address)
            gauge_info = self.client.get_curve_gauge_info(gauge_address)
            
            return {
                "gauge_address": gauge_address,
                "user_address": user_address,
                "staked_balance": str(balance),
                "lp_token": gauge_info.get("lp_token")
            }
        except Exception as e:
            logger.error(f"Failed to get Curve gauge balance: {e}")
            raise
    
    def get_curve_gauge_rewards(self, gauge_address: str, user_address: str) -> Dict[str, Any]:
        """Get claimable rewards for a Curve gauge."""
        if not self.client:
            raise FXProtocolError("SDK client not initialized")
        
        try:
            rewards = self.client.get_curve_gauge_rewards(
                gauge_address=gauge_address,
                user_address=user_address
            )
            
            # Convert rewards amounts to strings
            rewards_dict = {
                token: str(amount) if isinstance(amount, Decimal) else amount
                for token, amount in rewards.get("amounts", {}).items()
            }
            
            return {
                "gauge_address": gauge_address,
                "user_address": user_address,
                "rewards": rewards_dict,
                "reward_tokens": list(rewards_dict.keys())
            }
        except Exception as e:
            logger.error(f"Failed to get Curve gauge rewards: {e}")
            raise

