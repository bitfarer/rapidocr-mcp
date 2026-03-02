"""FastAPI Server with multiple transport protocols."""

import asyncio
import base64
from contextlib import asynccontextmanager
from typing import Any, Annotated
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger
import uvicorn

from ..config import settings
from ..core.ocr_service import ocr_service
from ..utils.image import bytes_to_pil, preprocess_image
from ..utils.output_formatter import format_output
from ..utils.url_downloader import url_downloader
from ..monitoring.metrics import metrics_server, ocr_requests_total, ocr_latency
from ..monitoring.tracing import tracer, init_tracing
from ..security.auth import verify_api_key, AuditLogger


class OCRRequest:
    """OCR request model."""

    def __init__(
        self,
        output_format: str = "json",
        auto_enhance: bool = False,
        rotate: bool = False,
        binarize: bool = False,
    ):
        self.output_format = output_format
        self.auto_enhance = auto_enhance
        self.rotate = rotate
        self.binarize = binarize


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RapidOCR MCP Server...")
    yield
    logger.info("Shutting down...")
    await url_downloader.close()


app = FastAPI(
    title="RapidOCR MCP Server",
    description="High-performance OCR via Model Context Protocol",
    version="1.0.0",
    lifespan=lifespan,
)

if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

init_tracing(app)


def get_optional_api_key(api_key: str | None = Depends(verify_api_key)) -> str | None:
    """Get optional API key."""
    return api_key


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/ocr/path")
async def ocr_by_path(
    path: str = Form(...),
    output_format: str = Form("json"),
    auto_enhance: bool = Form(False),
    rotate: bool = Form(False),
    binarize: bool = Form(False),
    api_key: str | None = Depends(get_optional_api_key),
) -> Any:
    """OCR by file path."""
    import time
    from pathlib import Path

    with tracer.start_as_current_span("ocr_by_path") as span:
        span.set_attribute("path", path)
        start = time.perf_counter()

        try:
            from ..utils.image import validate_image_format, validate_image_size

            if not validate_image_format(path, settings.allowed_image_formats):
                raise HTTPException(status_code=400, detail="Unsupported image format")
            if not validate_image_size(path, settings.max_image_size):
                raise HTTPException(status_code=400, detail="Image too large")

            img = bytes_to_pil(Path(path).read_bytes())
            img = preprocess_image(img, auto_enhance, rotate, binarize)
            results = ocr_service.ocr(img)

            elapsed = time.perf_counter() - start
            ocr_latency.labels(method="path").observe(elapsed)
            ocr_requests_total.labels(method="path", status="success").inc()

            return format_output(results, output_format)
        except Exception as e:
            ocr_requests_total.labels(method="path", status="error").inc()
            logger.error(f"OCR error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/base64")
async def ocr_by_base64(
    image: str = Form(...),
    output_format: str = Form("json"),
    auto_enhance: bool = Form(False),
    rotate: bool = Form(False),
    binarize: bool = Form(False),
    api_key: str | None = Depends(get_optional_api_key),
) -> Any:
    """OCR by base64 image."""
    import time
    from ..utils.image import base64_to_pil

    with tracer.start_as_current_span("ocr_by_base64") as span:
        start = time.perf_counter()

        try:
            img = base64_to_pil(image)
            img = preprocess_image(img, auto_enhance, rotate, binarize)
            results = ocr_service.ocr(img)

            elapsed = time.perf_counter() - start
            ocr_latency.labels(method="base64").observe(elapsed)
            ocr_requests_total.labels(method="base64", status="success").inc()

            return format_output(results, output_format)
        except Exception as e:
            ocr_requests_total.labels(method="base64", status="error").inc()
            logger.error(f"OCR error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/url")
async def ocr_by_url(
    url: str = Form(...),
    output_format: str = Form("json"),
    use_cache: bool = Form(True),
    auto_enhance: bool = Form(False),
    rotate: bool = Form(False),
    binarize: bool = Form(False),
    api_key: str | None = Depends(get_optional_api_key),
) -> Any:
    """OCR by image URL."""
    import time

    with tracer.start_as_current_span("ocr_by_url") as span:
        span.set_attribute("url", url)
        start = time.perf_counter()

        try:
            data = await url_downloader.download(url, use_cache)
            img = bytes_to_pil(data)
            img = preprocess_image(img, auto_enhance, rotate, binarize)
            results = ocr_service.ocr(img)

            elapsed = time.perf_counter() - start
            ocr_latency.labels(method="url").observe(elapsed)
            ocr_requests_total.labels(method="url", status="success").inc()

            return format_output(results, output_format)
        except Exception as e:
            ocr_requests_total.labels(method="url", status="error").inc()
            logger.error(f"OCR error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/upload")
async def ocr_upload(
    file: UploadFile = File(...),
    output_format: str = Form("json"),
    auto_enhance: bool = Form(False),
    rotate: bool = Form(False),
    binarize: bool = Form(False),
    api_key: str | None = Depends(get_optional_api_key),
) -> Any:
    """OCR by file upload."""
    import time

    with tracer.start_as_current_span("ocr_upload") as span:
        start = time.perf_counter()

        try:
            contents = await file.read()
            if len(contents) > settings.max_image_size:
                raise HTTPException(status_code=400, detail="File too large")

            img = bytes_to_pil(contents)
            img = preprocess_image(img, auto_enhance, rotate, binarize)
            results = ocr_service.ocr(img)

            elapsed = time.perf_counter() - start
            ocr_latency.labels(method="upload").observe(elapsed)
            ocr_requests_total.labels(method="upload", status="success").inc()

            return format_output(results, output_format)
        except HTTPException:
            raise
        except Exception as e:
            ocr_requests_total.labels(method="upload", status="error").inc()
            logger.error(f"OCR error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    return StreamingResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        workers=settings.server_workers,
    )


if __name__ == "__main__":
    run_server()
