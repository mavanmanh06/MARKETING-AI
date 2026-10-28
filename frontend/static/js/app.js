// Main Application Controller & Router with Distinct Role Switching

function switchView(viewName, e) {
    if (e) e.preventDefault();

    const user = api.getUser();
    const isManager = user && isManagementRole(user.role);
    const isAdmin = user && user.role === "admin";

    // BẢO VỆ CHẶT CHẼ: CHỈ ADMIN MỚI ĐƯỢC PHÉP TRUY CẬP VÀO QUẢN LÝ NHẬT KÝ AI
    if (viewName === "admin-ai-logs") {
        if (!isAdmin) {
            showToast("Bạn không có quyền truy cập chức năng này. Quản lý Nhật ký AI chỉ dành riêng cho Quản trị viên (Admin)!", "error");
            if (isManager) {
                switchView("dashboard");
            } else {
                switchView("marketer-workspace");
            }
            return;
        }
    }

    // Update active nav items across both suites
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
        item.classList.remove("active");
    });
    
    // Find matching nav item
    const currentNavItem = document.querySelector(`.sidebar-nav a[href="#${viewName}"]`);
    if (currentNavItem) {
        currentNavItem.classList.add("active");
    }

    // Update active view panels
    document.querySelectorAll(".page-view").forEach(v => {
        v.classList.remove("active");
    });

    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.classList.add("active");
    }

    // Update header titles & descriptions
    const titles = {
        "dashboard": { 
            title: "Tổng quan Điều hành (Executive Dashboard)", 
            desc: "Theo dõi chỉ số tài chính, ROI toàn diện & phê duyệt nhanh các chiến dịch" 
        },
        "marketer-workspace": { 
            title: "Bàn làm việc của tôi (My Creative Workspace)", 
            desc: "Quản lý bản nháp cá nhân, nhận xét từ Quản lý và sáng tạo nội dung đa kênh với AI" 
        },
        "approval-center": { 
            title: "Trung tâm Phê duyệt (Approval Center)", 
            desc: "Kiểm duyệt nội dung marketing do nhân viên khởi tạo trước khi xuất bản (Human-in-the-Loop)" 
        },
        "team-management": { 
            title: "Quản lý Đội ngũ & Nhân sự (Team Management)", 
            desc: "Danh sách thành viên marketing, phân quyền và thống kê năng suất hoạt động" 
        },
        "feedback-center": { 
            title: "Hộp thư Góp ý & Sửa bài (Revisions Required)", 
            desc: "Xem chi tiết lời nhắn phản hồi của Quản lý để hiệu chỉnh nội dung và gửi duyệt lại" 
        },
        "my-performance": { 
            title: "Hiệu quả Bài viết của tôi", 
            desc: "Theo dõi trạng thái duyệt, lịch phát hành và đóng góp cá nhân vào chiến dịch" 
        },
        "campaigns": { 
            title: "Quản lý Chiến dịch & Ngân sách", 
            desc: "Danh sách, lọc và điều phối ngân sách các chiến dịch marketing" 
        },
        "content": { 
            title: "Studio Nội dung & Lịch đăng", 
            desc: "Soạn thảo bài viết, lịch xuất bản và quy trình phê duyệt Human-in-the-Loop" 
        },
        "ai-assistant": { 
            title: isManager ? "Trợ lý AI Phân tích Chiến lược" : "Trợ lý AI Sáng tạo Nội dung", 
            desc: "Sáng tạo ý tưởng viral, viết caption đa kênh và phân tích chuyên sâu" 
        },
        "admin-ai-logs": { 
            title: "🛡️ Quản Lý & Giám Sát Nhật Ký AI (Admin AI Supervision Console)", 
            desc: "Giám sát chi tiết xem những ai đã sử dụng AI để tạo chiến dịch, tạo ý tưởng và soạn thảo nội dung" 
        },
        "metrics": { 
            title: "Chỉ số & Báo cáo ROI Toàn diện", 
            desc: "Ghi nhận số liệu thực tế, theo dõi chi phí và tỷ suất sinh lời ROI" 
        },
        "settings": { 
            title: "Cài đặt & Tài khoản", 
            desc: "Quản trị người dùng, vai trò RBAC và cấu hình AI Engine" 
        }
    };

    if (titles[viewName]) {
        document.getElementById("current-page-title").textContent = titles[viewName].title;
        document.getElementById("current-page-desc").textContent = titles[viewName].desc;
    }

    // Trigger data loading for active view
    if (viewName === "dashboard" || viewName === "marketer-workspace") loadDashboardData();
    if (viewName === "campaigns") loadCampaigns();
    if (viewName === "content" || viewName === "approval-center" || viewName === "feedback-center" || viewName === "my-performance") loadContent();
    if (viewName === "team-management") loadTeamManagement();
    if (viewName === "metrics") loadMetricsData();
    if (viewName === "ai-assistant") {
        loadChannels();
        loadCampaigns();
    }
    if (viewName === "admin-ai-logs") {
        if (typeof loadAdminAIStats === "function") loadAdminAIStats();
        if (typeof loadAdminAILogs === "function") loadAdminAILogs();
    }

    lucide.createIcons();
}

