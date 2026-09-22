import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_header(email="admin@marketing.ai", password="admin123"):
    login_resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_ai_generate_ideas():
    headers = get_auth_header()
    payload = {
        "campaign_id": 1,
        "objective": "Brand Awareness",
        "channel": "Facebook",
        "tone": "Trẻ trung, năng động",
        "quantity": 5
    }
    response = client.post("/api/ai/generate-ideas", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "ideas" in data
    assert len(data["ideas"]) == 5
    assert "System: Bạn là trợ lý marketing" in data["raw_prompt"]

def test_ai_generate_content():
    headers = get_auth_header()
    payload = {
        "campaign_id": 1,
        "topic_or_idea": "Giới thiệu camera AI chụp đêm siêu nét",
        "channel": "TikTok",
        "tone": "Trẻ trung",
        "content_type": "video_script"
    }
    response = client.post("/api/ai/generate-content", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "content" in data
    assert "hashtags" in data
    assert "call_to_action" in data

def test_ai_analyze_campaign():
    headers = get_auth_header()
    response = client.post("/api/ai/analyze-campaign", json={"campaign_id": 1}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert len(data["strengths"]) > 0
    assert len(data["recommendations"]) > 0
