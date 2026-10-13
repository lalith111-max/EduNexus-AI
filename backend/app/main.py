from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.seed import seed_database
from app.api.health import router as health_router
from app.api.courses import router as courses_router
from app.api.sources import router as sources_router
from app.api.tutor import router as tutor_router
from app.api.assessments import router as assessments_router
from app.api.mastery import router as mastery_router
from app.api.evaluation import router as evaluation_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database initialized & seeded with competition datasets
    seed_database()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multimodal AI Learning & Source-Grounded Tutoring Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(health_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(tutor_router, prefix="/api")
app.include_router(assessments_router, prefix="/api")
app.include_router(mastery_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }
