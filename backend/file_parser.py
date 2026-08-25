import os
import tempfile
from typing import Optional

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _allowed(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


def _read_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


def _read_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            texts = []
            with pdfplumber.open(tmp.name) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        texts.append(t)
            return "\n".join(texts)
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF: {e}")


def _read_docx(file_bytes: bytes) -> str:
    try:
        import docx

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=True) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            doc = docx.Document(tmp.name)
            return "\n".join(p.text for p in doc.paragraphs if p.text)
    except Exception as e:
        raise RuntimeError(f"Failed to parse DOCX: {e}")


def _read_image(file_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            image = Image.open(tmp.name)
            return pytesseract.image_to_string(image)
    except Exception as e:
        raise RuntimeError(f"Failed to read image (OCR): {e}")


def extract_text(filename: str, content: bytes) -> str:
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 10MB limit")
    if not _allowed(filename):
        raise ValueError(f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext == ".txt":
        return _read_txt(content)
    if ext == ".pdf":
        return _read_pdf(content)
    if ext == ".docx":
        return _read_docx(content)
    if ext in (".png", ".jpg", ".jpeg"):
        return _read_image(content)

    raise ValueError(f"Unsupported file type: {ext}")
