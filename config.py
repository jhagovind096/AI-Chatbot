import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HELPDESK_BASE_URL: str = os.getenv("HELPDESK_BASE_URL", "https://rddcgrs.in/api/helpdesk/v1")
    HELPDESK_API_KEY: str = os.getenv("HELPDESK_API_KEY", "your-secure-api-key")
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_EXTENSIONS: set = {".pdf", ".jpg", ".jpeg", ".png"}

    class Config:
        env_file = ".env"

settings = Settings()