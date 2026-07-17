from typing import Optional, List, Any
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.planilha import Planilha

class PlanilhaRepository(BaseRepository[Planilha]):
    def __init__(self):
        super().__init__(Planilha)

    def get(self, db: Session, id: Any) -> Optional[Planilha]:
        return (
            db.query(Planilha)
            .options(joinedload(Planilha.obra))
            .filter(Planilha.id == id)
            .first()
        )

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Planilha]:
        return (
            db.query(Planilha)
            .options(joinedload(Planilha.obra))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active(self, db: Session) -> List[Planilha]:
        return (
            db.query(Planilha)
            .options(joinedload(Planilha.obra))
            .filter(Planilha.status == "ATIVO")
            .all()
        )

planilha_repository = PlanilhaRepository()
