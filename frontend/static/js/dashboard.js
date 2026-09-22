// Dashboard & Analytics Module (Executive Manager Dashboard & Marketer Creative Workspace)

let timelineChartInstance = null;
let channelChartInstance = null;

async function loadDashboardData() {
    const user = api.getUser();
    if (!user) return;

    if (user.role === "manager") {
        await loadExecutiveDashboard();
    } else {
        await loadMarketerWorkspaceData();
    }
}

// ================= 1. EXECUTIVE MANAGER DASHBOARD =================
async function loadExecutiveDashboard() {
    try {
        const summary = await api.get("/api/metrics/dashboard");
        renderKPICards(summary);
        renderTimelineChart(summary.performance_timeline);
        renderChannelChart(summary.channel_performance);
        renderRecentCampaigns(summary.recent_campaigns);
        renderWorkflowFunnel(summary.posts_by_status);
        await renderManagerQuickApprovalQueue();
    } catch (err) {
        console.error("Lỗi tải dữ liệu Executive dashboard:", err);
    }
}

function renderKPICards(s) {
    // 1. Budget & Spend
    const budgetSpendEl = document.getElementById("kpi-budget-spend");
    const spendRateEl = document.getElementById("kpi-spend-rate");
    if (budgetSpendEl) {
        budgetSpendEl.textContent = `${formatVND(s.total_spend)} / ${formatVND(s.total_budget)}`;
    }
    if (spendRateEl) {
        const rate = s.total_budget > 0 ? ((s.total_spend / s.total_budget) * 100).toFixed(1) : 0;
        spendRateEl.textContent = `Tỷ lệ giải ngân: ${rate}% hạn mức`;
    }

    // 2. Revenue & ROI
    const revRoiEl = document.getElementById("kpi-revenue-roi");
    const roiBadgeEl = document.getElementById("kpi-roi-badge");
    if (revRoiEl) {
        revRoiEl.textContent = formatVND(s.total_revenue);
    }
    if (roiBadgeEl) {
        roiBadgeEl.textContent = `ROI tổng thể: +${s.overall_roi}%`;
    }

    // 3. Conversions & CPA
    const convCpaEl = document.getElementById("kpi-conversions-cpa");
    const cpaTextEl = document.getElementById("kpi-cpa-text");
    if (convCpaEl) {
        convCpaEl.textContent = s.total_conversions.toLocaleString("vi-VN");
    }
    if (cpaTextEl) {
        cpaTextEl.textContent = `CPA trung bình: ${formatVND(s.avg_cpa)}/lead`;
    }

    // 4. Pending Reviews Count
    const pendingCountEl = document.getElementById("kpi-pending-reviews-count");
    const inReviewCount = s.posts_by_status["in_review"] || 0;
    if (pendingCountEl) {
        pendingCountEl.textContent = `${inReviewCount} bài`;
    }

    // Update Sidebar badge for Manager Approval Center
    const approvalBadge = document.getElementById("badge-approval-count");
    if (approvalBadge) {
        approvalBadge.textContent = inReviewCount;
        approvalBadge.style.display = inReviewCount > 0 ? "inline-block" : "none";
    }
}

