import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_service import document_service

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
        document_service.validate_file("image.png", 1000)
    assert "Unsupported file type" in str(exc.value)

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
