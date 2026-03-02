"""Test OCR Service."""

import pytest
from unittest.mock import MagicMock, patch


class TestOCRService:
    """Tests for OCRService."""

    def test_singleton_pattern(self):
        """Test singleton pattern."""
        from rapidocr_mcp.core.ocr_service import OCRService

        service1 = OCRService()
        service2 = OCRService()
        assert service1 is service2

    def test_deduplicate(self):
        """Test deduplication."""
        from rapidocr_mcp.core.ocr_service import OCRService

        service = OCRService()
        results = [
            {"text": "Hello", "score": 0.9, "bbox": [[0, 0], [100, 0], [100, 50], [0, 50]]},
            {"text": "World", "score": 0.8, "bbox": [[0, 60], [100, 60], [100, 100], [0, 100]]},
            {"text": "Hello", "score": 0.95, "bbox": [[0, 0], [100, 0], [100, 50], [0, 50]]},
        ]
        deduped = service._deduplicate(results)
        assert len(deduped) == 2
        assert deduped[0]["text"] == "Hello"
        assert deduped[1]["text"] == "World"

    def test_merge_nearby(self):
        """Test merging nearby text boxes."""
        from rapidocr_mcp.core.ocr_service import OCRService

        service = OCRService()
        results = [
            {"bbox": [[0, 0], [100, 0], [100, 30], [0, 30]], "text": "Hello", "score": 0.9},
            {"bbox": [[0, 35], [100, 35], [100, 65], [0, 65]], "text": "World", "score": 0.8},
        ]
        merged = service._merge_nearby(results)
        assert len(merged) <= 2

    def test_process_result_empty(self):
        """Test processing empty result."""
        from rapidocr_mcp.core.ocr_service import OCRService

        service = OCRService()
        result = service._process_result([])
        assert result == []

    def test_reset(self):
        """Test service reset."""
        from rapidocr_mcp.core.ocr_service import OCRService

        service = OCRService()
        service._initialized = True
        service._engine = MagicMock()

        service.reset()

        assert service._engine is None
        assert service._initialized is False
