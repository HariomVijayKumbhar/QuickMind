import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_service import document_service
from app.services.ai_service import ai_service

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "QuickMind" in data["app"]

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gemini_api_configured" in data

def test_document_validation_file_type():
    with pytest.raises(ValueError) as exc:
        document_service.validate_file("image.gif", 1000)
    assert "Unsupported file type" in str(exc.value)

def test_document_image_types_accepted():
    # .jpg, .jpeg, .png should now be accepted without raising
    for name in ["photo.jpg", "scan.jpeg", "screenshot.png"]:
        ext = document_service.validate_file(name, 500)
        assert ext in {".jpg", ".jpeg", ".png"}

def test_ocr_path_detection():
    assert document_service.is_ocr_path("scan.jpg") is True
    assert document_service.is_ocr_path("scan.jpeg") is True
    assert document_service.is_ocr_path("photo.png") is True
    assert document_service.is_ocr_path("document.pdf") is False
    assert document_service.is_ocr_path("notes.docx") is False
    assert document_service.is_ocr_path("data.txt") is False

def test_document_validation_text_length():
    with pytest.raises(ValueError) as exc:
        document_service.validate_text_length("a" * 10001)
    assert "exceeds the limit" in str(exc.value)

def test_txt_extraction():
    text_bytes = "Hello QuickMind test".encode("utf-8")
    extracted = document_service.extract_text(text_bytes, "test.txt")
    assert extracted == "Hello QuickMind test"

def test_summarize_empty_input():
    response = client.post("/api/summarize", json={"text": "", "length": "short"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "provide either" in data["error"].lower()

def test_ask_empty_input():
    response = client.post("/api/ask", json={"question": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "provide a question" in data["error"].lower()

def test_generate_empty_input():
    response = client.post("/api/generate", json={"topic": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "provide a topic" in data["error"].lower()

def test_analyze_empty_input():
    response = client.post("/api/analyze", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "provide either" in data["error"].lower()

def test_provider_configuration_check():
    assert isinstance(ai_service._is_provider_configured("gemini"), bool)
    assert ai_service._is_provider_configured("unknown_provider") is False

def test_continuation_stitching(monkeypatch):
    calls = []
    def mock_dispatch(prompt, provider, is_json=False):
        calls.append((prompt, provider))
        if len(calls) == 1:
            return {"text": "Part 1 of answer", "finish_reason": "MAX_TOKENS"}
        elif len(calls) == 2:
            return {"text": "Part 2 of answer.", "finish_reason": "STOP"}
            
    monkeypatch.setattr(ai_service, "_dispatch_provider", mock_dispatch)
    result = ai_service._generate_with_continuation("Write long article", provider="gemini")
    assert result == "Part 1 of answer Part 2 of answer."
    assert len(calls) == 2
    # Verify both continuation calls used the SAME provider
    assert calls[0][1] == "gemini"
    assert calls[1][1] == "gemini"

def test_fallback_mechanism(monkeypatch):
    providers_called = []
    def mock_continuation(prompt, provider, is_json=False):
        providers_called.append(provider)
        if provider == "gemini":
            raise ValueError("Gemini connection error 500")
        return "Response from Groq"

    monkeypatch.setattr(ai_service, "_is_provider_configured", lambda p: True)
    monkeypatch.setattr(ai_service, "_generate_with_continuation", mock_continuation)
    
    result = ai_service._generate_with_fallback("Test prompt")
    assert result == "Response from Groq"
    assert providers_called == ["gemini", "groq"]
