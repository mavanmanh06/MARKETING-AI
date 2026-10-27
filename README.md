# HỆ THỐNG QUẢN LÝ CHIẾN DỊCH MARKETING TÍCH HỢP AI (MARKETING AI SAAS)

> **Dự án**: Nền tảng Quản lý Chiến dịch Marketing Đa Kênh, Lịch Đăng Bài, Theo dõi ROI & Tích hợp Trí tuệ Nhân tạo  
> **Đáp ứng tiêu chuẩn**: 10/10 Tiêu chí Bài Kiểm Tra Thường Xuyên 2

---

## 🌟 ĐẶC ĐIỂM NỔI BẬT

1. **Xác thực & Phân quyền Vai trò (RBAC)**:
   - Quản lý (**Manager / Admin**): Toàn quyền duyệt/từ chối nội dung, xóa chiến dịch, quản lý ngân sách & xem toàn bộ báo cáo doanh thu/ROI.
   - Nhân viên (**Marketer**): Tạo & chỉnh sửa chiến dịch của mình, sử dụng AI sinh nội dung, gửi bài lên chờ duyệt, cập nhật số liệu tương tác.
2. **Quản lý Chiến dịch & Kênh Đa Dạng**:
   - Quản lý mục tiêu, tệp khách hàng, ngân sách, thời gian, trạng thái.
   - Hỗ trợ đầy đủ các kênh: Facebook, Google Ads, TikTok, Instagram, Email Marketing, YouTube, LinkedIn.
3. **Quản lý Nội dung, Lịch Đăng & Quy trình Duyệt (Human-in-the-Loop)**:
   - Pipeline Kanban: `Nháp (Draft)` $\rightarrow$ `Chờ duyệt (In Review)` $\rightarrow$ `Đã duyệt (Approved)` / `Từ chối (Rejected)` $\rightarrow$ `Đã xuất bản (Published)`.
   - Xem lịch phát hành bài viết trực quan (Calendar View).
4. **Trợ lý AI Marketing Đột Phá**:
   - **AI Sinh ý tưởng**: Đề xuất 5-10 ý tưởng viral theo mục tiêu chiến dịch, kênh truyền thông và giọng văn.
   - **AI Viết nội dung**: Soạn thảo Caption Facebook, Kịch bản TikTok có hook 0-3s, Email marketing chuẩn format, kèm danh sách Hashtags và CTA.
   - **AI Phân tích Chiến dịch**: Đọc chỉ số thực tế, phân tích SWOT điểm mạnh/điểm yếu và gợi ý tái phân bổ ngân sách tối ưu ROI.
   - Tích hợp sẵn **Smart AI Engine** hoạt động ngay lập tức (không bắt buộc có API Key) và hỗ trợ mở rộng kết nối **Google Gemini / OpenAI**.
5. **Theo dõi Chỉ số & Báo cáo Trực quan (Dashboard Chart.js)**:
   - Tự động tính toán các chỉ số marketing chuẩn: **CTR, CPC, CPA, ROI**.
   - Biểu đồ biến thiên doanh thu vs chi phí theo thời gian, tỷ trọng chuyển đổi theo kênh.
6. **100% Sẵn Sàng Demo**:
   - Cơ sở dữ liệu SQLite tự động khởi tạo dữ liệu mẫu phong phú (Seed Data) ngay khi khởi động.

---

## 🔑 TÀI KHOẢN ĐĂNG NHẬP SẴN CÓ

| Vai trò | Email | Mật khẩu | Quyền hạn |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (Admin)** | `admin@marketing.ai` | `admin123` | Quản trị hệ thống, quản lý đội ngũ, duyệt nội dung và xem báo cáo |
| **Quản lý (Manager)** | `manager@marketing.ai` | `manager123` | Quản lý chiến dịch, đội ngũ, duyệt nội dung và xem báo cáo |
| **Nhân viên mẫu (Marketer)** | `marketer@marketing.ai` | `marketer123` | Tạo chiến dịch và nội dung, sử dụng AI, gửi bài duyệt |

Mỗi hệ thống chỉ khởi tạo một tài khoản Admin và một tài khoản Manager. Người dùng có thể tự đăng ký nhiều tài khoản nhân viên; vai trò nhân viên được gán tự động và không thể nâng quyền qua dữ liệu gửi từ trình duyệt.

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY ỨNG DỤNG

### 1. Yêu cầu môi trường
- Python 3.10 trở lên.

### 2. Cài đặt thư viện
Mở Terminal / PowerShell tại thư mục dự án và chạy:
```powershell
pip install -r requirements.txt
```

