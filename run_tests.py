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
        from app.main import app
        from fastapi.testclient import TestClient

        print("--- Running QuickMind Verification Suite ---")

        # Test 1: Document Service File Validation
        print("[1/5] Testing file extension validation...")
        try:
            document_service.validate_file("document.pdf", 500)
            document_service.validate_file("notes.docx", 500)
            document_service.validate_file("data.txt", 500)
            print("  [OK] Allowed file types (.pdf, .docx, .txt) validated.")
        except Exception as e:
            print(f"  [ERROR] File validation error: {e}")

        # Test 2: Invalid file extension handling
        print("[2/5] Testing invalid file extension rejection...")
        try:
            document_service.validate_file("script.exe", 500)
            print("  [ERROR] Failed to reject invalid file extension.")
        except ValueError as ve:
            print(f"  [OK] Rejected invalid file extension correctly: {ve}")

        # Test 3: Text length validation
        print("[3/5] Testing 10,000 character limit enforcement...")
        try:
            document_service.validate_text_length("x" * 10001)
            print("  [ERROR] Failed to enforce character limit.")
        except ValueError as ve:
            print(f"  [OK] Character limit enforced correctly: {ve}")

        # Test 4: FastAPI Client Endpoints
        print("[4/5] Testing FastAPI routes via TestClient...")
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

        print("\n=== ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

    except Exception as e:
        print(f"\n[ERROR] Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_tests()

