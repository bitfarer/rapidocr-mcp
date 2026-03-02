"""RapidOCR MCP Server - High-performance OCR via Model Context Protocol."""

__version__ = "1.0.0"
__author__ = "RapidOCR Team"

from .core.ocr_service import OCRService
from .config import settings

__all__ = ["OCRService", "settings", "__version__"]