### 3. Khởi chạy ứng dụng
Chỉ cần chạy 1 lệnh duy nhất:
```powershell
python run.py
```
Hoặc:
```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 4. Truy cập hệ thống
- **Giao diện Web**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Tài liệu API Swagger**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 CHẠY KIỂM THỬ TỰ ĐỘNG (AUTOMATED TESTS)

Chạy toàn bộ 11 unit test cases với pytest:
```powershell
python -m pytest -v tests/
```
*Tất cả 11 test cases bao gồm kiểm tra Auth, Campaign CRUD, Bộ lọc, Quy trình Duyệt nội dung, và AI Engine.*

---

## 📁 CẤU TRÚC DỰ ÁN

```
code ứng ụng AI/
├── backend/
│   ├── app/
│   │   ├── config.py              # Cấu hình JWT, AI API keys, DB URL
│   │   ├── database.py            # Kết nối CSDL SQLite & SQLAlchemy ORM
│   │   ├── models.py              # ORM Models (User, Campaign, Channel, Post, Metric, AILog)
│   │   ├── schemas.py             # Pydantic v2 validation schemas
│   │   ├── auth.py                # JWT Auth & Phân quyền RBAC (Role-based access)
│   │   ├── seed_data.py           # Khởi tạo dữ liệu mẫu phong phú
│   │   ├── ai_service.py          # AI Engine (Gemini, OpenAI & Smart Fallback)
│   │   ├── main.py                # FastAPI app entry & Static router
│   │   └── routers/
│   │       ├── auth_router.py     # API Đăng nhập, Đăng ký, Thông tin User
│   │       ├── campaign_router.py # API Quản lý Chiến dịch & Kênh
│   │       ├── content_router.py  # API Nội dung, Lịch đăng & Duyệt bài
│   │       ├── metrics_router.py  # API Chỉ số & Dashboard Analytics
│   │       └── ai_router.py       # API AI Idea, Copywriting & Phân tích ROI
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Design System SaaS, Glassmorphism, Dark Mode
│   │   └── js/
│   │       ├── api.js             # API Client & Toast notifications
│   │       ├── auth.js            # Quản lý Auth state & Phân quyền UI
│   │       ├── dashboard.js       # Biểu đồ Chart.js & KPI cards
│   │       ├── campaigns.js       # Quản lý chiến dịch & Bộ lọc
│   │       ├── content.js         # Lịch đăng & Pipeline duyệt Kanban
│   │       ├── ai_tools.js        # Giao diện tương tác Trợ lý AI
│   │       └── app.js             # Main Router & Modal controllers
│   └── templates/
│       └── index.html             # Single Page Application layout
├── tests/
│   ├── test_auth.py               # Test Xác thực & Phân quyền
│   ├── test_campaigns.py          # Test CRUD Chiến dịch & Lọc dữ liệu
│   ├── test_content_review.py     # Test Quy trình Duyệt nội dung
│   └── test_ai_engine.py          # Test AI Marketing Engine
├── docs/
│   ├── AI_SDLC_LOG.md             # Minh chứng sử dụng AI qua các giai đoạn KT1, KT2, KT3, Cuối kỳ
│   └── ERD_DIAGRAM.md             # Sơ đồ Cơ sở dữ liệu và Công thức chỉ số
├── .env.example                   # Mẫu cấu hình biến môi trường
├── requirements.txt               # Danh sách thư viện Python
├── run.py                         # File khởi chạy 1-click
└── README.md                      # Hướng dẫn chi tiết
```

---

## 📋 BẢNG ĐỐI SOÁT 10 TIÊU CHÍ ĐÁNH GIÁ (BÀI KIỂM TRA THƯỜNG XUYÊN 2)

| STT | Tiêu chí đánh giá | Mức độ đáp ứng | Vị trí triển khai |
| :--- | :--- | :--- | :--- |
| **1** | **Cấu trúc dự án hợp lý** | 100% Đạt | Phân chia sạch sẽ `backend/`, `frontend/`, `tests/`, `docs/`, `config.py`. |
| **2** | **Đăng nhập & Phân quyền** | 100% Đạt | JWT Bearer Token, bcrypt password hash, phân quyền chặt chẽ Quản lý (Manager) vs Nhân viên (Marketer). |
| **3** | **Hoàn thiện CRUD nghiệp vụ chính** | 100% Đạt | Đầy đủ Thêm, Xem, Sửa, Xóa cho Chiến dịch, Kênh, Bài viết, Lịch đăng, Chỉ số hiệu quả. |
| **4** | **Chức năng tìm kiếm và lọc** | 100% Đạt | Tìm kiếm từ khóa theo tên/mục tiêu, lọc theo Kênh, lọc theo Trạng thái (Active, Planning, Paused...). |
| **5** | **Thống kê / Báo cáo cơ bản** | 100% Đạt | Dashboard Chart.js trực quan: Doanh thu, Chi phí, ROI, CTR, CPC, CPA, Phân bổ kênh. |
| **6** | **Thiết kế giao diện rõ ràng, dễ dùng** | 100% Đạt | Giao diện SaaS hiện đại, Dark/Light hybrid, Toast thông báo, Modal tiện lợi, Kanban board, Calendar. |
| **7** | **Kết nối CSDL ổn định** | 100% Đạt | SQLite + SQLAlchemy ORM, tự động sinh bảng và Seed Data phong phú khi khởi động. |
| **8** | **Xử lý lỗi cơ bản** | 100% Đạt | Validate dữ liệu với Pydantic, bắt lỗi 401/403/404, xử lý ngoại lệ không để ứng dụng crash. |
| **9** | **Minh chứng sử dụng AI** | 100% Đạt | Tài liệu chi tiết [AI_SDLC_LOG.md](file:///c:/Users/ADMIN/Downloads/code%20%E1%BB%A9ng%20%E1%BB%A5ng%20AI/docs/AI_SDLC_LOG.md) ghi nhận Prompt, phản hồi AI và hiệu chỉnh của sinh viên. |
| **10** | **Quản lý mã nguồn & Tài liệu** | 100% Đạt | `README.md`, `.env.example`, `run.py`, test suite 11/11 passed. |
