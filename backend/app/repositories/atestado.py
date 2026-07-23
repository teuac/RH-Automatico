from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.atestado import Atestado
from app.models.colaborador import Colaborador

class AtestadoRepository(BaseRepository[Atestado]):
    def __init__(self):
        super().__init__(Atestado)

    def get_with_relations(self, db: Session, id: int) -> Optional[Atestado]:
        return db.query(Atestado).options(joinedload(Atestado.colaborador)).filter(Atestado.id == id).first()

    def get_multi_with_relations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 1000,
        obra_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Atestado]:
        query = db.query(Atestado).options(joinedload(Atestado.colaborador)).join(Atestado.colaborador)
        if obra_id:
            query = query.filter(Colaborador.obra_id == obra_id)
        if status:
            query = query.filter(Atestado.status == status)
        return query.order_by(Atestado.data_inicio.desc()).offset(skip).limit(limit).all()

    def get_active_atestados_for_date(
        self,
        db: Session,
        target_date: date,
        obra_id: Optional[int] = None
    ) -> List[Atestado]:
        query = db.query(Atestado).options(joinedload(Atestado.colaborador)).join(Atestado.colaborador).filter(
            Atestado.status == "HOMOLOGADO",
            Atestado.data_inicio <= target_date,
            Atestado.data_fim >= target_date
        )
        if obra_id:
            query = query.filter(Colaborador.obra_id == obra_id)
        return query.all()

atestado_repository = AtestadoRepository()
