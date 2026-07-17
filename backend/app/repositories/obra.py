from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.obra import Obra

class ObraRepository(BaseRepository[Obra]):
    def __init__(self):
        super().__init__(Obra)

    def get_by_codigo(self, db: Session, codigo: str) -> Optional[Obra]:
        return db.query(Obra).filter(Obra.codigo == codigo).first()

    def get_active(self, db: Session) -> List[Obra]:
        return db.query(Obra).filter(Obra.status == "ATIVO").all()

obra_repository = ObraRepository()
