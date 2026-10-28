// AI Marketing Assistant Suite & Admin AI Supervision Module

let currentGeneratedContent = null;
let adminAILogsCache = [];
let adminAISearchTimer = null;

function switchAITab(tabName, e) {
    if (e) e.preventDefault();

    const currentUser = api.getUser();
    const isAdmin = currentUser && currentUser.role === "admin";

    // Nếu tab là logs và người dùng không phải Admin, chặn và thông báo
    if (tabName === "logs" && !isAdmin) {
        showToast("Bạn không có quyền xem nhật ký AI. Chức năng này chỉ dành cho Quản trị viên (Admin)!", "error");
        return;
    }

    document.querySelectorAll(".ai-nav-tabs .ai-tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".ai-subview").forEach(v => {
        v.classList.remove("active");
        v.style.display = "none";
    });

    if (e && e.currentTarget) e.currentTarget.classList.add("active");
    const target = document.getElementById(`ai-tab-${tabName}`);
    if (target) {
        target.classList.add("active");
        target.style.display = "block";
    }

    if (tabName === "logs" && isAdmin) {
        loadAILogs();
    }
}

async function triggerAIIdeaGenerator() {
    const campaignId = document.getElementById("ai-idea-campaign-select").value;
    const objective = document.getElementById("ai-idea-objective").value.trim() || "Brand Awareness";
    const channel = document.getElementById("ai-idea-channel").value;
    const tone = document.getElementById("ai-idea-tone").value;
    const audience = document.getElementById("ai-idea-audience").value.trim();
    const btn = document.getElementById("btn-ai-gen-ideas");
    const resultBox = document.getElementById("ai-idea-results");

    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="spin"></i> AI đang suy nghĩ & sinh ý tưởng...`;
    resultBox.innerHTML = `<div class="empty-placeholder"><i data-lucide="loader" class="spin"></i><p>Đang phân tích tệp khách hàng và sinh 5 góc nhìn nội dung sáng tạo...</p></div>`;
    lucide.createIcons();

    try {
        const payload = {
            campaign_id: campaignId ? parseInt(campaignId) : null,
            objective,
            channel,
            tone,
            target_audience: audience,
            quantity: 5
        };

        const res = await api.post("/api/ai/generate-ideas", payload);

        resultBox.innerHTML = res.ideas.map((idea, idx) => `
            <div class="ai-idea-item">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
                    <h5>💡 #${idx + 1}: ${idea.title}</h5>
                    <div style="display: flex; gap: 0.4rem;">
                        <button class="btn btn-outline btn-sm" onclick="useIdeaForCampaign('${encodeURIComponent(idea.title)}', '${encodeURIComponent(idea.concept)}')">
                            <i data-lucide="target"></i> Tạo chiến dịch
                        </button>
                        <button class="btn btn-outline btn-sm" onclick="useIdeaForContent('${encodeURIComponent(idea.title)}', '${channel}')">
                            <i data-lucide="pen-tool"></i> Viết bài này
                        </button>
                    </div>
                </div>
                <p>${idea.concept}</p>
                <div class="ai-idea-meta">
                    <span>📐 Định dạng: <strong>${idea.format}</strong></span>
                    <span>🎯 Góc tiếp cận: <strong>${idea.angle}</strong></span>
                </div>
                <div style="font-size: 0.75rem; color: #10b981; margin-top: 0.4rem;">
                    ✨ Kỳ vọng: ${idea.expected_impact}
                </div>
            </div>
        `).join("");

        showToast("AI đã sinh thành công 5 ý tưởng sáng tạo!", "success");
        if (typeof updateAdminAILogsBadge === "function") updateAdminAILogsBadge();
    } catch (err) {
        resultBox.innerHTML = `<div class="empty-placeholder text-danger"><p>Lỗi sinh ý tưởng: ${err.message}</p></div>`;
        showToast(err.message || "Lỗi sinh ý tưởng", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="sparkles"></i> AI Sinh 5 Ý Tưởng Sáng Tạo`;
        lucide.createIcons();
    }
}

