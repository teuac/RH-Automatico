from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os
import json

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

    # Google Sheets Service Account - Opção 1: variáveis individuais (recomendado)
    GOOGLE_SA_TYPE: str = "service_account"
    GOOGLE_SA_PROJECT_ID: str = ""
    GOOGLE_SA_PRIVATE_KEY_ID: str = ""
    GOOGLE_SA_PRIVATE_KEY: str = ""
    GOOGLE_SA_CLIENT_EMAIL: str = ""
    GOOGLE_SA_CLIENT_ID: str = ""
    GOOGLE_SA_CLIENT_X509_CERT_URL: str = ""

    # Google Sheets Service Account - Opção 2: JSON completo em uma variável
    GOOGLE_SERVICE_ACCOUNT_INFO: str = ""

    # Google Sheets Service Account - Opção 3: caminho para arquivo JSON local
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "credentials/service_account.json"

    @property
    def google_service_account_dict(self) -> Optional[dict]:
        """Monta o dict de credenciais da Service Account a partir das variáveis individuais.
        Retorna None se os campos obrigatórios não estiverem preenchidos."""
        if self.GOOGLE_SA_CLIENT_EMAIL and self.GOOGLE_SA_PRIVATE_KEY and self.GOOGLE_SA_PROJECT_ID:
            # Garante que \\n no .env seja interpretado como quebra de linha real
            private_key = self.GOOGLE_SA_PRIVATE_KEY.replace("\\n", "\n")
            return {
                "type": self.GOOGLE_SA_TYPE,
                "project_id": self.GOOGLE_SA_PROJECT_ID,
                "private_key_id": self.GOOGLE_SA_PRIVATE_KEY_ID,
                "private_key": private_key,
                "client_email": self.GOOGLE_SA_CLIENT_EMAIL,
                "client_id": self.GOOGLE_SA_CLIENT_ID,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": self.GOOGLE_SA_CLIENT_X509_CERT_URL,
                "universe_domain": "googleapis.com"
            }
        return None

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
print("Loaded Database URL:", settings.DATABASE_URL)
