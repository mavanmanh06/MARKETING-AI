import uvicorn
import sys
import os

if __name__ == "__main__":
    # Ensure current directory is in Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    print("=====================================================================")
    print("🚀 ĐANG KHỞI CHẠY HỆ THỐNG QUẢN LÝ CHIẾN DỊCH MARKETING TÍCH HỢP AI")
    print("👉 Website: http://127.0.0.1:8000")
    print("👉 Swagger API Docs: http://127.0.0.1:8000/docs")
    print("👉 Tài khoản Quản lý: admin@marketing.ai / admin123")
    print("👉 Tài khoản Marketer: marketer@marketing.ai / marketer123")
    print("=====================================================================")
    
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
