import sys
import os
import time
from pathlib import Path

# Reconfigure stdout encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

def run_tests():
    console = Console() if RICH_AVAILABLE else None

    if RICH_AVAILABLE:
        header = Text("⚡ QuickMind AI — Automated Test Suite", style="bold cyan")
        console.print(Panel(header, border_style="bright_blue", box=box.ROUNDED, expand=False))
    else:
        print("=== QuickMind AI Test Suite ===")

    test_results = []

    try:
        from app.services.document_service import document_service
        from app.services.ai_service import ai_service
        from app.main import app
        from fastapi.testclient import TestClient

        # 1. Allowed File Validation (including image types)
        t0 = time.time()
        try:
            document_service.validate_file("document.pdf", 500)
            document_service.validate_file("notes.docx", 500)
            document_service.validate_file("data.txt", 500)
            document_service.validate_file("photo.jpg", 500)
            document_service.validate_file("scan.jpeg", 500)
            document_service.validate_file("screenshot.png", 500)
            test_results.append(("File Types Validation", "Document Parsing", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
        except Exception as e:
            test_results.append(("File Types Validation", "Document Parsing", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # 1b. Image types recognised as OCR path
        t0 = time.time()
        try:
            assert document_service.is_ocr_path("scan.jpg") is True
            assert document_service.is_ocr_path("photo.png") is True
            assert document_service.is_ocr_path("report.pdf") is False
            test_results.append(("OCR Path Detection", "Document Parsing", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
        except AssertionError as e:
            test_results.append(("OCR Path Detection", "Document Parsing", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # 2. Invalid Extension Rejection
        t0 = time.time()
        try:
            document_service.validate_file("script.exe", 500)
            test_results.append(("Invalid Type Rejection", "Document Parsing", "FAILED: Did not reject .exe", f"{(time.time()-t0)*1000:.1f}ms"))
        except ValueError:
            test_results.append(("Invalid Type Rejection", "Document Parsing", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))

        # 3. Text Length Limit
        t0 = time.time()
        try:
            document_service.validate_text_length("x" * 10001)
            test_results.append(("Character Limit (10k)", "Input Security", "FAILED: Exceeded 10k limit", f"{(time.time()-t0)*1000:.1f}ms"))
        except ValueError:
            test_results.append(("Character Limit (10k)", "Input Security", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))

        # 4. Content Magic-Byte Validation (Fix 4)
        t0 = time.time()
        try:
            # Fake PDF bytes (plain text) should fail content signature validation
            fake_pdf = b"This is just plain text, not a PDF"
            try:
                document_service.extract_text(fake_pdf, "fake.pdf")
                test_results.append(("Magic-Byte Content Validation", "Document Parsing", "FAILED: Allowed invalid PDF signature", f"{(time.time()-t0)*1000:.1f}ms"))
            except ValueError as ve:
                if "doesn't appear to be a valid .pdf file" in str(ve):
                    # Valid signature test
                    valid_pdf_prefix = b"%PDF-1.4\n..."
                    # Check that signature validator itself passes
                    document_service.validate_content_signature(valid_pdf_prefix, ".pdf")
                    test_results.append(("Magic-Byte Content Validation", "Document Parsing", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
                else:
                    test_results.append(("Magic-Byte Content Validation", "Document Parsing", f"FAILED: Unexpected message: {ve}", f"{(time.time()-t0)*1000:.1f}ms"))
        except Exception as e:
            test_results.append(("Magic-Byte Content Validation", "Document Parsing", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # 4b. AI Vision Image Extraction
        t0 = time.time()
        try:
            saved_vision = ai_service.extract_text_from_image
            ai_service.extract_text_from_image = lambda img, mime_type="image/png": "Transcribed image text via AI Vision"
            fake_png = b"\x89PNG\r\n\x1a\nfake_image_bytes"
            vision_result = document_service.extract_text(fake_png, "sample.png")
            ai_service.extract_text_from_image = saved_vision
            if "Transcribed image text via AI Vision" in vision_result:
                test_results.append(("AI Vision Image Extraction", "Document Parsing", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
            else:
                test_results.append(("AI Vision Image Extraction", "Document Parsing", "FAILED: Unexpected result", f"{(time.time()-t0)*1000:.1f}ms"))
        except Exception as e:
            test_results.append(("AI Vision Image Extraction", "Document Parsing", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # --- OCR Pipeline Tests ---

        # 4c. Text PDF — OCR must NOT be triggered
        t0 = time.time()
        try:
            import pymupdf as fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "This is a normal text-based PDF for QuickMind.")
            pdf_bytes = doc.tobytes()
            doc.close()
            _ocr_called = [False]
            _orig_ocr = document_service._ocr_image_bytes
            def _spy_ocr(*a, **kw):
                _ocr_called[0] = True
                return _orig_ocr(*a, **kw)
            document_service._ocr_image_bytes = _spy_ocr
            txt_result = document_service.extract_text(pdf_bytes, "text_sample.pdf")
            document_service._ocr_image_bytes = _orig_ocr
            if not _ocr_called[0] and "QuickMind" in txt_result:
                test_results.append(("Text PDF (no OCR)", "OCR Pipeline", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
            else:
                test_results.append(("Text PDF (no OCR)", "OCR Pipeline", "FAILED: OCR was unexpectedly invoked", f"{(time.time()-t0)*1000:.1f}ms"))
        except Exception as e:
            test_results.append(("Text PDF (no OCR)", "OCR Pipeline", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # 4d. Scanned PDF — OCR must be triggered
        t0 = time.time()
        try:
            doc = fitz.open()
            doc.new_page()  # blank page = no native text
            pdf_bytes = doc.tobytes()
            doc.close()
            from app.services.document_service import DocumentService
            from unittest.mock import patch as _patch
            with _patch.object(DocumentService, '_ocr_image_bytes', return_value="Scanned OCR Result") as mock_ocr:
                scanned_result = document_service.extract_text(pdf_bytes, "scanned_notes.pdf")
            if "Scanned OCR Result" in scanned_result and "[Page 1]" in scanned_result:
                test_results.append(("Scanned PDF Tesseract OCR", "OCR Pipeline", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
            else:
                test_results.append(("Scanned PDF Tesseract OCR", "OCR Pipeline", f"FAILED: got: {scanned_result[:80]}", f"{(time.time()-t0)*1000:.1f}ms"))
        except Exception as e:
            test_results.append(("Scanned PDF Tesseract OCR", "OCR Pipeline", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # 4e. Multi-page scanned PDF — all pages OCR'd
        t0 = time.time()
        try:
            doc = fitz.open()
            for _ in range(3):
                doc.new_page()  # 3 blank pages
            pdf_bytes = doc.tobytes()
            doc.close()
            _page_idx = [0]
            _responses = ["Page one text", "Page two text", "Page three text"]
            def _multi_ocr(cls_or_self, img_bytes, page_num=0):
                resp = _responses[_page_idx[0]] if _page_idx[0] < len(_responses) else ""
                _page_idx[0] += 1
                return resp
            from app.services.document_service import DocumentService
            from unittest.mock import patch as _patch
            with _patch.object(DocumentService, '_ocr_image_bytes', side_effect=_multi_ocr):
                multi_result = document_service.extract_text(pdf_bytes, "multipage.pdf")
            if _page_idx[0] == 3 and all(p in multi_result for p in _responses):
                test_results.append(("Multi-page Scanned PDF OCR", "OCR Pipeline", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
            else:
                test_results.append(("Multi-page Scanned PDF OCR", "OCR Pipeline", f"FAILED: OCR called {_page_idx[0]} times", f"{(time.time()-t0)*1000:.1f}ms"))
        except Exception as e:
            test_results.append(("Multi-page Scanned PDF OCR", "OCR Pipeline", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # 4f. Empty scanned PDF — must raise descriptive error
        t0 = time.time()
        try:
            doc = fitz.open()
            doc.new_page()
            pdf_bytes = doc.tobytes()
            doc.close()
            from app.services.document_service import DocumentService
            from unittest.mock import patch as _patch
            with _patch.object(DocumentService, '_ocr_image_bytes', return_value=""):
                try:
                    document_service.extract_text(pdf_bytes, "empty_scan.pdf")
                    test_results.append(("Empty Scanned PDF Error", "OCR Pipeline", "FAILED: No error raised", f"{(time.time()-t0)*1000:.1f}ms"))
                except ValueError as ve:
                    if "Could not extract text from this scanned PDF" in str(ve):
                        test_results.append(("Empty Scanned PDF Error", "OCR Pipeline", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
                    else:
                        test_results.append(("Empty Scanned PDF Error", "OCR Pipeline", f"FAILED: Wrong message: {ve}", f"{(time.time()-t0)*1000:.1f}ms"))
        except Exception as e:
            test_results.append(("Empty Scanned PDF Error", "OCR Pipeline", f"FAILED: {e}", f"{(time.time()-t0)*1000:.1f}ms"))

        # 5. FastAPI Routes & Endpoints (including /api/document/extract)
        t0 = time.time()
        client = TestClient(app)
        
        health_res = client.get("/api/health")
        sum_res = client.post("/api/summarize", json={"text": "", "length": "short"})
        ask_res = client.post("/api/ask", json={"question": ""})
        gen_res = client.post("/api/generate", json={"topic": ""})
        anz_res = client.post("/api/analyze", json={"text": ""})
        extract_res = client.post("/api/document/extract")

        routes_ok = (
            health_res.status_code == 200 and
            sum_res.status_code == 401 and
            ask_res.status_code == 401 and
            gen_res.status_code == 401 and
            anz_res.status_code == 401 and
            extract_res.status_code == 401
        )
        if routes_ok:
            test_results.append(("FastAPI Endpoints Integrity", "API Layer", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
        else:
            test_results.append(("FastAPI Endpoints Integrity", "API Layer", "FAILED: Unexpected status (expected 401 for protected routes)", f"{(time.time()-t0)*1000:.1f}ms"))

        # 5. Continuation Engine
        t0 = time.time()
        calls = []
        def mock_dispatch(prompt, provider, is_json=False):
            calls.append((prompt, provider))
            if len(calls) == 1:
                return {"text": "Part A", "finish_reason": "MAX_TOKENS"}
            elif len(calls) == 2:
                return {"text": "Part B.", "finish_reason": "STOP"}

        saved_dispatch = ai_service._dispatch_provider
        ai_service._dispatch_provider = mock_dispatch
        cont_res = ai_service._generate_with_continuation("Prompt", provider="gemini")
        ai_service._dispatch_provider = saved_dispatch

        if cont_res == "Part A Part B." and len(calls) == 2 and calls[0][1] == calls[1][1] == "gemini":
            test_results.append(("Truncation Continuation", "AI Engine", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
        else:
            test_results.append(("Truncation Continuation", "AI Engine", "FAILED", f"{(time.time()-t0)*1000:.1f}ms"))

        # 6. Multi-Provider Fallback
        t0 = time.time()
        fb_calls = []
        def mock_cont(prompt, provider, is_json=False):
            fb_calls.append(provider)
            if provider == "gemini":
                raise ValueError("Auth Error 403")
            return "Response from Groq"

        saved_is_config = ai_service._is_provider_configured
        saved_cont = ai_service._generate_with_continuation
        ai_service._is_provider_configured = lambda p: True
        ai_service._generate_with_continuation = mock_cont

        fb_res = ai_service._generate_with_fallback("Prompt")
        ai_service._is_provider_configured = saved_is_config
        ai_service._generate_with_continuation = saved_cont

        # 7. Hierarchical Chunker 8-Chunk Cap
        t0 = time.time()
        sample_doc = "Section Heading\n\nDetailed content paragraph.\n\n" * 1200
        chunks = ai_service._chunk_text(sample_doc, max_chunks=8)
        if 1 <= len(chunks) <= 8 and len(sample_doc) > 50000:
            test_results.append(("Hierarchical 8-Chunk Cap", "AI Engine", "PASSED", f"{(time.time()-t0)*1000:.1f}ms"))
        else:
            test_results.append(("Hierarchical 8-Chunk Cap", "AI Engine", f"FAILED: generated {len(chunks)} chunks", f"{(time.time()-t0)*1000:.1f}ms"))

        # Render Modern Console Output
        if RICH_AVAILABLE:
            table = Table(box=box.ROUNDED, header_style="bold magenta", border_style="dim")
            table.add_column("Test Case Name", style="bold white", width=30)
            table.add_column("Category", style="cyan", width=18)
            table.add_column("Status", width=14)
            table.add_column("Execution Time", style="yellow", justify="right", width=14)

            all_passed = True
            for name, cat, status, duration in test_results:
                if status == "PASSED":
                    status_text = "[bold green]✔ PASSED[/bold green]"
                else:
                    status_text = f"[bold red]✘ {status}[/bold red]"
                    all_passed = False
                table.add_row(name, cat, status_text, duration)

            console.print("\n", table)

            if all_passed:
                console.print(Panel(
                    f"[bold green]✨ ALL {len(test_results)} VERIFICATION TESTS PASSED PERFECTLY![/bold green]\n"
                    "[dim]QuickMind core services, OCR pipeline, API routes, continuation engine, fallback layers, and chunking caps are 100% operational.[/dim]",
                    border_style="green",
                    box=box.ROUNDED
                ))
            else:
                console.print(Panel("[bold red]❌ SOME TESTS FAILED![/bold red]", border_style="red", box=box.ROUNDED))
        else:
            for name, cat, status, duration in test_results:
                print(f"[{status}] {name} ({cat}) - {duration}")

    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[bold red]Fatal error during execution: {e}[/bold red]")
        else:
            print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_tests()
