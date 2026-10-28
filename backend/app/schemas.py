from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ================= USER & AUTH SCHEMAS =================
class UserBase(BaseModel):
    email: str
    full_name: str
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ================= CHANNEL SCHEMAS =================
class ChannelBase(BaseModel):
    name: str
    code: str
    icon: Optional[str] = "share-2"
    color: Optional[str] = "#3b82f6"
    description: Optional[str] = None
    is_active: bool = True

class ChannelCreate(ChannelBase):
    pass

class ChannelResponse(ChannelBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ================= CAMPAIGN SCHEMAS =================
class CampaignBase(BaseModel):
    name: str
    objective: str
    target_audience: Optional[str] = None
    budget: float = 0.0
    start_date: datetime
    end_date: datetime
    status: str = "planning"  # planning, active, paused, completed
    description: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    objective: Optional[str] = None
    target_audience: Optional[str] = None
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    description: Optional[str] = None

class CampaignResponse(CampaignBase):
    id: int
    created_by_id: int
    creator_name: Optional[str] = None
    total_spend: float = 0.0
    total_impressions: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    total_revenue: float = 0.0
    post_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ================= POST / CONTENT SCHEMAS =================
class PostBase(BaseModel):
    campaign_id: int
    channel_id: int
    title: str
    content: str
    hashtags: Optional[str] = None
    call_to_action: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: str = "draft"  # draft, in_review, approved, rejected, published
    ai_generated: bool = False
    prompt_used: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    campaign_id: Optional[int] = None
    channel_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    hashtags: Optional[str] = None
    call_to_action: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None

class PostReviewRequest(BaseModel):
    action: str  # "approve", "reject", "publish"
    feedback: Optional[str] = None

class PostResponse(PostBase):
    id: int
    author_id: int
    author_name: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    reviewer_feedback: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    campaign_name: Optional[str] = None
    channel_name: Optional[str] = None
    channel_color: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ================= METRIC SCHEMAS =================
class MetricBase(BaseModel):
    campaign_id: int
    channel_id: int
    record_date: datetime
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    notes: Optional[str] = None

class MetricCreate(MetricBase):
    pass

class MetricResponse(MetricBase):
    id: int
    campaign_name: Optional[str] = None
    channel_name: Optional[str] = None
    ctr: float = 0.0
    cpc: float = 0.0
    cpa: float = 0.0
    roi: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardSummary(BaseModel):
    total_campaigns: int
    active_campaigns: int
    total_budget: float
    total_spend: float
    total_revenue: float
    total_impressions: int
    total_clicks: int
    total_conversions: int
    avg_ctr: float
    avg_cpc: float
    avg_cpa: float
    overall_roi: float
    posts_by_status: Dict[str, int]
    channel_performance: List[Dict[str, Any]]
    recent_campaigns: List[Dict[str, Any]]
    performance_timeline: List[Dict[str, Any]]


# ================= AI SCHEMAS =================
class AIIdeaRequest(BaseModel):
    campaign_id: Optional[int] = None
    campaign_name: Optional[str] = None
    objective: str
    target_audience: Optional[str] = None
    channel: str = "Facebook"
    tone: str = "Trẻ trung, hấp dẫn"
    product_brief: Optional[str] = None
    quantity: int = 5

class AIIdeaResponse(BaseModel):
    ideas: List[Dict[str, Any]]
    raw_prompt: str

class AIContentRequest(BaseModel):
    campaign_id: Optional[int] = None
    campaign_name: Optional[str] = None
    channel: str = "Facebook"
    topic_or_idea: str
    target_audience: Optional[str] = None
    tone: str = "Trẻ trung, năng động"
    content_type: str = "caption"  # caption, email, ad_copy, video_script
    keywords: Optional[str] = None

class AIContentResponse(BaseModel):
    title: str
    content: str
    hashtags: str
    call_to_action: str
    channel: str
    raw_prompt: str
    notes_for_human_review: str

class AIInsightRequest(BaseModel):
    campaign_id: int

class AIInsightResponse(BaseModel):
    campaign_id: int
    campaign_name: str
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    suggested_budget_allocation: Dict[str, Any]
    generated_at: datetime

class AICampaignGenerateRequest(BaseModel):
    product_or_service: str
    objective: str = "Brand Awareness & Sales Conversion"
    target_audience: Optional[str] = None
    budget: Optional[float] = 50000000.0
    duration_days: Optional[int] = 30
    preferred_channel: Optional[str] = "Facebook"

class AICampaignGenerateResponse(BaseModel):
    name: str
    objective: str
    target_audience: str
    budget: float
    duration_days: int
    description: str
    suggested_channels: List[str]
    raw_prompt: str

class AILogResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    user_avatar: Optional[str] = None
    campaign_id: Optional[int] = None
    campaign_name: Optional[str] = None
    action_type: str
    prompt: str
    response_text: str
    created_at: str

class AILogUserStat(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    total_calls: int
    campaign_calls: int
    content_calls: int
    insight_calls: int
    last_activity: Optional[str] = None

class AILogStatsResponse(BaseModel):
    total_logs: int
    total_users_used: int
    campaign_ai_count: int
    content_ai_count: int
    insight_ai_count: int
    user_stats: List[AILogUserStat]
