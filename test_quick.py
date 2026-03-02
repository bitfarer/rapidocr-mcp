"""Quick test script for RapidOCR MCP Server."""

import asyncio
import base64
import io
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent / "src"))

from rapidocr_mcp.core.ocr_service import OCRService
from rapidocr_mcp.utils.image import base64_to_pil, pil_to_base64
from rapidocr_mcp.utils.output_formatter import format_output


def create_test_image(text: str = "Hello World") -> Image.Image:
    """Create a test image with text."""
    img = Image.new("RGB", (400, 100), color="white")
    from PIL import ImageDraw, ImageFont

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    draw.text((10, 25), text, fill="black", font=font)
    return img


def test_ocr_service():
    """Test OCR service directly."""
    print("=== Testing OCR Service ===")

    service = OCRService()

    # Create test image
    img = create_test_image("Test OCR")

    # Save to temp file
    test_file = Path("test_image.png")
    img.save(test_file)
    print(f"Created test image: {test_file}")

    # Test OCR
    results = service.ocr(str(test_file))
    print(f"OCR results: {results}")

    # Test output formatters
    print("\n=== Testing Output Formatters ===")
    print("Plain:", format_output(results, "plain"))
    print("JSON:", format_output(results, "json")[:200] + "...")
    print("Structured:", format_output(results, "structured"))

    # Cleanup
    test_file.unlink()
    print("\n=== Test Complete ===")


def test_image_utils():
    """Test image utilities."""
    print("\n=== Testing Image Utils ===")

    img = create_test_image("Base64 Test")

    # Test base64 conversion
    b64 = pil_to_base64(img)
    print(f"Base64 length: {len(b64)}")

    img_back = base64_to_pil(b64)
    print(f"Restored image size: {img_back.size}")

    print("Image utils OK")


def test_config():
    """Test configuration."""
    print("\n=== Testing Config ===")
    from rapidocr_mcp.config import settings

    print(f"Lang: {settings.lang}")
    print(f"Max image size: {settings.max_image_size}")
    print(f"Output format: {settings.default_output_format}")
    print("Config OK")


if __name__ == "__main__":
    test_config()
    test_image_utils()
    test_ocr_service()
