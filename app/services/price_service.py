"""
Price service for calculating USD values of tokens.

Uses NAV values from the protocol for f-tokens and x-tokens,
and external price APIs for other tokens.
"""

import logging
from decimal import Decimal
from typing import Dict, Optional, Any
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


class PriceService:
    """Service for fetching token prices and calculating USD values."""
    
    # Stablecoins that should be ~$1
    STABLECOINS = {"fxusd", "rusd", "arusd", "btcusd", "cvxusd", "fxsave", "fxsp"}
    
    # Tokens that use NAV pricing (f-tokens and x-tokens)
    NAV_TOKENS = {"feth", "xeth", "xcvx", "xwbtc", "xeeth", "xezeth", "xsteth", "xfrxeth"}
    
    def __init__(self, sdk_client):
        """
        Initialize price service.
        
        Args:
            sdk_client: ProtocolClient instance for NAV queries
        """
        self.sdk_client = sdk_client
        self._price_cache: Dict[str, Decimal] = {}
    
    def clear_cache(self):
        """Clear the price cache (useful for ensuring fresh NAV values)."""
        self._price_cache.clear()
    
    def get_token_price(self, token_name: str) -> Optional[Decimal]:
        """
        Get USD price for a token.
        
        Args:
            token_name: Token name (e.g., 'fxusd', 'fxn', 'feth')
            
        Returns:
            Price in USD, or None if unavailable
        """
        token_lower = token_name.lower()
        
        # Check cache first
        if token_lower in self._price_cache:
            return self._price_cache[token_lower]
        
        price = None
        
        try:
            # Stablecoins are ~$1
            if token_lower in self.STABLECOINS:
                price = Decimal("1.0")
            
            # f-tokens use f_nav
            elif token_lower == "feth":
                try:
                    nav = self.sdk_client.get_treasury_nav()
                    price = nav.get("f_nav", Decimal("0"))
                except Exception:
                    price = None
            
            # x-tokens use x_nav (except xCVX which uses CVX price)
            elif token_lower in ["xeth", "xwbtc", "xeeth", "xezeth", "xsteth", "xfrxeth"]:
                try:
                    nav = self.sdk_client.get_treasury_nav()
                    price = nav.get("x_nav", Decimal("0"))
                except Exception:
                    price = None
            
            # xCVX uses CVX price (not x_nav)
            elif token_lower == "xcvx":
                price = self._fetch_coingecko_price("cvx")
            
            # For other tokens (FXN, veFXN, cvxFXN), try to fetch from CoinGecko
            elif token_lower in ["fxn", "vefxn", "cvxfxn"]:
                price = self._fetch_coingecko_price(token_lower)
            
            # Cache the price
            if price is not None:
                self._price_cache[token_lower] = price
            
        except Exception as e:
            logger.warning(f"Failed to get price for {token_name}: {e}")
        
        return price
    
    def _fetch_coingecko_price(self, token_name: str) -> Optional[Decimal]:
        """
        Fetch token price from CoinGecko API.
        
        Args:
            token_name: Token name
            
        Returns:
            Price in USD, or None if unavailable
        """
        # CoinGecko token IDs
        coingecko_ids = {
            "fxn": "function-x",
            "vefxn": "function-x",  # veFXN typically trades at a discount to FXN
            "cvxfxn": "convex-finance",  # cvxFXN is a Convex token, approximate
            "cvx": "convex-finance",  # CVX token for xCVX pricing
        }
        
        token_id = coingecko_ids.get(token_name.lower())
        if not token_id:
            return None
        
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available, cannot fetch CoinGecko prices")
            return None
        
        try:
            # Use CoinGecko simple price API
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": token_id,
                "vs_currencies": "usd"
            }
            
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if token_id in data and "usd" in data[token_id]:
                    price = Decimal(str(data[token_id]["usd"]))
                    # For veFXN, apply a discount (typically 0.7-0.9x FXN price)
                    if token_name.lower() == "vefxn":
                        price = price * Decimal("0.8")  # Approximate discount
                    return price
        except Exception as e:
            logger.warning(f"Failed to fetch CoinGecko price for {token_name}: {e}")
        
        return None
    
    def calculate_total_usd_value(self, balances: Dict[str, str]) -> Decimal:
        """
        Calculate total USD value of all balances.
        
        Args:
            balances: Dictionary mapping token names to balances (as strings)
            
        Returns:
            Total USD value
        """
        total = Decimal("0")
        
        for token_name, balance_str in balances.items():
            try:
                balance = Decimal(balance_str)
                if balance == 0:
                    continue
                
                price = self.get_token_price(token_name)
                if price is not None:
                    total += balance * price
            except Exception as e:
                logger.warning(f"Failed to calculate value for {token_name}: {e}")
                continue
        
        return total

