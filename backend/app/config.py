import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load local environment variables when running locally.
# On Render, environment variables configured in the dashboard are used.
load_dotenv(dotenv_path=ENV_PATH, override=False)


class Settings:
    @staticmethod
    def _get_env(name: str, default: str = "") -> str:
        return os.getenv(name, default)

    @property
    def GEMINI_API_KEY(self) -> str:
        return self._get_env("GEMINI_API_KEY")

    @property
    def GROQ_API_KEY(self) -> str:
        return self._get_env("GROQ_API_KEY")

    @property
    def OPENAI_API_KEY(self) -> str:
        return self._get_env("OPENAI_API_KEY")

    @property
    def JWT_SECRET_KEY(self) -> str:
        key = self._get_env("JWT_SECRET_KEY")
        if not key or key == "your_secret_key_here_change_this":
            # Local fallback only. Set JWT_SECRET_KEY in Render for production
            # so tokens remain valid after a restart/redeploy.
            return secrets.token_hex(32)
        return key

    # Provider Priority Order
    PROVIDER_PRIORITY: list = ["gemini", "groq", "openai"]

    # Render provides the PORT environment variable. Keep 8000 as a local fallback.
    HOST: str = _get_env.__func__("HOST", "0.0.0.0")
    PORT: int = int(_get_env.__func__("PORT", "8000"))

    # Input limits
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_TEXT_LENGTH: int = 10000
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"}

    # JWT settings
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/quickmind.db"


settings = Settings()
