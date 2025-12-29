"""
Pytest configuration and fixtures for API tests.
"""

# IMPORTANT: Patch httpx BEFORE importing TestClient
import httpx

# Patch Client.__init__ to remove follow_redirects for older httpx versions
_original_client_init = httpx.Client.__init__

def _patched_client_init(self, *args, **kwargs):
    """Patch httpx.Client to remove follow_redirects for older versions."""
    kwargs.pop('follow_redirects', None)
    return _original_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_client_init

# Patch request method
_original_request = httpx.Client.request

def _patched_request(self, *args, **kwargs):
    """Patch httpx.Client.request to remove unsupported kwargs for older versions."""
    kwargs.pop('follow_redirects', None)
    kwargs.pop('allow_redirects', None)  # Older httpx uses this instead
    kwargs.pop('extensions', None)
    kwargs.pop('content', None)  # Some versions don't support this in options()
    return _original_request(self, *args, **kwargs)

httpx.Client.request = _patched_request

# Patch convenience methods (get, post, etc.)
for method_name in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
    original_method = getattr(httpx.Client, method_name)
    def make_patched(orig):
        def patched(self, *args, **kwargs):
            kwargs.pop('follow_redirects', None)
            kwargs.pop('allow_redirects', None)
            kwargs.pop('extensions', None)
            kwargs.pop('content', None)
            return orig(self, *args, **kwargs)
        return patched
    setattr(httpx.Client, method_name, make_patched(original_method))

# Now import TestClient after patching httpx
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_rpc_url():
    """Mock RPC URL for testing."""
    return "https://eth.llamarpc.com"


@pytest.fixture
def sample_address():
    """Sample Ethereum address for testing."""
    return "0x1234567890123456789012345678901234567890"


@pytest.fixture
def sample_invalid_address():
    """Sample invalid address for testing."""
    return "invalid_address"


@pytest.fixture
def mock_sdk_client():
    """Mock SDK client for testing."""
    mock_client = Mock()
    mock_client.w3 = Mock()
    mock_client.w3.is_connected = Mock(return_value=True)
    mock_client.w3.eth = Mock()
    mock_client.w3.eth.block_number = 19000000
    return mock_client

