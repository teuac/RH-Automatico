from sqlalchemy.orm import Session, joinedload
from typing import List
from app.repositories.base import BaseRepository
from app.models.upload import Upload

class UploadRepository(BaseRepository[Upload]):
    def __init__(self):
        super().__init__(Upload)

    def get_uploads_with_relations(self, db: Session, skip: int = 0, limit: int = 100) -> List[Upload]:
        return (
            db.query(Upload)
            .options(joinedload(Upload.user), joinedload(Upload.obra), joinedload(Upload.planilha))
            .order_by(Upload.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_daily_uploads_count(self, db: Session) -> int:
        import datetime
        today = datetime.datetime.utcnow().date()
        start_of_day = datetime.datetime.combine(today, datetime.time.min)
        return db.query(Upload).filter(Upload.created_at >= start_of_day).count()

upload_repository = UploadRepository()
