from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Metric, Campaign, Channel, Post, User
from ..schemas import MetricCreate, MetricResponse, DashboardSummary
from ..auth import get_current_user

router = APIRouter(prefix="/api/metrics", tags=["Metrics & Analytics"])

def _calculate_metric_ratios(spend: float, impressions: int, clicks: int, conversions: int, revenue: float):
    ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
    cpc = (spend / clicks) if clicks > 0 else 0.0
    cpa = (spend / conversions) if conversions > 0 else 0.0
    roi = ((revenue - spend) / spend * 100) if spend > 0 else 0.0
    return ctr, cpc, cpa, roi

@router.get("", response_model=List[MetricResponse])
def get_metrics(
    campaign_id: Optional[int] = Query(None),
    channel_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Metric)
    if campaign_id:
        query = query.filter(Metric.campaign_id == campaign_id)
    if channel_id:
        query = query.filter(Metric.channel_id == channel_id)

    metrics = query.order_by(Metric.record_date.desc()).all()
    results = []
    for m in metrics:
        ctr, cpc, cpa, roi = _calculate_metric_ratios(m.spend, m.impressions, m.clicks, m.conversions, m.revenue)
        results.append(MetricResponse(
            id=m.id,
            campaign_id=m.campaign_id,
            channel_id=m.channel_id,
            record_date=m.record_date,
            impressions=m.impressions,
            clicks=m.clicks,
            conversions=m.conversions,
            spend=m.spend,
            revenue=m.revenue,
            notes=m.notes,
            campaign_name=m.campaign.name if m.campaign else None,
            channel_name=m.channel.name if m.channel else None,
            ctr=round(ctr, 2),
            cpc=round(cpc, 0),
            cpa=round(cpa, 0),
            roi=round(roi, 1),
            created_at=m.created_at
        ))
    return results

