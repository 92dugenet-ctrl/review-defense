# Review Defense V6.16 — Evidence Text/OCR Pipeline

V6.16 extends V6.6 fact extraction to readable PDF evidence and image evidence using bounded local extraction. PDF text is extracted with `pdftotext`; images use local Tesseract OCR. Extracted text is immediately fed through the existing deterministic suggestion engine.

## Implemented
- `src/evidence_ocr.py` provides bounded PDF and image text extraction.
- `POST /v1/cases/{case_id}/extract-facts` now supports PDF and image evidence in addition to native text.
- SHA-256 integrity is verified before any extraction.
- Extraction uses fixed subprocess arguments, no shell, a 15-second timeout and a 500,000-character output limit.
- Extraction provenance (`native-text`, `pdf-text`, `ocr`) is included with each suggestion.
- Extraction and extraction failures are audit events.
- All extracted facts remain suggestions and remain `verified=false` until the existing human verification flow is used.

## Security invariants
- Tenant isolation and RBAC remain server-side.
- No external network I/O is introduced.
- OCR/PDF parsing cannot directly create verified facts or decisions.
- Evidence SHA-256 integrity is checked before parsing.
- Google deletion/reporting/reply APIs are not called.
- Existing human approval gates are unchanged.

## Limitation
OCR quality depends on the locally installed Tesseract language data and image quality. Scanned PDFs are not rasterized/OCRed in V6.16; only their embedded text layer is extracted. OCR and PDF parsing are synchronous and bounded by a 15-second process timeout.
