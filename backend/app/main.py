import sys
import logging
from pathlib import Path

# Automatically add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.models import Base
from app.routes.summarize import router as summarize_router
from app.routes.ask import router as ask_router
from app.routes.generate import router as generate_router
from app.routes.analyze import router as analyze_router
from app.routes.auth import router as auth_router
from app.routes.history import router as history_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quickmind.main")

# Create DB tables on startup (safe to run on every boot — no-op if already exist)
Base.metadata.create_all(bind=engine)
logger.info("Database tables verified/created at startup.")

app = FastAPI(
    title="QuickMind AI Smart Assistant API",
    description="Backend API for QuickMind AI Productivity Application",
    version="2.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registration
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(summarize_router)
app.include_router(ask_router)
app.include_router(generate_router)
app.include_router(analyze_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": "QuickMind AI Smart Assistant API",
        "version": "2.0.0"
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "gemini_api_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "auth": "enabled",
    }

# Global exception handler for uncaught errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Something went wrong while processing your request. Please try again."
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