@router.post("", response_model=MetricResponse)
def create_metric(
    metric_in: MetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign = db.query(Campaign).filter(Campaign.id == metric_in.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=400, detail="Không tìm thấy chiến dịch")

    channel = db.query(Channel).filter(Channel.id == metric_in.channel_id).first()
    if not channel:
        raise HTTPException(status_code=400, detail="Không tìm thấy kênh")

    new_metric = Metric(**metric_in.model_dump())
    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)

    ctr, cpc, cpa, roi = _calculate_metric_ratios(
        new_metric.spend, new_metric.impressions, new_metric.clicks, new_metric.conversions, new_metric.revenue
    )

    return MetricResponse(
        id=new_metric.id,
        campaign_id=new_metric.campaign_id,
        channel_id=new_metric.channel_id,
        record_date=new_metric.record_date,
        impressions=new_metric.impressions,
        clicks=new_metric.clicks,
        conversions=new_metric.conversions,
        spend=new_metric.spend,
        revenue=new_metric.revenue,
        notes=new_metric.notes,
        campaign_name=campaign.name,
        channel_name=channel.name,
        ctr=round(ctr, 2),
        cpc=round(cpc, 0),
        cpa=round(cpa, 0),
        roi=round(roi, 1),
        created_at=new_metric.created_at
    )

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total & active campaigns
    total_campaigns = db.query(Campaign).count()
    active_campaigns = db.query(Campaign).filter(Campaign.status == "active").count()
    
    # Total budget
    total_budget = db.query(func.coalesce(func.sum(Campaign.budget), 0.0)).scalar() or 0.0

    # Total Metrics aggregation
    m_totals = db.query(
        func.coalesce(func.sum(Metric.spend), 0.0).label("spend"),
        func.coalesce(func.sum(Metric.revenue), 0.0).label("revenue"),
        func.coalesce(func.sum(Metric.impressions), 0).label("impressions"),
        func.coalesce(func.sum(Metric.clicks), 0).label("clicks"),
        func.coalesce(func.sum(Metric.conversions), 0).label("conversions"),
    ).first()

    total_spend = float(m_totals.spend)
    total_revenue = float(m_totals.revenue)
    total_impressions = int(m_totals.impressions)
    total_clicks = int(m_totals.clicks)
    total_conversions = int(m_totals.conversions)

    avg_ctr, avg_cpc, avg_cpa, overall_roi = _calculate_metric_ratios(
        total_spend, total_impressions, total_clicks, total_conversions, total_revenue
    )

    # Posts by status
    statuses = ["draft", "in_review", "approved", "rejected", "published"]
    posts_by_status = {}
    for st in statuses:
        cnt = db.query(func.count(Post.id)).filter(Post.status == st).scalar() or 0
        posts_by_status[st] = cnt

    # Channel Performance breakdown
    channels = db.query(Channel).filter(Channel.is_active == True).all()
    channel_perf = []
    for ch in channels:
        ch_m = db.query(
            func.coalesce(func.sum(Metric.spend), 0.0).label("spend"),
            func.coalesce(func.sum(Metric.revenue), 0.0).label("revenue"),
            func.coalesce(func.sum(Metric.impressions), 0).label("impressions"),
            func.coalesce(func.sum(Metric.clicks), 0).label("clicks"),
            func.coalesce(func.sum(Metric.conversions), 0).label("conversions"),
        ).filter(Metric.channel_id == ch.id).first()

        sp = float(ch_m.spend)
        rev = float(ch_m.revenue)
        imp = int(ch_m.impressions)
        clk = int(ch_m.clicks)
        conv = int(ch_m.conversions)
        c_ctr, c_cpc, c_cpa, c_roi = _calculate_metric_ratios(sp, imp, clk, conv, rev)

        channel_perf.append({
            "channel_id": ch.id,
            "channel_name": ch.name,
            "channel_code": ch.code,
            "channel_color": ch.color,
            "spend": sp,
            "revenue": rev,
            "impressions": imp,
            "clicks": clk,
            "conversions": conv,
            "ctr": round(c_ctr, 2),
            "cpc": round(c_cpc, 0),
            "cpa": round(c_cpa, 0),
            "roi": round(c_roi, 1)
        })

    # Recent Campaigns with KPIs
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(5).all()
    recent_camps = []
    for c in campaigns:
        c_m = db.query(
            func.coalesce(func.sum(Metric.spend), 0.0).label("spend"),
            func.coalesce(func.sum(Metric.revenue), 0.0).label("revenue"),
            func.coalesce(func.sum(Metric.impressions), 0).label("impressions"),
            func.coalesce(func.sum(Metric.clicks), 0).label("clicks"),
            func.coalesce(func.sum(Metric.conversions), 0).label("conversions"),
        ).filter(Metric.campaign_id == c.id).first()
        
        c_spend = float(c_m.spend)
        c_rev = float(c_m.revenue)
        _, _, _, c_roi = _calculate_metric_ratios(c_spend, int(c_m.impressions), int(c_m.clicks), int(c_m.conversions), c_rev)

        recent_camps.append({
            "id": c.id,
            "name": c.name,
            "objective": c.objective,
            "budget": c.budget,
            "spend": c_spend,
            "revenue": c_rev,
            "roi": round(c_roi, 1),
            "status": c.status,
            "start_date": c.start_date.strftime("%d/%m/%Y"),
            "end_date": c.end_date.strftime("%d/%m/%Y")
        })

    # Performance Timeline (Grouped by date)
    timeline_records = db.query(
        func.date(Metric.record_date).label("m_date"),
        func.sum(Metric.spend).label("spend"),
        func.sum(Metric.revenue).label("revenue"),
        func.sum(Metric.clicks).label("clicks"),
        func.sum(Metric.conversions).label("conversions")
    ).group_by(func.date(Metric.record_date)).order_by(func.date(Metric.record_date).asc()).all()

    timeline = []
    for r in timeline_records:
        timeline.append({
            "date": str(r.m_date),
            "spend": float(r.spend or 0),
            "revenue": float(r.revenue or 0),
            "clicks": int(r.clicks or 0),
            "conversions": int(r.conversions or 0)
        })

    return DashboardSummary(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_budget=total_budget,
        total_spend=total_spend,
        total_revenue=total_revenue,
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_conversions=total_conversions,
        avg_ctr=round(avg_ctr, 2),
        avg_cpc=round(avg_cpc, 0),
        avg_cpa=round(avg_cpa, 0),
        overall_roi=round(overall_roi, 1),
        posts_by_status=posts_by_status,
        channel_performance=channel_perf,
        recent_campaigns=recent_camps,
        performance_timeline=timeline
    )

