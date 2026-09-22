import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_header(email="admin@marketing.ai", password="admin123"):
    login_resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_content_review_workflow():
    admin_headers = get_auth_header("admin@marketing.ai", "admin123")
    marketer_headers = get_auth_header("marketer@marketing.ai", "marketer123")

    # 1. Marketer creates a draft post
    post_payload = {
        "campaign_id": 1,
        "channel_id": 1,
        "title": "Bài viết test quy trình duyệt",
        "content": "Nội dung bài viết thử nghiệm hệ thống duyệt bài.",
        "hashtags": "#Test #Marketing",
        "call_to_action": "Bấm vào đây",
        "status": "draft"
    }
    create_resp = client.post("/api/content", json=post_payload, headers=marketer_headers)
    assert create_resp.status_code == 200
    post_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "draft"

    # 2. Marketer submits for review
    submit_resp = client.put(f"/api/content/{post_id}/review", json={"action": "submit_for_review"}, headers=marketer_headers)
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "in_review"

    # 3. Marketer tries to approve (Should fail with 403)
    unauth_approve = client.put(f"/api/content/{post_id}/review", json={"action": "approve"}, headers=marketer_headers)
    assert unauth_approve.status_code == 403

    # 4. Manager approves the post
    approve_resp = client.put(f"/api/content/{post_id}/review", json={"action": "approve", "feedback": "Đã duyệt bài viết tốt!"}, headers=admin_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"
    assert approve_resp.json()["reviewer_feedback"] == "Đã duyệt bài viết tốt!"

def test_team_stats_and_marketer_dashboard():
    admin_headers = get_auth_header("admin@marketing.ai", "admin123")
    marketer_headers = get_auth_header("marketer@marketing.ai", "marketer123")

    # Test Team stats endpoint
    team_resp = client.get("/api/auth/team-stats", headers=admin_headers)
    assert team_resp.status_code == 200
    team_data = team_resp.json()
    assert len(team_data) >= 2
    assert any(m["role"] == "manager" for m in team_data)
    assert any(m["role"] == "marketer" for m in team_data)

    # Test Marketer dashboard endpoint
    dash_resp = client.get("/api/metrics/marketer-dashboard", headers=marketer_headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "total_posts" in dash_data
    assert "approval_rate" in dash_data
    assert "recent_drafts" in dash_data
    assert "feedbacks" in dash_data

