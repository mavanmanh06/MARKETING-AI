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


def test_ai_logs_management_admin_only():
    # 1. Admin đăng nhập -> truy cập được /api/ai/logs và /api/ai/logs/stats
    admin_login = client.post("/api/auth/login", json={"email": "admin@marketing.ai", "password": "admin123"})
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    logs_res = client.get("/api/ai/logs", headers=admin_headers)
    assert logs_res.status_code == 200
    assert isinstance(logs_res.json(), list)

    stats_res = client.get("/api/ai/logs/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    assert "total_logs" in stats_res.json()
    assert "user_stats" in stats_res.json()

    # 2. Manager đăng nhập -> BỊ TỪ CHỐI 403 FORBIDDEN
    manager_login = client.post("/api/auth/login", json={"email": "manager@marketing.ai", "password": "manager123"})
    assert manager_login.status_code == 200
    manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}

    mgr_logs_res = client.get("/api/ai/logs", headers=manager_headers)
    assert mgr_logs_res.status_code == 403
    mgr_stats_res = client.get("/api/ai/logs/stats", headers=manager_headers)
    assert mgr_stats_res.status_code == 403

    # 3. Marketer đăng nhập -> BỊ TỪ CHỐI 403 FORBIDDEN
    marketer_login = client.post("/api/auth/login", json={"email": "marketer@marketing.ai", "password": "marketer123"})
    assert marketer_login.status_code == 200
    marketer_headers = {"Authorization": f"Bearer {marketer_login.json()['access_token']}"}

    mkt_logs_res = client.get("/api/ai/logs", headers=marketer_headers)
    assert mkt_logs_res.status_code == 403
    mkt_stats_res = client.get("/api/ai/logs/stats", headers=marketer_headers)
    assert mkt_stats_res.status_code == 403


def test_ai_campaign_generation_logged_for_admin_supervision():
    # Marketer sử dụng AI để tạo chiến dịch
    marketer_login = client.post("/api/auth/login", json={"email": "marketer@marketing.ai", "password": "marketer123"})
    marketer_headers = {"Authorization": f"Bearer {marketer_login.json()['access_token']}"}

    camp_res = client.post("/api/ai/generate-campaign", json={
        "product_or_service": "Bộ sưu tập Tai nghe Gaming Pro",
        "objective": "Sales Conversion",
        "budget": 75000000.0,
        "duration_days": 30
    }, headers=marketer_headers)
    assert camp_res.status_code == 200
    camp_data = camp_res.json()
    assert "name" in camp_data
    assert "description" in camp_data

    # Admin giám sát xem ai đã sử dụng AI tạo chiến dịch
    admin_login = client.post("/api/auth/login", json={"email": "admin@marketing.ai", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    logs_res = client.get("/api/ai/logs?action_type=campaign_generation", headers=admin_headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) > 0
    # Thấy rõ marketer là người thực hiện
    assert any(l["user_email"] == "marketer@marketing.ai" and "Tai nghe Gaming Pro" in l["prompt"] for l in logs)


def test_admin_only_can_delete_team_members():
    import uuid

    # 1. Tạo một tài khoản thành viên để kiểm tra tính năng xóa
    unique_suffix = uuid.uuid4().hex[:8]
    test_email = f"staff_to_delete_{unique_suffix}@example.com"
    test_password = "password123"
    reg_resp = client.post("/api/auth/register", json={
        "full_name": f"Nhân viên Thử Nghiệm {unique_suffix}",
        "email": test_email,
        "password": test_password
    })
    assert reg_resp.status_code == 200

    # Lấy ID của thành viên vừa tạo bằng tài khoản Admin
    admin_login = client.post("/api/auth/login", json={"email": "admin@marketing.ai", "password": "admin123"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_id = admin_login.json()["user"]["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    users_list = client.get("/api/auth/users", headers=admin_headers).json()
    target_user = next((u for u in users_list if u["email"] == test_email), None)
    assert target_user is not None
    target_user_id = target_user["id"]

    # 2. Nhân viên (Marketer) KHÔNG ĐƯỢC PHÉP XÓA THÀNH VIÊN (Trả về 403 Forbidden)
    marketer_login = client.post("/api/auth/login", json={"email": "marketer@marketing.ai", "password": "marketer123"})
    assert marketer_login.status_code == 200
    marketer_headers = {"Authorization": f"Bearer {marketer_login.json()['access_token']}"}

    del_as_marketer = client.delete(f"/api/auth/users/{target_user_id}", headers=marketer_headers)
    assert del_as_marketer.status_code == 403, "Marketer không được phép xóa thành viên nhóm"

    # 3. Quản lý (Manager) KHÔNG ĐƯỢC PHÉP XÓA THÀNH VIÊN (Trả về 403 Forbidden)
    manager_login = client.post("/api/auth/login", json={"email": "manager@marketing.ai", "password": "manager123"})
    assert manager_login.status_code == 200
    manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}

    del_as_manager = client.delete(f"/api/auth/users/{target_user_id}", headers=manager_headers)
    assert del_as_manager.status_code == 403, "Manager không được phép xóa thành viên nhóm"

    # 4. Quản trị viên (Admin) không thể tự xóa chính mình (Trả về 400 Bad Request)
    del_self = client.delete(f"/api/auth/users/{admin_id}", headers=admin_headers)
    assert del_self.status_code == 400
    assert "Không thể tự xóa chính tài khoản" in del_self.json()["detail"]

    # 5. Quản trị viên (Admin) CÓ QUYỀN XÓA THÀNH VIÊN (Trả về 200 OK)
    del_as_admin = client.delete(f"/api/auth/users/{target_user_id}", headers=admin_headers)
    assert del_as_admin.status_code == 200
    assert del_as_admin.json()["id"] == target_user_id

    # 6. Kiểm tra lại danh sách thành viên: không còn tài khoản vừa bị xóa
    users_after_delete = client.get("/api/auth/users", headers=admin_headers).json()
    assert not any(u["id"] == target_user_id for u in users_after_delete)

    # 7. Tài khoản bị xóa không thể đăng nhập được nữa
    login_deleted_user = client.post("/api/auth/login", json={"email": test_email, "password": test_password})
    assert login_deleted_user.status_code == 401
