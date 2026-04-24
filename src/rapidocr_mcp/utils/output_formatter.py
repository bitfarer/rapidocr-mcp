"""Output formatters for OCR results."""

import json
from typing import Any


class OutputFormatter:
    """Base class for output formatters."""

    @staticmethod
    def format(results: list[dict[str, Any]]) -> Any:
        raise NotImplementedError


class PlainFormatter(OutputFormatter):
    """Plain text output."""

    @staticmethod
    def format(results: list[dict[str, Any]]) -> str:
        if not results:
            return ""
        return "\n".join(r["text"] for r in results)


class JsonFormatter(OutputFormatter):
    """JSON output."""

    @staticmethod
    def format(results: list[dict[str, Any]]) -> str:
        return json.dumps(results, ensure_ascii=False, indent=2)


class MarkdownFormatter(OutputFormatter):
    """Markdown output."""

    @staticmethod
    def format(results: list[dict[str, Any]]) -> str:
        if not results:
            return ""
        lines = ["# OCR Results\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"## Text {i}\n")
            lines.append(f"```\n{r['text']}\n```\n")
            lines.append(f"Confidence: {r['score']:.2%}\n")
            lines.append(f"Bounding Box: {r['bbox']}\n\n")
        return "".join(lines)


class StructuredFormatter(OutputFormatter):
    """Structured output for MCP."""

    @staticmethod
    def format(results: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "results": results,
            "total": len(results),
            "texts": [r["text"] for r in results],
            "average_confidence": sum(r["score"] for r in results) / len(results)
            if results
            else 0.0,
        }


FORMATTERS = {
    "plain": PlainFormatter,
    "json": JsonFormatter,
    "markdown": MarkdownFormatter,
    "structured": StructuredFormatter,
}


def format_output(results: list[dict[str, Any]], format_type: str) -> Any:
    """Format OCR results based on the specified format type."""
    formatter_class = FORMATTERS.get(format_type, JsonFormatter)
    formatter = formatter_class()
    return formatter.format(results)
