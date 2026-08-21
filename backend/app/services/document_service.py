import io
import re
import logging
import shutil
from typing import Optional
import pypdf
import docx
from app.config import settings

logger = logging.getLogger("quickmind.document_service")

# ---------------------------------------------------------------------------
# Runtime availability checks for optional OCR dependencies
# ---------------------------------------------------------------------------
try:
    import pytesseract
    from PIL import Image
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    _PYTESSERACT_AVAILABLE = False
    logger.warning(
        "pytesseract / Pillow not installed. OCR for images and scanned PDFs will be unavailable. "
        "Install with: pip install pytesseract Pillow"
    )

try:
    from pdf2image import convert_from_bytes
    _PDF2IMAGE_AVAILABLE = True
except ImportError:
    _PDF2IMAGE_AVAILABLE = False
    logger.warning(
        "pdf2image not installed. OCR for scanned PDFs will be unavailable. "
        "Install with: pip install pdf2image  (also requires system poppler)"
    )

# Check Tesseract binary at module load time
_TESSERACT_BINARY_AVAILABLE = False
if _PYTESSERACT_AVAILABLE:
    if shutil.which("tesseract") is not None:
        _TESSERACT_BINARY_AVAILABLE = True
    else:
        logger.warning(
            "Tesseract OCR binary not found on PATH. "
            "Install via: apt-get install tesseract-ocr  (Linux), "
            "brew install tesseract  (macOS), or download from https://github.com/UB-Mannheim/tesseract/wiki  (Windows)."
        )

# Minimum useful characters from native PDF extraction before triggering OCR
_MIN_NATIVE_PDF_CHARS = 20


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
        """Return True if this file will be processed via OCR (for UI messaging)."""
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
          .pdf              → pypdf native extraction; falls back to OCR if
                              fewer than _MIN_NATIVE_PDF_CHARS useful chars.
          .jpg/.jpeg/.png   → pytesseract OCR directly on the image
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
            return cls._extract_image(file_bytes)
        else:
            raise ValueError(f"Unsupported extension: {ext}")

    # ------------------------------------------------------------------
    # Text-based extractors (unchanged behaviour)
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
    # PDF extraction with transparent OCR fallback
    # ------------------------------------------------------------------

    @classmethod
    def _extract_pdf_with_ocr_fallback(cls, file_bytes: bytes) -> str:
        """
        Attempt native pypdf extraction.
        If the result is too short (< _MIN_NATIVE_PDF_CHARS), treat the PDF as
        a scanned document and run OCR via pdf2image + pytesseract.
        """
        # --- Native extraction attempt ---
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
            extracted = "\n\n".join(text_pages).strip()
        except Exception as e:
            extracted = ""
            logger.warning("pypdf extraction failed (%s). Attempting OCR fallback.", e)

        if len(extracted) >= _MIN_NATIVE_PDF_CHARS:
            return extracted  # Fast path: text-based PDF ✓

        # --- OCR fallback for scanned PDFs ---
        logger.info("Native PDF extraction yielded %d chars — triggering OCR.", len(extracted))
        return cls._ocr_pdf(file_bytes)

    @classmethod
    def _ocr_pdf(cls, file_bytes: bytes) -> str:
        """Render scanned PDF pages to images, then OCR each page."""
        cls._require_ocr()

        if not _PDF2IMAGE_AVAILABLE:
            raise ValueError(
                "Scanned PDF detected, but pdf2image is not installed. "
                "Install it with: pip install pdf2image  (and ensure system poppler is available)."
            )

        try:
            images = convert_from_bytes(file_bytes, dpi=200)
        except Exception as e:
            raise ValueError(
                "Could not render scanned PDF to images. "
                "Make sure poppler is installed on your system."
            ) from e

        page_texts = []
        for i, img in enumerate(images, start=1):
            raw = pytesseract.image_to_string(img, lang="eng")
            cleaned = cls._normalize_ocr_text(raw)
            if cleaned:
                page_texts.append(f"[Page {i}]\n{cleaned}")

        combined = "\n\n".join(page_texts).strip()
        if not combined:
            raise ValueError(
                "Could not extract readable text from this file. "
                "Please try a clearer scan or a text-based document."
            )
        return combined

    # ------------------------------------------------------------------
    # Image OCR extractor (.jpg / .jpeg / .png)
    # ------------------------------------------------------------------

    @classmethod
    def _extract_image(cls, file_bytes: bytes) -> str:
        """Run OCR directly on an image file."""
        cls._require_ocr()

        try:
            img = Image.open(io.BytesIO(file_bytes))
            # Convert to RGB if needed (e.g. RGBA, palette-mode PNG)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
        except Exception as e:
            raise ValueError(
                "Could not open image file. The file may be corrupted or in an unsupported format."
            ) from e

        try:
            raw = pytesseract.image_to_string(img, lang="eng")
        except Exception as e:
            raise ValueError(
                "OCR processing failed. Ensure Tesseract is installed correctly."
            ) from e

        result = cls._normalize_ocr_text(raw).strip()
        if not result:
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
        Clean raw OCR output:
        - Collapse runs of 3+ newlines into a paragraph break (double newline).
        - Strip trailing whitespace on every line.
        - Collapse internal spaces to single spaces.
        """
        # Normalize line endings
        text = raw.replace("\r\n", "\n").replace("\r", "\n")
        # Strip trailing whitespace per line
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        # Collapse 3+ consecutive blank lines to two
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse multiple spaces/tabs on a single line
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    @staticmethod
    def _require_ocr() -> None:
        """Raise a clear, user-friendly error if OCR prerequisites are missing."""
        if not _PYTESSERACT_AVAILABLE:
            raise ValueError(
                "OCR is not available: pytesseract or Pillow is not installed. "
                "Run: pip install pytesseract Pillow"
            )
        if not _TESSERACT_BINARY_AVAILABLE:
            raise ValueError(
                "OCR is not available: the Tesseract binary was not found on PATH. "
                "Install Tesseract: apt-get install tesseract-ocr  (Linux), "
                "brew install tesseract  (macOS), or download from "
                "https://github.com/UB-Mannheim/tesseract/wiki  (Windows)."
            )


document_service = DocumentService()
