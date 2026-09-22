import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_login_admin():
    response = client.post("/api/auth/login", json={
        "email": "admin@marketing.ai",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "manager"

def test_login_marketer():
    response = client.post("/api/auth/login", json={
        "email": "marketer@marketing.ai",
        "password": "marketer123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "marketer"

def test_login_invalid_password():
    response = client.post("/api/auth/login", json={
        "email": "admin@marketing.ai",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_me_unauthorized():
    response = client.get("/api/auth/me")
    assert response.status_code == 403 or response.status_code == 401

def test_register_standard_user():
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/register", json={
        "full_name": "Test Staff",
        "email": unique_email,
        "password": "password123",
        "role": "manager"  # Even if trying to pass manager, backend forces marketer
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "marketer"
    assert data["email"] == unique_email

