"""Test output formatters."""

import pytest
from rapidocr_mcp.utils.output_formatter import (
    format_output,
    PlainFormatter,
    JsonFormatter,
    MarkdownFormatter,
    StructuredFormatter,
)


class TestOutputFormatters:
    """Tests for output formatters."""

    @pytest.fixture
    def sample_results(self):
        """Sample OCR results."""
        return [
            {"bbox": [[0, 0], [100, 0], [100, 50], [0, 50]], "text": "Hello", "score": 0.95},
            {"bbox": [[0, 60], [100, 60], [100, 100], [0, 100]], "text": "World", "score": 0.88},
        ]

    def test_plain_formatter(self, sample_results):
        """Test plain text formatter."""
        result = PlainFormatter.format(sample_results)
        assert "Hello" in result
        assert "World" in result

    def test_json_formatter(self, sample_results):
        """Test JSON formatter."""
        result = JsonFormatter.format(sample_results)
        assert "Hello" in result
        assert "World" in result

    def test_markdown_formatter(self, sample_results):
        """Test markdown formatter."""
        result = MarkdownFormatter.format(sample_results)
        assert "# OCR Results" in result
        assert "Hello" in result

    def test_structured_formatter(self, sample_results):
        """Test structured formatter."""
        result = StructuredFormatter.format(sample_results)
        assert result["total"] == 2
        assert "Hello" in result["texts"]
        assert result["average_confidence"] > 0

    def test_format_output(self, sample_results):
        """Test format_output function."""
        assert "Hello" in format_output(sample_results, "plain")
        assert "World" in format_output(sample_results, "json")
        assert "# OCR Results" in format_output(sample_results, "markdown")
        assert format_output(sample_results, "structured")["total"] == 2

    def test_empty_results(self):
        """Test with empty results."""
        assert format_output([], "plain") == ""
        assert format_output([], "json") == "[]"
        result = format_output([], "structured")
        assert result["total"] == 0
