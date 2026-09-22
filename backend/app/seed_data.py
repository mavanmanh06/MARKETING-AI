from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import User, Channel, Campaign, Post, Metric, AILog
from .auth import hash_password

def seed_database(db: Session):
    # Check if users already exist
    if db.query(User).count() > 0:
        return

    print("[Seed Data] Bắt đầu khởi tạo dữ liệu mẫu cho hệ thống...")

    # 1. Seed Users (Quản lý - Manager & Nhân viên - Marketer)
    admin_user = User(
        email="admin@marketing.ai",
        hashed_password=hash_password("admin123"),
        full_name="Nguyễn Văn Quản Lý (Admin)",
        role="manager",
        avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        is_active=True
    )
    marketer_user = User(
        email="marketer@marketing.ai",
        hashed_password=hash_password("marketer123"),
        full_name="Trần Thị Marketer",
        role="marketer",
        avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
        is_active=True
    )
    db.add_all([admin_user, marketer_user])
    db.commit()
    db.refresh(admin_user)
    db.refresh(marketer_user)

    # 2. Seed Channels
    channels = [
        Channel(name="Facebook", code="facebook", icon="facebook", color="#1877F2", description="Fanpage chính và quảng cáo Facebook Ads"),
        Channel(name="Google Ads", code="google_ads", icon="search", color="#EA4335", description="Quảng cáo Google Search, Display Network & Performance Max"),
        Channel(name="TikTok", code="tiktok", icon="video", color="#000000", description="Kênh video ngắn viral và TikTok Ads"),
        Channel(name="Instagram", code="instagram", icon="instagram", color="#E1306C", description="Nội dung hình ảnh/story và influencer marketing"),
        Channel(name="Email Marketing", code="email", icon="mail", color="#8B5CF6", description="Bản tin tuần, automation lead nurture và khuyến mãi"),
        Channel(name="YouTube", code="youtube", icon="play-circle", color="#FF0000", description="Video đánh giá sản phẩm dài và Shorts"),
        Channel(name="LinkedIn", code="linkedin", icon="briefcase", color="#0A66C2", description="Truyền thông B2B và tuyển dụng thương hiệu")
    ]
    db.add_all(channels)
    db.commit()
    for ch in channels:
        db.refresh(ch)

    # 3. Seed Campaigns
    now = datetime.utcnow()
    c1 = Campaign(
        name="Ra mắt Siêu phẩm Smartphone AI Phone X",
        objective="Brand Awareness & Sales Conversion",
        target_audience="Giới trẻ 18-35 tuổi đam mê công nghệ, sinh viên và dân văn phòng",
        budget=150000000.0,
        start_date=now - timedelta(days=15),
        end_date=now + timedelta(days=30),
        status="active",
        description="Chiến dịch truyền thông đa kênh phủ sóng sự kiện mở bán dòng điện thoại thông minh tích hợp trí tuệ nhân tạo thế hệ mới.",
        created_by_id=admin_user.id
    )

    c2 = Campaign(
        name="Bộ sưu tập Mùa Hè Rực Rỡ - Fashion Summer 2026",
        objective="Lead Generation & Direct Sales",
        target_audience="Nữ giới 20-40 tuổi quan tâm phong cách thời trang nghỉ dưỡng và du lịch",
        budget=80000000.0,
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=20),
        status="active",
        description="Tung bộ sưu tập đầm váy mùa hè, đẩy mạnh livestream bán hàng và minigame tương tác trên mạng xã hội.",
        created_by_id=marketer_user.id
    )

    c3 = Campaign(
        name="Giải pháp B2B SaaS CRM Doanh nghiệp",
        objective="B2B Lead Generation",
        target_audience="Chủ doanh nghiệp SME, Giám đốc Marketing & Trưởng phòng Kinh doanh",
        budget=120000000.0,
        start_date=now - timedelta(days=25),
        end_date=now + timedelta(days=15),
        status="active",
        description="Quảng bá phần mềm quản trị quan hệ khách hàng ứng dụng AI, tặng 14 ngày dùng thử miễn phí.",
        created_by_id=admin_user.id
    )

    c4 = Campaign(
        name="Khai trương Chuỗi Nhà hàng Golden Taste",
        objective="Local Footfall & Brand Awareness",
        target_audience="Gia đình trẻ, nhóm bạn văn phòng khu vực quận trung tâm",
        budget=50000000.0,
        start_date=now - timedelta(days=40),
        end_date=now - timedelta(days=5),
        status="completed",
        description="Quảng bá sự kiện khai trương cơ sở thứ 5 với voucher giảm giá 30% và buffet hải sản cao cấp.",
        created_by_id=marketer_user.id
    )

    db.add_all([c1, c2, c3, c4])
    db.commit()
    for camp in [c1, c2, c3, c4]:
        db.refresh(camp)

    # 4. Seed Posts with different workflow statuses
    fb_channel = channels[0]
    gg_channel = channels[1]
    tk_channel = channels[2]
    em_channel = channels[4]

    posts = [
        Post(
            campaign_id=c1.id,
            channel_id=fb_channel.id,
            author_id=marketer_user.id,
            title="🔥 BÙNG NỔ TRẢI NGHIỆM VỚI AI PHONE X - ĐẶT TRƯỚC NHẬN QUÀ 5 TRIỆU!",
            content="🚀 Công nghệ tương lai đã chính thức có mặt trên tay bạn! AI Phone X với chip xử lý NPU siêu tốc, camera AI xóa phông chuẩn studio và pin 2 ngày liên tục.\n\nƯu đãi mở bán sớm cho 500 khách hàng đầu tiên:\n- Tặng tai nghe không dây Hi-Res trị giá 2.500.000đ\n- Bảo hành rơi vỡ 1 đổi 1 trong 12 tháng\n- Trả góp 0% lãi suất xét duyệt 5 phút",
            hashtags="#AIPhoneX #FutureTech #SmartPhone2026 #SaleOff",
            call_to_action="👉 Đặt Trước Ngay Tại Link Dưới Comment",
            scheduled_at=now - timedelta(days=5),
            status="published",
            ai_generated=True,
            prompt_used="Hãy viết bài giới thiệu tính năng AI Phone X kèm ưu đãi mở bán cho Facebook",
            reviewer_id=admin_user.id,
            reviewer_feedback="Nội dung rất hấp dẫn, CTA rõ ràng. Phê duyệt xuất bản!",
            reviewed_at=now - timedelta(days=6),
            published_at=now - timedelta(days=5)
        ),
        Post(
            campaign_id=c1.id,
            channel_id=tk_channel.id,
            author_id=marketer_user.id,
            title="🎬 Kịch bản Shorts: 3 Tính Năng Ảo Ma Trên AI Phone X",
            content="[Hook 0-3s]: Đừng mua điện thoại mới nếu bạn chưa biết đến tính năng dịch thuật tức thì bằng AI này!\n[Body]: Test trực tiếp camera chụp đêm vs AI Phone X... Quá nét và mượt mà!\n[CTA]: Bấm giỏ hàng bên dưới để săn voucher giảm 1 triệu!",
            hashtags="#ReviewCongNghe #TikTokMadeMeBuyIt #AIPhoneX",
            call_to_action="Nhấn vào giỏ hàng TikTok Shop để nhận ưu đãi",
            scheduled_at=now + timedelta(days=1),
            status="in_review",
            ai_generated=True,
            prompt_used="Tạo kịch bản TikTok 30s review điện thoại AI Phone X phong cách Gen Z",
        ),
        Post(
            campaign_id=c2.id,
            channel_id=fb_channel.id,
            author_id=marketer_user.id,
            title="👗 RẠNG RỠ ĐÓN NẮNG HÈ VỚI SUMMER COLLECTION 2026",
            content="Mùa hè này, hãy để sự tự tin và nét thanh lịch đồng hành cùng bạn trên mọi hành trình khám phá! Chất liệu lụa tơ tằm thoáng mát, màu sắc pastel tươi tắn tôn dáng tuyệt đối.",
            hashtags="#SummerFashion #OOTD #ThoiTrangNu #HolidayVibes",
            call_to_action="Inbox ngay để nhận tư vấn size và mã giảm 15%",
            scheduled_at=now - timedelta(days=2),
            status="published",
            ai_generated=False,
            reviewer_id=admin_user.id,
            reviewer_feedback="Hình ảnh đẹp, câu từ trau chuốt.",
            reviewed_at=now - timedelta(days=3),
            published_at=now - timedelta(days=2)
        ),
        Post(
            campaign_id=c3.id,
            channel_id=em_channel.id,
            author_id=marketer_user.id,
            title="📩 Tối Ưu Hóa 40% Hiệu Suất Bán Hàng Cùng AI CRM",
            content="Kính gửi Quý Doanh nghiệp, giải pháp AI CRM tự động phân loại khách hàng tiềm năng, dự báo doanh số và tối ưu quy trình chăm sóc sau bán.",
            hashtags="#B2B #CRM #MarketingAutomation",
            call_to_action="Đăng ký nhận Demo 1:1 miễn phí cùng Chuyên gia",
            scheduled_at=now + timedelta(days=3),
            status="approved",
            ai_generated=True,
            prompt_used="Soạn thảo email B2B gửi giám đốc kinh doanh giới thiệu phần mềm CRM",
            reviewer_id=admin_user.id,
            reviewer_feedback="Duyệt bài gửi vào thứ 3 tới lúc 9:00 sáng.",
            reviewed_at=now - timedelta(hours=4)
        ),
        Post(
            campaign_id=c2.id,
            channel_id=tk_channel.id,
            author_id=marketer_user.id,
            title="💃 Biến Hình 7 Ngày Cùng BST Váy Hè Năng Động",
            content="Thử thách 7 ngày 7 phong cách phối đồ đi biển cực xinh xắn! Bạn thích set đồ số mấy nhất?",
            hashtags="#OOTDSummer #FashionHacks #BienHinh",
            call_to_action="Comment số thứ tự set bạn ưng ý nhất để nhận voucher",
            scheduled_at=now + timedelta(days=4),
            status="draft",
            ai_generated=True,
            prompt_used="Ý tưởng video biến hình thời trang mùa hè"
        ),
        Post(
            campaign_id=c1.id,
            channel_id=gg_channel.id,
            author_id=marketer_user.id,
            title="🔍 Mẫu Quảng Cáo Google Ads: Mua AI Phone X Nhận Quà",
            content="Headline: Mua AI Phone X Chính Hãng - Giá Tốt Nhất 2026.\nDescription: Siêu phẩm điện thoại AI giảm 30% hôm nay. Bảo hành 12 tháng, giao hàng hỏa tốc 2h.",
            hashtags="#GoogleAds #Promo #AIPhone",
            call_to_action="Nhấp vào để xem chi tiết",
            scheduled_at=now + timedelta(days=2),
            status="rejected",
            ai_generated=True,
            prompt_used="Viết mẫu quảng cáo Google Ads Search cho điện thoại AI Phone",
            reviewer_id=admin_user.id,
            reviewer_feedback="Cần chỉnh lại headline để làm nổi bật tính năng camera AI và cam kết bảo hành rơi vỡ 1 đổi 1 thay vì chỉ giảm giá thông thường. Sửa lại và gửi duyệt lại nhé!",
            reviewed_at=now - timedelta(hours=2)
        )
    ]
    db.add_all(posts)
    db.commit()

    # 5. Seed Metrics
    metrics = [
        # AI Phone X metrics
        Metric(campaign_id=c1.id, channel_id=fb_channel.id, record_date=now - timedelta(days=10), impressions=120000, clicks=5400, conversions=280, spend=22000000.0, revenue=84000000.0, notes="Chiến dịch mở màn Facebook Ads"),
        Metric(campaign_id=c1.id, channel_id=gg_channel.id, record_date=now - timedelta(days=8), impressions=85000, clicks=4800, conversions=310, spend=28000000.0, revenue=112000000.0, notes="Google Search từ khóa AI Phone"),
        Metric(campaign_id=c1.id, channel_id=tk_channel.id, record_date=now - timedelta(days=4), impressions=250000, clicks=8900, conversions=420, spend=18000000.0, revenue=98000000.0, notes="TikTok Ads viral video"),
        
        # Fashion Summer metrics
        Metric(campaign_id=c2.id, channel_id=fb_channel.id, record_date=now - timedelta(days=7), impressions=95000, clicks=4100, conversions=190, spend=14000000.0, revenue=45000000.0, notes="Facebook Carousel Post Ads"),
        Metric(campaign_id=c2.id, channel_id=tk_channel.id, record_date=now - timedelta(days=3), impressions=160000, clicks=6200, conversions=240, spend=12000000.0, revenue=52000000.0, notes="Livestream TikTok Shop"),
        
        # B2B CRM metrics
        Metric(campaign_id=c3.id, channel_id=gg_channel.id, record_date=now - timedelta(days=12), impressions=45000, clicks=1800, conversions=95, spend=35000000.0, revenue=145000000.0, notes="Google Search B2B Enterprise Keywords"),
        Metric(campaign_id=c3.id, channel_id=em_channel.id, record_date=now - timedelta(days=5), impressions=18000, clicks=1200, conversions=60, spend=4500000.0, revenue=72000000.0, notes="Email Marketing chiến dịch nuôi dưỡng Leads"),
        
        # Golden Taste metrics
        Metric(campaign_id=c4.id, channel_id=fb_channel.id, record_date=now - timedelta(days=20), impressions=110000, clicks=5200, conversions=380, spend=25000000.0, revenue=78000000.0, notes="Quảng cáo sự kiện khai trương tại cơ sở mới")
    ]
    db.add_all(metrics)
    db.commit()

    # 6. Seed AI Log
    ai_log1 = AILog(
        user_id=marketer_user.id,
        action_type="idea_generation",
        prompt="Chiến dịch: Ra mắt Siêu phẩm Smartphone AI Phone X. Hãy đề xuất 5 ý tưởng nội dung cho kênh Facebook, giọng văn trẻ trung.",
        response_text="[AI Idea Generator Output] 5 Ý tưởng: Storytelling trải nghiệm AI thế hệ mới, Minigame dự đoán giá ra mắt, Infographic so sánh camera AI, Hậu trường mở hộp unboxing, Ưu đãi mở bán flash sale."
    )
    db.add(ai_log1)
    db.commit()

    print("[Seed Data] Đã khởi tạo thành công dữ liệu mẫu cho hệ thống!")
