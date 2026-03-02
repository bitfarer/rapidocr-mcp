"""Monitoring and metrics."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Any
import time

from rapidocr_mcp.config import settings

ocr_requests_total = Counter(
    "ocr_requests_total",
    "Total OCR requests",
    ["method", "status"],
)

ocr_latency = Histogram(
    "ocr_latency_seconds",
    "OCR request latency",
    ["method"],
)

ocr_images_processed = Counter(
    "ocr_images_processed_total",
    "Total images processed",
)

ocr_texts_detected = Counter(
    "ocr_texts_detected_total",
    "Total text regions detected",
)

model_load_time = Gauge(
    "model_load_time_seconds",
    "Model loading time",
)

active_requests = Gauge(
    "active_requests",
    "Number of active OCR requests",
)

cache_hits = Counter(
    "cache_hits_total",
    "Total cache hits",
)

cache_misses = Counter(
    "cache_misses_total",
    "Total cache misses",
)


class MetricsServer:
    """Prometheus metrics HTTP server."""

    def __init__(self, port: int = 9090):
        self.port = port

    async def handle_request(self, scope, receive, send):
        """Handle HTTP request for metrics."""
        if scope["path"] == "/metrics":
            await self._send_metrics(send)
        else:
            await self._send_not_found(send)

    async def _send_metrics(self, send):
        body = generate_latest()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", CONTENT_TYPE_LATEST]],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )

    async def _send_not_found(self, send):
        await send(
            {
                "type": "http.response.start",
                "status": 404,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"Not Found",
            }
        )


metrics_server = MetricsServer(settings.metrics_port)
