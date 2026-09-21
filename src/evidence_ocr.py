"""V6.16 bounded evidence text/OCR extraction.

This module converts supported evidence binaries into readable text for the existing
V6.6 fact-suggestion engine. It never verifies facts and never performs external
network I/O. Subprocesses are invoked without a shell and are bounded by timeout.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import tempfile

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
        proc = subprocess.run(
            ["pdftotext", "-layout", "-", "-"], input=content, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=MAX_PROCESS_SECONDS, check=False
        )
        if proc.returncode != 0:
            raise ExtractionError("PDF text extraction failed")
        return ExtractedText(_bounded(proc.stdout.decode("utf-8", errors="replace")), "pdf-text")
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