// Modal Helpers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add("active");
        lucide.createIcons();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove("active");
    }
}

// Global quick actions
function openAIGeneratorModal() {
    switchView("ai-assistant");
    switchAITab("content");
}

// Metrics View Specifics
async function loadMetricsData() {
    const tbody = document.getElementById("tbody-metrics-table");
    if (!tbody) return;

    try {
        const metrics = await api.get("/api/metrics");
        if (!metrics || metrics.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">Chưa có dữ liệu chỉ số nào</td></tr>`;
            return;
        }

        tbody.innerHTML = metrics.map(m => `
            <tr>
                <td><strong>${formatDate(m.record_date)}</strong></td>
                <td>${m.campaign_name}</td>
                <td><span class="badge-tag">${m.channel_name}</span></td>
                <td>${m.impressions.toLocaleString("vi-VN")}</td>
                <td>${m.clicks.toLocaleString("vi-VN")} <small class="text-muted">(${m.ctr}%)</small></td>
                <td>${m.conversions.toLocaleString("vi-VN")} <small class="text-muted">(${formatVND(m.cpa)})</small></td>
                <td>${formatVND(m.spend)}</td>
                <td><strong class="text-success">${formatVND(m.revenue)}</strong> <small class="text-success">(+${m.roi}%)</small></td>
                <td><small class="text-muted">${m.notes || '-'}</small></td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Lỗi tải metrics:", err);
    }
}

function openRecordMetricModal() {
    document.getElementById("form-record-metric").reset();
    document.getElementById("metric-form-date").value = new Date().toISOString().split("T")[0];
    openModal("modal-record-metric");
}

async function handleSaveMetric(e) {
    e.preventDefault();
    const campaign_id = parseInt(document.getElementById("metric-form-campaign").value);
    const channel_id = parseInt(document.getElementById("metric-form-channel").value);
    const record_date = new Date(document.getElementById("metric-form-date").value).toISOString();
    const impressions = parseInt(document.getElementById("metric-form-impressions").value) || 0;
    const clicks = parseInt(document.getElementById("metric-form-clicks").value) || 0;
    const conversions = parseInt(document.getElementById("metric-form-conversions").value) || 0;
    const spend = parseFloat(document.getElementById("metric-form-spend").value) || 0.0;
    const revenue = parseFloat(document.getElementById("metric-form-revenue").value) || 0.0;
    const notes = document.getElementById("metric-form-notes").value.trim();

    try {
        await api.post("/api/metrics", {
            campaign_id,
            channel_id,
            record_date,
            impressions,
            clicks,
            conversions,
            spend,
            revenue,
            notes
        });

        showToast("Đã ghi nhận chỉ số marketing mới thành công!", "success");
        closeModal("modal-record-metric");
        loadMetricsData();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi lưu chỉ số", "error");
    }
}

async function exportMetricsJSON() {
    try {
        const metrics = await api.get("/api/metrics");
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(metrics, null, 2));
        const dlAnchorElem = document.createElement('a');
        dlAnchorElem.setAttribute("href", dataStr);
        dlAnchorElem.setAttribute("download", `marketing_metrics_report_${new Date().toISOString().split("T")[0]}.json`);
        dlAnchorElem.click();
        showToast("Đã xuất báo cáo số liệu JSON thành công!", "success");
    } catch (err) {
        showToast("Lỗi xuất dữ liệu", "error");
    }
}

function handleSaveAIConfig(e) {
    e.preventDefault();
    showToast("Cấu hình AI đã được cập nhật thành công!", "success");
}

// App Initialization
async function initAppAfterAuth() {
    const user = api.getUser();
    if (!user) return;

    document.getElementById("auth-screen").style.display = "none";
    document.getElementById("main-layout").style.display = "flex";

    updateUserInfoUI(user);

    await loadChannels();
    await loadCampaigns();

    // Direct user to their respective default dashboard
    if (isManagementRole(user.role)) {
        switchView("dashboard");
    } else {
        switchView("marketer-workspace");
    }

    await loadContent();

    lucide.createIcons();
}

document.addEventListener("DOMContentLoaded", async () => {
    lucide.createIcons();

    const token = api.getToken();
    if (token) {
        try {
            const user = await api.get("/api/auth/me");
            api.setUser(user);
            initAppAfterAuth();
        } catch (err) {
            console.log("Token không hợp lệ hoặc đã hết hạn");
            api.clearToken();
            document.getElementById("auth-screen").style.display = "flex";
        }
    } else {
        document.getElementById("auth-screen").style.display = "flex";
    }
});
