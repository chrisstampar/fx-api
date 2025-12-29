"""
Error handling middleware.

Converts SDK exceptions to appropriate HTTP responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from fx_sdk.exceptions import (
    FXProtocolError,
    ContractCallError,
    TransactionFailedError,
    InsufficientBalanceError,
    ConfigurationError
)
from app.models.responses import ErrorResponse
from app.config import settings


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    # Handle both string and dict detail types
    detail = exc.detail
    
    # If detail is already an ErrorResponse dict, use it directly
    if isinstance(detail, dict) and "error" in detail and "code" in detail and "message" in detail:
        # Validate it's a proper ErrorResponse format
        if isinstance(detail.get("message"), str):
            return JSONResponse(
                status_code=exc.status_code,
                content=detail
            )
    
    # Otherwise, create a new ErrorResponse
    # Extract message from dict if needed
    if isinstance(detail, dict):
        # If it's a dict but not ErrorResponse format, try to extract message
        message = detail.get("message")
        if message is None:
            # Try to stringify the dict
            message = str(detail)
        elif not isinstance(message, str):
            # If message exists but isn't a string, convert it
            message = str(message)
    else:
        message = str(detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=True,
            code=f"HTTP_{exc.status_code}",
            message=message,
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with helpful suggestions."""
    # Extract common validation errors
    error_messages = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        error_type = error.get("type", "")
        error_msg = error.get("msg", "")
        
        if error_type == "value_error.missing":
            error_messages.append(f"Missing required field: {field}")
        elif error_type == "value_error.str.regex":
            if "address" in field.lower():
                error_messages.append(f"Invalid Ethereum address format for {field}. Addresses must start with '0x' and be 42 characters long.")
            else:
                error_messages.append(f"Invalid format for {field}: {error_msg}")
        elif error_type == "type_error":
            error_messages.append(f"Invalid type for {field}: expected {error_msg}")
        else:
            error_messages.append(f"{field}: {error_msg}")
    
    help_text = "Check the request body and ensure all required fields are provided with correct types and formats."
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=True,
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={
                "errors": exc.errors(),
                "summary": error_messages,
                "help": help_text
            }
        ).model_dump()
    )


async def fx_protocol_error_handler(request: Request, exc: FXProtocolError):
    """Handle fx-sdk protocol errors with enhanced context."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    help_text = None
    documentation_url = "https://docs.fxprotocol.io"
    
    if isinstance(exc, ContractCallError):
        status_code = status.HTTP_400_BAD_REQUEST
        help_text = "This error usually means the contract call failed. Check that the contract address is correct and the function parameters are valid."
    elif isinstance(exc, InsufficientBalanceError):
        status_code = status.HTTP_400_BAD_REQUEST
        help_text = "The account does not have sufficient balance for this operation. Check your token balances using /v1/balances/{address}."
    elif isinstance(exc, TransactionFailedError):
        status_code = status.HTTP_400_BAD_REQUEST
        help_text = "The transaction failed on-chain. Check the transaction hash on Etherscan for more details."
    elif isinstance(exc, ConfigurationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        help_text = "There was a configuration error. Please contact support if this persists."
    
    error_response = ErrorResponse(
        error=True,
        code=type(exc).__name__.upper(),
        message=str(exc),
    )
    
    # Add help field if available
    if help_text:
        error_response.details = error_response.details or {}
        error_response.details["help"] = help_text
        error_response.details["documentation"] = documentation_url
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=True,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__} if settings.API_ENV == "development" else None
        ).model_dump()
    )

