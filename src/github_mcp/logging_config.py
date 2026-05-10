"""Structured logging configuration for the MCP server."""

import logging
import sys
import traceback
from typing import Any, Dict, Optional


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure structured logging for the MCP server.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format ('json' or 'text')
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplication
    root_logger.handlers.clear()
    
    # Add stderr handler (stdout is reserved for MCP protocol)
    handler = logging.StreamHandler(sys.stderr)
    
    if log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured logs with safe serialization."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string, safely handling non-serializable objects."""
        # Base log entry with standard fields
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": self._safe_string(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Include exception info if present - convert to string to avoid serialization issues
        if record.exc_info:
            log_entry["exception"] = self._safe_string(
                "".join(traceback.format_exception(*record.exc_info))
            )
        
        # Include extra fields (like request_id) if present - ensure they're serializable
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_entry:
                continue
            try:
                # Test if value is JSON serializable
                import json
                json.dumps(value)
                log_entry[key] = value
            except (TypeError, ValueError):
                # Convert non-serializable objects to string representation
                log_entry[key] = self._safe_string(str(value))
        
        import json
        return json.dumps(log_entry)
    
    def _safe_string(self, value: Any) -> str:
        """Convert any value to string safely."""
        if value is None:
            return ""
        try:
            return str(value)
        except Exception:
            return "<unable to convert to string>"