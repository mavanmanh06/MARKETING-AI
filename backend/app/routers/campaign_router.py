from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Campaign, Channel, Metric, Post, User
from ..schemas import CampaignCreate, CampaignUpdate, CampaignResponse, ChannelCreate, ChannelResponse
from ..auth import get_current_user, require_manager

router = APIRouter(prefix="/api", tags=["Campaigns & Channels"])

# ================= CHANNELS =================
@router.get("/channels", response_model=List[ChannelResponse])
def get_channels(db: Session = Depends(get_db)):
    return db.query(Channel).filter(Channel.is_active == True).all()

@router.post("/channels", response_model=ChannelResponse)
def create_channel(
    channel_in: ChannelCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_manager)
):
    existing = db.query(Channel).filter(
        or_(Channel.name == channel_in.name, Channel.code == channel_in.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Kênh này đã tồn tại")
    
    new_channel = Channel(**channel_in.model_dump())
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)
    return new_channel


# ================= CAMPAIGNS =================
@router.get("/campaigns", response_model=List[CampaignResponse])
def get_campaigns(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên chiến dịch hoặc mục tiêu"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: planning, active, paused, completed"),
    channel_id: Optional[int] = Query(None, description="Lọc theo kênh truyền thông"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Campaign)

    if status and status != "all":
        query = query.filter(Campaign.status == status)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Campaign.name.ilike(search_fmt),
                Campaign.objective.ilike(search_fmt),
                Campaign.target_audience.ilike(search_fmt),
                Campaign.description.ilike(search_fmt)
            )
        )

    if channel_id:
        # filter campaigns that have metrics or posts with this channel_id
        campaign_ids_with_channel = db.query(Metric.campaign_id).filter(Metric.channel_id == channel_id).distinct()
        post_campaign_ids = db.query(Post.campaign_id).filter(Post.channel_id == channel_id).distinct()
        query = query.filter(or_(Campaign.id.in_(campaign_ids_with_channel), Campaign.id.in_(post_campaign_ids)))

    campaigns = query.order_by(Campaign.created_at.desc()).all()

    # Enrich with summary stats
    result = []
    for c in campaigns:
        # Metrics aggregates
        m_agg = db.query(
            func.coalesce(func.sum(Metric.spend), 0.0).label("spend"),
            func.coalesce(func.sum(Metric.impressions), 0).label("impressions"),
            func.coalesce(func.sum(Metric.clicks), 0).label("clicks"),
            func.coalesce(func.sum(Metric.conversions), 0).label("conversions"),
            func.coalesce(func.sum(Metric.revenue), 0.0).label("revenue"),
        ).filter(Metric.campaign_id == c.id).first()

        post_count = db.query(func.count(Post.id)).filter(Post.campaign_id == c.id).scalar() or 0

        creator_name = c.creator.full_name if c.creator else "Admin"

        result.append(CampaignResponse(
            id=c.id,
            name=c.name,
            objective=c.objective,
            target_audience=c.target_audience,
            budget=c.budget,
            start_date=c.start_date,
            end_date=c.end_date,
            status=c.status,
            description=c.description,
            created_by_id=c.created_by_id,
            creator_name=creator_name,
            total_spend=float(m_agg.spend),
            total_impressions=int(m_agg.impressions),
            total_clicks=int(m_agg.clicks),
            total_conversions=int(m_agg.conversions),
            total_revenue=float(m_agg.revenue),
            post_count=post_count,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))

    return result

@router.post("/campaigns", response_model=CampaignResponse)
def create_campaign(
    campaign_in: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_campaign = Campaign(
        **campaign_in.model_dump(),
        created_by_id=current_user.id
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    return CampaignResponse(
        id=new_campaign.id,
        name=new_campaign.name,
        objective=new_campaign.objective,
        target_audience=new_campaign.target_audience,
        budget=new_campaign.budget,
        start_date=new_campaign.start_date,
        end_date=new_campaign.end_date,
        status=new_campaign.status,
        description=new_campaign.description,
        created_by_id=new_campaign.created_by_id,
        creator_name=current_user.full_name,
        total_spend=0.0,
        total_impressions=0,
        total_clicks=0,
        total_conversions=0,
        total_revenue=0.0,
        post_count=0,
        created_at=new_campaign.created_at,
        updated_at=new_campaign.updated_at
    )

@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch này")

    m_agg = db.query(
        func.coalesce(func.sum(Metric.spend), 0.0).label("spend"),
        func.coalesce(func.sum(Metric.impressions), 0).label("impressions"),
        func.coalesce(func.sum(Metric.clicks), 0).label("clicks"),
        func.coalesce(func.sum(Metric.conversions), 0).label("conversions"),
        func.coalesce(func.sum(Metric.revenue), 0.0).label("revenue"),
    ).filter(Metric.campaign_id == c.id).first()

    post_count = db.query(func.count(Post.id)).filter(Post.campaign_id == c.id).scalar() or 0

    return CampaignResponse(
        id=c.id,
        name=c.name,
        objective=c.objective,
        target_audience=c.target_audience,
        budget=c.budget,
        start_date=c.start_date,
        end_date=c.end_date,
        status=c.status,
        description=c.description,
        created_by_id=c.created_by_id,
        creator_name=c.creator.full_name if c.creator else "Admin",
        total_spend=float(m_agg.spend),
        total_impressions=int(m_agg.impressions),
        total_clicks=int(m_agg.clicks),
        total_conversions=int(m_agg.conversions),
        total_revenue=float(m_agg.revenue),
        post_count=post_count,
        created_at=c.created_at,
        updated_at=c.updated_at
    )

@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign_in: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")

    # Marketer can only edit their own campaigns, Manager can edit any
    if current_user.role != "manager" and c.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn chỉ có thể chỉnh sửa chiến dịch do bạn tạo")

    update_data = campaign_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(c, key, value)
    
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return get_campaign(campaign_id, db, current_user)

@router.delete("/campaigns/{campaign_id}")
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")
    
    db.delete(c)
    db.commit()
    return {"message": "Đã xóa chiến dịch thành công", "id": campaign_id}
