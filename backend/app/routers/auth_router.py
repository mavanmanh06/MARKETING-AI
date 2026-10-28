from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import User, Post, Campaign, AILog, LoginLog
from ..schemas import UserLogin, UserCreate, Token, UserResponse
from ..auth import verify_password, hash_password, create_access_token, get_current_user, require_manager, require_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này đã bị tạm khóa"
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng"
        )
    
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role="marketer",
        avatar_url=user_data.avatar_url or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    return db.query(User).all()

@router.get("/team-stats")
def get_team_stats(db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    users = db.query(User).all()
    result = []
    for u in users:
        total_posts = db.query(func.count(Post.id)).filter(Post.author_id == u.id).scalar() or 0
        approved_posts = db.query(func.count(Post.id)).filter(Post.author_id == u.id, Post.status == "approved").scalar() or 0
        published_posts = db.query(func.count(Post.id)).filter(Post.author_id == u.id, Post.status == "published").scalar() or 0
        in_review_posts = db.query(func.count(Post.id)).filter(Post.author_id == u.id, Post.status == "in_review").scalar() or 0
        rejected_posts = db.query(func.count(Post.id)).filter(Post.author_id == u.id, Post.status == "rejected").scalar() or 0
        ai_generated_posts = db.query(func.count(Post.id)).filter(Post.author_id == u.id, Post.ai_generated == True).scalar() or 0
        campaign_count = db.query(func.count(Campaign.id)).filter(Campaign.created_by_id == u.id).scalar() or 0
        
        pass_rate = round(((approved_posts + published_posts) / total_posts * 100), 1) if total_posts > 0 else 100.0

        result.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "avatar_url": u.avatar_url,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "total_posts": total_posts,
            "approved_posts": approved_posts,
            "published_posts": published_posts,
            "in_review_posts": in_review_posts,
            "rejected_posts": rejected_posts,
            "ai_generated_posts": ai_generated_posts,
            "campaign_count": campaign_count,
            "pass_rate": pass_rate
        })
    return result

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # BẢO VỆ CHẶT CHẼ: CHỈ ADMIN MỚI CÓ QUYỀN XÓA
):
    """
    Xóa thành viên khỏi hệ thống (Chỉ dành riêng cho Quản trị viên - Admin).
    Quản lý và Nhân viên không có quyền xóa.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên này")

    # Không thể tự xóa chính mình
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự xóa chính tài khoản Quản trị viên bạn đang đăng nhập"
        )

    # Không thể xóa tài khoản admin gốc
    if target_user.email == "admin@marketing.ai":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa tài khoản Quản trị viên gốc của hệ thống"
        )

    # 1. Xóa các log AI của thành viên này
    db.query(AILog).filter(AILog.user_id == user_id).delete()

    # 2. Xóa các login log của thành viên này
    db.query(LoginLog).filter(LoginLog.user_id == user_id).delete()

    # 3. Gỡ liên kết người duyệt (reviewer) trên các bài viết
    db.query(Post).filter(Post.reviewer_id == user_id).update({"reviewer_id": None})

    # 4. Xóa các bài viết do thành viên này tạo
    db.query(Post).filter(Post.author_id == user_id).delete()

    # 5. Chuyển giao các chiến dịch do thành viên này tạo về cho Admin hiện tại quản trị
    db.query(Campaign).filter(Campaign.created_by_id == user_id).update({"created_by_id": current_user.id})

    # 6. Xóa người dùng
    user_name = target_user.full_name
    db.delete(target_user)
    db.commit()

    return {"message": f"Đã xóa thành viên '{user_name}' thành công", "id": user_id}
