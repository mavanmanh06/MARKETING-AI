// Auth Module with Full Role-Based UI Architecture

function isManagementRole(role) {
    return role === "admin" || role === "manager";
}

function getRoleName(role) {
    if (role === "admin") return "Quản trị viên (Admin)";
    if (role === "manager") return "Quản lý (Manager)";
    return "Nhân viên (Marketer)";
}

function quickFill(email, password) {
    const emailEl = document.getElementById("login-email");
    const passEl = document.getElementById("login-password");
    if (emailEl) emailEl.value = email || "";
    if (passEl) passEl.value = password || "";
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
    } else {
        input.type = "password";
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const btn = document.getElementById("btn-login-submit");

    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="spin"></i> Đang xác thực...`;
    lucide.createIcons();

    try {
        const res = await api.post("/api/auth/login", { email, password });
        api.setToken(res.access_token);
        api.setUser(res.user);

        showToast(`Đăng nhập thành công! Chào mừng ${res.user.full_name} [${getRoleName(res.user.role)}]`, "success");
        initAppAfterAuth();
    } catch (err) {
        showToast(err.message || "Đăng nhập thất bại", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="log-in"></i> Đăng nhập vào Hệ thống`;
        lucide.createIcons();
    }
}

function handleLogout() {
    api.clearToken();
    document.getElementById("main-layout").style.display = "none";
    document.getElementById("auth-screen").style.display = "flex";
    showToast("Đã đăng xuất an toàn khỏi hệ thống", "info");
}

function showRegisterModal(e) {
    if (e) e.preventDefault();
    openModal("modal-register");
}

async function handleRegister(e) {
    e.preventDefault();
    const full_name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    try {
        await api.post("/api/auth/register", { full_name, email, password });
        showToast("Đăng ký tài khoản thành công! Vui lòng đăng nhập với tài khoản vừa tạo.", "success");
        closeModal("modal-register");
        quickFill(email, password);
    } catch (err) {
        showToast(err.message || "Đăng ký thất bại", "error");
    }
}

function updateUserInfoUI(user) {
    if (!user) return;
    
    const isManager = isManagementRole(user.role);

    // 1. Update Body Theme Class
    document.body.className = isManager ? "role-manager" : "role-marketer";

    // 2. Switch Sidebar Navigation Suites
    const managerNav = document.getElementById("nav-manager-suite");
    const marketerNav = document.getElementById("nav-marketer-suite");
    if (managerNav && marketerNav) {
        managerNav.style.display = isManager ? "block" : "none";
        marketerNav.style.display = isManager ? "none" : "block";
    }

    // 3. Sidebar Indicator & User Footer
    const sidebarIndicator = document.getElementById("sidebar-role-indicator");
    const sidebarRoleText = document.getElementById("sidebar-role-text");
    const sidebarName = document.getElementById("sidebar-user-name");
    const sidebarRole = document.getElementById("sidebar-user-role");
    const sidebarAvatar = document.getElementById("user-avatar");
    
    if (sidebarIndicator) {
        sidebarIndicator.className = `sidebar-role-indicator ${isManager ? "indicator-manager" : "indicator-marketer"}`;
    }
    if (sidebarRoleText) {
        sidebarRoleText.textContent = isManager ? "CHẾ ĐỘ QUẢN LÝ (DIRECTOR)" : "CHẾ ĐỘ NHÂN VIÊN (CREATIVE)";
    }
    if (sidebarName) sidebarName.textContent = user.full_name;
    if (sidebarRole) {
        sidebarRole.textContent = user.role === "admin" ? "🛡️ ADMIN" : isManager ? "🛡️ QUẢN LÝ" : "⚡ MARKETER";
        sidebarRole.className = `user-role-badge ${isManager ? "manager-badge" : "marketer-badge"}`;
    }
    if (sidebarAvatar && user.avatar_url) sidebarAvatar.src = user.avatar_url;

    // 4. Header Role Banner
    const headerBanner = document.getElementById("header-role-banner");
    if (headerBanner) {
        if (isManager) {
            headerBanner.className = "role-pill-banner banner-manager";
            const roleName = user.role === "admin" ? "Admin" : "Manager";
            headerBanner.innerHTML = `<i data-lucide="shield-check"></i> <span>Giao diện Quản trị (${roleName} Mode)</span>`;
        } else {
            headerBanner.className = "role-pill-banner banner-marketer";
            headerBanner.innerHTML = `<i data-lucide="sparkles"></i> <span>Không gian Tác nghiệp Sáng tạo (Marketer Mode)</span>`;
        }
    }

    // 5. Header Action Buttons
    const headerActions = document.getElementById("header-actions-container");
    if (headerActions) {
        if (isManager) {
            headerActions.innerHTML = `
                <button class="btn btn-outline" onclick="switchView('approval-center')">
                    <i data-lucide="shield-check"></i> Phê duyệt bài
                </button>
                <button class="btn btn-primary" onclick="openCreateCampaignModal()" id="btn-header-create-campaign">
                    <i data-lucide="plus"></i> Tạo chiến dịch mới
                </button>
            `;
        } else {
            headerActions.innerHTML = `
                <button class="btn btn-outline" onclick="openAIGeneratorModal()">
                    <i data-lucide="sparkles"></i> AI Viết nội dung
                </button>
                <button class="btn btn-primary" onclick="openCreatePostModal()">
                    <i data-lucide="plus"></i> Soạn bài viết mới
                </button>
            `;
        }
    }

    // 6. Marketer Hero Card Greetings
    const heroName = document.getElementById("marketer-hero-name");
    if (heroName) heroName.textContent = user.full_name;

    // 7. Settings Profile
    const settingsName = document.getElementById("settings-fullname");
    const settingsEmail = document.getElementById("settings-email");
    const settingsRoleTag = document.getElementById("settings-role-tag");
    const settingsAvatar = document.getElementById("settings-avatar");

    if (settingsName) settingsName.textContent = user.full_name;
    if (settingsEmail) settingsEmail.textContent = user.email;
    if (settingsRoleTag) {
        settingsRoleTag.textContent = getRoleName(user.role);
        settingsRoleTag.className = `role-tag ${isManager ? "manager-badge" : "marketer-badge"}`;
    }
    if (settingsAvatar && user.avatar_url) settingsAvatar.src = user.avatar_url;

    // 8. Role-based elements visibility
    document.querySelectorAll(".manager-only").forEach(el => {
        el.style.display = isManager ? "" : "none";
    });
    document.querySelectorAll(".marketer-only").forEach(el => {
        el.style.display = !isManager ? "" : "none";
    });

    lucide.createIcons();
}
