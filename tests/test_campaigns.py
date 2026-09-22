import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_header(email="admin@marketing.ai", password="admin123"):
    login_resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_campaigns():
    headers = get_auth_header()
    response = client.get("/api/campaigns", headers=headers)
    assert response.status_code == 200
    campaigns = response.json()
    assert len(campaigns) >= 4

def test_filter_campaigns_by_status():
    headers = get_auth_header()
    response = client.get("/api/campaigns?status=active", headers=headers)
    assert response.status_code == 200
    for c in response.json():
        assert c["status"] == "active"

def test_create_campaign():
    headers = get_auth_header()
    now = datetime.utcnow()
    payload = {
        "name": "Chiến dịch Test Tự Động",
        "objective": "Lead Generation",
        "target_audience": "Doanh nghiệp",
        "budget": 20000000.0,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=15)).isoformat(),
        "status": "planning",
        "description": "Mô tả test tự động"
    }
    response = client.post("/api/campaigns", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Chiến dịch Test Tự Động"
    assert data["budget"] == 20000000.0
