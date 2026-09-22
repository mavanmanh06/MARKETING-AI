// AI Marketing Assistant Suite Module

let currentGeneratedContent = null;

function switchAITab(tabName, e) {
    if (e) e.preventDefault();
    document.querySelectorAll(".ai-nav-tabs .ai-tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".ai-subview").forEach(v => v.classList.remove("active"));

    if (e && e.currentTarget) e.currentTarget.classList.add("active");
    const target = document.getElementById(`ai-tab-${tabName}`);
    if (target) target.classList.add("active");

    if (tabName === "logs") {
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
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h5>💡 #${idx + 1}: ${idea.title}</h5>
                    <button class="btn btn-outline btn-sm" onclick="useIdeaForContent('${encodeURIComponent(idea.title)}', '${channel}')">
                        <i data-lucide="pen-tool"></i> Viết bài này
                    </button>
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
    } catch (err) {
        resultBox.innerHTML = `<div class="empty-placeholder text-danger"><p>Lỗi sinh ý tưởng: ${err.message}</p></div>`;
        showToast(err.message || "Lỗi sinh ý tưởng", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="sparkles"></i> AI Sinh 5 Ý Tưởng Sáng Tạo`;
        lucide.createIcons();
    }
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
    document.getElementById("post-form-status").value = "in_review"; // Automatically ready for review

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
    } catch (err) {
        container.innerHTML = `<div class="empty-placeholder text-danger"><p>Lỗi phân tích: ${err.message}</p></div>`;
        showToast(err.message || "Lỗi phân tích", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="brain"></i> Phân tích Chuyên sâu AI`;
        lucide.createIcons();
    }
}

async function loadAILogs() {
    const tbody = document.getElementById("tbody-ai-logs");
    if (!tbody) return;

    try {
        const logs = await api.get("/api/ai/logs");
        if (!logs || logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Chưa có nhật ký AI nào</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td><small class="text-muted">${l.created_at}</small></td>
                <td><strong>${l.user_name}</strong></td>
                <td><span class="badge-tag">${l.action_type}</span></td>
                <td><small style="max-width: 250px; display: inline-block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${l.prompt}">${l.prompt}</small></td>
                <td><small style="max-width: 250px; display: inline-block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${l.response_text}">${l.response_text}</small></td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Lỗi tải AI logs:", err);
    }
}
