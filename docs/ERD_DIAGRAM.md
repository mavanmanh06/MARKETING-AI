# THIẾT KẾ CƠ SỞ DỮ LIỆU & SƠ ĐỒ THỰC THỂ QUAN HỆ (ERD)

## 1. Sơ đồ Thực thể Quan hệ (ERD)

```mermaid
erDiagram
    USERS ||--o{ CAMPAIGNS : creates
    USERS ||--o{ POSTS : authors
    USERS ||--o{ POSTS : reviews
    USERS ||--o{ AI_LOGS : performs
    CAMPAIGNS ||--o{ POSTS : contains
    CAMPAIGNS ||--o{ METRICS : tracks
    CHANNELS ||--o{ POSTS : targets
    CHANNELS ||--o{ METRICS : records

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string role "manager / marketer"
        string avatar_url
        boolean is_active
        datetime created_at
    }

    CHANNELS {
        int id PK
        string name UK "Facebook, TikTok, Google Ads..."
        string code UK
        string icon
        string color
        text description
        boolean is_active
        datetime created_at
    }

    CAMPAIGNS {
        int id PK
        string name
        string objective
        text target_audience
        float budget
        datetime start_date
        datetime end_date
        string status "planning, active, paused, completed"
        text description
        int created_by_id FK
        datetime created_at
        datetime updated_at
    }

    POSTS {
        int id PK
        int campaign_id FK
        int channel_id FK
        int author_id FK
        string title
        text content
        string hashtags
        string call_to_action
        datetime scheduled_at
        string status "draft, in_review, approved, rejected, published"
        boolean ai_generated
        text prompt_used
        int reviewer_id FK
        text reviewer_feedback
        datetime reviewed_at
        datetime published_at
        datetime created_at
        datetime updated_at
    }

    METRICS {
        int id PK
        int campaign_id FK
        int channel_id FK
        datetime record_date
        int impressions
        int clicks
        int conversions
        float spend
        float revenue
        text notes
        datetime created_at
    }

    AI_LOGS {
        int id PK
        int user_id FK
        string action_type
        text prompt
        text response_text
        datetime created_at
    }
```

---

## 2. Công thức Chỉ số Nghiệp vụ (Key Marketing Formulas)

1. **Tỷ lệ nhấp chuột (Click-Through Rate - CTR)**:
   $$\text{CTR} = \frac{\text{Clicks}}{\text{Impressions}} \times 100\%$$

2. **Chi phí trên mỗi lượt nhấp (Cost Per Click - CPC)**:
   $$\text{CPC} = \frac{\text{Spend}}{\text{Clicks}} \text{ (VNĐ)}$$

3. **Chi phí trên mỗi lượt chuyển đổi (Cost Per Acquisition - CPA)**:
   $$\text{CPA} = \frac{\text{Spend}}{\text{Conversions}} \text{ (VNĐ)}$$

4. **Tỷ suất sinh lời trên chi phí marketing (Return on Investment - ROI)**:
   $$\text{ROI} = \frac{\text{Revenue} - \text{Spend}}{\text{Spend}} \times 100\%$$
