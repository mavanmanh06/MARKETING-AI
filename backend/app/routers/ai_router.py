from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from ..database import get_db
from ..models import Campaign, Metric, Channel, AILog, User
from ..schemas import (
    AIIdeaRequest, AIIdeaResponse,
    AIContentRequest, AIContentResponse,
    AIInsightRequest, AIInsightResponse
)
from ..ai_service import AIMarketingService
from ..auth import get_current_user, is_management_role

router = APIRouter(prefix="/api/ai", tags=["AI Marketing Assistant"])

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

    # Save to AI Log
    ai_log = AILog(
        user_id=current_user.id,
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

    # Save to AI Log
    ai_log = AILog(
        user_id=current_user.id,
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

    # Save to AI Log
    ai_log = AILog(
        user_id=current_user.id,
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

@router.get("/logs")
def get_ai_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AILog)
    if not is_management_role(current_user):
        query = query.filter(AILog.user_id == current_user.id)
    logs = query.order_by(AILog.created_at.desc()).limit(20).all()
    return [
        {
            "id": l.id,
            "user_name": l.user.full_name if l.user else "User",
            "action_type": l.action_type,
            "prompt": l.prompt,
            "response_text": l.response_text,
            "created_at": l.created_at.strftime("%d/%m/%Y %H:%M:%S")
        }
        for l in logs
    ]
