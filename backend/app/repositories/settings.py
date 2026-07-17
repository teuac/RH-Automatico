from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.settings import SystemSettings

class SystemSettingsRepository(BaseRepository[SystemSettings]):
    def __init__(self):
        super().__init__(SystemSettings)

    def get_by_key(self, db: Session, key: str) -> Optional[SystemSettings]:
        return db.query(SystemSettings).filter(SystemSettings.key == key).first()

    def set_value(self, db: Session, key: str, value: str, description: Optional[str] = None) -> SystemSettings:
        setting = self.get_by_key(db, key)
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SystemSettings(key=key, value=value, description=description)
            db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

system_settings_repository = SystemSettingsRepository()
