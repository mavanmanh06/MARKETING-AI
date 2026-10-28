// API Client Module
const API_BASE = "";

const api = {
    getToken() {
        return localStorage.getItem("marketing_ai_token") || "";
    },

    setToken(token) {
        localStorage.setItem("marketing_ai_token", token);
    },

    clearToken() {
        localStorage.removeItem("marketing_ai_token");
        localStorage.removeItem("marketing_ai_user");
    },

    getUser() {
        const u = localStorage.getItem("marketing_ai_user");
        return u ? JSON.parse(u) : null;
    },

    setUser(user) {
        localStorage.setItem("marketing_ai_user", JSON.stringify(user));
    },

    async request(endpoint, options = {}) {
        const headers = {
            "Content-Type": "application/json",
            ...(options.headers || {})
        };

        const token = this.getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, config);
            
            if (res.status === 401) {
                this.clearToken();
                showToast("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại", "error");
                document.getElementById("main-layout").style.display = "none";
                document.getElementById("auth-screen").style.display = "flex";
                throw new Error("Unauthorized");
            }

            const data = await res.json();
            if (!res.ok) {
                const errMsg = data.detail || (Array.isArray(data.detail) ? data.detail[0].msg : "Đã có lỗi xảy ra");
                throw new Error(errMsg);
            }
            return data;
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: "GET" });
    },

    post(endpoint, body) {
        return this.request(endpoint, {
            method: "POST",
            body: JSON.stringify(body)
        });
    },

    put(endpoint, body) {
        return this.request(endpoint, {
            method: "PUT",
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: "DELETE" });
    }
};

// Toast notification helper
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconName = "info";
    if (type === "success") iconName = "check-circle";
    if (type === "error") iconName = "alert-circle";

    toast.innerHTML = `
        <i data-lucide="${iconName}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function formatVND(amount) {
    if (amount === undefined || amount === null) return "0 đ";
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);
}

function formatDate(dateStr) {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return d.toLocaleDateString("vi-VN");
}

function formatDateTime(dateStr) {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return `${d.toLocaleDateString("vi-VN")} ${d.toLocaleTimeString("vi-VN", { hour: '2-digit', minute: '2-digit' })}`;
}


function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