function useIdeaForCampaign(encodedTitle, encodedConcept) {
    const title = decodeURIComponent(encodedTitle);
    const concept = decodeURIComponent(encodedConcept);
    openCreateCampaignModal();
    const nameEl = document.getElementById("camp-form-name");
    const descEl = document.getElementById("camp-form-desc");
    if (nameEl) nameEl.value = title.replace(/^Ý tưởng \d+:\s*/i, "");
    if (descEl) descEl.value = concept;
    showToast("Đã đưa ý tưởng AI vào form Tạo Chiến Dịch mới!", "info");
}

function useIdeaForContent(encodedTitle, channel) {
    const title = decodeURIComponent(encodedTitle);
    switchAITab("content");
    document.getElementById("ai-content-topic").value = title;
    document.getElementById("ai-content-channel").value = channel;
    showToast("Đã chuyển ý tưởng sang bộ soạn thảo AI!", "info");
}

async function triggerAIContentGenerator() {
    const campaignId = document.getElementById("ai-content-campaign-select").value;
    const topic = document.getElementById("ai-content-topic").value.trim();
    const channel = document.getElementById("ai-content-channel").value;
    const tone = document.getElementById("ai-content-tone").value;
    const btn = document.getElementById("btn-ai-gen-content");
    const resultBox = document.getElementById("ai-content-result-box");
    const pushBtn = document.getElementById("btn-push-ai-to-draft");

    if (!topic) {
        showToast("Vui lòng nhập chủ đề hoặc ý tưởng bài viết", "warning");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="spin"></i> AI đang viết bài nháp...`;
    pushBtn.style.display = "none";
    resultBox.innerHTML = `<div class="empty-placeholder"><i data-lucide="loader" class="spin"></i><p>Đang áp dụng kỹ thuật Copywriting theo chuẩn kênh ${channel}...</p></div>`;
    lucide.createIcons();

    try {
        const payload = {
            campaign_id: campaignId ? parseInt(campaignId) : null,
            topic_or_idea: topic,
            channel,
            tone,
            content_type: channel.toLowerCase().includes("tiktok") ? "video_script" : "caption"
        };

        const res = await api.post("/api/ai/generate-content", payload);
        currentGeneratedContent = res;
        currentGeneratedContent.campaign_id = campaignId;

        resultBox.innerHTML = `
            <div class="content-headline">${res.title}</div>
            <div class="content-body">${res.content}</div>
            <div class="content-tags">${res.hashtags}</div>
            <div class="content-cta-box">${res.call_to_action}</div>
            <div style="font-size: 0.75rem; color: #f59e0b; margin-top: 1rem; border-top: 1px dashed var(--border-color); padding-top: 0.5rem;">
                ⚠️ <em>${res.notes_for_human_review}</em>
            </div>
        `;

        pushBtn.style.display = "inline-flex";
        showToast("AI đã hoàn thành bản nháp nội dung!", "success");
        if (typeof updateAdminAILogsBadge === "function") updateAdminAILogsBadge();
    } catch (err) {
        resultBox.innerHTML = `<div class="empty-placeholder text-danger"><p>Lỗi tạo nội dung: ${err.message}</p></div>`;
        showToast(err.message || "Lỗi tạo nội dung", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="feather"></i> AI Tạo Bản Nháp Đầy Đủ`;
        lucide.createIcons();
    }
}

function pushAIToContentDraft() {
    if (!currentGeneratedContent) return;

    // Open post modal and fill with AI data
    openCreatePostModal();

    if (currentGeneratedContent.campaign_id) {
        document.getElementById("post-form-campaign").value = currentGeneratedContent.campaign_id;
    }

    // Match channel
    const chSelect = document.getElementById("post-form-channel");
    for (let i = 0; i < chSelect.options.length; i++) {
        if (chSelect.options[i].text.toLowerCase().includes(currentGeneratedContent.channel.toLowerCase())) {
            chSelect.selectedIndex = i;
            break;
        }
    }

    document.getElementById("post-form-title").value = currentGeneratedContent.title;
    document.getElementById("post-form-content").value = currentGeneratedContent.content;
    document.getElementById("post-form-hashtags").value = currentGeneratedContent.hashtags;
    document.getElementById("post-form-cta").value = currentGeneratedContent.call_to_action;
    document.getElementById("post-form-status").value = "in_review";

    showToast("Đã nhập nội dung AI vào form! Bạn có thể chỉnh sửa trước khi lưu.", "info");
}

