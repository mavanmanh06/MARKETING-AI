import os
from pathlib import Path


def _load_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        return api_key

    key_file = Path(__file__).resolve().parents[2] / "APIkey.env"
    if not key_file.is_file():
        return ""

    value = key_file.read_text(encoding="utf-8").strip()
    if value.startswith("GEMINI_API_KEY="):
        value = value.partition("=")[2].strip()
    return value.strip("\"'")

class Settings:
    PROJECT_NAME: str = "Hệ thống Quản lý Chiến dịch Marketing tích hợp AI"
    PROJECT_VERSION: str = "1.0.0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "marketing-ai-super-secret-key-2026-secure-token-998877")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./marketing_ai.db")
    
    # AI Engine Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = _load_gemini_api_key()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    AI_MODEL: str = os.getenv("AI_MODEL", "smart-ai-engine")

settings = Settings()