async function renderManagerQuickApprovalQueue() {
    const container = document.getElementById("dashboard-quick-approval-list");
    if (!container) return;

    try {
        const posts = await api.get("/api/content?status=in_review");
        if (!posts || posts.length === 0) {
            container.innerHTML = `
                <div class="empty-placeholder" style="grid-column: 1/-1; padding: 1.5rem;">
                    <i data-lucide="check-circle" class="text-success"></i>
                    <p>Hiện không có bài viết nào đang chờ duyệt. Toàn bộ nội dung đã được xử lý!</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        // Render top 3 pending posts for quick review
        container.innerHTML = posts.slice(0, 3).map(p => `
            <div class="quick-approval-item">
                <div class="quick-approval-header">
                    <span class="badge-tag" style="border-left: 3px solid ${p.channel_color || '#3b82f6'};">${p.channel_name}</span>
                    <span class="badge-status status-in_review">CHỜ DUYỆT</span>
                </div>
                <h4 class="quick-post-title">${p.title}</h4>
                <p class="quick-post-snippet">${p.content.substring(0, 110)}...</p>
                <div class="quick-post-meta">
                    <span>👤 ${p.author_name || 'Marketer'}</span>
                    <span>🎯 ${p.campaign_name || 'Chiến dịch'}</span>
                </div>
                <div class="quick-approval-actions">
                    <button class="btn btn-outline btn-sm" onclick="openReviewModal(${p.id})">
                        <i data-lucide="eye"></i> Xem & Góp ý
                    </button>
                    <button class="btn btn-success btn-sm" onclick="quickApprovePost(${p.id})">
                        <i data-lucide="check"></i> Duyệt ngay
                    </button>
                </div>
            </div>
        `).join("");

        lucide.createIcons();
    } catch (err) {
        console.error("Lỗi tải quick approval queue:", err);
    }
}

function renderTimelineChart(timeline) {
    const ctx = document.getElementById("chart-timeline");
    if (!ctx) return;

    if (timelineChartInstance) {
        timelineChartInstance.destroy();
    }

    const labels = timeline.map(t => {
        const d = new Date(t.date);
        return `${d.getDate()}/${d.getMonth() + 1}`;
    });
    const revenues = timeline.map(t => t.revenue);
    const spends = timeline.map(t => t.spend);

    timelineChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels.length ? labels : ["1/9", "2/9", "3/9", "4/9", "5/9"],
            datasets: [
                {
                    label: "Doanh thu (VNĐ)",
                    data: revenues.length ? revenues : [20000000, 35000000, 48000000, 75000000, 92000000],
                    borderColor: "#10b981",
                    backgroundColor: "rgba(16, 185, 129, 0.12)",
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                },
                {
                    label: "Chi phí thực chi (VNĐ)",
                    data: spends.length ? spends : [8000000, 12000000, 15000000, 22000000, 28000000],
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99, 102, 241, 0.12)",
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: "#94a3b8" }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#64748b" }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: {
                        color: "#64748b",
                        callback: function(value) {
                            return (value / 1000000) + " Tr";
                        }
                    }
                }
            }
        }
    });
}

function renderChannelChart(channels) {
    const ctx = document.getElementById("chart-channel");
    if (!ctx) return;

    if (channelChartInstance) {
        channelChartInstance.destroy();
    }

    const labels = channels.map(c => c.channel_name);
    const data = channels.map(c => c.conversions);
    const colors = channels.map(c => c.channel_color || "#3b82f6");

    channelChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: { color: "#94a3b8", boxWidth: 12, padding: 15 }
                }
            },
            cutout: "68%"
        }
    });
}

function renderRecentCampaigns(campaigns) {
    const tbody = document.getElementById("tbody-recent-campaigns");
    if (!tbody) return;

    if (!campaigns || campaigns.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Chưa có chiến dịch nào</td></tr>`;
        return;
    }

    tbody.innerHTML = campaigns.map(c => {
        let statusBadge = `<span class="badge-status status-${c.status}">${c.status.toUpperCase()}</span>`;
        return `
            <tr>
                <td><strong>${c.name}</strong><br><small class="text-muted">${c.objective}</small></td>
                <td>${formatVND(c.budget)}</td>
                <td>${formatVND(c.spend)}</td>
                <td><span class="text-success font-weight-bold">+${c.roi}%</span></td>
                <td>${statusBadge}</td>
            </tr>
        `;
    }).join("");
}

function renderWorkflowFunnel(postsByStatus) {
    const container = document.getElementById("dashboard-workflow-funnel");
    if (!container) return;

    const items = [
        { key: "draft", label: "Bản nháp (Draft)", icon: "edit-3", color: "var(--text-muted)" },
        { key: "in_review", label: "Chờ Quản lý Duyệt (In Review)", icon: "clock", color: "var(--warning)" },
        { key: "approved", label: "Đã phê duyệt (Approved)", icon: "check-circle", color: "var(--info)" },
        { key: "published", label: "Đã xuất bản (Published)", icon: "send", color: "var(--success)" }
    ];

    container.innerHTML = items.map(it => {
        const count = postsByStatus[it.key] || 0;
        return `
            <div class="funnel-step">
                <div class="funnel-info">
                    <i data-lucide="${it.icon}" style="color: ${it.color}"></i>
                    <span>${it.label}</span>
                </div>
                <span class="funnel-count">${count}</span>
            </div>
        `;
    }).join("");

    lucide.createIcons();
}


// ================= 2. MARKETER CREATIVE WORKSPACE DATA =================
async function loadMarketerWorkspaceData() {
    try {
        const data = await api.get("/api/metrics/marketer-dashboard");
        renderMarketerWorkspace(data);
    } catch (err) {
        console.error("Lỗi tải Marketer Workspace:", err);
    }
}

function renderMarketerWorkspace(data) {
    if (!data) return;

    // 1. Marketer KPI Cards
    const totalPostsEl = document.getElementById("marketer-kpi-total-posts");
    const pubSubEl = document.getElementById("marketer-kpi-published-sub");
    const inReviewEl = document.getElementById("marketer-kpi-in-review");
    const rejectedEl = document.getElementById("marketer-kpi-rejected");
    const passRateEl = document.getElementById("marketer-kpi-pass-rate");
    const aiCountEl = document.getElementById("marketer-kpi-ai-count");

    if (totalPostsEl) totalPostsEl.textContent = data.total_posts;
    if (pubSubEl) pubSubEl.textContent = `${data.published_count} bài đã xuất bản`;
    if (inReviewEl) inReviewEl.textContent = data.in_review_count;
    if (rejectedEl) rejectedEl.textContent = data.rejected_count;
    if (passRateEl) passRateEl.textContent = `${data.approval_rate}%`;
    if (aiCountEl) aiCountEl.textContent = `${data.ai_posts_count} bài ứng dụng AI`;

    // 2. Feedback Alert Banner & Sidebar Badge
    const feedbackBanner = document.getElementById("marketer-feedback-alert-banner");
    const feedbackBadge = document.getElementById("badge-feedback-count");
    const feedbackCenterBadge = document.getElementById("feedback-center-badge-count");
    
    if (feedbackBadge) {
        feedbackBadge.textContent = data.rejected_count;
        feedbackBadge.style.display = data.rejected_count > 0 ? "inline-block" : "none";
    }
    if (feedbackCenterBadge) {
        feedbackCenterBadge.textContent = `${data.rejected_count} bài cần sửa`;
    }

    if (feedbackBanner) {
        if (data.rejected_count > 0) {
            feedbackBanner.style.display = "flex";
            const feedbackText = document.getElementById("marketer-feedback-alert-text");
            if (feedbackText && data.feedbacks && data.feedbacks.length > 0) {
                const latest = data.feedbacks[0];
                feedbackText.innerHTML = `<strong>Bài "${latest.post_title}":</strong> <em>"${latest.feedback}"</em> (Lời nhắn từ ${latest.reviewer_name})`;
            }
        } else {
            feedbackBanner.style.display = "none";
        }
    }

    // 3. Render Marketer Recent Drafts
    const tbodyDrafts = document.getElementById("tbody-marketer-recent-drafts");
    if (tbodyDrafts) {
        if (!data.recent_drafts || data.recent_drafts.length === 0) {
            tbodyDrafts.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Bạn chưa tạo bài viết nào. Hãy bấm "Soạn bài mới"!</td></tr>`;
        } else {
            tbodyDrafts.innerHTML = data.recent_drafts.map(p => {
                const statusBadge = `<span class="badge-status status-${p.status}">${p.status.toUpperCase()}</span>`;
                const isAI = p.ai_generated ? `<span class="badge-ai-flag"><i data-lucide="sparkles"></i> AI</span>` : '';
                
                let actionBtn = `<button class="btn btn-outline btn-sm" onclick="openEditPostModal(${p.id})"><i data-lucide="edit-2"></i></button>`;
                if (p.status === "draft") {
                    actionBtn += ` <button class="btn btn-primary btn-sm" onclick="submitPostForReview(${p.id})"><i data-lucide="send"></i> Gửi duyệt</button>`;
                } else if (p.status === "rejected") {
                    actionBtn += ` <button class="btn btn-warning btn-sm" onclick="openEditPostModal(${p.id})"><i data-lucide="tool"></i> Sửa lại</button>`;
                }

                return `
                    <tr>
                        <td>
                            <strong>${p.title}</strong>
                            <div style="margin-top: 0.2rem;">
                                <span class="badge-tag" style="border-left: 3px solid ${p.channel_color};">${p.channel_name}</span>
                                ${isAI}
                            </div>
                        </td>
                        <td>${p.campaign_name || '-'}</td>
                        <td>${statusBadge}</td>
                        <td>${actionBtn}</td>
                    </tr>
                `;
            }).join("");
        }
    }

    // 4. Render Upcoming Scheduled Events
    const eventsContainer = document.getElementById("marketer-upcoming-events-list");
    if (eventsContainer) {
        if (!data.upcoming_posts || data.upcoming_posts.length === 0) {
            eventsContainer.innerHTML = `
                <div class="empty-placeholder" style="padding: 1.5rem;">
                    <i data-lucide="calendar"></i>
                    <p>Chưa có bài viết nào được lên lịch phát hành trong thời gian tới.</p>
                </div>
            `;
        } else {
            eventsContainer.innerHTML = data.upcoming_posts.map(ev => `
                <div class="upcoming-event-item">
                    <div class="event-time-badge">
                        <i data-lucide="clock"></i>
                        <span>${formatDateTime(ev.scheduled_at)}</span>
                    </div>
                    <div class="event-details">
                        <h5>${ev.title}</h5>
                        <span class="badge-tag">${ev.channel_name}</span>
                    </div>
                    <span class="badge-status status-${ev.status}">${ev.status.toUpperCase()}</span>
                </div>
            `).join("");
        }
    }

    lucide.createIcons();
}

// 3. Fast AI Creator Handler for Marketer
function handleFastAICreate() {
    const channel = document.getElementById("fast-ai-channel").value;
    const topic = document.getElementById("fast-ai-topic").value.trim();

    if (!topic) {
        showToast("Vui lòng nhập chủ đề hoặc ý tưởng bài viết!", "warning");
        return;
    }

    switchView("ai-assistant");
    switchAITab("content");

    const channelSelect = document.getElementById("ai-content-channel");
    const topicTextarea = document.getElementById("ai-content-topic");

    if (channelSelect) channelSelect.value = channel;
    if (topicTextarea) topicTextarea.value = topic;

    triggerAIContentGenerator();
}

async function quickApprovePost(postId) {
    try {
        await api.put(`/api/content/${postId}/review`, {
            action: "approve",
            feedback: "Đã phê duyệt nhanh qua Executive Approval Queue."
        });
        showToast("Đã phê duyệt bài viết thành công!", "success");
        loadDashboardData();
        loadContent();
    } catch (err) {
        showToast(err.message || "Lỗi phê duyệt bài viết", "error");
    }
}