async function triggerAICampaignAnalysis() {
    const campaignId = document.getElementById("ai-insight-campaign-select").value;
    const btn = document.getElementById("btn-ai-analyze");
    const container = document.getElementById("ai-insight-result-container");

    if (!campaignId) {
        showToast("Vui lòng chọn chiến dịch cần phân tích", "warning");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="spin"></i> AI đang phân tích dữ liệu...`;
    container.innerHTML = `<div class="empty-placeholder"><i data-lucide="loader" class="spin"></i><p>Đang đọc các chỉ số CTR, CPC, CPA, ROI và tính toán mô hình tối ưu...</p></div>`;
    lucide.createIcons();

    try {
        const res = await api.post("/api/ai/analyze-campaign", { campaign_id: parseInt(campaignId) });

        container.innerHTML = `
            <div class="card" style="background: rgba(15, 23, 42, 0.7); margin-bottom: 1.5rem;">
                <h4 style="color: var(--brand-primary); margin-bottom: 0.5rem;">📋 Tóm tắt Đánh giá Điều hành (Executive Summary)</h4>
                <p style="font-size: 0.95rem; line-height: 1.6; color: #e2e8f0;">${res.summary}</p>
            </div>

            <div class="insight-grid-2">
                <div class="swot-box">
                    <h5 class="text-success"><i data-lucide="check-circle"></i> Điểm Mạnh & Hiệu Quả Tốt</h5>
                    <ul class="swot-list">
                        ${res.strengths.map(s => `<li>${s}</li>`).join("")}
                    </ul>
                </div>

                <div class="swot-box">
                    <h5 class="text-warning"><i data-lucide="alert-triangle"></i> Điểm Yếu & Rủi Ro Cần Tối Ưu</h5>
                    <ul class="swot-list">
                        ${res.weaknesses.map(w => `<li>${w}</li>`).join("")}
                    </ul>
                </div>
            </div>

            <div class="card" style="margin-top: 1.5rem; background: rgba(15, 23, 42, 0.7);">
                <h4 style="color: #38bdf8; margin-bottom: 0.75rem;"><i data-lucide="zap"></i> Đề xuất Hành động Cụ thể từ AI</h4>
                <ul class="swot-list">
                    ${res.recommendations.map(r => `<li><strong>${r}</strong></li>`).join("")}
                </ul>

                <div style="margin-top: 1rem; padding: 0.75rem 1rem; background: rgba(99, 102, 241, 0.15); border-radius: var(--radius-sm); border-left: 3px solid var(--brand-primary); font-size: 0.85rem;">
                    💡 <strong>Gợi ý phân bổ ngân sách:</strong> ${res.suggested_budget_allocation.reallocate_note} (Ưu tiên kênh <strong>${res.suggested_budget_allocation.top_channel}</strong>).
                </div>
            </div>
        `;

        showToast("AI đã hoàn thành phân tích hiệu suất chiến dịch!", "success");
        if (typeof updateAdminAILogsBadge === "function") updateAdminAILogsBadge();
    } catch (err) {
        container.innerHTML = `<div class="empty-placeholder text-danger"><p>Lỗi phân tích: ${err.message}</p></div>`;
        showToast(err.message || "Lỗi phân tích", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="brain"></i> Phân tích Chuyên sâu AI`;
        lucide.createIcons();
    }
}


// ================= TÍNH NĂNG TẠO CHIẾN DỊCH BẰNG AI =================
function openAIGenerateCampaignModal() {
    document.getElementById("form-ai-gen-campaign").reset();
    openModal("modal-ai-gen-campaign");
}

