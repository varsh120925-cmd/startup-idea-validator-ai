import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the new project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-startup-validator-key-2026")
    BASE_DIR = BASE_DIR
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "startup_validator.db"))
    EXPORTS_DIR = BASE_DIR / "exports"

    # AI & Search configurations
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

    # Available Groq models
    AVAILABLE_MODELS = [
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile (Recommended)"},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant (Ultra-fast)"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B (High Context)"},
        {"id": "gemma2-9b-it", "name": "Gemma 2 9B IT"}
    ]

    # Server settings
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "127.0.0.1")
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"

    @classmethod
    def update_runtime_keys(cls, groq_key=None, tavily_key=None, model=None, demo_mode=None):
        """Update runtime API keys and settings dynamically from the Settings UI"""
        if groq_key is not None:
            cls.GROQ_API_KEY = groq_key.strip()
        if tavily_key is not None:
            cls.TAVILY_API_KEY = tavily_key.strip()
        if model is not None and model.strip():
            cls.GROQ_MODEL = model.strip()
        if demo_mode is not None:
            cls.DEMO_MODE = bool(demo_mode)
