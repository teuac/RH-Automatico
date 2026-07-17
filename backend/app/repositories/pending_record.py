from sqlalchemy.orm import Session, joinedload
from typing import List
from app.repositories.base import BaseRepository
from app.models.pending_record import PendingRecord

class PendingRecordRepository(BaseRepository[PendingRecord]):
    def __init__(self):
        super().__init__(PendingRecord)

    def get_pending(self, db: Session, skip: int = 0, limit: int = 100) -> List[PendingRecord]:
        return (
            db.query(PendingRecord)
            .options(joinedload(PendingRecord.upload))
            .filter(PendingRecord.status == "PENDENTE")
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_count(self, db: Session) -> int:
        return db.query(PendingRecord).filter(PendingRecord.status == "PENDENTE").count()

pending_record_repository = PendingRecordRepository()
