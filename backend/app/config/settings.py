from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/rh_presenca"
    SECRET_KEY: str = "supersecretkeychangeinproduction1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str = "your-google-client-id.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = "your-google-client-secret"
    ALLOWED_DOMAIN: str = "acengenharia.com.br"
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "credentials/service_account.json"
    GOOGLE_SERVICE_ACCOUNT_INFO: str = ""

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
print("Loaded Database URL:", settings.DATABASE_URL)
