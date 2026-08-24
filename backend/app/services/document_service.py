import io
import os
import re
import sys
import logging
from typing import Optional
import pymupdf as fitz
import docx
from PIL import Image
from app.config import settings
from app.services.ai_service import ai_service

logger = logging.getLogger("quickmind.document_service")

# Minimum useful characters from native PDF text extraction before treating as scanned
_MIN_NATIVE_PDF_CHARS = 20

# ---------------------------------------------------------------------------
# Tesseract OCR setup — auto-detect on Windows, fall through to PATH on Linux
# ---------------------------------------------------------------------------
try:
    import pytesseract  # type: ignore

    # On Windows, Tesseract is typically installed to a fixed location.
    # On Linux (Render / Ubuntu), it is on PATH via apt-get install tesseract-ocr.
    # Priority: env-var override → known Windows path → system PATH
    _tesseract_cmd = os.getenv("TESSERACT_CMD")  # explicit override always wins
    if not _tesseract_cmd and sys.platform.startswith("win"):
        _win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.isfile(_win_path):
            _tesseract_cmd = _win_path

    if _tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd

    # Verify Tesseract is actually callable at startup
    pytesseract.get_tesseract_version()
    _TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR detected and available (cmd=%s).", _tesseract_cmd or "system PATH")
except Exception as _tess_err:
    _TESSERACT_AVAILABLE = False
    pytesseract = None  # type: ignore
    logger.warning(
        "Tesseract OCR not available (%s). Scanned PDFs will fall back to AI Vision.", _tess_err
    )


