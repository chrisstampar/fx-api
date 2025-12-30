# f(x) Protocol REST API - Complete Documentation

**Version:** 1.0.0  
**Last Updated:** December 29, 2025  
**Framework:** FastAPI (Python)  
**Production API:** https://fx-api-production.up.railway.app

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
4. [Authentication & Security](#authentication--security)
5. [Rate Limiting](#rate-limiting)
6. [Error Handling](#error-handling)
7. [Performance Features](#performance-features)
8. [Transaction Flow](#transaction-flow)
9. [Examples](#examples)
10. [Deployment](#deployment)

---

## Overview

The f(x) Protocol REST API provides a comprehensive HTTP interface for interacting with the f(x) Protocol ecosystem. Built on FastAPI, it offers:

- **RESTful Design**: Clean, intuitive endpoint structure
- **Type Safety**: Pydantic models for request/response validation
- **Security First**: No private key handling - client-side signing required
- **High Performance**: Response caching and batch operations
- **Developer Friendly**: Auto-generated OpenAPI docs, helpful error messages

### Key Features

- ✅ Complete read operations (balances, protocol info, Convex, Curve)
- ✅ Transaction preparation endpoints (unsigned transactions)
- ✅ Transaction broadcasting and tracking
- ✅ Response caching (30s for balances, 5min for protocol info)
- ✅ Batch operations for multiple addresses
- ✅ RPC fallback for reliability
- ✅ Enhanced error messages with context
- ✅ Gas estimation support
- ✅ Comprehensive health checks and metrics

---

## Quick Start

### Production API

**Live API:** https://fx-api-production.up.railway.app

- **API Documentation:** https://fx-api-production.up.railway.app/docs
- **Health Check:** https://fx-api-production.up.railway.app/v1/health

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the API:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/v1/health

---

## API Endpoints

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/health` | GET | Basic health check |
| `/v1/status` | GET | Detailed API status with RPC connectivity |
| `/v1/health/detailed` | GET | Comprehensive health check with component status |
| `/v1/metrics` | GET | API metrics and statistics |

### Balances

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/balances/{address}` | GET | Get all token balances for an address |
| `/v1/balances/batch` | POST | Get balances for multiple addresses |
| `/v1/balances/{address}/fxusd` | GET | Get fxUSD balance |
| `/v1/balances/{address}/fxn` | GET | Get FXN balance |
| `/v1/balances/{address}/feth` | GET | Get fETH balance |
| `/v1/balances/{address}/xeth` | GET | Get xETH balance |
| `/v1/balances/{address}/xcvx` | GET | Get xCVX balance |
| `/v1/balances/{address}/xwbtc` | GET | Get xWBTC balance |
| `/v1/balances/{address}/xeeth` | GET | Get xeETH balance |
| `/v1/balances/{address}/xezeth` | GET | Get xezETH balance |
| `/v1/balances/{address}/xsteth` | GET | Get xstETH balance |
| `/v1/balances/{address}/xfrxeth` | GET | Get xfrxETH balance |
| `/v1/balances/{address}/vefxn` | GET | Get veFXN balance |
| `/v1/balances/{address}/fxsave` | GET | Get fxSAVE balance |
| `/v1/balances/{address}/fxsp` | GET | Get fxSP balance |
| `/v1/balances/{address}/rusd` | GET | Get rUSD balance |
| `/v1/balances/{address}/arusd` | GET | Get arUSD balance |
| `/v1/balances/{address}/btcusd` | GET | Get btcUSD balance |
| `/v1/balances/{address}/cvxusd` | GET | Get cvxUSD balance |
| `/v1/balances/{address}/token/{token_address}` | GET | Get balance for any ERC-20 token |

### Protocol Information

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/protocol/nav` | GET | Get protocol NAV (fETH/xETH) |
| `/v1/protocol/nav/batch` | POST | Get NAV for multiple tokens |
| `/v1/protocol/nav/{token}` | GET | Get NAV for specific token |
| `/v1/protocol/pool-info/{pool_address}` | GET | Get V2 pool manager info |
| `/v1/protocol/market-info/{market_address}` | GET | Get V1 market info |
| `/v1/protocol/treasury-info` | GET | Get stETH treasury info |
| `/v1/protocol/steth-price` | GET | Get stETH price |
| `/v1/protocol/fxusd/supply` | GET | Get fxUSD total supply |
| `/v1/protocol/v1/nav` | GET | Get V1 NAV |
| `/v1/protocol/v1/collateral-ratio` | GET | Get V1 collateral ratio |
| `/v1/protocol/v1/rebalance-pools` | GET | Get all V1 rebalance pools |
| `/v1/protocol/v1/rebalance-pool/{pool_address}/balances/{address}` | GET | Get rebalance pool balances |
| `/v1/protocol/peg-keeper` | GET | Get peg keeper info |

### V2 Protocol

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/v2/pool/{pool_address}/info` | GET | Get V2 pool info |
| `/v1/v2/position/{position_id}/info` | GET | Get V2 position info |
| `/v1/v2/pool-manager/{pool_address}/info` | GET | Get pool manager info |
| `/v1/v2/reserve-pool/{token_address}/bonus-ratio` | GET | Get reserve pool bonus ratio |

### Convex Finance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/convex/pools` | GET | List all Convex pools (paginated) |
| `/v1/convex/pool/{pool_id}/info` | GET | Get Convex pool info |
| `/v1/convex/vault/{vault_address}/info` | GET | Get Convex vault info |
| `/v1/convex/vault/{vault_address}/balance` | GET | Get vault staked balance |
| `/v1/convex/vault/{vault_address}/rewards` | GET | Get claimable rewards |
| `/v1/convex/user/{address}/vaults` | GET | Get user's Convex vaults |

### Curve Finance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/curve/pools` | GET | List all Curve pools (paginated) |
| `/v1/curve/pool/{pool_address}/info` | GET | Get Curve pool info |
| `/v1/curve/gauge/{gauge_address}/balance` | GET | Get gauge staked balance |
| `/v1/curve/gauge/{gauge_address}/rewards` | GET | Get claimable rewards |

### Gauges & Governance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/gauges/{address}/all` | GET | Get all gauge balances for address |
| `/v1/gauges/{gauge_address}/weight` | GET | Get gauge weight |
| `/v1/gauges/{gauge_address}/relative-weight` | GET | Get gauge relative weight |
| `/v1/gauges/{gauge_address}/rewards/{address}` | GET | Get claimable rewards |

### veFXN

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/vefxn/{address}/info` | GET | Get veFXN locked info |

### Transactions

#### Broadcast

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/transactions/broadcast` | POST | Broadcast a signed transaction |
| `/v1/transactions/{tx_hash}/status` | GET | Get transaction status |

#### Prepare (Unsigned Transactions)

All prepare endpoints return unsigned transaction data that must be signed client-side.

**Minting:**
- `/v1/transactions/mint/f-token/prepare` - Mint f-token
- `/v1/transactions/mint/x-token/prepare` - Mint x-token
- `/v1/transactions/mint/both/prepare` - Mint both tokens
- `/v1/transactions/mint/treasury/prepare` - Mint via treasury
- `/v1/transactions/mint/f-token/gateway/prepare` - Mint f-token via gateway
- `/v1/transactions/mint/x-token/gateway/prepare` - Mint x-token via gateway

**Redemption:**
- `/v1/transactions/redeem/prepare` - Redeem tokens
- `/v1/transactions/redeem/treasury/prepare` - Redeem via treasury

**V1 Operations:**
- `/v1/transactions/v1/rebalance-pool/{pool_address}/deposit/prepare` - Deposit to rebalance pool
- `/v1/transactions/v1/rebalance-pool/{pool_address}/unlock/prepare` - Unlock from rebalance pool
- `/v1/transactions/v1/rebalance-pool/{pool_address}/withdraw/prepare` - Withdraw from rebalance pool
- `/v1/transactions/v1/rebalance-pool/{pool_address}/claim/prepare` - Claim from rebalance pool

**Savings & Stability Pool:**
- `/v1/transactions/savings/deposit/prepare` - Deposit to savings
- `/v1/transactions/savings/redeem/prepare` - Redeem from savings
- `/v1/transactions/stability-pool/deposit/prepare` - Deposit to stability pool
- `/v1/transactions/stability-pool/withdraw/prepare` - Withdraw from stability pool

**Vesting:**
- `/v1/transactions/vesting/{token_type}/claim/prepare` - Claim vesting (fxn, feth, fxusd)

**Advanced Operations:**
- `/v1/transactions/pool-manager/{pool_address}/harvest/prepare` - Harvest pool manager
- `/v1/transactions/reserve-pool/request-bonus/prepare` - Request bonus from reserve pool
- `/v1/transactions/swap/prepare` - Execute swap
- `/v1/transactions/flash-loan/prepare` - Execute flash loan
- `/v1/transactions/treasury/harvest/prepare` - Harvest treasury

**V2 Position Operations:**
- `/v1/transactions/positions/{position_id}/operate/prepare` - Operate position
- `/v1/transactions/positions/{position_id}/rebalance/prepare` - Rebalance position
- `/v1/transactions/positions/{position_id}/liquidate/prepare` - Liquidate position

**Gauge Operations:**
- `/v1/transactions/gauges/{gauge_address}/vote/prepare` - Vote on gauge
- `/v1/transactions/gauges/{gauge_address}/claim/prepare` - Claim gauge rewards
- `/v1/transactions/gauges/claim-all/prepare` - Claim all gauge rewards

**veFXN:**
- `/v1/transactions/vefxn/deposit/prepare` - Deposit FXN to veFXN

**Token Operations:**
- `/v1/transactions/approve/prepare` - Approve token spending
- `/v1/transactions/transfer/prepare` - Transfer tokens

---

## Authentication & Security

### Client-Side Signing

The API **never handles private keys**. All transactions follow this secure flow:

1. **Client Builds Transaction**: Using SDK or web3 library
2. **Client Signs Offline**: Private key never leaves client device
3. **API Broadcasts**: API only receives and broadcasts signed transaction
4. **Transaction Tracking**: Status can be queried after broadcast

### Input Validation

- **Pydantic Models**: Type-safe request/response validation
- **Address Validation**: Ethereum address format checking (EIP-55 checksum)
- **Amount Validation**: Non-negative, properly formatted amounts
- **Clear Error Messages**: Helpful validation error responses

---

## Rate Limiting

### Free Tier (All Users)

- **Per Minute**: 100 requests
- **Per Hour**: 5,000 requests
- **Per Day**: 50,000 requests

### Rate Limit Headers

All responses include rate limit information:
- `X-RateLimit-Limit-Minute`
- `X-RateLimit-Limit-Hour`
- `X-RateLimit-Limit-Day`
- `X-RateLimit-Remaining-*`
- `Retry-After` (when limit exceeded)

### Rate Limit Exceeded

When rate limit is exceeded, you'll receive:
- HTTP 429 status code
- Error message with retry time
- `Retry-After` header with seconds to wait

---

## Error Handling

### Error Response Format

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable error message"
}
```

### Common Error Codes

- `INVALID_ADDRESS` - Invalid Ethereum address format
- `INVALID_AMOUNT` - Invalid amount format or value
- `CONTRACT_CALL_ERROR` - Error calling smart contract
- `TRANSACTION_FAILED` - Transaction failed on blockchain
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded
- `INTERNAL_ERROR` - Server-side error

### Enhanced Error Messages

Error messages include:
- **Helpful Context**: Suggestions and context
- **Documentation Links**: Direct links to relevant docs
- **Validation Details**: Detailed validation error messages
- **Error Codes**: Consistent error codes for programmatic handling

---

## Performance Features

### Response Caching

- **In-Memory Caching**: Fast, efficient caching for read operations
- **TTL-Based Expiration**: 
  - Balances: 30 seconds
  - Protocol info: 5 minutes
- **Automatic Cache Management**: Expired entries are automatically cleaned up
- **Cache Statistics**: Track cache hits/misses via metrics endpoint

### Batch Operations

- **Batch Balances**: Query multiple addresses in one request (`POST /v1/balances/batch`)
- **Batch NAV**: Query multiple token NAVs in one request (`POST /v1/protocol/nav/batch`)
- **Parallel Processing**: Batch requests are processed concurrently
- **Reduced HTTP Overhead**: Fewer round trips for multiple queries

### RPC Fallback

- **Multiple RPC Endpoints**: Automatic fallback to backup RPCs
- **Health Monitoring**: RPC connectivity is continuously monitored
- **Graceful Degradation**: API continues operating even if some RPCs fail

### Gas Estimation

- **Optional Gas Estimation**: Request gas estimates for prepare endpoints
- **Cost Calculation**: Estimated total gas cost in Wei
- **Query Parameter**: Add `?estimate_gas=true&from_address=...` to any prepare endpoint

---

## Transaction Flow

### Complete Transaction Flow

1. **Prepare Transaction**: Call prepare endpoint to get unsigned transaction data
2. **Sign Locally**: Sign transaction using your private key (never send to API)
3. **Broadcast**: Send signed transaction to `/v1/transactions/broadcast`
4. **Track Status**: Query `/v1/transactions/{tx_hash}/status` for confirmation

### Example Flow

```python
# 1. Prepare transaction
response = requests.post(
    "https://fx-api-production.up.railway.app/v1/transactions/mint/f-token/prepare",
    json={
        "market_address": "0x...",
        "base_in": "1000000000000000000",
        "wallet_address": "0x..."
    }
)
unsigned_tx = response.json()["transaction"]

# 2. Sign locally (using web3.py, ethers.js, etc.)
signed_tx = sign_transaction(unsigned_tx, private_key)

# 3. Broadcast
broadcast_response = requests.post(
    "https://fx-api-production.up.railway.app/v1/transactions/broadcast",
    json={"signed_transaction": signed_tx}
)
tx_hash = broadcast_response.json()["transaction_hash"]

# 4. Track status
status_response = requests.get(
    f"https://fx-api-production.up.railway.app/v1/transactions/{tx_hash}/status"
)
status = status_response.json()["status"]
```

---

## Examples

### Get All Balances

```bash
curl https://fx-api-production.up.railway.app/v1/balances/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

### Get Protocol NAV

```bash
curl https://fx-api-production.up.railway.app/v1/protocol/nav
```

### Batch Query Balances

```bash
curl -X POST https://fx-api-production.up.railway.app/v1/balances/batch \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "0x1234567890123456789012345678901234567890"
    ]
  }'
```

### Prepare Mint Transaction

```bash
curl -X POST https://fx-api-production.up.railway.app/v1/transactions/mint/f-token/prepare \
  -H "Content-Type: application/json" \
  -d '{
    "market_address": "0x...",
    "base_in": "1000000000000000000",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
  }'
```

### Broadcast Signed Transaction

```bash
curl -X POST https://fx-api-production.up.railway.app/v1/transactions/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "signed_transaction": "0x..."
  }'
```

### Get Transaction Status

```bash
curl https://fx-api-production.up.railway.app/v1/transactions/0x.../status
```

---

## Deployment

### Railway Deployment

The production API is deployed on Railway. See `RAILWAY_DEPLOYMENT.md` for details.

### Environment Variables

Key environment variables:
- `RPC_URLS` - Comma-separated list of RPC endpoints
- `RATE_LIMIT_PER_MINUTE` - Rate limit per minute (default: 100)
- `RATE_LIMIT_PER_HOUR` - Rate limit per hour (default: 5000)
- `RATE_LIMIT_PER_DAY` - Rate limit per day (default: 50000)
- `ALLOWED_ORIGINS` - CORS allowed origins (default: "*")

See `.env.example` for all available configuration options.

---

## Documentation

### Interactive Documentation

- **Swagger UI**: `/docs` - Full interactive API explorer
- **ReDoc**: `/redoc` - Alternative documentation format
- **OpenAPI JSON**: `/openapi.json` - Machine-readable schema

### Response Headers

All responses include:
- `X-Request-ID` - Unique identifier for each request
- `X-Process-Time` - Request processing time in seconds
- `X-RateLimit-*` - Rate limit information

---

## Support

For issues, questions, or contributions:
- **GitHub**: https://github.com/chrisstampar/fx-api
- **API Health**: https://fx-api-production.up.railway.app/v1/health
- **Interactive Docs**: https://fx-api-production.up.railway.app/docs

**Note**: This API is designed to be free for all users with no paid tiers. Rate limits are generous and should accommodate most use cases.

