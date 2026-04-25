import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import ChatRequest

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "election-navigator-ai"}

def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert b"Election Navigator AI" in response.content

def test_chat_endpoint_valid_request():
    payload = {
        "session_id": "test_session_123",
        "message": "What is a Voter ID?",
        "language": "en"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "suggested_actions" in data
    assert isinstance(data["suggested_actions"], list)

def test_chat_endpoint_invalid_payload():
    payload = {
        "message": "What is a Voter ID?" # Missing session_id
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 422 # Unprocessable Entity (Pydantic validation)
