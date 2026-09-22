// Campaigns Management Module

let globalCampaigns = [];
let globalChannels = [];

async function loadChannels() {
    try {
        globalChannels = await api.get("/api/channels");
        populateChannelDropdowns(globalChannels);
    } catch (err) {
        console.error("Lỗi tải kênh:", err);
    }
}

function populateChannelDropdowns(channels) {
    // 1. Filter dropdown in campaigns view
    const filterSelect = document.getElementById("campaign-channel-filter");
    if (filterSelect) {
        filterSelect.innerHTML = `<option value="all">Tất cả các kênh</option>` + 
            channels.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    }

    // 2. Modal post channel select
    const postChannelSelect = document.getElementById("post-form-channel");
    if (postChannelSelect) {
        postChannelSelect.innerHTML = channels.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    }

    // 3. Modal metric channel select
    const metricChannelSelect = document.getElementById("metric-form-channel");
    if (metricChannelSelect) {
        metricChannelSelect.innerHTML = channels.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    }
}

async function loadCampaigns() {
    const search = document.getElementById("campaign-search-input") ? document.getElementById("campaign-search-input").value.trim() : "";
    const status = document.getElementById("campaign-status-filter") ? document.getElementById("campaign-status-filter").value : "all";
    const channelId = document.getElementById("campaign-channel-filter") ? document.getElementById("campaign-channel-filter").value : "all";

    let url = "/api/campaigns?";
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (status && status !== "all") url += `status=${encodeURIComponent(status)}&`;
    if (channelId && channelId !== "all") url += `channel_id=${encodeURIComponent(channelId)}&`;

    try {
        globalCampaigns = await api.get(url);
        renderCampaignGrid(globalCampaigns);
        populateCampaignDropdowns(globalCampaigns);
    } catch (err) {
        console.error("Lỗi tải chiến dịch:", err);
    }
}

function populateCampaignDropdowns(campaigns) {
    const selects = [
        "post-form-campaign",
        "metric-form-campaign",
        "ai-idea-campaign-select",
        "ai-content-campaign-select",
        "ai-insight-campaign-select"
    ];

    selects.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const hasDefault = id.startsWith("ai-");
            const defaultOpt = hasDefault ? `<option value="">-- Chọn chiến dịch liên kết --</option>` : "";
            el.innerHTML = defaultOpt + campaigns.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
        }
    });
}

function handleCampaignFilter() {
    loadCampaigns();
}

