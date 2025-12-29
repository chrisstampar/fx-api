"""
Configuration management for the API.

Loads settings from environment variables with sensible defaults.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_ENV: str = "development"
    API_VERSION: str = "v1"
    API_TITLE: str = "f(x) Protocol API"
    API_DESCRIPTION: str = "REST API for f(x) Protocol interactions"
    
    # RPC Configuration
    RPC_URLS: str = "https://eth.llamarpc.com,https://rpc.ankr.com/eth,https://ethereum.publicnode.com"
    RPC_TIMEOUT: int = 30
    
    # Rate Limiting (Free tier for all users)
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 5000
    RATE_LIMIT_PER_DAY: int = 50000
    
    # Redis (Optional - for caching and persistent rate limiting)
    REDIS_URL: Optional[str] = None
    REDIS_TTL: int = 300  # Cache TTL in seconds
    
    # CORS
    ALLOWED_ORIGINS: str = "*"  # Comma-separated list, or "*" for all
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def rpc_urls_list(self) -> List[str]:
        """Get RPC URLs as a list."""
        return [url.strip() for url in self.RPC_URLS.split(",") if url.strip()]
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


# Global settings instance
settings = Settings()

