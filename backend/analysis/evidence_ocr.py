"""V6.16 bounded evidence text/OCR extraction.

This module converts supported evidence binaries into readable text for the existing
V6.6 fact-suggestion engine. It never verifies facts and never performs external
network I/O. Image OCR uses an optional system tesseract binary; the application
does not depend on OCR being installed at startup.
"""
from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
import shutil
import subprocess

from PIL import Image
from pypdf import PdfReader

MAX_EXTRACTED_CHARS = 500_000
MAX_OCR_SECONDS = 15
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

def _extract_image_text(content: bytes) -> str:
    if shutil.which("tesseract") is None:
        raise ExtractionError("OCR unavailable: tesseract is not installed")
    try:
        image = Image.open(BytesIO(content)).convert("RGB")
        png_buffer = BytesIO()
        image.save(png_buffer, format="PNG")
        completed = subprocess.run(
            ["tesseract", "stdin", "stdout", "--psm", "6"],
            input=png_buffer.getvalue(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=MAX_OCR_SECONDS,
            check=False,
        )
        if completed.returncode != 0:
            raise ExtractionError("OCR extraction failed")
        return _bounded(completed.stdout.decode("utf-8", errors="strict").strip())
    except ExtractionError:
        raise
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError("OCR extraction timed out") from exc
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
