"""OpenTelemetry tracing."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from typing import Any

tracer_provider = TracerProvider(resource=Resource.create({"service.name": "rapidocr-mcp"}))
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)


def init_tracing(app: Any = None) -> None:
    """Initialize OpenTelemetry tracing."""
    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            pass


class TraceContext:
    """Context manager for tracing OCR operations."""

    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
        self.span = None

    def __enter__(self):
        self.span = tracer.start_span(self.name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("error", True)
                self.span.set_attribute("error.message", str(exc_val))
            self.span.end()