function renderCampaignGrid(campaigns) {
    const grid = document.getElementById("campaign-cards-grid");
    if (!grid) return;

    if (!campaigns || campaigns.length === 0) {
        grid.innerHTML = `
            <div class="empty-placeholder" style="grid-column: 1/-1;">
                <i data-lucide="target"></i>
                <p>Không tìm thấy chiến dịch nào phù hợp với bộ lọc.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    const currentUser = api.getUser();
    const isManager = currentUser && currentUser.role === "manager";

    grid.innerHTML = campaigns.map(c => {
        const spendRate = c.budget > 0 ? ((c.total_spend / c.budget) * 100).toFixed(1) : 0;
        const roi = c.total_spend > 0 ? (((c.total_revenue - c.total_spend) / c.total_spend) * 100).toFixed(1) : 0;
        
        const canEdit = isManager || (currentUser && c.created_by_id === currentUser.id);

        return `
            <div class="campaign-card">
                <div>
                    <div class="campaign-card-header">
                        <h4 class="campaign-title">${c.name}</h4>
                        <span class="badge-status status-${c.status}">${c.status.toUpperCase()}</span>
                    </div>

                    <div class="campaign-objective">
                        <i data-lucide="compass"></i>
                        <span>${c.objective}</span>
                    </div>

                    <div class="campaign-metrics-row">
                        <div class="c-metric">
                            <span class="c-metric-label">Lượt xem</span>
                            <span class="c-metric-val">${c.total_impressions.toLocaleString("vi-VN")}</span>
                        </div>
                        <div class="c-metric">
                            <span class="c-metric-label">Clicks</span>
                            <span class="c-metric-val">${c.total_clicks.toLocaleString("vi-VN")}</span>
                        </div>
                        <div class="c-metric">
                            <span class="c-metric-label">ROI</span>
                            <span class="c-metric-val text-success">+${roi}%</span>
                        </div>
                    </div>

                    <div class="progress-bar-container">
                        <div class="progress-label-row">
                            <span>Chi tiêu: ${formatVND(c.total_spend)} / ${formatVND(c.budget)}</span>
                            <span>${spendRate}%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${Math.min(spendRate, 100)}%;"></div>
                        </div>
                    </div>

                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                        📅 ${formatDate(c.start_date)} - ${formatDate(c.end_date)} | 👤 ${c.creator_name || 'Admin'}
                    </div>
                </div>

                <div class="campaign-card-actions">
                    <button class="btn btn-outline btn-sm" onclick="analyzeCampaignWithAI(${c.id})" title="AI Phân tích hiệu suất">
                        <i data-lucide="sparkles"></i> AI Đánh giá
                    </button>
                    ${canEdit ? `
                        <button class="btn btn-outline btn-sm" onclick="openEditCampaignModal(${c.id})" title="Sửa chiến dịch">
                            <i data-lucide="edit"></i> Sửa
                        </button>
                    ` : ''}
                    ${isManager ? `
                        <button class="btn btn-outline btn-sm text-danger" onclick="handleDeleteCampaign(${c.id})" title="Xóa chiến dịch">
                            <i data-lucide="trash-2"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join("");

    lucide.createIcons();
}

function openCreateCampaignModal() {
    document.getElementById("form-campaign").reset();
    document.getElementById("campaign-edit-id").value = "";
    document.getElementById("modal-campaign-title").textContent = "Tạo Chiến dịch Marketing Mới";

    // Set default dates (today to +30 days)
    const today = new Date().toISOString().split("T")[0];
    const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
    document.getElementById("camp-form-start-date").value = today;
    document.getElementById("camp-form-end-date").value = nextMonth;

    openModal("modal-campaign");
}

function openEditCampaignModal(campaignId) {
    const c = globalCampaigns.find(item => item.id === campaignId);
    if (!c) return;

    document.getElementById("campaign-edit-id").value = c.id;
    document.getElementById("modal-campaign-title").textContent = "Chỉnh sửa Chiến dịch";
    document.getElementById("camp-form-name").value = c.name;
    document.getElementById("camp-form-objective").value = c.objective;
    document.getElementById("camp-form-audience").value = c.target_audience || "";
    document.getElementById("camp-form-budget").value = c.budget;
    document.getElementById("camp-form-status").value = c.status;
    document.getElementById("camp-form-start-date").value = c.start_date ? c.start_date.split("T")[0] : "";
    document.getElementById("camp-form-end-date").value = c.end_date ? c.end_date.split("T")[0] : "";
    document.getElementById("camp-form-desc").value = c.description || "";

    openModal("modal-campaign");
}

async function handleSaveCampaign(e) {
    e.preventDefault();
    const editId = document.getElementById("campaign-edit-id").value;
    const name = document.getElementById("camp-form-name").value.trim();
    const objective = document.getElementById("camp-form-objective").value.trim();
    const target_audience = document.getElementById("camp-form-audience").value.trim();
    const budget = parseFloat(document.getElementById("camp-form-budget").value) || 0;
    const status = document.getElementById("camp-form-status").value;
    const start_date = new Date(document.getElementById("camp-form-start-date").value).toISOString();
    const end_date = new Date(document.getElementById("camp-form-end-date").value).toISOString();
    const description = document.getElementById("camp-form-desc").value.trim();

    const payload = {
        name,
        objective,
        target_audience,
        budget,
        status,
        start_date,
        end_date,
        description
    };

    try {
        if (editId) {
            await api.put(`/api/campaigns/${editId}`, payload);
            showToast("Đã cập nhật chiến dịch thành công!", "success");
        } else {
            await api.post("/api/campaigns", payload);
            showToast("Đã tạo chiến dịch marketing mới thành công!", "success");
        }
        closeModal("modal-campaign");
        loadCampaigns();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi lưu chiến dịch", "error");
    }
}

async function handleDeleteCampaign(campaignId) {
    if (!confirm("Bạn có chắc chắn muốn xóa chiến dịch này cùng toàn bộ bài viết và chỉ số liên quan?")) {
        return;
    }

    try {
        await api.delete(`/api/campaigns/${campaignId}`);
        showToast("Đã xóa chiến dịch thành công!", "success");
        loadCampaigns();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi xóa chiến dịch", "error");
    }
}

function analyzeCampaignWithAI(campaignId) {
    switchView("ai-assistant");
    switchAITab("insights");
    const select = document.getElementById("ai-insight-campaign-select");
    if (select) {
        select.value = campaignId;
        triggerAICampaignAnalysis();
    }
}
