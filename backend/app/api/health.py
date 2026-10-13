from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="", tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "demo_mode": settings.DEFAULT_LLM_PROVIDER == "demo" or not settings.GEMINI_API_KEY,
        "timestamp": "2026-10-13T09:30:00Z"
    }
