import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .config import settings
from .database import engine, Base, SessionLocal
from .seed_data import seed_database
from .routers import auth_router, campaign_router, content_router, metrics_router, ai_router

# Create DB tables
Base.metadata.create_all(bind=engine)

# Auto migrate campaign_id into ai_logs if SQLite table already exists without it
with engine.connect() as conn:
    try:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(ai_logs)")).fetchall()]
        if cols and "campaign_id" not in cols:
            conn.execute(text("ALTER TABLE ai_logs ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id)"))
            conn.commit()
    except Exception as e:
        print(f"[Migration] Note: {e}")

# Auto seed database with initial demo data
db = SessionLocal()
try:
    seed_database(db)
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Hệ thống Quản lý Chiến dịch Marketing tích hợp AI (FastAPI + SQLite + Modern SPA)"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router.router)
app.include_router(campaign_router.router)
app.include_router(content_router.router)
app.include_router(metrics_router.router)
app.include_router(ai_router.router)

# Mount Frontend Static Assets & HTML
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_home():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Marketing AI Management API is running. Please access /docs for OpenAPI specifications."}

@app.get("/api/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}
