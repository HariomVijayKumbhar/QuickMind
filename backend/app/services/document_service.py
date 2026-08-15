import io
from typing import Tuple
import pypdf
import docx
from app.config import settings

class DocumentService:
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
        """Validate filename extension and file size."""
        if size > settings.MAX_FILE_SIZE_BYTES:
            max_mb = settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise ValueError(f"File size exceeds maximum limit of {max_mb} MB.")
            
        ext = filename.lower().split('.')[-1] if '.' in filename else ""
        ext_with_dot = f".{ext}"
        
        if ext_with_dot not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext_with_dot}'. "
                f"Allowed types are: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
            )
            
        return ext_with_dot

    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str) -> str:
        """Extract text from file bytes based on file extension."""
        ext = cls.validate_file(filename, len(file_bytes))
        
        if ext == ".txt":
            return cls._extract_txt(file_bytes)
        elif ext == ".pdf":
            return cls._extract_pdf(file_bytes)
        elif ext == ".docx":
            return cls._extract_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported extension: {ext}")

    @staticmethod
    def _extract_txt(file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1")
            except Exception as e:
                raise ValueError("Could not decode text file with UTF-8 or Latin-1 encoding.") from e

    @staticmethod
    def _extract_pdf(file_bytes: bytes) -> str:
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_pages = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
            extracted = "\n\n".join(text_pages).strip()
            if not extracted:
                raise ValueError("PDF file appears to be empty or contains scanned images without extractable text.")
            return extracted
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise ValueError("Failed to parse PDF document. The file may be corrupt or encrypted.") from e

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
            raise ValueError("Failed to parse DOCX document. File might be corrupted.") from e

document_service = DocumentService()
