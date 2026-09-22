import uvicorn
import sys
import os

if __name__ == "__main__":
    # Ensure current directory is in Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Render cung cấp PORT qua biến môi trường
    port = int(os.environ.get("PORT", 8000))

    print("=====================================================================")
    print("🚀 ĐANG KHỞI CHẠY HỆ THỐNG QUẢN LÝ CHIẾN DỊCH MARKETING TÍCH HỢP AI")

    if os.environ.get("PORT"):
        print(f"👉 Server đang chạy trên port: {port}")
    else:
        print(f"👉 Website: http://127.0.0.1:{port}")
        print(f"👉 Swagger API Docs: http://127.0.0.1:{port}/docs")

    print("👉 Tài khoản Quản lý: admin@marketing.ai / admin123")
    print("👉 Tài khoản Marketer: marketer@marketing.ai / marketer123")
    print("=====================================================================")

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=port
    )