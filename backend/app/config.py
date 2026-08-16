import os
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
        # Re-read .env dynamically so key updates take effect immediately
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return os.getenv("GEMINI_API_KEY", "")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Input limits
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_TEXT_LENGTH: int = 10000                 # 10,000 characters
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt"}

settings = Settings()

