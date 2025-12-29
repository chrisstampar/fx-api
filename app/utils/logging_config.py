"""
Structured logging configuration for the API.

Provides JSON-formatted logging for better observability.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        
        if hasattr(record, "method"):
            log_data["method"] = record.method
        
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        # Add any extra fields from the record
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Set up structured logging for the API.
    
    Args:
        log_level: Logging level (defaults to INFO, or from settings)
    """
    if log_level is None:
        log_level = settings.API_ENV.upper() if settings.API_ENV == "production" else "INFO"
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Use JSON formatter in production, simple formatter in development
    if settings.API_ENV == "production":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set levels for specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Request/Response logging middleware helper
def log_request(request_id: str, method: str, path: str, **kwargs) -> None:
    """
    Log an API request.
    
    Args:
        request_id: Unique request ID
        method: HTTP method
        path: Request path
        **kwargs: Additional fields to log
    """
    logger = logging.getLogger("api.request")
    logger.info(
        f"{method} {path}",
        extra={
            "request_id": request_id,
            "method": method,
            "endpoint": path,
            **kwargs
        }
    )


def log_response(request_id: str, status_code: int, duration_ms: float, **kwargs) -> None:
    """
    Log an API response.
    
    Args:
        request_id: Unique request ID
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional fields to log
    """
    logger = logging.getLogger("api.response")
    level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR
    logger.log(
        level,
        f"Response {status_code}",
        extra={
            "request_id": request_id,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            **kwargs
        }
    )


def log_error(request_id: str, error: Exception, **kwargs) -> None:
    """
    Log an error.
    
    Args:
        request_id: Unique request ID
        error: Exception instance
        **kwargs: Additional fields to log
    """
    logger = logging.getLogger("api.error")
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs
        }
    )