@router.get("/marketer-dashboard")
def get_marketer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Personal post counts
    my_posts = db.query(Post).filter(Post.author_id == current_user.id).all()
    
    total_my_posts = len(my_posts)
    my_drafts = sum(1 for p in my_posts if p.status == "draft")
    my_in_review = sum(1 for p in my_posts if p.status == "in_review")
    my_approved = sum(1 for p in my_posts if p.status == "approved")
    my_rejected = sum(1 for p in my_posts if p.status == "rejected")
    my_published = sum(1 for p in my_posts if p.status == "published")
    my_ai_posts = sum(1 for p in my_posts if p.ai_generated)

    # Calculate personal approval rate
    completed_reviews = my_approved + my_published + my_rejected
    approval_rate = round(((my_approved + my_published) / completed_reviews * 100), 1) if completed_reviews > 0 else 100.0

    # Recent feedback items (with reviewer_feedback)
    feedbacks = (
        db.query(Post)
        .filter(Post.author_id == current_user.id, Post.reviewer_feedback != None)
        .order_by(Post.reviewed_at.desc())
        .limit(5)
        .all()
    )
    feedback_list = []
    for p in feedbacks:
        feedback_list.append({
            "post_id": p.id,
            "post_title": p.title,
            "status": p.status,
            "channel_name": p.channel.name if p.channel else "Kênh",
            "campaign_name": p.campaign.name if p.campaign else "",
            "feedback": p.reviewer_feedback,
            "reviewer_name": p.reviewer.full_name if p.reviewer else "Quản lý",
            "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None
        })

    # Recent drafts / work in progress
    recent_drafts = (
        db.query(Post)
        .filter(Post.author_id == current_user.id)
        .order_by(Post.updated_at.desc())
        .limit(6)
        .all()
    )
    draft_list = []
    for p in recent_drafts:
        draft_list.append({
            "id": p.id,
            "title": p.title,
            "status": p.status,
            "channel_name": p.channel.name if p.channel else "Kênh",
            "channel_color": p.channel.color if p.channel else "#3b82f6",
            "campaign_name": p.campaign.name if p.campaign else "",
            "ai_generated": p.ai_generated,
            "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None
        })

    # Upcoming scheduled posts
    now = datetime.utcnow()
    upcoming_posts = (
        db.query(Post)
        .filter(Post.author_id == current_user.id, Post.scheduled_at != None, Post.scheduled_at >= now)
        .order_by(Post.scheduled_at.asc())
        .limit(4)
        .all()
    )
    upcoming_list = []
    for p in upcoming_posts:
        upcoming_list.append({
            "id": p.id,
            "title": p.title,
            "status": p.status,
            "channel_name": p.channel.name if p.channel else "Kênh",
            "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None
        })

    return {
        "user_id": current_user.id,
        "user_name": current_user.full_name,
        "total_posts": total_my_posts,
        "drafts_count": my_drafts,
        "in_review_count": my_in_review,
        "approved_count": my_approved,
        "rejected_count": my_rejected,
        "published_count": my_published,
        "ai_posts_count": my_ai_posts,
        "approval_rate": approval_rate,
        "feedbacks": feedback_list,
        "recent_drafts": draft_list,
        "upcoming_posts": upcoming_list
    }
