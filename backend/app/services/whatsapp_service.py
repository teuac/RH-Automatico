import requests
import base64
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.settings import system_settings_repository

logger = logging.getLogger("app")

class WhatsAppService:
    def _get_credentials(self, db: Session) -> Dict[str, str]:
        """Loads Evolution API configurations dynamically from the database."""
        url_setting = system_settings_repository.get_by_key(db, "EVOLUTION_API_URL")
        token_setting = system_settings_repository.get_by_key(db, "EVOLUTION_API_TOKEN")
        instance_setting = system_settings_repository.get_by_key(db, "EVOLUTION_API_INSTANCE")

        return {
            "url": (url_setting.value if url_setting else "").rstrip("/"),
            "token": token_setting.value if token_setting else "",
            "instance": instance_setting.value if instance_setting else ""
        }

    def is_configured(self, db: Session) -> bool:
        creds = self._get_credentials(db)
        return bool(creds["url"] and creds["token"] and creds["instance"])

    def send_message(self, db: Session, to_number: str, text: str) -> Optional[Dict[str, Any]]:
        """Sends a text message to a specific WhatsApp number."""
        creds = self._get_credentials(db)
        if not creds["url"] or not creds["token"] or not creds["instance"]:
            logger.error("WhatsApp credentials are not fully configured.")
            return None

        # Clean number formatting (remove +, spaces, dashes)
        clean_num = to_number.replace("+", "").replace(" ", "").replace("-", "")
        
        # Auto-prepend Brazilian country code 55 if missing (10 or 11 digits local format)
        if len(clean_num) in (10, 11) and not clean_num.startswith("55"):
            clean_num = "55" + clean_num
        
        url = f"{creds['url']}/message/sendText/{creds['instance']}"
        headers = {
            "apikey": creds["token"],
            "Content-Type": "application/json"
        }
        payload = {
            "number": clean_num,
            "text": text,
            "delay": 1200
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return None

    def download_media(self, db: Session, message_id: str, remote_jid: str) -> Optional[bytes]:
        """Downloads candidate media (image/document) from Evolution API and returns bytes."""
        creds = self._get_credentials(db)
        if not creds["url"] or not creds["token"] or not creds["instance"]:
            logger.error("WhatsApp credentials not configured for media download.")
            return None

        url = f"{creds['url']}/chat/getBase64FromMediaMessage/{creds['instance']}"
        headers = {
            "apikey": creds["token"],
            "Content-Type": "application/json"
        }
        
        # Evolution API getBase64FromMediaMessage payload uses the message ID
        payload = {
            "message": {
                "key": {
                    "id": message_id
                }
            },
            "convertToMp4": False
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            # The API usually returns base64 data under the "base64" key, or "buffer" key,
            # or directly if it's string. Let's check both possibilities.
            b64_str = data.get("base64") or data.get("buffer")
            if not b64_str and isinstance(data, str):
                b64_str = data
                
            if b64_str:
                # Strip potential base64 mime header if present (e.g. data:image/jpeg;base64,...)
                if "," in b64_str:
                    b64_str = b64_str.split(",")[1]
                return base64.b64decode(b64_str)
            
            logger.error(f"Could not extract base64 data from download media response for message {message_id}")
            return None
        except Exception as e:
            logger.error(f"Error downloading WhatsApp media for message {message_id}: {str(e)}")
            return None

    def configure_webhook(self, db: Session, backend_url: str) -> bool:
        """Registers the backend webhook endpoint in the active Evolution API instance."""
        creds = self._get_credentials(db)
        if not creds["url"] or not creds["token"] or not creds["instance"]:
            logger.warning("WhatsApp credentials not configured. Webhook skipped.")
            return False

        url = f"{creds['url']}/webhook/set/{creds['instance']}"
        headers = {
            "apikey": creds["token"],
            "Content-Type": "application/json"
        }
        
        webhook_url = f"{backend_url.rstrip('/')}/api/v1/contratacoes/webhook"
        
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "events": ["MESSAGES_UPSERT"]
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Evolution API webhook configured successfully for: {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Error setting Evolution API webhook: {str(e)}")
            return False

whatsapp_service = WhatsAppService()
