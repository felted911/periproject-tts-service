# Logging infrastructure for the TTS service
import os
import sys
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Import config from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from config import settings


class JsonFormatter(logging.Formatter):
    """Format logs as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
            
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for key, value in record.extra.items():
                log_data[key] = value
                
        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Format logs for console output with colors."""
    
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",   # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[91m\033[1m", # Bold Red
        "RESET": "\033[0m",   # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        
        # Base format
        message = f"{level_color}{record.levelname}{reset} [{record.name}] {record.getMessage()}"
        
        # Add request ID if available
        if hasattr(record, "request_id"):
            message = f"{message} [request_id: {record.request_id}]"
            
        # Add exception info if present
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
            
        return message


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger.
    
    Args:
        name: Logger name
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level
    level = getattr(logging, settings.LOG_LEVEL.upper())
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add handlers based on format
    if settings.LOG_FORMAT.lower() == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ConsoleFormatter())
        logger.addHandler(handler)
    
    return logger


def with_request_context(logger: logging.Logger, request_id: Optional[str] = None) -> logging.LoggerAdapter:
    """Add request context to logger.
    
    Args:
        logger: Base logger
        request_id: Request ID (generated if not provided)
    
    Returns:
        Logger with request context
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    return logging.LoggerAdapter(
        logger, 
        {"request_id": request_id}
    )
