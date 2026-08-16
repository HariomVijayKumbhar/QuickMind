import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Initial load of environment variables
load_dotenv(dotenv_path=ENV_PATH, override=True)

class Settings:
    @property
    def GEMINI_API_KEY(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def GROQ_API_KEY(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return os.getenv("GROQ_API_KEY", "")

    @property
    def OPENAI_API_KEY(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def JWT_SECRET_KEY(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        key = os.getenv("JWT_SECRET_KEY", "")
        if not key or key == "your_secret_key_here_change_this":
            # Auto-generate a secure key if not set; stable per-process but
            # note: tokens won't survive server restarts without a fixed key.
            return secrets.token_hex(32)
        return key

    # Provider Priority Order
    PROVIDER_PRIORITY: list = ["gemini", "groq", "openai"]

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Input limits
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_TEXT_LENGTH: int = 10000                 # 10,000 characters
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"}

    # JWT settings
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/quickmind.db"

settings = Settings()