async function handleExecuteAIGenCampaign(e) {
    e.preventDefault();
    const product = document.getElementById("ai-camp-product").value.trim();
    const objective = document.getElementById("ai-camp-objective").value;
    const audience = document.getElementById("ai-camp-audience").value.trim();
    const budget = parseFloat(document.getElementById("ai-camp-budget").value) || 50000000;
    const duration = parseInt(document.getElementById("ai-camp-duration").value) || 30;
    const btn = document.getElementById("btn-submit-ai-gen-camp");

    if (!product) {
        showToast("Vui lòng nhập tên sản phẩm hoặc dịch vụ", "warning");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="spin"></i> AI đang nghiên cứu & lập kế hoạch chiến dịch...`;
    lucide.createIcons();

    try {
        const payload = {
            product_or_service: product,
            objective: objective,
            target_audience: audience,
            budget: budget,
            duration_days: duration,
            preferred_channel: "Facebook"
        };

        const res = await api.post("/api/ai/generate-campaign", payload);

        // Đóng modal AI wizard
        closeModal("modal-ai-gen-campaign");

        // Điền dữ liệu trực tiếp vào modal Tạo Chiến Dịch
        openCreateCampaignModal();
        document.getElementById("camp-form-name").value = res.name;
        document.getElementById("camp-form-objective").value = res.objective;
        document.getElementById("camp-form-audience").value = res.target_audience;
        document.getElementById("camp-form-budget").value = res.budget;
        document.getElementById("camp-form-status").value = "planning";
        document.getElementById("camp-form-desc").value = res.description;

        // Tính ngày bắt đầu và kết thúc
        const today = new Date();
        const endDate = new Date(Date.now() + duration * 24 * 60 * 60 * 1000);
        document.getElementById("camp-form-start-date").value = today.toISOString().split("T")[0];
        document.getElementById("camp-form-end-date").value = endDate.toISOString().split("T")[0];

        showToast("✨ AI đã lập kế hoạch chiến dịch thành công! Dữ liệu đã được nạp vào form.", "success");
        if (typeof updateAdminAILogsBadge === "function") updateAdminAILogsBadge();
    } catch (err) {
        showToast(err.message || "Lỗi tạo kế hoạch bằng AI", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="wand-2"></i> AI Tạo Kế Hoạch Ngay`;
        lucide.createIcons();
    }
}


// ================= QUẢN LÝ NHẬT KÝ AI (DÀNH RIÊNG CHO ADMIN) =================
async function updateAdminAILogsBadge() {
    const user = api.getUser();
    if (!user || user.role !== "admin") return;

    try {
        const stats = await api.get("/api/ai/logs/stats");
        const badge = document.getElementById("badge-admin-ai-count");
        if (badge && stats) {
            badge.textContent = stats.total_logs;
        }
    } catch (e) {
        // Silent fail
    }
}

