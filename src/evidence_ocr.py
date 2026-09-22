"""V6.16 bounded evidence text/OCR extraction.

This module converts supported evidence binaries into readable text for the existing
V6.6 fact-suggestion engine. It never verifies facts and never performs external
network I/O. Image OCR uses bundled ONNX models rather than a system tesseract binary,
so the managed Python runtime remains self-contained.
"""
from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
import threading

from PIL import Image
from pypdf import PdfReader
from onnxocr.onnx_paddleocr import ONNXPaddleOcr

MAX_EXTRACTED_CHARS = 500_000
SUPPORTED = {
    "text/plain", "text/csv", "application/json",
    "application/pdf", "image/jpeg", "image/png", "image/webp",
}

@dataclass(frozen=True)
class ExtractedText:
    text: str
    method: str
    pages: int | None = None

class ExtractionError(ValueError):
    pass

def _bounded(text: str) -> str:
    if len(text) > MAX_EXTRACTED_CHARS:
        raise ExtractionError("extracted text exceeds configured limit")
    return text

_ocr_lock = threading.Lock()
_ocr_engine: ONNXPaddleOcr | None = None

def _get_ocr_engine() -> ONNXPaddleOcr:
    global _ocr_engine
    if _ocr_engine is None:
        with _ocr_lock:
            if _ocr_engine is None:
                _ocr_engine = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)
    return _ocr_engine

def _extract_image_text(content: bytes) -> str:
    try:
        image = Image.open(BytesIO(content)).convert("RGB")
        result = _get_ocr_engine().ocr(image)
        texts: list[str] = []
        if result:
            for item in result[0] or []:
                if not item or len(item) < 2:
                    continue
                text_info = item[1]
                if isinstance(text_info, (list, tuple)) and text_info:
                    text = str(text_info[0]).strip()
                    if text:
                        texts.append(text)
        return _bounded("\n".join(texts))
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("OCR extraction failed") from exc

def extract_readable_text(*, content: bytes, content_type: str, filename: str = "evidence") -> ExtractedText:
    ctype = content_type.lower().split(';', 1)[0].strip()
    if ctype not in SUPPORTED:
        raise ExtractionError("unsupported evidence type")
    if ctype in {"text/plain", "text/csv", "application/json"}:
        return ExtractedText(_bounded(content.decode("utf-8", errors="strict")), "native-text")
    if ctype == "application/pdf":
        try:
            reader = PdfReader(BytesIO(content))
            parts: list[str] = []
            total_chars = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                parts.append(text)
                total_chars += len(text)
                if total_chars > MAX_EXTRACTED_CHARS:
                    raise ExtractionError("extracted text exceeds configured limit")
            return ExtractedText(_bounded("\n".join(parts)), "pdf-text", pages=len(reader.pages))
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError("PDF text extraction failed") from exc
    return ExtractedText(_extract_image_text(content), "ocr")
