from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Post, Campaign, Channel, User
from ..schemas import PostCreate, PostUpdate, PostResponse, PostReviewRequest
from ..auth import get_current_user, require_manager, is_management_role

router = APIRouter(prefix="/api/content", tags=["Content & Calendar"])

def _enrich_post_response(p: Post) -> PostResponse:
    return PostResponse(
        id=p.id,
        campaign_id=p.campaign_id,
        channel_id=p.channel_id,
        title=p.title,
        content=p.content,
        hashtags=p.hashtags,
        call_to_action=p.call_to_action,
        scheduled_at=p.scheduled_at,
        status=p.status,
        ai_generated=p.ai_generated,
        prompt_used=p.prompt_used,
        author_id=p.author_id,
        author_name=p.author.full_name if p.author else None,
        reviewer_id=p.reviewer_id,
        reviewer_name=p.reviewer.full_name if p.reviewer else None,
        reviewer_feedback=p.reviewer_feedback,
        reviewed_at=p.reviewed_at,
        published_at=p.published_at,
        campaign_name=p.campaign.name if p.campaign else None,
        channel_name=p.channel.name if p.channel else None,
        channel_color=p.channel.color if p.channel else "#3b82f6",
        created_at=p.created_at,
        updated_at=p.updated_at
    )

@router.get("", response_model=List[PostResponse])
def get_posts(
    campaign_id: Optional[int] = Query(None),
    channel_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    author_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Post)
    if not is_management_role(current_user):
        query = query.filter(Post.author_id == current_user.id)
    if campaign_id:
        query = query.filter(Post.campaign_id == campaign_id)
    if channel_id:
        query = query.filter(Post.channel_id == channel_id)
    if status and status != "all":
        query = query.filter(Post.status == status)
    if author_id and is_management_role(current_user):
        query = query.filter(Post.author_id == author_id)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(or_(Post.title.ilike(search_fmt), Post.content.ilike(search_fmt)))

    posts = query.order_by(Post.created_at.desc()).all()
    return [_enrich_post_response(p) for p in posts]

@router.post("", response_model=PostResponse)
def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify campaign and channel exist
    campaign = db.query(Campaign).filter(Campaign.id == post_in.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=400, detail="Không tìm thấy chiến dịch được chọn")
    
    channel = db.query(Channel).filter(Channel.id == post_in.channel_id).first()
    if not channel:
        raise HTTPException(status_code=400, detail="Không tìm thấy kênh được chọn")

    if not is_management_role(current_user) and post_in.status in ("approved", "published"):
        raise HTTPException(status_code=403, detail="Nhân viên không thể tự duyệt hoặc xuất bản bài viết")

    new_post = Post(
        **post_in.model_dump(),
        author_id=current_user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return _enrich_post_response(new_post)

@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Post).filter(Post.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
    if not is_management_role(current_user) and p.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
    return _enrich_post_response(p)

@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Post).filter(Post.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")

    # Only author or manager can update
    if not is_management_role(current_user) and p.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bài viết của người khác")

    update_data = post_in.model_dump(exclude_unset=True)
    if not is_management_role(current_user) and update_data.get("status") in ("approved", "published"):
        raise HTTPException(status_code=403, detail="Nhân viên không thể tự duyệt hoặc xuất bản bài viết")
    for key, value in update_data.items():
        setattr(p, key, value)
    
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return _enrich_post_response(p)

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Post).filter(Post.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")

    if not is_management_role(current_user) and p.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa bài viết này")

    db.delete(p)
    db.commit()
    return {"message": "Đã xóa bài viết thành công", "id": post_id}

@router.put("/{post_id}/review", response_model=PostResponse)
def review_post(
    post_id: int,
    review_in: PostReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Post).filter(Post.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")

    action = review_in.action.lower()
    if not is_management_role(current_user) and p.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")

    if action == "submit_for_review":
        # Any user can submit their own draft for review
        p.status = "in_review"
    elif action == "approve":
        # Only manager can approve
        if not is_management_role(current_user):
            raise HTTPException(status_code=403, detail="Chỉ Quản lý (Manager) mới có quyền duyệt bài viết")
        p.status = "approved"
        p.reviewer_id = current_user.id
        p.reviewer_feedback = review_in.feedback or "Nội dung đạt chuẩn, đã phê duyệt."
        p.reviewed_at = datetime.utcnow()
    elif action == "reject":
        # Only manager can reject
        if not is_management_role(current_user):
            raise HTTPException(status_code=403, detail="Chỉ Quản lý (Manager) mới có quyền từ chối bài viết")
        p.status = "rejected"
        p.reviewer_id = current_user.id
        p.reviewer_feedback = review_in.feedback or "Cần chỉnh sửa lại câu từ và bổ sung thông tin."
        p.reviewed_at = datetime.utcnow()
    elif action == "publish":
        if p.status != "approved":
            raise HTTPException(status_code=400, detail="Chỉ có thể xuất bản bài viết đã được duyệt")
        p.status = "published"
        p.published_at = datetime.utcnow()
    else:
        raise HTTPException(status_code=400, detail="Hành động không hợp lệ (submit_for_review, approve, reject, publish)")

    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return _enrich_post_response(p)

@router.get("/calendar/events")
def get_calendar_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Post).filter(Post.scheduled_at != None)
    if not is_management_role(current_user):
        query = query.filter(Post.author_id == current_user.id)
    posts = query.all()
    events = []
    for p in posts:
        events.append({
            "id": p.id,
            "title": p.title,
            "start": p.scheduled_at.isoformat() if p.scheduled_at else None,
            "channel": p.channel.name if p.channel else "Social",
            "channel_color": p.channel.color if p.channel else "#3b82f6",
            "campaign": p.campaign.name if p.campaign else "",
            "status": p.status,
            "author": p.author.full_name if p.author else ""
        })
    return events
