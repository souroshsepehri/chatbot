import logging
import sys
import json
import io
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar

# Context variable for request_id (shared with middleware)
request_id_var: ContextVar[str] = ContextVar('request_id', default='unknown')


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request_id if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs", "message",
                          "pathname", "process", "processName", "relativeCreated", "thread",
                          "threadName", "exc_info", "exc_text", "stack_info", "request_id"]:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


class RequestIDFilter(logging.Filter):
    """Filter to add request_id to log records from context variable"""
    def filter(self, record):
        # Get request_id from context variable and add to record
        # This runs AFTER the record is created and extra is processed
        # Only set if not already set (to avoid conflicts)
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get('unknown')
        return True


class SimpleFormatter(logging.Formatter):
    """Simple formatter for console (human-readable)"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Build base message
        parts = [
            f"[{self.formatTime(record, self.datefmt)}]",
            f"{record.levelname:8s}",
            f"{record.name}",
        ]
        
        # Add request_id if present
        if hasattr(record, "request_id"):
            parts.append(f"[req:{record.request_id[:8]}]")
        
        # Get message and make it ASCII-safe for console
        try:
            msg = record.getMessage()
        except Exception:
            msg = str(record.msg) if hasattr(record, 'msg') else "Unable to format message"
        
        # Make message ASCII-safe to prevent encoding errors
        # This is critical for Windows console (cp1252) which can't handle Persian/Unicode
        try:
            # Convert to bytes with ASCII encoding (replacing non-ASCII), then back to string
            safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
        except Exception:
            safe_msg = "Message contains non-ASCII characters"
        
        parts.append(f"- {safe_msg}")
        
        # Join parts and ensure final string is also ASCII-safe
        result = " ".join(parts)
        try:
            # Double-check the final result is ASCII-safe
            return result.encode('ascii', errors='replace').decode('ascii')
        except Exception:
            return f"[{record.levelname}] {record.name} - Log message"


def setup_logging():
    """Configure application logging with structured JSON for files"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create and add request_id filter to all handlers
    request_id_filter = RequestIDFilter()
    
    # Console handler - human-readable format
    # SimpleFormatter already converts messages to ASCII-safe, so use standard handler
    # but wrap it to catch any remaining encoding errors
    class SafeStreamHandler(logging.StreamHandler):
        """StreamHandler that safely handles Unicode encoding errors"""
        def handleError(self, record):
            """Override to prevent Python's error handler from printing to stderr"""
            # Do nothing - prevent recursion and encoding errors
            pass
        
        def emit(self, record):
            try:
                # Format message (SimpleFormatter makes it ASCII-safe)
                msg = self.format(record)
                # Ensure it's truly ASCII-safe
                safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
                # Write using buffer to avoid encoding issues
                if hasattr(self.stream, 'buffer'):
                    self.stream.buffer.write((safe_msg + self.terminator).encode('ascii'))
                    self.stream.buffer.flush()
                else:
                    self.stream.write(safe_msg + self.terminator)
                    self.flush()
            except Exception:
                # Silently ignore all errors to prevent recursion
                # Don't call handleError() to avoid Python's error handler
                pass
    
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = SimpleFormatter()
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(request_id_filter)  # Add request_id filter
    
    # File handler - structured JSON format
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(request_id_filter)  # Add request_id filter
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Suppress noisy logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

