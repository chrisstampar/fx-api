"""
Main FastAPI application.

This is the entry point for the f(x) Protocol REST API.
"""

import logging
import time
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from mangum import Mangum

from app.config import settings
from app.utils.logging_config import setup_logging, log_request, log_response, log_error
from app.routes import health, balances, protocol, convex, curve, v2, gauges, vefxn, transactions
from app.middleware.rate_limit import limiter, rate_limit_handler
from app.middleware.swagger_css import SwaggerCSSMiddleware
from slowapi.errors import RateLimitExceeded
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    fx_protocol_error_handler,
    general_exception_handler
)
from fx_sdk.exceptions import FXProtocolError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

# Configure structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files for custom CSS (if directory exists)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Custom Swagger UI configuration for better readability
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom Swagger UI config
    openapi_schema["x-swagger-ui-config"] = {
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    }
    
    # Inject custom CSS
    if os.path.exists(static_dir):
        openapi_schema["x-custom-css"] = "/static/custom-swagger.css"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Note: Swagger CSS is now injected via custom /docs endpoint above
# app.add_middleware(SwaggerCSSMiddleware)  # Not needed with custom endpoint

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(FXProtocolError, fx_protocol_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Override Swagger UI HTML to inject custom CSS
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with improved readability CSS."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        init_oauth=app.swagger_ui_init_oauth,
    ).body.decode("utf-8").replace(
        "</head>",
        """
        <style>
        /* Custom Swagger UI Styles for Better Readability */
        .swagger-ui .info .title { color: #1f2937 !important; font-size: 36px !important; font-weight: 700 !important; }
        .swagger-ui .info .description { color: #374151 !important; font-size: 14px !important; line-height: 1.6 !important; }
        .swagger-ui .opblock-body pre { background-color: #f7f7f7 !important; border: 1px solid #e0e0e0 !important; color: #1f2937 !important; font-size: 13px !important; line-height: 1.6 !important; }
        .swagger-ui .opblock-body pre code { color: #1f2937 !important; background: transparent !important; }
        .swagger-ui .parameter__name { color: #1f2937 !important; font-weight: 600 !important; }
        .swagger-ui .parameter__type { color: #3b82f6 !important; font-weight: 500 !important; }
        .swagger-ui .parameter__description { color: #4b5563 !important; line-height: 1.6 !important; }
        .swagger-ui table thead tr th { background-color: #f9fafb !important; color: #1f2937 !important; font-weight: 600 !important; }
        .swagger-ui table tbody tr td { color: #374151 !important; border-color: #e5e7eb !important; }
        .swagger-ui .response-col_status { font-weight: 600 !important; }
        .swagger-ui .btn.execute { background-color: #3b82f6 !important; color: white !important; font-weight: 600 !important; }
        .swagger-ui .btn.execute:hover { background-color: #2563eb !important; }
        .swagger-ui .model-box { background-color: #f9fafb !important; border: 1px solid #e5e7eb !important; }
        .swagger-ui .model-title { color: #1f2937 !important; font-weight: 600 !important; }
        .swagger-ui .property-name { color: #1f2937 !important; font-weight: 600 !important; }
        .swagger-ui .property-type { color: #3b82f6 !important; }
        .swagger-ui { color: #374151 !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; }
        .swagger-ui p { color: #4b5563 !important; line-height: 1.6 !important; }
        .swagger-ui .parameter__required { color: #dc2626 !important; font-weight: 600 !important; }
        .swagger-ui input[type="text"], .swagger-ui input[type="password"], .swagger-ui textarea { border: 1px solid #d1d5db !important; color: #1f2937 !important; background-color: white !important; }
        .swagger-ui input[type="text"]:focus, .swagger-ui input[type="password"]:focus, .swagger-ui textarea:focus { border-color: #3b82f6 !important; outline: 2px solid rgba(59, 130, 246, 0.2) !important; }
        </style>
        </head>
    """
    )

# Include routers
app.include_router(health.router, prefix=f"/{settings.API_VERSION}", tags=["health"])
app.include_router(balances.router, prefix=f"/{settings.API_VERSION}/balances", tags=["balances"])
app.include_router(protocol.router, prefix=f"/{settings.API_VERSION}/protocol", tags=["protocol"])
app.include_router(convex.router, prefix=f"/{settings.API_VERSION}/convex", tags=["convex"])
app.include_router(curve.router, prefix=f"/{settings.API_VERSION}/curve", tags=["curve"])
app.include_router(v2.router, prefix=f"/{settings.API_VERSION}/v2", tags=["v2"])
app.include_router(gauges.router, prefix=f"/{settings.API_VERSION}/gauges", tags=["gauges"])
app.include_router(vefxn.router, prefix=f"/{settings.API_VERSION}/vefxn", tags=["vefxn"])
app.include_router(transactions.router, prefix=f"/{settings.API_VERSION}/transactions", tags=["transactions"])

# Convenience endpoints without version prefix
@app.get("/health", tags=["health"], include_in_schema=False)
async def health_check_root():
    """Health check endpoint (convenience route without version prefix)."""
    from app.models.responses import HealthResponse
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "f(x) Protocol API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": f"/{settings.API_VERSION}/health"
    }


@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    """Add process time and request ID headers to responses, and log requests."""
    import uuid
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params) if request.query_params else None
    )
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Log response
        log_response(
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=process_time
        )
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time / 1000)  # Keep in seconds for header
        response.headers["X-Request-ID"] = request_id
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        log_error(
            request_id=request_id,
            error=e,
            duration_ms=process_time
        )
        raise


# Add rate limit headers middleware
from app.middleware.rate_limit import add_rate_limit_headers
app.middleware("http")(add_rate_limit_headers)


# Vercel requires this for serverless functions
# Use Mangum to wrap FastAPI for Vercel/Lambda compatibility
handler = Mangum(app, lifespan="off")

