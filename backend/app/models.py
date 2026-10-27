from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="marketer", nullable=False)  # "admin", "manager", or "marketer"
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaigns = relationship("Campaign", back_populates="creator", foreign_keys="Campaign.created_by_id")
    posts = relationship("Post", back_populates="author", foreign_keys="Post.author_id")
    reviewed_posts = relationship("Post", back_populates="reviewer", foreign_keys="Post.reviewer_id")
    ai_logs = relationship("AILog", back_populates="user")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)  # facebook, google_ads, tiktok, instagram, email, youtube, linkedin
    icon = Column(String(50), default="share-2")
    color = Column(String(50), default="#3b82f6")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="channel")
    metrics = relationship("Metric", back_populates="channel")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    objective = Column(String(255), nullable=False)  # Brand Awareness, Lead Gen, Sales Conversion, Event Promotion...
    target_audience = Column(Text, nullable=True)
    budget = Column(Float, default=0.0, nullable=False)  # VNĐ
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="planning", nullable=False)  # planning, active, paused, completed
    description = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="campaigns", foreign_keys=[created_by_id])
    posts = relationship("Post", back_populates="campaign", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="campaign", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    hashtags = Column(String(255), nullable=True)
    call_to_action = Column(String(255), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    
    # Review workflow: draft -> in_review -> approved / rejected -> published
    status = Column(String(50), default="draft", nullable=False)
    
    # AI Metadata
    ai_generated = Column(Boolean, default=False)
    prompt_used = Column(Text, nullable=True)
    
    # Reviewer fields (Human in the loop)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_feedback = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="posts")
    channel = relationship("Channel", back_populates="posts")
    author = relationship("User", back_populates="posts", foreign_keys=[author_id])
    reviewer = relationship("User", back_populates="reviewed_posts", foreign_keys=[reviewer_id])


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    record_date = Column(DateTime, nullable=False)
    
    impressions = Column(Integer, default=0, nullable=False)  # Lượt xem
    clicks = Column(Integer, default=0, nullable=False)       # Lượt click
    conversions = Column(Integer, default=0, nullable=False)  # Lượt chuyển đổi
    spend = Column(Float, default=0.0, nullable=False)        # Chi phí (VNĐ)
    revenue = Column(Float, default=0.0, nullable=False)      # Doanh thu ghi nhận (VNĐ)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="metrics")
    channel = relationship("Channel", back_populates="metrics")


class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # idea_generation, content_draft, performance_summary
    prompt = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ai_logs")


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(100), default="127.0.0.1")
    user_agent = Column(String(500), default="Chrome / Windows")
    status = Column(String(50), default="success")  # success / failed
    role = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
