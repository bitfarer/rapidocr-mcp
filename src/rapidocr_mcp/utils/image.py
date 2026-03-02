import base64
import io
from pathlib import Path
from typing import Any
from PIL import Image
import numpy as np


def base64_to_pil(b64: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    if b64.startswith("data:image"):
        b64 = b64.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(b64)))


def pil_to_base64(img: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def bytes_to_pil(data: bytes) -> Image.Image:
    """Convert bytes to PIL Image."""
    return Image.open(io.BytesIO(data))


def path_to_pil(path: str) -> Image.Image:
    """Load image from file path."""
    return Image.open(path)


def validate_image_format(path: str, allowed_formats: list[str]) -> bool:
    """Validate image file format."""
    ext = Path(path).suffix.lstrip(".").lower()
    return ext in [f.lower() for f in allowed_formats]


def validate_image_size(path: str, max_size: int) -> bool:
    """Validate image file size."""
    return Path(path).stat().st_size <= max_size


def preprocess_image(
    img: Image.Image,
    auto_enhance: bool = False,
    rotate: bool = False,
    binarize: bool = False,
    threshold: int = 128,
) -> Image.Image:
    """Preprocess image for better OCR results."""
    if auto_enhance:
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)

    if rotate:
        from PIL import ImageOps

        img = ImageOps.exif_transpose(img)

    if binarize:
        img = img.convert("L")
        img = img.point(lambda x: 255 if x > threshold else 0, mode="1")

    return img


def np_to_pil(arr: np.ndarray) -> Image.Image:
    """Convert numpy array to PIL Image."""
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)
    return Image.fromarray(arr)


def pil_to_np(img: Image.Image) -> np.ndarray:
    """Convert PIL Image to numpy array."""
    return np.array(img)


def resize_image(img: Image.Image, max_width: int = 2048, max_height: int = 2048) -> Image.Image:
    """Resize image if too large."""
    if img.width <= max_width and img.height <= max_height:
        return img

    ratio = min(max_width / img.width, max_height / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    return img.resize(new_size, Image.LANCZOS)
