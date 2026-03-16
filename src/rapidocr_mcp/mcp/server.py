"""MCP Server with FastMCP."""

import time
from pathlib import Path
from typing import Any
from mcp.server.fastmcp import FastMCP, Context
from loguru import logger

from ..core.ocr_service import ocr_service
from ..config import settings
from ..utils.image import (
    base64_to_pil,
    path_to_pil,
    validate_image_format,
    validate_image_size,
    preprocess_image,
)
from ..utils.output_formatter import format_output
from ..utils.url_downloader import url_downloader
from ..utils.rate_limit import rate_limiter, concurrent_limiter
from ..monitoring.metrics import ocr_requests_total, ocr_latency

mcp = FastMCP("rapidocr-mcp", json_response=True)


@mcp.tool()
async def ocr_by_path(
    image_path: str,
    output_format: str = "json",
    auto_enhance: bool = False,
    rotate: bool = False,
    binarize: bool = False,
    ctx: Context | None = None,
) -> Any:
    """对本地图像文件执行 OCR 识别。

    Args:
        image_path: 图像文件的绝对路径或相对路径
        output_format: 输出格式 (plain/json/markdown/structured)
        auto_enhance: 自动增强图像对比度和锐度
        rotate: 自动旋转图像（基于 EXIF）
        binarize: 二值化图像

    Returns:
        OCR 识别结果
    """
    if ctx:
        await ctx.info(f"OCR file: {image_path}")

    if settings.enable_rate_limit:
        await rate_limiter.wait_and_acquire()

    if settings.enable_path_whitelist and not settings.is_path_allowed(image_path):
        raise ValueError(f"Path not allowed: {image_path}")

    if not validate_image_format(image_path, settings.allowed_image_formats):
        raise ValueError(f"Unsupported image format: {Path(image_path).suffix}")

    if not validate_image_size(image_path, settings.max_image_size):
        raise ValueError(f"Image too large: {Path(image_path).stat().st_size} bytes")

    start = time.perf_counter()
    await concurrent_limiter.acquire()
    try:
        img = path_to_pil(image_path)
        img = preprocess_image(img, auto_enhance, rotate, binarize)
        results = ocr_service.ocr(img)
        ocr_latency.labels(method="path").observe(time.perf_counter() - start)
        ocr_requests_total.labels(method="path", status="success").inc()
        return format_output(results, output_format)
    except Exception as e:
        logger.error(f"OCR error: {e}")
        ocr_requests_total.labels(method="path", status="error").inc()
        raise
    finally:
        concurrent_limiter.release()


@mcp.tool()
async def ocr_by_content(
    image_base64: str,
    output_format: str = "json",
    auto_enhance: bool = False,
    rotate: bool = False,
    binarize: bool = False,
    ctx: Context | None = None,
) -> Any:
    """对 Base64 编码的图像执行 OCR 识别。

    Args:
        image_base64: Base64 编码的图像（支持 data:image/... 前缀）
        output_format: 输出格式 (plain/json/markdown/structured)
        auto_enhance: 自动增强图像对比度和锐度
        rotate: 自动旋转图像（基于 EXIF）
        binarize: 二值化图像

    Returns:
        OCR 识别结果
    """
    if ctx:
        await ctx.info("OCR base64 image")

    if settings.enable_rate_limit:
        await rate_limiter.wait_and_acquire()

    start = time.perf_counter()
    with concurrent_limiter:  # type: ignore[misc]
        try:
            img = base64_to_pil(image_base64)
            img = preprocess_image(img, auto_enhance, rotate, binarize)
            results = ocr_service.ocr(img)
            ocr_latency.labels(method="content").observe(time.perf_counter() - start)
            ocr_requests_total.labels(method="content", status="success").inc()
            return format_output(results, output_format)
        except Exception as e:
            logger.error(f"OCR base64 error: {e}")
            ocr_requests_total.labels(method="content", status="error").inc()
            raise


@mcp.tool()
async def ocr_by_url(
    image_url: str,
    output_format: str = "json",
    use_cache: bool = True,
    auto_enhance: bool = False,
    rotate: bool = False,
    binarize: bool = False,
    ctx: Context | None = None,
) -> Any:
    """对 URL 图像执行 OCR 识别。

    Args:
        image_url: 图像的 HTTP/HTTPS URL
        output_format: 输出格式 (plain/json/markdown/structured)
        use_cache: 是否使用 URL 缓存
        auto_enhance: 自动增强图像对比度和锐度
        rotate: 自动旋转图像（基于 EXIF）
        binarize: 二值化图像

    Returns:
        OCR 识别结果
    """
    if ctx:
        await ctx.info(f"OCR URL: {image_url}")

    if settings.enable_rate_limit:
        await rate_limiter.wait_and_acquire()

    start = time.perf_counter()
    with concurrent_limiter:  # type: ignore[misc]
        try:
            data = await url_downloader.download(image_url, use_cache)
            from ..utils.image import bytes_to_pil

            img = bytes_to_pil(data)
            img = preprocess_image(img, auto_enhance, rotate, binarize)
            results = ocr_service.ocr(img)
            ocr_latency.labels(method="url").observe(time.perf_counter() - start)
            ocr_requests_total.labels(method="url", status="success").inc()
            return format_output(results, output_format)
        except Exception as e:
            logger.error(f"OCR URL error: {e}")
            ocr_requests_total.labels(method="url", status="error").inc()
            raise


@mcp.tool()
async def ocr_batch(
    image_paths: list[str],
    output_format: str = "json",
    auto_enhance: bool = False,
    rotate: bool = False,
    binarize: bool = False,
    ctx: Context | None = None,
) -> Any:
    """批量 OCR - 对多张图像执行 OCR 识别。

    Args:
        image_paths: 图像文件路径列表
        output_format: 输出格式 (plain/json/markdown/structured)
        auto_enhance: 自动增强图像对比度和锐度
        rotate: 自动旋转图像（基于 EXIF）
        binarize: 二值化图像

    Returns:
        所有图像的 OCR 识别结果
    """
    if ctx:
        await ctx.info(f"Batch OCR: {len(image_paths)} images")

    if settings.enable_rate_limit:
        await rate_limiter.wait_and_acquire()

    all_results = []

    start = time.perf_counter()
    await concurrent_limiter.acquire()
    try:
        for image_path in image_paths:
            try:
                if not validate_image_format(image_path, settings.allowed_image_formats):
                    continue
                if not validate_image_size(image_path, settings.max_image_size):
                    continue
                img = path_to_pil(image_path)
                img = preprocess_image(img, auto_enhance, rotate, binarize)
                results = ocr_service.ocr(img)
                all_results.append({"path": image_path, "results": results})
            except Exception as e:
                logger.error(f"Batch OCR error for {image_path}: {e}")
                all_results.append({"path": image_path, "error": str(e)})
    finally:
        concurrent_limiter.release()

    ocr_latency.labels(method="batch").observe(time.perf_counter() - start)
    ocr_requests_total.labels(method="batch", status="success").inc()

    if output_format == "structured":
        return {
            "total_images": len(image_paths),
            "successful": sum(1 for r in all_results if "error" not in r),
            "failed": sum(1 for r in all_results if "error" in r),
            "results": all_results,
        }
    return format_output(
        [
            {"path": r["path"], "texts": [t["text"] for t in r.get("results", [])]}
            for r in all_results
        ],
        output_format,
    )


def main():
    """Main entry point for MCP server."""
    mcp.run(transport="stdio")


async def main_async():
    """Async main entry point."""
    try:
        mcp.run(transport="stdio")
    finally:
        await url_downloader.close()
