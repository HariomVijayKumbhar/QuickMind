import io
import re
import logging
from typing import Optional
import pymupdf as fitz
import docx
from app.config import settings
from app.services.ai_service import ai_service

logger = logging.getLogger("quickmind.document_service")

# Minimum useful characters from native PDF page extraction before triggering AI Vision fallback
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
          .pdf              → PyMuPDF (fitz) page extraction; falls back to AI Vision
                              per scanned page if page text < _MIN_NATIVE_PDF_CHARS.
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
    # PDF extraction using PyMuPDF (fitz) with AI Vision fallback
    # ------------------------------------------------------------------

    @classmethod
    def _extract_pdf_with_ocr_fallback(cls, file_bytes: bytes) -> str:
        """
        Open PDF with PyMuPDF (fitz).
        First attempt native text extraction per page (page.get_text()).
        If a page's extracted text is empty or near-empty (< _MIN_NATIVE_PDF_CHARS),
        render that page to PNG (200 DPI) and send to AI Vision service.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(
                "Failed to parse PDF document. File might be corrupted."
            ) from e

        total_pages = len(doc)
        max_vision_pages = getattr(settings, "MAX_VISION_PAGES", 20)

        page_texts = []
        text_page_count = 0
        vision_page_count = 0
        truncated_for_vision = False

        for page_num in range(total_pages):
            page = doc[page_num]
            native_text = page.get_text().strip()

            if len(native_text) >= _MIN_NATIVE_PDF_CHARS:
                page_texts.append(native_text)
                text_page_count += 1
            else:
                # Scanned or image-based page
                if vision_page_count >= max_vision_pages:
                    truncated_for_vision = True
                    break

                try:
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    vision_raw = ai_service.extract_text_from_image(img_bytes, mime_type="image/png")
                    cleaned = cls._normalize_ocr_text(vision_raw)
                    if cleaned and cleaned != "NO_TEXT_FOUND":
                        page_texts.append(f"[Page {page_num + 1}]\n{cleaned}")
                        vision_page_count += 1
                except Exception as e:
                    logger.warning("AI Vision extraction failed for PDF page %d: %s", page_num + 1, e)

        logger.info(
            "PDF extraction finished: %d native text pages, %d vision pages (total %d pages).",
            text_page_count, vision_page_count, total_pages
        )

        combined = "\n\n".join(page_texts).strip()
        if not combined:
            raise ValueError(
                "Could not extract readable text from this file. "
                "Please try a clearer scan or a text-based document."
            )

        if truncated_for_vision:
            combined += f"\n\n[Note: Document exceeded maximum limit of {max_vision_pages} pages for AI vision extraction and was truncated.]"

        return combined

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
                "Could not extract readable text from this file. "
                "Please try a clearer scan or a text-based document."
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