async function loadAdminAIStats() {
    const user = api.getUser();
    if (!user || user.role !== "admin") return;

    try {
        const stats = await api.get("/api/ai/logs/stats");
        if (!stats) return;

        // Cập nhật các KPI
        const elTotal = document.getElementById("admin-ai-stat-total");
        const elUsers = document.getElementById("admin-ai-stat-users-count");
        const elCampaigns = document.getElementById("admin-ai-stat-campaigns");
        const elContent = document.getElementById("admin-ai-stat-content");
        const elInsights = document.getElementById("admin-ai-stat-insights");
        const badge = document.getElementById("badge-admin-ai-count");

        if (elTotal) elTotal.textContent = stats.total_logs;
        if (elUsers) elUsers.textContent = `${stats.total_users_used} thành viên đã dùng`;
        if (elCampaigns) elCampaigns.textContent = stats.campaign_ai_count;
        if (elContent) elContent.textContent = stats.content_ai_count;
        if (elInsights) elInsights.textContent = stats.insight_ai_count;
        if (badge) badge.textContent = stats.total_logs;

        // Cập nhật bảng Người dùng sử dụng AI
        const tbodyUsers = document.getElementById("tbody-admin-ai-users");
        if (tbodyUsers) {
            if (!stats.user_stats || stats.user_stats.length === 0) {
                tbodyUsers.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 1.5rem;">Chưa có dữ liệu người dùng nào sử dụng AI</td></tr>`;
            } else {
                tbodyUsers.innerHTML = stats.user_stats.map(u => {
                    const roleBadgeClass = u.user_role === "admin" ? "admin-badge" : u.user_role === "manager" ? "manager-badge" : "marketer-badge";
                    const roleLabel = u.user_role === "admin" ? "Admin" : u.user_role === "manager" ? "Quản lý" : "Nhân viên";
                    const hasCampaignAI = u.campaign_calls > 0;

                    return `
                        <tr style="cursor: pointer;" onclick="filterLogsByUser(${u.user_id})" title="Nhấp để xem các log của ${u.user_name}">
                            <td>
                                <div>
                                    <strong>${u.user_name}</strong>
                                    <small class="text-muted" style="display: block;">${u.user_email}</small>
                                </div>
                            </td>
                            <td><span class="user-role-badge ${roleBadgeClass}" style="font-size: 0.72rem;">${roleLabel}</span></td>
                            <td><strong style="color: var(--brand-primary); font-size: 1.1rem;">${u.total_calls}</strong> lượt</td>
                            <td>
                                <span class="badge-pill ${hasCampaignAI ? 'badge-primary' : ''}" style="${hasCampaignAI ? 'font-weight: 700;' : 'opacity: 0.6;'}">
                                    ${u.campaign_calls} lượt ${hasCampaignAI ? '🎯' : ''}
                                </span>
                            </td>
                            <td><span class="badge-pill">${u.content_calls} lượt</span></td>
                            <td><span class="badge-pill">${u.insight_calls} lượt</span></td>
                            <td><small class="text-muted">${u.last_activity || 'Chưa có'}</small></td>
                            <td>
                                <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); filterLogsByUser(${u.user_id})">
                                    <i data-lucide="filter"></i> Lọc log
                                </button>
                            </td>
                        </tr>
                    `;
                }).join("");
            }
        }

        // Cập nhật dropdown lọc người dùng
        const userSelect = document.getElementById("admin-ai-filter-user");
        if (userSelect && stats.user_stats) {
            const currentVal = userSelect.value;
            userSelect.innerHTML = `<option value="">-- Tất cả thành viên (${stats.user_stats.length}) --</option>` +
                stats.user_stats.map(u => `<option value="${u.user_id}">${u.user_name} (${u.user_role}) - ${u.total_calls} lượt</option>`).join("");
            if (currentVal) userSelect.value = currentVal;
        }

        lucide.createIcons();
    } catch (err) {
        console.error("Lỗi tải AI stats:", err);
    }
}

