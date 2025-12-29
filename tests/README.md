# API Test Suite

Comprehensive test suite for the f(x) Protocol REST API.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_health.py           # Health check endpoint tests
├── test_balances.py         # Balance endpoint tests
├── test_protocol.py         # Protocol information tests
├── test_validation.py       # Input validation tests
├── test_caching.py          # Caching functionality tests
├── test_pagination.py       # Pagination tests
├── test_transactions.py     # Transaction endpoint tests
├── test_error_handling.py   # Error handling tests
└── test_rate_limiting.py    # Rate limiting tests
```

## Running Tests

### Prerequisites

**Important**: The test suite requires `httpx>=0.25.0`. If you have dependency conflicts (e.g., with `spleeter`), use a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

See `../SETUP_TESTING.md` for detailed setup instructions.

### Quick Test (Standalone Script)

**Note:** The standalone `tests.py` script is deprecated. Use pytest instead:

```bash
cd api
python3 -m pytest tests/ -v
```

### Full Pytest Suite

**Important**: Always run tests from the `api/` directory, not from within `tests/`:

```bash
# From the api/ directory
cd api

# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio httpx>=0.25.0

# Run all tests
python3 -m pytest tests/ -v
# OR
pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_health.py -v

# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=html

# Run specific test
python3 -m pytest tests/test_balances.py::test_get_all_balances -v
```

**Note**: If you try to run test files directly (e.g., `python3 tests/test_caching.py`), you'll get a `ModuleNotFoundError` because Python can't find the `app` module. Always use `pytest` or `python3 -m pytest` from the `api/` directory.

## Test Coverage

### Health Endpoints
- ✅ Basic health check
- ✅ Status endpoint
- ✅ Detailed health check
- ✅ Metrics endpoint

### Balance Endpoints
- ✅ Get all balances
- ✅ Get specific token balances
- ✅ Batch balance queries
- ✅ Invalid address handling

### Protocol Endpoints
- ✅ Protocol NAV
- ✅ Token NAV
- ✅ Batch NAV queries
- ✅ stETH price
- ✅ fxUSD supply

### Validation
- ✅ Ethereum address validation
- ✅ Amount validation
- ✅ Hex string validation
- ✅ Error message format

### Caching
- ✅ Cache set/get operations
- ✅ Cache expiration
- ✅ Cache statistics
- ✅ Response caching

### Pagination
- ✅ Convex pools pagination
- ✅ Curve pools pagination
- ✅ Invalid pagination parameters

### Transactions
- ✅ Prepare transaction endpoints
- ✅ Gas estimation
- ✅ Transaction status tracking
- ✅ Invalid transaction handling

### Error Handling
- ✅ 404 errors
- ✅ Validation errors
- ✅ Error response structure
- ✅ Helpful error messages

### Response Headers
- ✅ Request ID
- ✅ Process time
- ✅ Rate limit headers

## Test Fixtures

The `conftest.py` file provides:
- `client`: FastAPI test client
- `mock_rpc_url`: Mock RPC URL
- `sample_address`: Sample Ethereum address
- `sample_invalid_address`: Invalid address for testing
- `mock_sdk_client`: Mock SDK client

## Notes

- Tests use the actual FastAPI app but may require RPC connectivity
- Some tests may fail if RPC endpoints are unavailable
- Transaction tests may fail if contracts are not accessible
- Caching tests verify functionality but timing may vary

## Continuous Integration

To run tests in CI/CD:

```bash
pytest tests/ -v --tb=short
```