class DocumentService:

    # ------------------------------------------------------------------
    # Public validators
    # ------------------------------------------------------------------

    @staticmethod
    def validate_text_length(text: str) -> None:
        """Validate pasted text length."""
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty.")
        if len(text) > settings.MAX_TEXT_LENGTH:
            raise ValueError(
                f"Pasted text exceeds the limit of {settings.MAX_TEXT_LENGTH:,} characters "
                f"(current length: {len(text):,} characters)."
            )

    @staticmethod
    def validate_file(filename: str, size: int) -> str:
        """Validate filename extension and file size. Returns the extension string."""
        if size > settings.MAX_FILE_SIZE_BYTES:
            max_mb = settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise ValueError(f"File size exceeds maximum limit of {max_mb} MB.")

        ext = filename.lower().split(".")[-1] if "." in filename else ""
        ext_with_dot = f".{ext}"

        if ext_with_dot not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext_with_dot}'. "
                f"Allowed types are: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
            )

        return ext_with_dot

    @staticmethod
    def validate_content_signature(file_bytes: bytes, ext: str) -> None:
        """
        Validate file content using magic byte signatures before attempting full extraction.
        Prevents mislabeled files (e.g. .txt renamed to .pdf) from failing deep in parsers.
        """
        signatures = {
            ".pdf": (b"%PDF-",),
            ".docx": (b"PK",),
            ".jpg": (b"\xff\xd8\xff",),
            ".jpeg": (b"\xff\xd8\xff",),
            ".png": (b"\x89PNG",),
        }
        expected = signatures.get(ext)
        if expected:
            if not any(file_bytes.startswith(sig) for sig in expected):
                raise ValueError(f"This file doesn't appear to be a valid {ext} file.")

    @classmethod
    def is_ocr_path(cls, filename: str) -> bool:
        """Return True if this file will be processed via AI Vision / OCR (for UI messaging)."""
        ext = ("." + filename.lower().split(".")[-1]) if "." in filename else ""
        return ext in {".jpg", ".jpeg", ".png"}

    # ------------------------------------------------------------------
    # Main extraction entry point — same signature as before
    # ------------------------------------------------------------------

    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str) -> str:
        """
        Extract text from file bytes.

        Routing:
          .txt              → UTF-8 / Latin-1 decode
          .docx             → python-docx paragraph extraction
          .pdf              → PyMuPDF native text; auto-falls back to Tesseract OCR
                              (then AI Vision) for scanned/image pages
          .jpg/.jpeg/.png   → AI Vision transcription directly on image bytes
        """
        ext = cls.validate_file(filename, len(file_bytes))
        cls.validate_content_signature(file_bytes, ext)

        if ext == ".txt":
            return cls._extract_txt(file_bytes)
        elif ext == ".docx":
            return cls._extract_docx(file_bytes)
        elif ext == ".pdf":
            return cls._extract_pdf_with_ocr_fallback(file_bytes)
        elif ext in {".jpg", ".jpeg", ".png"}:
            return cls._extract_image(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported extension: {ext}")

    # ------------------------------------------------------------------
    # Text-based extractors
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_txt(file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1")
            except Exception as e:
                raise ValueError(
                    "Could not decode text file with UTF-8 or Latin-1 encoding."
                ) from e

    @staticmethod
    def _extract_docx(file_bytes: bytes) -> str:
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            full_text = [p.text for p in doc.paragraphs if p.text.strip()]
            extracted = "\n".join(full_text).strip()
            if not extracted:
                raise ValueError("DOCX document appears to be empty.")
            return extracted
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise ValueError(
                "Failed to parse DOCX document. File might be corrupted."
            ) from e

    # ------------------------------------------------------------------
    # PDF extraction: native text → Tesseract OCR → AI Vision fallback
    # ------------------------------------------------------------------

    @classmethod
    def _extract_pdf_with_ocr_fallback(cls, file_bytes: bytes) -> str:
        """
        Open PDF with PyMuPDF (fitz).

        Pipeline per page:
          1. Try native text extraction (page.get_text()).
          2. If page has sufficient native text (>= _MIN_NATIVE_PDF_CHARS), use it directly.
          3. If page is scanned/image-based (empty or near-empty text):
             a. Render the page to a PNG image at 200 DPI.
             b. Try Tesseract OCR via pytesseract (if available).
             c. If Tesseract unavailable or fails, fall back to AI Vision.
          4. Combine all page texts in order.
          5. If the combined result is empty, raise a descriptive error.

        No API key or internet connection is required for Tesseract OCR.
        AI Vision fallback uses the configured Gemini/OpenAI key.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(
                "Failed to parse PDF document. File might be corrupted."
            ) from e

        total_pages = len(doc)
        max_ocr_pages = getattr(settings, "MAX_VISION_PAGES", 20)

        page_texts: list[str] = []
        text_page_count = 0
        ocr_page_count = 0
        truncated = False

        for page_num in range(total_pages):
            page = doc[page_num]
            native_text = page.get_text().strip()

            if len(native_text) >= _MIN_NATIVE_PDF_CHARS:
                # Text-based page — use native extraction unchanged
                page_texts.append(native_text)
                text_page_count += 1
            else:
                # Scanned / image-based page — needs OCR
                if ocr_page_count >= max_ocr_pages:
                    truncated = True
                    break

                # Render page to PNG at 200 DPI
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")

                ocr_text = cls._ocr_image_bytes(img_bytes, page_num + 1)
                if ocr_text:
                    page_texts.append(f"[Page {page_num + 1}]\n{ocr_text}")
                    ocr_page_count += 1

        logger.info(
            "PDF extraction complete: %d native-text pages, %d OCR pages (total %d pages).",
            text_page_count, ocr_page_count, total_pages,
        )

        combined = "\n\n".join(page_texts).strip()
        if not combined:
            raise ValueError(
                "Could not extract text from this scanned PDF. "
                "Please try a clearer document."
            )

        if truncated:
            combined += (
                f"\n\n[Note: Document exceeded the maximum of {max_ocr_pages} "
                "OCR pages and was truncated.]"
            )

        return combined

    @classmethod
    def _ocr_image_bytes(cls, img_bytes: bytes, page_num: int = 0) -> str:
        """
        Run OCR on raw PNG/JPEG bytes.

        Strategy:
          1. Tesseract OCR (local, free, no API key needed) — tried first.
          2. AI Vision (Gemini / OpenAI) — fallback if Tesseract is unavailable or fails.

        Returns cleaned OCR text, or empty string if nothing legible was found.
        """
        # --- Tesseract path ---
        if _TESSERACT_AVAILABLE and pytesseract is not None:
            try:
                pil_img = Image.open(io.BytesIO(img_bytes))
                raw = pytesseract.image_to_string(pil_img, lang="eng")
                cleaned = cls._normalize_ocr_text(raw)
                if cleaned:
                    logger.debug("Tesseract OCR succeeded for page %d.", page_num)
                    return cleaned
                # Tesseract returned blank — still try AI Vision below
                logger.debug("Tesseract returned no text for page %d; trying AI Vision.", page_num)
            except Exception as e:
                logger.warning(
                    "Tesseract OCR failed for page %d (%s); trying AI Vision.", page_num, e
                )

        # --- AI Vision fallback ---
        try:
            vision_raw = ai_service.extract_text_from_image(img_bytes, mime_type="image/png")
            cleaned = cls._normalize_ocr_text(vision_raw)
            if cleaned and cleaned != "NO_TEXT_FOUND":
                logger.debug("AI Vision OCR succeeded for page %d.", page_num)
                return cleaned
        except Exception as e:
            logger.warning("AI Vision extraction failed for PDF page %d: %s", page_num, e)

        return ""

    # ------------------------------------------------------------------
    # Image AI Vision extractor (.jpg / .jpeg / .png)
    # ------------------------------------------------------------------

    @classmethod
    def _extract_image(cls, file_bytes: bytes, filename: str) -> str:
        """Run AI Vision transcription directly on image bytes."""
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        mime_type = "image/png" if ext == "png" else "image/jpeg"

        try:
            raw = ai_service.extract_text_from_image(file_bytes, mime_type=mime_type)
        except Exception as e:
            raise ValueError(
                f"Image text extraction failed: {str(e)}"
            ) from e

        result = cls._normalize_ocr_text(raw).strip()
        if not result or result == "NO_TEXT_FOUND":
            raise ValueError(
                "Could not extract readable text from this file. "
                "Please try a clearer scan or a text-based document."
            )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_ocr_text(raw: str) -> str:
        """
        Clean raw transcription output:
        - Normalize line endings.
        - Strip trailing whitespace per line.
        - Collapse 3+ consecutive blank lines to two.
        - Collapse multiple spaces/tabs on a single line.
        """
        text = raw.replace("\r\n", "\n").replace("\r", "\n")
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()


document_service = DocumentService()
