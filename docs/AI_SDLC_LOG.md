# NHẬT KÝ ỨNG DỤNG AI TRONG CÁC GIAI ĐOẠN SDLC (MINH CHỨNG SỬ DỤNG AI)

> **Dự án**: Hệ thống Quản lý Chiến dịch Marketing tích hợp AI  
> **Khóa học / Bài tập**: Bài kiểm tra thường xuyên 2 - Ứng dụng Trí tuệ Nhân tạo trong Phát triển Phần mềm  

---

## 1. Giai đoạn Khảo sát & Thiết kế Kiến trúc (KT1)

### 1.1. Phân tích bài toán và thiết kế ERD
- **Mục tiêu**: Phân tích các thực thể nghiệp vụ marketing (Chiến dịch, Kênh truyền thông, Nội dung/Lịch đăng, Chỉ số hiệu quả, Nhật ký AI, Người dùng & Phân quyền).
- **Prompt sử dụng cho AI**:
  ```text
  System: Bạn là kiến trúc sư hệ thống phần mềm và chuyên gia tiếp thị số.
  User: Hãy thiết kế mô hình cơ sở dữ liệu quan hệ (ERD) bằng SQLAlchemy cho hệ thống quản lý chiến dịch marketing có tích hợp AI. Yêu cầu: Có bảng Users (phân quyền manager/marketer), Campaigns (ngân sách, mục tiêu, thời gian), Channels (Facebook, TikTok, Google Ads...), Posts (quy trình duyệt draft -> in_review -> approved -> published, cờ ai_generated, prompt_used, reviewer_feedback), Metrics (impressions, clicks, conversions, spend, revenue), và AILog.
  ```
- **Phản hồi từ AI**: Đề xuất thiết kế 6 bảng với khóa ngoại chặt chẽ, hỗ trợ cascade delete giữa Campaign và Posts/Metrics.
- **Kiểm tra & Hiệu chỉnh của Sinh viên**: 
  - Đã bổ sung thêm trường `call_to_action` và `hashtags` cho bảng `Post` để tối ưu cho việc sinh nội dung từ AI.
  - Thêm quan hệ kép giữa User và Post (`author_id` và `reviewer_id`) để hiện thực hóa quy trình Human-in-the-loop.

---

## 2. Giai đoạn Xây dựng Backend CRUD & Nghiệp vụ (KT2)

### 2.1. Sinh mã nguồn API CRUD & Bộ lọc tìm kiếm
- **Prompt sử dụng**:
  ```text
  Hãy viết FastAPI router cho Campaigns và Content Management có đầy đủ:
  1. Lọc theo kênh (channel_id), trạng thái (status), tìm kiếm từ khóa (ilike).
  2. Tự động tổng hợp số liệu thực chi (spend), tổng lượt xem, clicks, conversions và tính tỷ suất ROI.
  3. Phân quyền RBAC: Marketer chỉ chỉnh sửa bài của mình; Manager có quyền duyệt (Approve/Reject) và xóa chiến dịch.
  ```
- **Phản hồi từ AI**: Sinh các endpoint FastAPI chuẩn OpenAPI Pydantic v2 với Dependency Injection `get_current_user` và `require_manager`.
- **Kiểm tra & Hiệu chỉnh của Sinh viên**:
  - Chuyển `datetime.utcnow()` sang xử lý múi giờ đồng bộ.
  - Tinh chỉnh công thức tính toán tài chính: $ROI = \frac{\text{Revenue} - \text{Spend}}{\text{Spend}} \times 100\%$.

---

## 3. Giai đoạn Tích hợp AI Engine & Human-in-the-Loop Review (KT3)

### 3.1. Thiết kế Prompt Mẫu chuẩn cho Trợ lý Marketing AI
- **System Prompt chuẩn**:
  ```text
  System: Bạn là trợ lý marketing. Tạo nội dung nháp để con người duyệt, không đưa cam kết sai sự thật.
  ```
- **User Prompt mẫu sinh ý tưởng**:
  ```text
  User: Chiến dịch: {{campaign_brief}}. Hãy đề xuất 5 ý tưởng nội dung cho kênh {{channel}}, giọng văn {{tone}}.
  ```
- **User Prompt mẫu soạn thảo nội dung**:
  ```text
  User: Chiến dịch: {{campaign_name}}. Chủ đề: {{topic}}. Kênh: {{channel}}. Giọng văn: {{tone}}. Hãy tạo bản nháp có tiêu đề, nội dung, hashtag và CTA.
  ```
- **Cơ chế Duyệt bài (Human-in-the-Loop)**:
  - Khi AI sinh nội dung, trạng thái bài viết mặc định là `draft` hoặc `in_review`.
  - Marketer có thể chỉnh sửa nội dung trực tiếp trên giao diện trước khi gửi duyệt.
  - Manager xem xét bản nháp AI, đưa ra nhận xét phản hồi (Feedback) và bấm `Phê duyệt` hoặc `Từ chối`.

---

## 4. Giai đoạn Tối ưu hóa, Kiểm thử & Đánh giá (Cuối kỳ)

### 4.1. Sinh bộ kiểm thử tự động (Unit Tests)
- **Prompt sử dụng**:
  ```text
  Hãy viết bộ test tự động sử dụng pytest và FastAPI TestClient kiểm tra toàn diện 4 luồng chính: Xác thực JWT, CRUD chiến dịch và lọc trạng thái, Quy trình duyệt bài Human-in-the-loop, và AI Engine.
  ```
- **Kết quả**: Bộ test `tests/` gồm 11/11 test cases đã vượt qua 100% kiểm thử thành công.

### 4.2. Đánh giá chất lượng đầu ra của AI
- **Độ chính xác và tính thực tiễn**: Các bài viết sinh ra có đầy đủ Call-to-action và Hashtags phù hợp cho từng kênh đặc thù (TikTok video script có hook 0-3s, Email có tiêu đề trang trọng, Facebook có icon bắt mắt).
- **Tính an toàn**: Áp dụng triệt để nguyên tắc không hứa hẹn cam kết sai sự thật, luôn kèm cảnh báo kiểm duyệt trước khi đăng tải.
