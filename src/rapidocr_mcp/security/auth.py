"""Security utilities."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from loguru import logger

from ..config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuditLogger:
    """Audit logger for security events."""

    def __init__(self, log_file: str | None = None):
        self.log_file = Path(log_file) if log_file else None
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, data: dict[str, Any]) -> None:
        entry = {
            "timestamp": time.time(),
            "event": event,
            **data,
        }
        logger.info(f"AUDIT: {json.dumps(entry)}")
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")


audit_logger = AuditLogger()


async def verify_api_key(key: str | None = Security(api_key_header)) -> str | None:
    """Verify API key from header."""
    if settings.api_key is None:
        return None

    if key is None:
        raise HTTPException(status_code=401, detail="Missing API key")

    if key != settings.api_key:
        audit_logger.log(
            "api_key_invalid", {"key_hash": hashlib.sha256(key.encode()).hexdigest()[:8]}
        )
        raise HTTPException(status_code=403, detail="Invalid API key")

    audit_logger.log("api_key_valid", {})
    return key


def verify_path(path: str) -> bool:
    """Verify path is safe to access."""
    if not settings.enable_path_whitelist:
        return True
    return settings.is_path_allowed(path)


def verify_image_format(path: str) -> bool:
    """Verify image format is allowed."""
    ext = Path(path).suffix.lstrip(".").lower()
    return ext in [f.lower() for f in settings.allowed_image_formats]


def verify_image_size(path: str) -> bool:
    """Verify image size is within limits."""
    try:
        size = Path(path).stat().st_size
        return size <= settings.max_image_size
    except Exception:
        return False
