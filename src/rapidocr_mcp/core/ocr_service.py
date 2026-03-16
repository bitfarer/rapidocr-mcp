import time
from typing import Any

from loguru import logger

from ..config import settings


class OCREngineBase:
    """Base class for OCR engines."""

    def __init__(self, **kwargs):
        pass

    def __call__(self, image: Any) -> tuple[list, float]:
        raise NotImplementedError


class RapidOCREngine(OCREngineBase):
    """RapidOCR implementation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ocr = None
        self._init_engine()

    def _init_engine(self):
        from rapidocr_onnxruntime import RapidOCR

        logger.info("Initializing RapidOCR engine...")
        start = time.perf_counter()
        self._ocr = RapidOCR(
            det_model_path=settings.resolve_path(settings.det_model_path),
            rec_model_path=settings.resolve_path(settings.rec_model_path),
            cls_model_path=settings.resolve_path(settings.cls_model_path),
            use_angle_cls=settings.use_angle_cls,
            lang=settings.lang,
        )
        logger.success(f"RapidOCR initialized in {time.perf_counter() - start:.2f}s")

    def __call__(self, image: Any) -> tuple[list, float]:
        result, elapse = self._ocr(image)
        return result or [], elapse


class OCRService:
    """OCR Service - Singleton with lazy loading."""

    _instance = None
    _engine: RapidOCREngine | None = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _lazy_init(self):
        if not self._initialized:
            logger.info("Initializing OCR engine...")
            self._engine = RapidOCREngine()
            self._initialized = True

    def _process_result(self, result: list) -> list[dict[str, Any]]:
        """Process OCR result with filtering and postprocessing."""
        processed = []
        for item in result:
            if len(item) >= 3:
                box, text, score = item[0], item[1], item[2]
                if score >= settings.confidence_threshold:
                    processed.append(
                        {
                            "bbox": box,
                            "text": text,
                            "score": float(score),
                        }
                    )

        if settings.text_postprocessing_deduplicate:
            processed = self._deduplicate(processed)

        if settings.text_postprocessing_merge:
            processed = self._merge_nearby(processed)

        return processed

    def _deduplicate(self, results: list[dict]) -> list[dict]:
        """Remove duplicate texts."""
        seen = set()
        unique = []
        for r in results:
            if r["text"] not in seen:
                seen.add(r["text"])
                unique.append(r)
        return unique

    def _merge_nearby(self, results: list[dict]) -> list[dict]:
        """Merge nearby text boxes."""
        if not results:
            return results

        sorted_results = sorted(results, key=lambda x: (x["bbox"][0][1], x["bbox"][0][0]))
        merged = [sorted_results[0]]

        for current in sorted_results[1:]:
            last = merged[-1]
            last_bottom = max(b[1] for b in last["bbox"])
            current_top = min(b[1] for b in current["bbox"])

            if (
                current_top - last_bottom < 10
                and abs(current["bbox"][0][0] - last["bbox"][0][0]) < 50
            ):
                merged[-1] = {
                    "bbox": [
                        last["bbox"][0],
                        current["bbox"][1],
                        current["bbox"][2],
                        last["bbox"][3],
                    ],
                    "text": last["text"] + " " + current["text"],
                    "score": (last["score"] + current["score"]) / 2,
                }
            else:
                merged.append(current)

        return merged

    def ocr(self, image: Any) -> list[dict[str, Any]]:
        """Perform OCR on the given image."""
        self._lazy_init()
        start = time.perf_counter()
        raw = self._engine(image)

        if raw is None:
            result = []
            elapse = time.perf_counter() - start
        elif isinstance(raw, tuple):
            result = raw[0] if raw[0] else []
            times = raw[1] if len(raw) > 1 and raw[1] else []
            if isinstance(times, list) and times:
                elapse = (
                    times[0]
                    if isinstance(times[0], (int, float))
                    else (time.perf_counter() - start)
                )
            else:
                elapse = time.perf_counter() - start
        else:
            result = list(raw) if raw else []
            elapse = time.perf_counter() - start

        logger.info(f"OCR completed in {elapse:.3f}s, found {len(result)} text regions")

        processed = self._process_result(result)
        logger.info(f"After postprocessing: {len(processed)} text blocks")

        return processed

    def reset(self):
        """Reset the service (for testing)."""
        self._engine = None
        self._initialized = False


ocr_service = OCRService()
