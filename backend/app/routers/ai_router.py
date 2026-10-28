from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..database import get_db
from ..models import Campaign, Metric, Channel, AILog, User
from ..schemas import (
    AIIdeaRequest, AIIdeaResponse,
    AIContentRequest, AIContentResponse,
    AIInsightRequest, AIInsightResponse
)
from ..ai_service import AIMarketingService
from ..auth import get_current_user, require_admin, is_admin_role

# ================= LOCAL SCHEMAS CHO CHỨC NĂNG AI MỚI =================
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


router = APIRouter(prefix="/api/ai", tags=["AI Marketing Assistant"])

@router.post("/generate-campaign", response_model=AICampaignGenerateResponse)
def generate_campaign_plan(
    req: AICampaignGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sinh kế hoạch chiến dịch Marketing hoàn chỉnh bằng AI.
    Hành động này được ghi nhận vào nhật ký AI để Quản trị viên (Admin) giám sát.
    """
    result = AIMarketingService.generate_campaign_plan(
        product_or_service=req.product_or_service,
        objective=req.objective,
        target_audience=req.target_audience or "",
        budget=req.budget or 50000000.0,
        duration_days=req.duration_days or 30,
        preferred_channel=req.preferred_channel or "Facebook"
    )

    # Ghi nhận log AI hành động Tạo/Lập kế hoạch chiến dịch
    ai_log = AILog(
        user_id=current_user.id,
        action_type="campaign_generation",
        prompt=result["raw_prompt"],
        response_text=f"Tên chiến dịch: {result['name']} | Mục tiêu: {result['objective']} | Ngân sách: {result['budget']:,.0f}đ\nMô tả: {result['description']}"
    )
    db.add(ai_log)
    db.commit()

    return AICampaignGenerateResponse(**result)


@router.post("/generate-ideas", response_model=AIIdeaResponse)
def generate_ideas(
    req: AIIdeaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign_name = req.campaign_name or "Chiến dịch Marketing"
    target_audience = req.target_audience or ""
    
    if req.campaign_id:
        c = db.query(Campaign).filter(Campaign.id == req.campaign_id).first()
        if c:
            campaign_name = c.name
            target_audience = target_audience or (c.target_audience or "")

    result = AIMarketingService.generate_ideas(
        campaign_name=campaign_name,
        objective=req.objective,
        channel=req.channel,
        tone=req.tone,
        target_audience=target_audience,
        product_brief=req.product_brief or "",
        quantity=req.quantity
    )

    # Save to AI Log with campaign_id link
    ai_log = AILog(
        user_id=current_user.id,
        campaign_id=req.campaign_id,
        action_type="idea_generation",
        prompt=result["raw_prompt"],
        response_text=str(result["ideas"])
    )
    db.add(ai_log)
    db.commit()

    return AIIdeaResponse(
        ideas=result["ideas"],
        raw_prompt=result["raw_prompt"]
    )


@router.post("/generate-content", response_model=AIContentResponse)
def generate_content(
    req: AIContentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign_name = req.campaign_name or "Chiến dịch Marketing"
    target_audience = req.target_audience or ""

    if req.campaign_id:
        c = db.query(Campaign).filter(Campaign.id == req.campaign_id).first()
        if c:
            campaign_name = c.name
            target_audience = target_audience or (c.target_audience or "")

    result = AIMarketingService.generate_content(
        campaign_name=campaign_name,
        topic_or_idea=req.topic_or_idea,
        channel=req.channel,
        tone=req.tone,
        content_type=req.content_type,
        target_audience=target_audience,
        keywords=req.keywords or ""
    )

    # Save to AI Log with campaign_id link
    ai_log = AILog(
        user_id=current_user.id,
        campaign_id=req.campaign_id,
        action_type="content_draft",
        prompt=result["raw_prompt"],
        response_text=f"{result['title']}\n{result['content']}"
    )
    db.add(ai_log)
    db.commit()

    return AIContentResponse(**result)


@router.post("/analyze-campaign", response_model=AIInsightResponse)
def analyze_campaign(
    req: AIInsightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = db.query(Campaign).filter(Campaign.id == req.campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")

    # Metrics aggregation for campaign
    m_totals = db.query(
        func.coalesce(func.sum(Metric.spend), 0.0).label("spend"),
        func.coalesce(func.sum(Metric.revenue), 0.0).label("revenue"),
        func.coalesce(func.sum(Metric.impressions), 0).label("impressions"),
        func.coalesce(func.sum(Metric.clicks), 0).label("clicks"),
        func.coalesce(func.sum(Metric.conversions), 0).label("conversions"),
    ).filter(Metric.campaign_id == c.id).first()

    # Channel breakdown for campaign
    channel_breakdown = []
    channels = db.query(Channel).all()
    for ch in channels:
        ch_m = db.query(
            func.coalesce(func.sum(Metric.spend), 0.0).label("spend"),
            func.coalesce(func.sum(Metric.conversions), 0).label("conversions"),
        ).filter(Metric.campaign_id == c.id, Metric.channel_id == ch.id).first()
        
        if float(ch_m.spend) > 0 or int(ch_m.conversions) > 0:
            channel_breakdown.append({
                "channel_name": ch.name,
                "spend": float(ch_m.spend),
                "conversions": int(ch_m.conversions)
            })

    result = AIMarketingService.analyze_campaign_performance(
        campaign_name=c.name,
        objective=c.objective,
        budget=c.budget,
        total_spend=float(m_totals.spend),
        total_impressions=int(m_totals.impressions),
        total_clicks=int(m_totals.clicks),
        total_conversions=int(m_totals.conversions),
        total_revenue=float(m_totals.revenue),
        channel_breakdown=channel_breakdown
    )

    # Save to AI Log with campaign_id link
    ai_log = AILog(
        user_id=current_user.id,
        campaign_id=c.id,
        action_type="performance_summary",
        prompt=f"Phân tích hiệu quả chiến dịch: {c.name}",
        response_text=result["summary"]
    )
    db.add(ai_log)
    db.commit()

    return AIInsightResponse(
        campaign_id=c.id,
        **result
    )


# ================= QUẢN LÝ NHẬT KÝ AI (CHỈ DÀNH CHO ADMIN) =================
@router.get("/logs", response_model=List[AILogResponse])
def get_ai_logs(
    user_id: Optional[int] = Query(None, description="Lọc theo ID người dùng"),
    action_type: Optional[str] = Query(None, description="Lọc theo loại hành động AI"),
    campaign_id: Optional[int] = Query(None, description="Lọc theo chiến dịch"),
    search: Optional[str] = Query(None, description="Tìm kiếm trong prompt hoặc phản hồi"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # BẢO VỆ CHẶT CHẼ: CHỈ ADMIN MỚI ĐƯỢC PHÉP
):
    """
    Lấy danh sách nhật ký AI trong toàn hệ thống.
    Quyền: Chỉ tài khoản Quản trị viên (ADMIN) mới có quyền truy cập để giám sát xem những ai đã dùng AI.
    Nhân viên (marketer) và Quản lý (manager) sẽ bị chặn với mã 403 Forbidden.
    """
    query = db.query(AILog)

    if user_id:
        query = query.filter(AILog.user_id == user_id)

    if action_type and action_type != "all":
        query = query.filter(AILog.action_type == action_type)

    if campaign_id:
        query = query.filter(AILog.campaign_id == campaign_id)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                AILog.prompt.ilike(search_fmt),
                AILog.response_text.ilike(search_fmt),
                AILog.action_type.ilike(search_fmt)
            )
        )

    logs = query.order_by(AILog.created_at.desc()).offset(offset).limit(limit).all()

    result = []
    for l in logs:
        campaign_name = l.campaign.name if l.campaign else None
        result.append(AILogResponse(
            id=l.id,
            user_id=l.user_id,
            user_name=l.user.full_name if l.user else "Người dùng ẩn",
            user_email=l.user.email if l.user else "",
            user_role=l.user.role if l.user else "marketer",
            user_avatar=l.user.avatar_url if l.user else None,
            campaign_id=l.campaign_id,
            campaign_name=campaign_name,
            action_type=l.action_type,
            prompt=l.prompt,
            response_text=l.response_text,
            created_at=l.created_at.strftime("%d/%m/%Y %H:%M:%S") if l.created_at else ""
        ))
    return result


@router.get("/logs/stats", response_model=AILogStatsResponse)
def get_ai_logs_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # CHỈ ADMIN
):
    """
    Thống kê tổng quan tình hình sử dụng AI trong toàn hệ thống phục vụ Admin giám sát.
    Bao gồm thống kê theo người dùng để biết rõ ai đã dùng AI để tạo chiến dịch/nội dung.
    """
    total_logs = db.query(func.count(AILog.id)).scalar() or 0
    total_users_used = db.query(func.count(func.distinct(AILog.user_id))).scalar() or 0
    
    # Đếm theo loại hành động
    campaign_ai_count = db.query(func.count(AILog.id)).filter(
        AILog.action_type.in_(["campaign_generation", "idea_generation"])
    ).scalar() or 0
    
    content_ai_count = db.query(func.count(AILog.id)).filter(
        AILog.action_type == "content_draft"
    ).scalar() or 0
    
    insight_ai_count = db.query(func.count(AILog.id)).filter(
        AILog.action_type == "performance_summary"
    ).scalar() or 0

    # Thống kê chi tiết theo từng người dùng
    users = db.query(User).all()
    user_stats = []
    for u in users:
        u_calls = db.query(func.count(AILog.id)).filter(AILog.user_id == u.id).scalar() or 0
        if u_calls > 0:
            c_calls = db.query(func.count(AILog.id)).filter(
                AILog.user_id == u.id,
                AILog.action_type.in_(["campaign_generation", "idea_generation"])
            ).scalar() or 0
            cnt_calls = db.query(func.count(AILog.id)).filter(
                AILog.user_id == u.id,
                AILog.action_type == "content_draft"
            ).scalar() or 0
            ins_calls = db.query(func.count(AILog.id)).filter(
                AILog.user_id == u.id,
                AILog.action_type == "performance_summary"
            ).scalar() or 0
            
            latest_log = db.query(AILog).filter(AILog.user_id == u.id).order_by(AILog.created_at.desc()).first()
            last_activity = latest_log.created_at.strftime("%d/%m/%Y %H:%M") if (latest_log and latest_log.created_at) else None

            user_stats.append(AILogUserStat(
                user_id=u.id,
                user_name=u.full_name,
                user_email=u.email,
                user_role=u.role,
                total_calls=u_calls,
                campaign_calls=c_calls,
                content_calls=cnt_calls,
                insight_calls=ins_calls,
                last_activity=last_activity
            ))

    # Sắp xếp người dùng dùng AI nhiều nhất lên đầu
    user_stats.sort(key=lambda x: x.total_calls, reverse=True)

    return AILogStatsResponse(
        total_logs=total_logs,
        total_users_used=total_users_used,
        campaign_ai_count=campaign_ai_count,
        content_ai_count=content_ai_count,
        insight_ai_count=insight_ai_count,
        user_stats=user_stats
    )


@router.delete("/logs/{log_id}")
def delete_ai_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # CHỈ ADMIN
):
    """
    Xóa 1 bản ghi nhật ký AI (Quyền Admin).
    """
    log_entry = db.query(AILog).filter(AILog.id == log_id).first()
    if not log_entry:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi nhật ký này")
    
    db.delete(log_entry)
    db.commit()
    return {"message": "Đã xóa bản ghi nhật ký AI thành công", "id": log_id}


@router.delete("/logs")
def clear_all_ai_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # CHỈ ADMIN
):
    """
    Xóa toàn bộ nhật ký AI để dọn dẹp hệ thống (Quyền Admin).
    """
    deleted_count = db.query(AILog).delete()
    db.commit()
    return {"message": f"Đã dọn dẹp {deleted_count} bản ghi nhật ký AI thành công", "count": deleted_count}