async function loadAdminAILogs() {
    const user = api.getUser();
    if (!user || user.role !== "admin") return;

    const tbody = document.getElementById("tbody-admin-ai-logs");
    if (!tbody) return;

    const userFilter = document.getElementById("admin-ai-filter-user") ? document.getElementById("admin-ai-filter-user").value : "";
    const actionFilter = document.getElementById("admin-ai-filter-action") ? document.getElementById("admin-ai-filter-action").value : "all";
    const searchFilter = document.getElementById("admin-ai-filter-search") ? document.getElementById("admin-ai-filter-search").value.trim() : "";

    let url = "/api/ai/logs?limit=200&";
    if (userFilter) url += `user_id=${userFilter}&`;
    if (actionFilter && actionFilter !== "all") url += `action_type=${actionFilter}&`;
    if (searchFilter) url += `search=${encodeURIComponent(searchFilter)}&`;

    try {
        const logs = await api.get(url);
        adminAILogsCache = logs || [];

        const badgeCount = document.getElementById("admin-ai-logs-badge-count");
        if (badgeCount) badgeCount.textContent = `${adminAILogsCache.length} bản ghi`;

        if (!adminAILogsCache || adminAILogsCache.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2rem;">Không tìm thấy nhật ký AI nào phù hợp với bộ lọc</td></tr>`;
            return;
        }

        tbody.innerHTML = adminAILogsCache.map(l => {
            let actionBadge = `<span class="badge-tag">${l.action_type}</span>`;
            if (l.action_type === "campaign_generation") {
                actionBadge = `<span class="badge-tag" style="background: rgba(139, 92, 246, 0.25); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); font-weight: 700;">🎯 Tạo Chiến Dịch AI</span>`;
            } else if (l.action_type === "idea_generation") {
                actionBadge = `<span class="badge-tag" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3);">💡 Sinh Ý Tưởng</span>`;
            } else if (l.action_type === "content_draft") {
                actionBadge = `<span class="badge-tag" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3);">✍️ Viết Bài/Nội Dung</span>`;
            } else if (l.action_type === "performance_summary") {
                actionBadge = `<span class="badge-tag" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3);">📊 Phân Tích Hiệu Suất</span>`;
            }

            const roleBadgeClass = l.user_role === "admin" ? "admin-badge" : l.user_role === "manager" ? "manager-badge" : "marketer-badge";
            const roleName = l.user_role === "admin" ? "Admin" : l.user_role === "manager" ? "Quản lý" : "Nhân viên";
            const campaignBadge = l.campaign_name ? 
                `<span style="color: #38bdf8; font-weight: 600;" title="${l.campaign_name}">🎯 ${l.campaign_name.length > 25 ? l.campaign_name.substring(0, 25) + '...' : l.campaign_name}</span>` : 
                `<span class="text-muted" style="font-size: 0.8rem;">(Độc lập)</span>`;

            // Rút gọn text prompt và response
            const promptSnippet = l.prompt.replace(/^System:[^\n]*\nUser:\s*/i, "");
            const shortPrompt = promptSnippet.length > 55 ? promptSnippet.substring(0, 55) + '...' : promptSnippet;
            const shortResponse = l.response_text.length > 60 ? l.response_text.substring(0, 60) + '...' : l.response_text;

            return `
                <tr>
                    <td><small class="text-muted" style="white-space: nowrap;">${l.created_at}</small></td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <div>
                                <strong style="display: block;">${l.user_name}</strong>
                                <span class="user-role-badge ${roleBadgeClass}" style="font-size: 0.68rem; padding: 1px 6px;">${roleName}</span>
                            </div>
                        </div>
                    </td>
                    <td>${actionBadge}</td>
                    <td>${campaignBadge}</td>
                    <td>
                        <div style="max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.85rem;" title="${escapeHtml(promptSnippet)}">
                            ${escapeHtml(shortPrompt)}
                        </div>
                    </td>
                    <td>
                        <div style="max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.85rem; color: #94a3b8;" title="${escapeHtml(l.response_text)}">
                            ${escapeHtml(shortResponse)}
                        </div>
                    </td>
                    <td>
                        <div style="display: flex; gap: 0.35rem;">
                            <button class="btn btn-outline btn-sm" onclick="viewAILogDetail(${l.id})" title="Xem đầy đủ Prompt và Kết quả AI">
                                <i data-lucide="eye"></i>
                            </button>
                            <button class="btn btn-outline btn-sm text-danger" onclick="deleteAILog(${l.id})" title="Xóa log này">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        lucide.createIcons();
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Lỗi tải nhật ký AI: ${err.message}</td></tr>`;
    }
}

function filterAdminAILogs() {
    loadAdminAILogs();
}

function handleAdminAISearch() {
    clearTimeout(adminAISearchTimer);
    adminAISearchTimer = setTimeout(() => {
        loadAdminAILogs();
    }, 350);
}

function resetAdminAIFilters() {
    const userSelect = document.getElementById("admin-ai-filter-user");
    const actionSelect = document.getElementById("admin-ai-filter-action");
    const searchInput = document.getElementById("admin-ai-filter-search");
    if (userSelect) userSelect.value = "";
    if (actionSelect) actionSelect.value = "all";
    if (searchInput) searchInput.value = "";
    loadAdminAILogs();
    showToast("Đã đặt lại bộ lọc nhật ký AI", "info");
}

function filterLogsByUser(userId) {
    const userSelect = document.getElementById("admin-ai-filter-user");
    if (userSelect) {
        userSelect.value = userId;
        loadAdminAILogs();
        // Cuộn xuống bảng log
        const table = document.getElementById("tbody-admin-ai-logs");
        if (table) table.scrollIntoView({ behavior: "smooth" });
    }
}

function viewAILogDetail(logId) {
    const item = adminAILogsCache.find(l => l.id === logId);
    if (!item) return;

    document.getElementById("log-detail-user").textContent = `${item.user_name} (${item.user_email})`;
    document.getElementById("log-detail-role").textContent = item.user_role.toUpperCase();
    document.getElementById("log-detail-action").textContent = item.action_type;
    document.getElementById("log-detail-campaign").textContent = item.campaign_name || "Không gắn chiến dịch";
    document.getElementById("log-detail-time").textContent = item.created_at;

    document.getElementById("log-detail-prompt").textContent = item.prompt;
    document.getElementById("log-detail-response").textContent = item.response_text;

    openModal("modal-ai-log-detail");
}

async function deleteAILog(logId) {
    if (!confirm("Bạn có chắc chắn muốn xóa bản ghi nhật ký AI này?")) return;

    try {
        await api.delete(`/api/ai/logs/${logId}`);
        showToast("Đã xóa bản ghi nhật ký thành công!", "success");
        loadAdminAILogs();
        loadAdminAIStats();
    } catch (err) {
        showToast(err.message || "Lỗi xóa log", "error");
    }
}

async function clearAllAILogs() {
    if (!confirm("⚠️ CẢNH BÁO: Bạn có chắc chắn muốn xóa TOÀN BỘ nhật ký AI của hệ thống? Thao tác này không thể hoàn tác!")) {
        return;
    }

    try {
        const res = await api.delete("/api/ai/logs");
        showToast(res.message || "Đã dọn sạch toàn bộ nhật ký AI!", "success");
        loadAdminAILogs();
        loadAdminAIStats();
    } catch (err) {
        showToast(err.message || "Lỗi dọn sạch nhật ký", "error");
    }
}

function exportAILogs(format) {
    if (!adminAILogsCache || adminAILogsCache.length === 0) {
        showToast("Không có dữ liệu nhật ký AI để xuất", "warning");
        return;
    }

    const dateStr = new Date().toISOString().split("T")[0];

    if (format === "json") {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(adminAILogsCache, null, 2));
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute("href", dataStr);
        dlAnchor.setAttribute("download", `ai_audit_logs_${dateStr}.json`);
        dlAnchor.click();
        showToast("Đã xuất báo cáo Nhật ký AI dạng JSON!", "success");
    } else {
        // CSV export
        const headers = ["ID", "Thời Gian", "Người Thực Hiện", "Email", "Vai Trò", "Loại Hành Động", "Chiến Dịch", "Prompt", "Phản Hồi"];
        const rows = adminAILogsCache.map(l => [
            l.id,
            `"${l.created_at}"`,
            `"${(l.user_name || '').replace(/"/g, '""')}"`,
            `"${(l.user_email || '').replace(/"/g, '""')}"`,
            `"${l.user_role}"`,
            `"${l.action_type}"`,
            `"${(l.campaign_name || 'N/A').replace(/"/g, '""')}"`,
            `"${(l.prompt || '').replace(/"/g, '""').replace(/\n/g, ' ')}"`,
            `"${(l.response_text || '').replace(/"/g, '""').replace(/\n/g, ' ')}"`
        ]);

        const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute("href", url);
        dlAnchor.setAttribute("download", `ai_audit_logs_${dateStr}.csv`);
        dlAnchor.click();
        showToast("Đã xuất báo cáo Nhật ký AI dạng CSV!", "success");
    }
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Giữ lại loadAILogs cũ cho tab 4 trong view AI Assistant (chỉ admin mới gọi)
async function loadAILogs() {
    const user = api.getUser();
    if (!user || user.role !== "admin") return;

    const tbody = document.getElementById("tbody-ai-logs");
    if (!tbody) return;

    try {
        const logs = await api.get("/api/ai/logs?limit=50");
        if (!logs || logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Chưa có nhật ký AI nào</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td><small class="text-muted">${l.created_at}</small></td>
                <td><strong>${l.user_name}</strong> <small class="text-muted">(${l.user_role})</small></td>
                <td><span class="badge-tag">${l.action_type}</span></td>
                <td><small style="max-width: 250px; display: inline-block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(l.prompt)}">${escapeHtml(l.prompt)}</small></td>
                <td><small style="max-width: 250px; display: inline-block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(l.response_text)}">${escapeHtml(l.response_text)}</small></td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Lỗi tải AI logs:", err);
    }
}
