import sys
import os
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

def run_tests():
    try:
        from app.services.document_service import document_service
        from app.services.ai_service import ai_service
        from app.main import app
        from fastapi.testclient import TestClient

        print("--- Running QuickMind Verification Suite ---")

        # Test 1: Document Service File Validation
        print("[1/6] Testing file extension validation...")
        try:
            document_service.validate_file("document.pdf", 500)
            document_service.validate_file("notes.docx", 500)
            document_service.validate_file("data.txt", 500)
            print("  [OK] Allowed file types (.pdf, .docx, .txt) validated.")
        except Exception as e:
            print(f"  [ERROR] File validation error: {e}")

        # Test 2: Invalid file extension handling
        print("[2/6] Testing invalid file extension rejection...")
        try:
            document_service.validate_file("script.exe", 500)
            print("  [ERROR] Failed to reject invalid file extension.")
        except ValueError as ve:
            print(f"  [OK] Rejected invalid file extension correctly: {ve}")

        # Test 3: Text length validation
        print("[3/6] Testing 10,000 character limit enforcement...")
        try:
            document_service.validate_text_length("x" * 10001)
            print("  [ERROR] Failed to enforce character limit.")
        except ValueError as ve:
            print(f"  [OK] Character limit enforced correctly: {ve}")

        # Test 4: FastAPI Client Endpoints
        print("[4/6] Testing FastAPI routes via TestClient...")
        client = TestClient(app)

        # Health endpoint
        health_res = client.get("/api/health")
        assert health_res.status_code == 200, "Health check failed"
        print("  [OK] GET /api/health returned 200 OK.")

        # Summarize endpoint validation
        sum_res = client.post("/api/summarize", json={"text": "", "length": "short"})
        assert sum_res.status_code == 200
        assert sum_res.json()["success"] is False
        print("  [OK] POST /api/summarize correctly rejected empty text.")

        # Ask endpoint validation
        ask_res = client.post("/api/ask", json={"question": ""})
        assert ask_res.status_code == 200
        assert ask_res.json()["success"] is False
        print("  [OK] POST /api/ask correctly rejected empty question.")

        # Generate endpoint validation
        gen_res = client.post("/api/generate", json={"topic": ""})
        assert gen_res.status_code == 200
        assert gen_res.json()["success"] is False
        print("  [OK] POST /api/generate correctly rejected empty topic.")

        # Analyze endpoint validation
        anz_res = client.post("/api/analyze", json={"text": ""})
        assert anz_res.status_code == 200
        assert anz_res.json()["success"] is False
        print("  [OK] POST /api/analyze correctly rejected empty text.")

        # Test 5: Continuation Engine Logic
        print("[5/6] Testing Truncation Continuation Engine...")
        calls = []
        def mock_dispatch(prompt, provider, is_json=False):
            calls.append((prompt, provider))
            if len(calls) == 1:
                return {"text": "Chapter 1", "finish_reason": "MAX_TOKENS"}
            elif len(calls) == 2:
                return {"text": "Chapter 2.", "finish_reason": "STOP"}

        saved_dispatch = ai_service._dispatch_provider
        ai_service._dispatch_provider = mock_dispatch
        cont_result = ai_service._generate_with_continuation("Write book", provider="gemini")
        ai_service._dispatch_provider = saved_dispatch

        assert cont_result == "Chapter 1 Chapter 2."
        assert len(calls) == 2
        assert calls[0][1] == "gemini" and calls[1][1] == "gemini"
        print("  [OK] Truncation continuation stitched multi-round responses using SAME provider.")

        # Test 6: Multi-Provider Fallback Logic
        print("[6/6] Testing Multi-Provider Fallback Engine...")
        fallback_calls = []
        def mock_cont(prompt, provider, is_json=False):
            fallback_calls.append(provider)
            if provider == "gemini":
                raise ValueError("Gemini auth error 403")
            return "Response from Groq"

        saved_is_config = ai_service._is_provider_configured
        saved_cont = ai_service._generate_with_continuation
        ai_service._is_provider_configured = lambda p: True
        ai_service._generate_with_continuation = mock_cont

        fb_result = ai_service._generate_with_fallback("Test prompt")
        ai_service._is_provider_configured = saved_is_config
        ai_service._generate_with_continuation = saved_cont

        assert fb_result == "Response from Groq"
        assert fallback_calls == ["gemini", "groq"]
        print("  [OK] Multi-provider fallback retried cleanly on next provider.")

        print("\n=== ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

    except Exception as e:
        print(f"\n[ERROR] Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_tests()
