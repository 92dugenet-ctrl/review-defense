"""V6.16 bounded evidence text/OCR extraction.

This module converts supported evidence binaries into readable text for the existing
V6.6 fact-suggestion engine. It never verifies facts and never performs external
network I/O. OCR subprocesses are invoked without a shell and are bounded by timeout.
PDF text extraction uses the bundled pure-Python pypdf parser so the managed Python
runtime does not depend on a system-level pdftotext binary.
"""
from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import os
import subprocess
import tempfile

from pypdf import PdfReader

MAX_PROCESS_SECONDS = 15
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
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[ctype]
    with tempfile.TemporaryDirectory(prefix="rd-ocr-") as td:
        path = Path(td) / ("input" + suffix)
        path.write_bytes(content)
        proc = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", "eng+fra"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=MAX_PROCESS_SECONDS, check=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
        if proc.returncode != 0:
            raise ExtractionError("OCR extraction failed")
        return ExtractedText(_bounded(proc.stdout.decode("utf-8", errors="replace")), "ocr")
