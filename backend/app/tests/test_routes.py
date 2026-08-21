import sys
import io
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_service import document_service
from app.services.ai_service import ai_service

client = TestClient(app)


class TestRoutesAndServices(unittest.TestCase):
    def test_root_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("QuickMind", data["app"])

    def test_health_endpoint(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gemini_api_configured", data)

    def test_document_validation_file_type(self):
        with self.assertRaises(ValueError) as exc:
            document_service.validate_file("image.gif", 1000)
        self.assertIn("Unsupported file type", str(exc.exception))

    def test_document_image_types_accepted(self):
        # .jpg, .jpeg, .png should be accepted without raising
        for name in ["photo.jpg", "scan.jpeg", "screenshot.png"]:
            ext = document_service.validate_file(name, 500)
            self.assertIn(ext, {".jpg", ".jpeg", ".png"})

    def test_ocr_path_detection(self):
        self.assertTrue(document_service.is_ocr_path("scan.jpg"))
        self.assertTrue(document_service.is_ocr_path("scan.jpeg"))
        self.assertTrue(document_service.is_ocr_path("photo.png"))
        self.assertFalse(document_service.is_ocr_path("document.pdf"))
        self.assertFalse(document_service.is_ocr_path("notes.docx"))
        self.assertFalse(document_service.is_ocr_path("data.txt"))

    def test_document_validation_text_length(self):
        with self.assertRaises(ValueError) as exc:
            document_service.validate_text_length("a" * 10001)
        self.assertIn("exceeds the limit", str(exc.exception))

    def test_txt_extraction(self):
        text_bytes = "Hello QuickMind test".encode("utf-8")
        extracted = document_service.extract_text(text_bytes, "test.txt")
        self.assertEqual(extracted, "Hello QuickMind test")

    def test_document_magic_byte_validation(self):
        # Mislabelled file (txt content with .pdf extension)
        fake_pdf = b"Plain text disguised as PDF"
        with self.assertRaises(ValueError) as exc:
            document_service.extract_text(fake_pdf, "fake.pdf")
        self.assertIn("doesn't appear to be a valid .pdf file", str(exc.exception))

        # Valid magic bytes
        document_service.validate_content_signature(b"%PDF-1.4 sample", ".pdf")
        document_service.validate_content_signature(b"PK\x03\x04 docx data", ".docx")
        document_service.validate_content_signature(b"\xff\xd8\xff jpeg data", ".jpg")
        document_service.validate_content_signature(b"\x89PNG\r\n data", ".png")

    def test_ai_vision_image_extraction(self):
        fake_png = b"\x89PNG\r\n\x1a\nfake_image_bytes"
        with patch.object(ai_service, "extract_text_from_image", return_value="Sample text from vision model"):
            res = document_service.extract_text(fake_png, "sample.png")
            self.assertEqual(res, "Sample text from vision model")

    def test_document_extract_unauthenticated(self):
        response = client.post("/api/document/extract")
        self.assertEqual(response.status_code, 401)

    def test_summarize_unauthenticated(self):
        response = client.post("/api/summarize", json={"text": "", "length": "short"})
        self.assertEqual(response.status_code, 401)

    def test_ask_unauthenticated(self):
        response = client.post("/api/ask", json={"question": ""})
        self.assertEqual(response.status_code, 401)

    def test_generate_unauthenticated(self):
        response = client.post("/api/generate", json={"topic": ""})
        self.assertEqual(response.status_code, 401)

    def test_analyze_unauthenticated(self):
        response = client.post("/api/analyze", json={"text": ""})
        self.assertEqual(response.status_code, 401)

    def test_provider_configuration_check(self):
        self.assertIsInstance(ai_service._is_provider_configured("gemini"), bool)
        self.assertFalse(ai_service._is_provider_configured("unknown_provider"))

    def test_continuation_stitching(self):
        calls = []

        def mock_dispatch(prompt, provider, is_json=False):
            calls.append((prompt, provider))
            if len(calls) == 1:
                return {"text": "Part 1 of answer", "finish_reason": "MAX_TOKENS"}
            elif len(calls) == 2:
                return {"text": "Part 2 of answer.", "finish_reason": "STOP"}

        with patch.object(ai_service, "_dispatch_provider", side_effect=mock_dispatch):
            result = ai_service._generate_with_continuation("Write long article", provider="gemini")
            self.assertEqual(result, "Part 1 of answer Part 2 of answer.")
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][1], "gemini")
            self.assertEqual(calls[1][1], "gemini")

    def test_fallback_mechanism(self):
        providers_called = []

        def mock_continuation(prompt, provider, is_json=False):
            providers_called.append(provider)
            if provider == "gemini":
                raise ValueError("Gemini connection error 500")
            return "Response from Groq"

        with patch.object(ai_service, "_is_provider_configured", return_value=True), \
             patch.object(ai_service, "_generate_with_continuation", side_effect=mock_continuation):
            result = ai_service._generate_with_fallback("Test prompt")
            self.assertEqual(result, "Response from Groq")
            self.assertEqual(providers_called, ["gemini", "groq"])

    # ------------------------------------------------------------------
    # OCR Pipeline Tests
    # ------------------------------------------------------------------

    def _make_minimal_text_pdf(self) -> bytes:
        """Create a minimal valid text-based PDF in memory (no external library needed)."""
        # Minimal PDF that contains selectable text on page 1
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj
2 0 obj<</Type /Pages /Kids [3 0 R] /Count 1>>endobj
3 0 obj<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Contents 4 0 R /Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>
stream
BT /F1 12 Tf 100 700 Td (Hello PDF Text) Tj ET
endstream
endobj
5 0 obj<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000360 00000 n
trailer<</Size 6 /Root 1 0 R>>
startxref
441
%%EOF"""
        return pdf_content

    def test_text_pdf_extraction(self):
        """Text-based PDFs must be extracted natively without triggering OCR."""
        import pymupdf as fitz
        # Create a real in-memory PDF with selectable text using PyMuPDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is a normal text-based PDF for QuickMind.")
        pdf_bytes = doc.tobytes()
        doc.close()

        # AI Vision should NOT be called for a text-based PDF
        with patch.object(document_service, '_ocr_image_bytes') as mock_ocr:
            result = document_service.extract_text(pdf_bytes, "text_sample.pdf")
            mock_ocr.assert_not_called()
        self.assertIn("QuickMind", result)
        self.assertGreater(len(result.strip()), 0)

    def test_scanned_pdf_tesseract_ocr(self):
        """Scanned PDFs (image pages) must trigger OCR and return extracted text."""
        import pymupdf as fitz
        # Create a blank PDF with no text (simulates a scanned/image-based PDF)
        doc = fitz.open()
        doc.new_page()  # Blank page — no native text
        pdf_bytes = doc.tobytes()
        doc.close()

        expected_ocr_text = "Handwritten notes OCR extracted text"
        # Mock _ocr_image_bytes to simulate Tesseract returning text
        with patch.object(document_service, '_ocr_image_bytes', return_value=expected_ocr_text) as mock_ocr:
            result = document_service.extract_text(pdf_bytes, "scanned_notes.pdf")
            mock_ocr.assert_called_once()  # OCR must be attempted for the blank page
        self.assertIn(expected_ocr_text, result)
        self.assertIn("[Page 1]", result)

    def test_multipage_scanned_pdf_ocr(self):
        """Multi-page scanned PDFs must have OCR run on every blank page."""
        import pymupdf as fitz
        doc = fitz.open()
        for _ in range(3):  # 3 blank pages
            doc.new_page()
        pdf_bytes = doc.tobytes()
        doc.close()

        page_responses = ["Page one content", "Page two content", "Page three content"]
        call_count = [0]

        def mock_ocr_side_effect(img_bytes, page_num=0):
            idx = call_count[0]
            call_count[0] += 1
            return page_responses[idx] if idx < len(page_responses) else ""

        with patch.object(document_service, '_ocr_image_bytes', side_effect=mock_ocr_side_effect):
            result = document_service.extract_text(pdf_bytes, "multipage_scan.pdf")

        self.assertEqual(call_count[0], 3, "OCR must be called once per blank page")
        for page_text in page_responses:
            self.assertIn(page_text, result)

    def test_empty_scanned_pdf_raises_error(self):
        """A PDF where OCR produces no text must raise a descriptive ValueError."""
        import pymupdf as fitz
        doc = fitz.open()
        doc.new_page()  # Blank page — no native text, no OCR output
        pdf_bytes = doc.tobytes()
        doc.close()

        # Mock _ocr_image_bytes to return empty string (nothing legible)
        with patch.object(document_service, '_ocr_image_bytes', return_value=""):
            with self.assertRaises(ValueError) as exc:
                document_service.extract_text(pdf_bytes, "empty_scan.pdf")
        self.assertIn("Could not extract text from this scanned PDF", str(exc.exception))

    def test_invalid_pdf_raises_error(self):
        """Mislabelled or corrupted PDF bytes must raise a descriptive ValueError."""
        fake_pdf = b"%PDF-corrupted data that cannot be parsed"
        with self.assertRaises(ValueError):
            document_service.extract_text(fake_pdf, "corrupt.pdf")


if __name__ == "__main__":
    unittest.main()

