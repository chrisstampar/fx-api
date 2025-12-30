# f(x) Protocol REST API

RESTful API wrapper around the fx-sdk package.

## Quick Start

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

## API Endpoints

### Health
- `GET /v1/health` - Health check
- `GET /v1/status` - API status

### Balances
- `GET /v1/balances/{address}` - Get all balances
- `GET /v1/balances/{address}/fxusd` - Get fxUSD balance
- `GET /v1/balances/{address}/fxn` - Get FXN balance
- More token endpoints coming...

### Protocol
- `GET /v1/protocol/nav` - Get protocol NAV

## Rate Limiting

- **Free tier for all users:**
  - 100 requests/minute per IP
  - 5,000 requests/hour per IP
  - 50,000 requests/day per IP

## Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Environment Variables

See `.env.example` for all available configuration options.

## Project Structure

```
api/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── dependencies.py     # Dependency injection
│   ├── routes/             # API endpoints
│   ├── models/             # Pydantic models
│   ├── services/           # Business logic
│   └── middleware/         # Custom middleware
├── tests/                  # Tests
├── requirements.txt        # Dependencies
└── README.md              # This file
```
