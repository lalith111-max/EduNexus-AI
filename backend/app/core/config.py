import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "EduNexus AI"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'edunexus.db'}"
    
    # LLM & Embedding Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_PROVIDER: str = "demo"  # "demo", "gemini", "openai"
    
    # BKT Default Hyperparameters
    BKT_DEFAULT_P_L0: float = 0.20  # Prior mastery probability
    BKT_DEFAULT_P_T: float = 0.15   # Probability of learning transition
    BKT_DEFAULT_P_G: float = 0.25   # Probability of guess (for 4-choice MCQ)
    BKT_DEFAULT_P_S: float = 0.10   # Probability of slip
    
    # File limits
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".pptx", ".txt", ".md", ".mp3", ".mp4", ".wav", ".m4a"]
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
