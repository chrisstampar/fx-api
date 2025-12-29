"""
Dependency injection for FastAPI routes.

Provides shared dependencies like SDK service instances.
"""

from typing import Optional
from app.services.sdk_service import SDKService
from app.config import settings


# Global SDK service instance (singleton)
_sdk_service: Optional[SDKService] = None


def get_sdk_service() -> SDKService:
    """
    Get or create the SDK service instance.
    
    This ensures we reuse the same SDK client across requests,
    which is more efficient for RPC connections.
    """
    global _sdk_service
    
    if _sdk_service is None:
        try:
            # Use first RPC URL as primary, others as fallbacks
            primary_rpc = settings.rpc_urls_list[0] if settings.rpc_urls_list else "https://eth.llamarpc.com"
            _sdk_service = SDKService(rpc_url=primary_rpc, rpc_urls=settings.rpc_urls_list)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize SDK service: {e}", exc_info=True)
            raise
    
    return _sdk_service

