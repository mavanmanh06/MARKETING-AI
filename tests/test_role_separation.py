import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_static_html_contains_role_suites():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    
    # Check Manager navigation & views
    assert "nav-manager-suite" in html
    assert "view-dashboard" in html
    assert "view-approval-center" in html
    assert "view-team-management" in html
    assert "dashboard-quick-approval-list" in html

    # Check Marketer navigation & views
    assert "nav-marketer-suite" in html
    assert "view-marketer-workspace" in html
    assert "view-feedback-center" in html
    assert "view-my-performance" in html
    assert "marketer-hero-card" in html
    assert "ai-fast-creator-card" in html

    # Role switching must require a separate login.
    assert "toggleSwitchRole" not in html
    assert "header-role-banner" in html

def test_manager_role_endpoints():
    login_resp = client.post("/api/auth/login", json={"email": "admin@marketing.ai", "password": "admin123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    user = login_resp.json()["user"]
    assert user["role"] == "admin"
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Executive Dashboard summary
    dash_resp = client.get("/api/metrics/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    assert "total_budget" in dash_resp.json()
    assert "total_spend" in dash_resp.json()
    assert "posts_by_status" in dash_resp.json()

    # 2. Team management stats
    team_resp = client.get("/api/auth/team-stats", headers=headers)
    assert team_resp.status_code == 200
    team = team_resp.json()
    assert len(team) >= 2
    assert sum(m["role"] == "admin" for m in team) == 1
    assert sum(m["role"] == "manager" for m in team) == 1
    assert any(m["email"] == "admin@marketing.ai" and m["role"] == "admin" for m in team)
    assert any(m["email"] == "manager@marketing.ai" and m["role"] == "manager" for m in team)
    assert any(m["email"] == "marketer@marketing.ai" and m["role"] == "marketer" for m in team)

    # 3. Approval Center posts query
    in_review_resp = client.get("/api/content?status=in_review", headers=headers)
    assert in_review_resp.status_code == 200

def test_manager_account_has_management_permissions():
    login_resp = client.post("/api/auth/login", json={"email": "manager@marketing.ai", "password": "manager123"})
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    assert login_resp.json()["user"]["role"] == "manager"
    assert client.get("/api/metrics/dashboard", headers=headers).status_code == 200
    assert client.get("/api/auth/users", headers=headers).status_code == 200

def test_marketer_cannot_access_management_data():
    login_resp = client.post("/api/auth/login", json={"email": "marketer@marketing.ai", "password": "marketer123"})
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    assert client.get("/api/auth/users", headers=headers).status_code == 403
    assert client.get("/api/auth/team-stats", headers=headers).status_code == 403
    assert client.get("/api/metrics/dashboard", headers=headers).status_code == 403
    assert client.get("/api/metrics", headers=headers).status_code == 403

def test_marketer_cannot_read_other_users_posts():
    import uuid

    admin_login = client.post("/api/auth/login", json={"email": "admin@marketing.ai", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    post_resp = client.post("/api/content", json={
        "campaign_id": 1,
        "channel_id": 1,
        "title": "Bài viết riêng tư",
        "content": "Nội dung chỉ quản trị viên tạo.",
        "status": "draft"
    }, headers=admin_headers)
    assert post_resp.status_code == 200
    post_id = post_resp.json()["id"]

    email = f"staff_{uuid.uuid4().hex[:8]}@example.com"
    register_resp = client.post("/api/auth/register", json={
        "full_name": "Nhân viên mới",
        "email": email,
        "password": "password123"
    })
    assert register_resp.status_code == 200
    staff_login = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    staff_headers = {"Authorization": f"Bearer {staff_login.json()['access_token']}"}

    assert client.get("/api/content", headers=staff_headers).json() == []
    assert client.get(f"/api/content/{post_id}", headers=staff_headers).status_code == 404

def test_marketer_role_endpoints():
    login_resp = client.post("/api/auth/login", json={"email": "marketer@marketing.ai", "password": "marketer123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    user = login_resp.json()["user"]
    assert user["role"] == "marketer"
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Marketer Personal Dashboard
    m_dash_resp = client.get("/api/metrics/marketer-dashboard", headers=headers)
    assert m_dash_resp.status_code == 200
    data = m_dash_resp.json()
    assert data["user_name"] == "Trần Thị Marketer"
    assert "total_posts" in data
    assert "drafts_count" in data
    assert "in_review_count" in data
    assert "recent_drafts" in data
    assert "feedbacks" in data

    # 2. Marketer personal content filter
    my_content_resp = client.get(f"/api/content?author_id={user['id']}", headers=headers)
    assert my_content_resp.status_code == 200
    posts = my_content_resp.json()
    assert all(p["author_id"] == user["id"] for p in posts)

def test_human_in_the_loop_collaboration_cycle():
    admin_login = client.post("/api/auth/login", json={"email": "admin@marketing.ai", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    marketer_login = client.post("/api/auth/login", json={"email": "marketer@marketing.ai", "password": "marketer123"})
    marketer_headers = {"Authorization": f"Bearer {marketer_login.json()['access_token']}"}

    # Step 1: Marketer creates a new draft
    post_in = {
        "campaign_id": 1,
        "channel_id": 1,
        "title": "🎉 Khuyến Mãi Mùa Thu 2026 - Mua 1 Tặng 1",
        "content": "Ưu đãi sốc cho toàn bộ khách hàng ghé thăm cửa hàng trong tuần lễ vàng!",
        "hashtags": "#FallSale #BigSale",
        "call_to_action": "Bấm vào link để nhận mã",
        "status": "draft",
        "ai_generated": True
    }
    create_res = client.post("/api/content", json=post_in, headers=marketer_headers)
    assert create_res.status_code == 200
    post_id = create_res.json()["id"]

    # Step 2: Marketer submits for review
    submit_res = client.put(f"/api/content/{post_id}/review", json={"action": "submit_for_review"}, headers=marketer_headers)
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "in_review"

    # Step 3: Manager reviews and rejects with detailed feedback
    feedback_text = "Cần thêm điều kiện áp dụng và hotline liên hệ để khách hàng dễ hỏi thông tin."
    reject_res = client.put(f"/api/content/{post_id}/review", json={"action": "reject", "feedback": feedback_text}, headers=admin_headers)
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"
    assert reject_res.json()["reviewer_feedback"] == feedback_text

    # Step 4: Marketer dashboard receives this feedback
    m_dash = client.get("/api/metrics/marketer-dashboard", headers=marketer_headers).json()
    assert m_dash["rejected_count"] >= 1
    assert any(fb["post_id"] == post_id and fb["feedback"] == feedback_text for fb in m_dash["feedbacks"])

    # Step 5: Marketer updates post and re-submits
    update_res = client.put(f"/api/content/{post_id}", json={
        "content": "Ưu đãi sốc mua 1 tặng 1. Áp dụng hóa đơn trên 500k. Hotline: 1900-1234!",
        "status": "in_review"
    }, headers=marketer_headers)
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "in_review"

    # Step 6: Manager approves the updated post
    approve_res = client.put(f"/api/content/{post_id}/review", json={"action": "approve", "feedback": "Đã sửa tốt, duyệt ngay!"}, headers=admin_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"
