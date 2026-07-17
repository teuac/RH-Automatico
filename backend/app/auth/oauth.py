from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.config.settings import settings
from app.config.logging_config import error_logger

def verify_google_id_token(token: str) -> Optional[dict]:
    """
    Verifies a Google OAuth ID Token using Google Auth Library.
    Returns the user payload (dict) containing:
      - email
      - hd (Hosted Domain)
      - name
      - picture
    """
    # Allow local mock token for developer testing
    if settings.DEBUG and token == "mock-google-id-token":
        return {
            "email": f"admin@{settings.ALLOWED_DOMAIN}",
            "hd": settings.ALLOWED_DOMAIN,
            "name": "Administrador Local",
            "picture": None
        }

    try:
        # Note: In development, if GOOGLE_CLIENT_ID is not set, we can allow a mock payload
        # for developer testing. However, we'll implement the strict production validation.
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=60
        )
        
        # Verify Hosted Domain (hd) if domain restriction is enabled
        domain = id_info.get("hd")
        email = id_info.get("email")
        
        # Fallback split check if hd is missing (sometimes occurs on custom domains setup)
        email_domain = email.split("@")[-1] if email else None
        
        if settings.ALLOWED_DOMAIN:
            if domain != settings.ALLOWED_DOMAIN and email_domain != settings.ALLOWED_DOMAIN:
                error_logger.warning(f"OAuth attempt rejected: domain {domain or email_domain} does not match {settings.ALLOWED_DOMAIN}")
                return None
                
        return id_info
    except Exception as e:
        error_logger.exception(f"Google ID token verification failed: {str(e)}")
        return None
