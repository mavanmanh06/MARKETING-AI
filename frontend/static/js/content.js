// Content, Approval Center, Feedback & Team Management Module

let globalPosts = [];

function switchContentTab(tabName, e) {
    if (e) e.preventDefault();
    document.querySelectorAll(".sub-nav-bar .tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".content-subview").forEach(v => v.classList.remove("active"));

    if (e && e.currentTarget) e.currentTarget.classList.add("active");
    const target = document.getElementById(`content-tab-${tabName}`);
    if (target) target.classList.add("active");

    if (tabName === "calendar") {
        renderCalendarView();
    }
}

async function loadContent() {
    try {
        globalPosts = await api.get("/api/content");
        renderContentList(globalPosts);
        renderKanbanBoard(globalPosts);
        renderCalendarView();
        
        const user = api.getUser();
        if (user) {
            if (isManagementRole(user.role)) {
                renderApprovalCenter();
                loadTeamManagement();
            } else {
                renderFeedbackCenter();
                renderMyPerformance();
            }
        }
    } catch (err) {
        console.error("Lỗi tải nội dung:", err);
    }
}

function renderContentList(posts) {
    const tbody = document.getElementById("tbody-content-list");
    if (!tbody) return;

    if (!posts || posts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Chưa có bài viết nào</td></tr>`;
        return;
    }

    const currentUser = api.getUser();
    const isManager = currentUser && isManagementRole(currentUser.role);

    tbody.innerHTML = posts.map(p => {
        const isAI = p.ai_generated ? `<span class="badge-ai-flag"><i data-lucide="sparkles"></i> AI</span>` : `<span class="badge-tag">Thủ công</span>`;
        const channelBadge = `<span class="badge-tag" style="border-left: 3px solid ${p.channel_color || '#3b82f6'};">${p.channel_name}</span>`;
        const statusBadge = `<span class="badge-status status-${p.status}">${p.status.toUpperCase()}</span>`;

        let actionBtns = '';
        if (p.status === "in_review" && isManager) {
            actionBtns += `
                <button class="btn btn-primary btn-sm" onclick="openReviewModal(${p.id})">
                    <i data-lucide="check-square"></i> Duyệt bài
                </button>
            `;
        } else if (p.status === "draft") {
            actionBtns += `
                <button class="btn btn-outline btn-sm" onclick="submitPostForReview(${p.id})">
                    <i data-lucide="send"></i> Gửi duyệt
                </button>
            `;
        } else if (p.status === "approved") {
            actionBtns += `
                <button class="btn btn-success btn-sm" onclick="publishPostDirectly(${p.id})">
                    <i data-lucide="upload"></i> Xuất bản
                </button>
            `;
        } else if (p.status === "rejected" && !isManager) {
            actionBtns += `
                <button class="btn btn-warning btn-sm" onclick="openEditPostModal(${p.id})" title="Xem góp ý và sửa lại">
                    <i data-lucide="tool"></i> Sửa lại
                </button>
            `;
        }

        actionBtns += `
            <button class="btn btn-outline btn-sm" onclick="openEditPostModal(${p.id})" title="Chỉnh sửa">
                <i data-lucide="edit-2"></i>
            </button>
        `;

        if (isManager || (currentUser && p.author_id === currentUser.id)) {
            actionBtns += `
                <button class="btn btn-outline btn-sm text-danger" onclick="handleDeletePost(${p.id})" title="Xóa">
                    <i data-lucide="trash"></i>
                </button>
            `;
        }

        return `
            <tr>
                <td>
                    <strong>${p.title}</strong>
                    <div style="margin-top: 0.25rem;">${channelBadge}</div>
                </td>
                <td>${p.campaign_name || '-'}</td>
                <td>${p.author_name || 'Admin'}</td>
                <td>${formatDateTime(p.scheduled_at)}</td>
                <td>${isAI}</td>
                <td>${statusBadge}</td>
                <td><div style="display: flex; gap: 0.35rem; align-items: center;">${actionBtns}</div></td>
            </tr>
        `;
    }).join("");

    lucide.createIcons();
}

function renderKanbanBoard(posts) {
    const container = document.getElementById("kanban-board-container");
    if (!container) return;

    const columns = [
        { status: "draft", title: "Bản nháp (Draft)", color: "#94a3b8", icon: "edit-3" },
        { status: "in_review", title: "Chờ Phê duyệt (In Review)", color: "#f59e0b", icon: "clock" },
        { status: "approved", title: "Đã duyệt (Approved)", color: "#3b82f6", icon: "check-circle" },
        { status: "published", title: "Đã xuất bản (Published)", color: "#10b981", icon: "send" }
    ];

    const currentUser = api.getUser();
    const isManager = currentUser && isManagementRole(currentUser.role);

    container.innerHTML = columns.map(col => {
        const colPosts = posts.filter(p => p.status === col.status);
        const cardsHtml = colPosts.map(p => {
            const isAI = p.ai_generated ? `<span class="badge-ai-flag"><i data-lucide="sparkles"></i> AI</span>` : '';
            return `
                <div class="kanban-card">
                    <div class="kanban-card-meta">
                        <span class="badge-tag" style="border-left: 2px solid ${p.channel_color || '#3b82f6'};">${p.channel_name}</span>
                        ${isAI}
                    </div>
                    <h5>${p.title}</h5>
                    <p class="kanban-snippet">${p.content.substring(0, 80)}...</p>
                    <div class="kanban-footer">
                        <span>👤 ${p.author_name || 'Admin'}</span>
                        <div class="kanban-actions">
                            ${(p.status === "in_review" && isManager) ? `
                                <button class="btn btn-primary btn-sm" onclick="openReviewModal(${p.id})">Duyệt</button>
                            ` : ''}
                            <button class="btn btn-outline btn-sm" onclick="openEditPostModal(${p.id})"><i data-lucide="edit-2"></i></button>
                        </div>
                    </div>
                </div>
            `;
        }).join("");

        return `
            <div class="kanban-column">
                <div class="kanban-column-header">
                    <div class="kanban-col-title" style="color: ${col.color}">
                        <i data-lucide="${col.icon}"></i>
                        <span>${col.title}</span>
                    </div>
                    <span class="badge-pill" style="background: rgba(255,255,255,0.1); color: var(--text-primary);">${colPosts.length}</span>
                </div>
                <div class="kanban-cards-wrapper">
                    ${cardsHtml || '<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 2rem 0;">Không có bài</div>'}
                </div>
            </div>
        `;
    }).join("");

    lucide.createIcons();
}

function renderCalendarView() {
    const grid = document.getElementById("calendar-grid-container");
    if (!grid) return;

    const daysInMonth = 28;
    let html = '';

    for (let day = 1; day <= daysInMonth; day++) {
        const dayPosts = globalPosts.filter(p => {
            if (!p.scheduled_at) return false;
            const d = new Date(p.scheduled_at);
            return d.getDate() === day;
        });

        const postPills = dayPosts.map(p => `
            <div class="cal-event-pill" onclick="openEditPostModal(${p.id})" title="${p.title}">
                [${p.channel_name}] ${p.title}
            </div>
        `).join("");

        html += `
            <div class="calendar-day-box">
                <span class="cal-day-num">${day}/9</span>
                ${postPills}
            </div>
        `;
    }

    grid.innerHTML = html;
}


// ================= 1. APPROVAL CENTER (FOR MANAGER) =================
function renderApprovalCenter() {
    const container = document.getElementById("approval-cards-container");
    if (!container) return;

    const filterSelect = document.getElementById("approval-filter-status");
    const filterVal = filterSelect ? filterSelect.value : "in_review";

    let filteredPosts = globalPosts;
    if (filterVal !== "all") {
        filteredPosts = globalPosts.filter(p => p.status === filterVal);
    }

    // Stats Pills
    const pendingCount = globalPosts.filter(p => p.status === "in_review").length;
    const approvedCount = globalPosts.filter(p => p.status === "approved" || p.status === "published").length;
    const rejectedCount = globalPosts.filter(p => p.status === "rejected").length;

    const elPending = document.getElementById("approval-count-pending");
    const elApproved = document.getElementById("approval-count-approved");
    const elRejected = document.getElementById("approval-count-rejected");
    if (elPending) elPending.textContent = pendingCount;
    if (elApproved) elApproved.textContent = approvedCount;
    if (elRejected) elRejected.textContent = rejectedCount;

    if (!filteredPosts || filteredPosts.length === 0) {
        container.innerHTML = `
            <div class="empty-placeholder" style="grid-column: 1/-1; padding: 3rem;">
                <i data-lucide="check-circle-2" class="text-success" style="width: 48px; height: 48px;"></i>
                <h3>Không có bài viết nào cần xử lý</h3>
                <p>Mọi bài viết trong danh mục này đã được cập nhật trạng thái mới nhất.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    container.innerHTML = filteredPosts.map(p => {
        const isAI = p.ai_generated ? `<span class="badge-ai-flag"><i data-lucide="sparkles"></i> AI Generated</span>` : `<span class="badge-tag">Thủ công</span>`;
        const channelBadge = `<span class="badge-tag" style="border-left: 3px solid ${p.channel_color || '#3b82f6'};">${p.channel_name}</span>`;
        const statusBadge = `<span class="badge-status status-${p.status}">${p.status.toUpperCase()}</span>`;

        return `
            <div class="approval-card ${p.status === 'in_review' ? 'approval-card-pending' : ''}">
                <div class="approval-card-header">
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        ${channelBadge}
                        ${isAI}
                    </div>
                    ${statusBadge}
                </div>

                <h3 class="approval-card-title">${p.title}</h3>
                <div class="approval-card-body">${p.content}</div>

                ${p.hashtags ? `<div class="approval-hashtags">${p.hashtags}</div>` : ''}

                <div class="approval-card-meta">
                    <span>👤 Tác giả: <strong>${p.author_name || 'Marketer'}</strong></span>
                    <span>🎯 Chiến dịch: <strong>${p.campaign_name || '-'}</strong></span>
                    <span>📅 Dự kiến: <strong>${formatDateTime(p.scheduled_at)}</strong></span>
                </div>

                ${p.reviewer_feedback ? `
                    <div class="approval-feedback-history">
                        <strong>💬 Góp ý trước đó của Quản lý:</strong>
                        <p><em>"${p.reviewer_feedback}"</em></p>
                    </div>
                ` : ''}

                <div class="approval-card-actions">
                    <button class="btn btn-outline" onclick="openEditPostModal(${p.id})">
                        <i data-lucide="edit-2"></i> Chỉnh sửa
                    </button>
                    ${p.status === "in_review" ? `
                        <button class="btn btn-danger" onclick="openReviewModal(${p.id})">
                            <i data-lucide="x-circle"></i> Từ chối & Góp ý
                        </button>
                        <button class="btn btn-success" onclick="quickApprovePost(${p.id})">
                            <i data-lucide="check-circle-2"></i> Phê Duyệt Ngay
                        </button>
                    ` : (p.status === "approved" ? `
                        <button class="btn btn-success" onclick="publishPostDirectly(${p.id})">
                            <i data-lucide="upload"></i> Xuất bản ngay
                        </button>
                    ` : '')}
                </div>
            </div>
        `;
    }).join("");

    lucide.createIcons();
}


// ================= 2. FEEDBACK & REVISIONS CENTER (FOR MARKETER) =================
function renderFeedbackCenter() {
    const container = document.getElementById("feedback-cards-container");
    if (!container) return;

    const currentUser = api.getUser();
    if (!currentUser) return;

    // Filter posts of this marketer that have status = 'rejected' or have feedback
    const rejectedPosts = globalPosts.filter(p => p.author_id === currentUser.id && (p.status === "rejected" || p.reviewer_feedback));

    const badgeCount = document.getElementById("feedback-center-badge-count");
    const activeRejections = globalPosts.filter(p => p.author_id === currentUser.id && p.status === "rejected").length;
    if (badgeCount) {
        badgeCount.textContent = `${activeRejections} bài cần sửa`;
    }

    if (!rejectedPosts || rejectedPosts.length === 0) {
        container.innerHTML = `
            <div class="empty-placeholder" style="grid-column: 1/-1; padding: 3rem;">
                <i data-lucide="check-circle-2" class="text-success" style="width: 48px; height: 48px;"></i>
                <h3>Tuyệt vời! Không có bài viết nào bị yêu cầu sửa đổi</h3>
                <p>Tất cả nội dung bạn soạn thảo đều đạt chuẩn hoặc đang trong quá trình xét duyệt.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    container.innerHTML = rejectedPosts.map(p => `
        <div class="feedback-card ${p.status === 'rejected' ? 'feedback-card-urgent' : ''}">
            <div class="feedback-card-header">
                <span class="badge-tag" style="border-left: 3px solid ${p.channel_color || '#3b82f6'};">${p.channel_name}</span>
                <span class="badge-status status-${p.status}">${p.status.toUpperCase()}</span>
            </div>

            <h3 class="feedback-title">${p.title}</h3>
            <p class="feedback-snippet">${p.content.substring(0, 160)}...</p>

            <div class="feedback-quote-box">
                <div class="feedback-quote-header">
                    <i data-lucide="message-square-warning" class="text-danger"></i>
                    <strong>Lời nhắn từ ${p.reviewer_name || 'Quản lý'}:</strong>
                </div>
                <p class="feedback-quote-text">"${p.reviewer_feedback || 'Vui lòng kiểm tra và trau chuốt lại câu từ.'}"</p>
                <span class="feedback-quote-time">🕒 Gửi lúc: ${formatDateTime(p.reviewed_at)}</span>
            </div>

            <div class="feedback-card-footer">
                <div class="feedback-meta">
                    <span>🎯 ${p.campaign_name || 'Chiến dịch'}</span>
                </div>
                <div class="feedback-actions">
                    <button class="btn btn-warning" onclick="openEditPostModal(${p.id})">
                        <i data-lucide="edit-3"></i> Chỉnh sửa theo góp ý & Gửi duyệt lại
                    </button>
                </div>
            </div>
        </div>
    `).join("");

    lucide.createIcons();
}


// ================= 3. MY PERFORMANCE (FOR MARKETER) =================
function renderMyPerformance() {
    const tbody = document.getElementById("tbody-my-performance");
    if (!tbody) return;

    const currentUser = api.getUser();
    if (!currentUser) return;

    const myPosts = globalPosts.filter(p => p.author_id === currentUser.id);
    if (!myPosts || myPosts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Bạn chưa tạo bài viết nào trong hệ thống</td></tr>`;
        return;
    }

    tbody.innerHTML = myPosts.map(p => {
        const isAI = p.ai_generated ? `<span class="badge-ai-flag"><i data-lucide="sparkles"></i> AI</span>` : `<span class="badge-tag">Thủ công</span>`;
        const channelBadge = `<span class="badge-tag" style="border-left: 3px solid ${p.channel_color || '#3b82f6'};">${p.channel_name}</span>`;
        const statusBadge = `<span class="badge-status status-${p.status}">${p.status.toUpperCase()}</span>`;

        let feedbackText = '-';
        if (p.reviewer_feedback) {
            feedbackText = `<small class="text-warning"><strong>${p.reviewer_name || 'Quản lý'}:</strong> "${p.reviewer_feedback.substring(0, 50)}..."</small>`;
        }

        let actionBtn = `<button class="btn btn-outline btn-sm" onclick="openEditPostModal(${p.id})"><i data-lucide="edit-2"></i></button>`;
        if (p.status === "draft") {
            actionBtn += ` <button class="btn btn-primary btn-sm" onclick="submitPostForReview(${p.id})"><i data-lucide="send"></i></button>`;
        } else if (p.status === "rejected") {
            actionBtn += ` <button class="btn btn-warning btn-sm" onclick="openEditPostModal(${p.id})"><i data-lucide="tool"></i> Sửa</button>`;
        }

        return `
            <tr>
                <td><strong>${p.title}</strong></td>
                <td>${p.campaign_name || '-'}</td>
                <td>${channelBadge}</td>
                <td>${isAI}</td>
                <td>${formatDateTime(p.scheduled_at)}</td>
                <td>${statusBadge}</td>
                <td>${feedbackText}</td>
                <td>${actionBtn}</td>
            </tr>
        `;
    }).join("");

    lucide.createIcons();
}


// ================= 4. TEAM MANAGEMENT (FOR MANAGER & ADMIN) =================
async function loadTeamManagement() {
    const tbody = document.getElementById("tbody-team-members");
    if (!tbody) return;

    try {
        const team = await api.get("/api/auth/team-stats");
        if (!team || team.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">Chưa có thành viên nào</td></tr>`;
            return;
        }

        // Summary stats
        const totalMembers = team.length;
        const totalPosts = team.reduce((acc, u) => acc + u.total_posts, 0);
        const avgPassRate = team.length > 0 ? (team.reduce((acc, u) => acc + u.pass_rate, 0) / team.length).toFixed(1) : 100;

        const elTotalMembers = document.getElementById("team-stat-total-members");
        const elTotalPosts = document.getElementById("team-stat-total-posts");
        const elAvgPass = document.getElementById("team-stat-avg-pass-rate");
        if (elTotalMembers) elTotalMembers.textContent = totalMembers;
        if (elTotalPosts) elTotalPosts.textContent = totalPosts;
        if (elAvgPass) elAvgPass.textContent = `${avgPassRate}%`;

        const currentUser = api.getUser();
        const isAdmin = currentUser && currentUser.role === "admin";

        tbody.innerHTML = team.map(u => {
            const roleBadge = u.role === "admin"
                ? `<span class="user-role-badge manager-badge">🛡️ Quản trị viên</span>`
                : u.role === "manager"
                    ? `<span class="user-role-badge manager-badge">🛡️ Quản lý</span>`
                    : `<span class="user-role-badge marketer-badge">⚡ Nhân viên</span>`;
            
            // Xử lý cột thao tác: Chỉ Quản trị viên (Admin) mới có quyền xóa thành viên khỏi nhóm
            let actionHtml = "";
            if (isAdmin) {
                if (currentUser && u.id === currentUser.id) {
                    actionHtml = `<span class="badge-tag text-muted" style="font-size: 0.75rem;">(Chính bạn)</span>`;
                } else if (u.email === "admin@marketing.ai") {
                    actionHtml = `<span class="badge-tag text-muted" style="font-size: 0.75rem;">(Admin gốc)</span>`;
                } else {
                    const safeName = (u.full_name || "Thành viên").replace(/'/g, "\'");
                    actionHtml = `
                        <button class="btn btn-outline btn-sm text-danger" style="padding: 4px 10px; border-color: rgba(239, 68, 68, 0.4); font-size: 0.8rem; display: inline-flex; align-items: center; gap: 4px;" onclick="deleteTeamMember(${u.id}, '${safeName}')">
                            <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i> Xóa
                        </button>
                    `;
                }
            } else {
                actionHtml = `<span class="text-muted" style="font-size: 0.75rem;">(Chỉ xem)</span>`;
            }

            return `
                <tr>
                    <td>
                        <div class="team-member-cell">
                            <img src="${u.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'}" class="user-img-sm" alt="Avatar">
                            <div>
                                <strong>${u.full_name}</strong>
                                <small class="text-muted d-block">${formatDate(u.created_at)}</small>
                            </div>
                        </div>
                    </td>
                    <td>${u.email}</td>
                    <td>${roleBadge}</td>
                    <td><strong>${u.total_posts}</strong></td>
                    <td><span class="text-success">${u.approved_posts + u.published_posts}</span> bài</td>
                    <td><span class="badge-ai-flag">${u.ai_generated_posts} bài</span></td>
                    <td><strong class="text-success">${u.pass_rate}%</strong></td>
                    <td><span class="badge-tag" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">Đang hoạt động</span></td>
                    <td>${actionHtml}</td>
                </tr>
            `;
        }).join("");

        lucide.createIcons();
    } catch (err) {
        console.error("Lỗi tải thông tin Team Management:", err);
    }
}

async function deleteTeamMember(userId, fullName) {
    const user = api.getUser();
    if (!user || user.role !== "admin") {
        showToast("Chỉ Quản trị viên (Admin) mới có quyền xóa thành viên khỏi hệ thống!", "error");
        return;
    }

    if (!confirm(`Bạn có chắc chắn muốn xóa thành viên "${fullName}" khỏi hệ thống?\n\nLưu ý: Các bài viết của thành viên sẽ được dọn dẹp và các chiến dịch sẽ được bàn giao về cho Quản trị viên quản lý.`)) {
        return;
    }

    try {
        const res = await api.delete(`/api/auth/users/${userId}`);
        showToast(res.message || `Đã xóa thành viên "${fullName}" thành công!`, "success");
        await loadTeamManagement();
    } catch (err) {
        showToast(err.message || "Lỗi xóa thành viên", "error");
    }
}


// ================= 5. MODAL HELPERS & POST CRUD =================
function openCreatePostModal() {
    document.getElementById("form-post").reset();
    document.getElementById("post-edit-id").value = "";
    document.getElementById("modal-post-title").textContent = "Tạo Bài Viết & Lịch Đăng Mới";

    const d = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000);
    d.setHours(9, 0, 0, 0);
    const dateLocal = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    document.getElementById("post-form-scheduled").value = dateLocal;

    openModal("modal-post");
}

function openEditPostModal(postId) {
    const p = globalPosts.find(item => item.id === postId);
    if (!p) return;

    document.getElementById("post-edit-id").value = p.id;
    document.getElementById("modal-post-title").textContent = "Chỉnh sửa Bài viết";
    document.getElementById("post-form-campaign").value = p.campaign_id;
    document.getElementById("post-form-channel").value = p.channel_id;
    document.getElementById("post-form-title").value = p.title;
    document.getElementById("post-form-content").value = p.content;
    document.getElementById("post-form-hashtags").value = p.hashtags || "";
    document.getElementById("post-form-cta").value = p.call_to_action || "";
    document.getElementById("post-form-status").value = p.status;

    if (p.scheduled_at) {
        const d = new Date(p.scheduled_at);
        const dateLocal = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
        document.getElementById("post-form-scheduled").value = dateLocal;
    }

    openModal("modal-post");
}

async function handleSavePost(e) {
    e.preventDefault();
    const editId = document.getElementById("post-edit-id").value;
    const campaign_id = parseInt(document.getElementById("post-form-campaign").value);
    const channel_id = parseInt(document.getElementById("post-form-channel").value);
    const title = document.getElementById("post-form-title").value.trim();
    const content = document.getElementById("post-form-content").value.trim();
    const hashtags = document.getElementById("post-form-hashtags").value.trim();
    const call_to_action = document.getElementById("post-form-cta").value.trim();
    const status = document.getElementById("post-form-status").value;
    const schedVal = document.getElementById("post-form-scheduled").value;
    const scheduled_at = schedVal ? new Date(schedVal).toISOString() : null;

    const payload = {
        campaign_id,
        channel_id,
        title,
        content,
        hashtags,
        call_to_action,
        status,
        scheduled_at
    };

    try {
        if (editId) {
            await api.put(`/api/content/${editId}`, payload);
            showToast("Đã cập nhật bài viết thành công!", "success");
        } else {
            await api.post("/api/content", payload);
            showToast("Đã thêm bài viết mới vào hệ thống!", "success");
        }
        closeModal("modal-post");
        loadContent();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi lưu bài viết", "error");
    }
}

async function submitPostForReview(postId) {
    try {
        await api.put(`/api/content/${postId}/review`, { action: "submit_for_review" });
        showToast("Đã gửi bài viết lên Quản lý để phê duyệt!", "success");
        loadContent();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi gửi duyệt", "error");
    }
}

async function publishPostDirectly(postId) {
    try {
        await api.put(`/api/content/${postId}/review`, { action: "publish" });
        showToast("Đã xuất bản bài viết thành công lên kênh!", "success");
        loadContent();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi xuất bản", "error");
    }
}

function openReviewModal(postId) {
    const p = globalPosts.find(item => item.id === postId);
    if (!p) return;

    document.getElementById("review-post-id").value = p.id;
    document.getElementById("review-post-title").textContent = p.title;
    document.getElementById("review-post-channel").textContent = p.channel_name;
    document.getElementById("review-post-campaign").textContent = p.campaign_name;
    document.getElementById("review-post-author").textContent = `Tác giả: ${p.author_name || 'Marketer'}`;
    document.getElementById("review-post-body").textContent = p.content;
    document.getElementById("review-feedback-input").value = p.reviewer_feedback || "";

    const aiTag = document.getElementById("review-post-ai-tag");
    if (aiTag) aiTag.style.display = p.ai_generated ? "inline-flex" : "none";

    openModal("modal-review-post");
}

async function executePostReview(action) {
    const postId = document.getElementById("review-post-id").value;
    const feedback = document.getElementById("review-feedback-input").value.trim();

    try {
        await api.put(`/api/content/${postId}/review`, { action, feedback });
        const msg = action === "approve" 
            ? "Đã phê duyệt bài viết thành công!" 
            : "Đã yêu cầu chỉnh sửa và gửi phản hồi đến Hộp thư của nhân viên.";
        showToast(msg, action === "approve" ? "success" : "info");
        closeModal("modal-review-post");
        loadContent();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi phê duyệt bài viết", "error");
    }
}

async function handleDeletePost(postId) {
    if (!confirm("Bạn có chắc chắn muốn xóa bài viết này?")) return;
    try {
        await api.delete(`/api/content/${postId}`);
        showToast("Đã xóa bài viết thành công!", "success");
        loadContent();
        loadDashboardData();
    } catch (err) {
        showToast(err.message || "Lỗi xóa bài viết", "error");
    }
}

function openAIGenForCurrentPost() {
    closeModal("modal-post");
    switchView("ai-assistant");
    switchAITab("content");
}
