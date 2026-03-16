"""OCR Engine plugins - Multi-engine support."""

from abc import ABC, abstractmethod
from importlib.util import find_spec
from typing import Any


class OCREngine(ABC):
    """Base class for OCR engines."""

    name: str = "base"

    @abstractmethod
    def __init__(self, **config):
        """Initialize the engine with config."""
        pass

    @abstractmethod
    def __call__(self, image: Any) -> tuple[list, float]:
        """Process image and return results."""
        pass

    @abstractmethod
    def available(self) -> bool:
        """Check if engine is available."""
        pass


class RapidOCRPlugin(OCREngine):
    """RapidOCR engine plugin."""

    name = "rapidocr"

    def __init__(self, **config):
        self._ocr = None
        self._config = config

    def available(self) -> bool:
        return find_spec("rapidocr_onnxruntime") is not None

    def __call__(self, image: Any) -> tuple[list, float]:
        from rapidocr_onnxruntime import RapidOCR

        if self._ocr is None:
            self._ocr = RapidOCR(**self._config)
        return self._ocr(image)


class PaddleOCRPlugin(OCREngine):
    """PaddleOCR engine plugin (placeholder)."""

    name = "paddleocr"

    def __init__(self, **config):
        self._config = config

    def available(self) -> bool:
        return False

    def __call__(self, image: Any) -> tuple[list, float]:
        raise NotImplementedError("PaddleOCR not installed")


class EasyOCRPlugin(OCREngine):
    """EasyOCR engine plugin (placeholder)."""

    name = "easyocr"

    def __init__(self, **config):
        self._config = config

    def available(self) -> bool:
        return False

    def __call__(self, image: Any) -> tuple[list, float]:
        raise NotImplementedError("EasyOCR not installed")


class TesseractPlugin(OCREngine):
    """Tesseract OCR engine plugin (placeholder)."""

    name = "tesseract"

    def __init__(self, **config):
        self._config = config

    def available(self) -> bool:
        return False

    def __call__(self, image: Any) -> tuple[list, float]:
        raise NotImplementedError("Tesseract not installed")


ENGINES = {
    "rapidocr": RapidOCRPlugin,
    "paddleocr": PaddleOCRPlugin,
    "easyocr": EasyOCRPlugin,
    "tesseract": TesseractPlugin,
}


def get_engine(name: str, **config) -> OCREngine:
    """Get OCR engine by name."""
    engine_class = ENGINES.get(name)
    if engine_class is None:
        raise ValueError(f"Unknown engine: {name}")
    return engine_class(**config)


def list_available_engines() -> dict[str, bool]:
    """List all available engines."""
    return {name: engine_class().available() for name, engine_class in ENGINES.items()}
