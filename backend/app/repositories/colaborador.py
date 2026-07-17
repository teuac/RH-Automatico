from typing import Optional, List, Any
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.colaborador import Colaborador


class ColaboradorRepository(BaseRepository[Colaborador]):
    def __init__(self):
        super().__init__(Colaborador)

    def get(self, db: Session, id: Any) -> Optional[Colaborador]:
        return (
            db.query(Colaborador)
            .options(joinedload(Colaborador.obra))
            .filter(Colaborador.id == id)
            .first()
        )

    def get_by_matricula(self, db: Session, matricula: str) -> Optional[Colaborador]:
        return db.query(Colaborador).filter(Colaborador.matricula == matricula).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 200,
        obra_id: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Colaborador]:
        query = db.query(Colaborador).options(joinedload(Colaborador.obra))
        if obra_id:
            query = query.filter(Colaborador.obra_id == obra_id)
        if status:
            query = query.filter(Colaborador.status == status)
        if search:
            like = f"%{search}%"
            query = query.filter(
                Colaborador.nome.ilike(like) | Colaborador.matricula.ilike(like)
            )
        return query.order_by(Colaborador.nome).offset(skip).limit(limit).all()

    def count(self, db: Session) -> int:
        return db.query(Colaborador).count()

    def bulk_create(self, db: Session, items: List[dict]) -> List[Colaborador]:
        """Insert multiple colaboradores, skipping duplicates by matricula."""
        created = []
        for item in items:
            existing = self.get_by_matricula(db, item["matricula"])
            if not existing:
                obj = Colaborador(**item)
                db.add(obj)
                created.append(obj)
        db.commit()
        for obj in created:
            db.refresh(obj)
        return created

    def migrate_obra(self, db: Session, ids: List[int], nova_obra_id: int) -> int:
        """Bulk update obra_id for given colaborador ids. Returns count updated."""
        count = (
            db.query(Colaborador)
            .filter(Colaborador.id.in_(ids))
            .update({"obra_id": nova_obra_id}, synchronize_session="fetch")
        )
        db.commit()
        return count


colaborador_repository = ColaboradorRepository()
