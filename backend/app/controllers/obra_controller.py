import json
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.repositories.obra import obra_repository
from app.repositories.audit import audit_repository
from app.schemas.obra import ObraCreate, ObraUpdate, ObraResponse
from app.auth.rbac import get_active_user
from app.models.user import User

class ObraController:
    @staticmethod
    def get_all(db: Session = Depends(get_db), current_user: User = Depends(get_active_user)) -> List[ObraResponse]:
        return obra_repository.get_multi(db)

    @staticmethod
    def get_by_id(obra_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)) -> ObraResponse:
        obra = obra_repository.get(db, obra_id)
        if not obra:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra não encontrada.")
        return obra

    @staticmethod
    def create(
        request: Request,
        payload: ObraCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> ObraResponse:
        # Check uniqueness of code
        existing = obra_repository.get_by_codigo(db, payload.codigo)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código de obra já cadastrado.")
            
        obra = obra_repository.create(db, payload.model_dump())
        
        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Obras",
            action="CREATE",
            description=f"Cadastrou nova obra: {obra.nome} (Código: {obra.codigo})",
            object_changed="obras",
            object_id=str(obra.id),
            result="SUCESSO",
            after_state=json.dumps(payload.model_dump())
        )
        return obra

    @staticmethod
    def update(
        obra_id: int,
        request: Request,
        payload: ObraUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> ObraResponse:
        obra = obra_repository.get(db, obra_id)
        if not obra:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra não encontrada.")
            
        before_state = {
            "nome": obra.nome,
            "codigo": obra.codigo,
            "status": obra.status,
            "observacoes": obra.observacoes
        }
        
        # Update Obra
        updated_data = payload.model_dump(exclude_unset=True)
        updated_obra = obra_repository.update(db, obra, updated_data)
        
        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Obras",
            action="UPDATE",
            description=f"Atualizou a obra: {updated_obra.nome}",
            object_changed="obras",
            object_id=str(updated_obra.id),
            result="SUCESSO",
            before_state=json.dumps(before_state),
            after_state=json.dumps(updated_data)
        )
        return updated_obra

    @staticmethod
    def delete(
        obra_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ):
        obra = obra_repository.get(db, obra_id)
        if not obra:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra não encontrada.")
            
        before_state = {
            "nome": obra.nome,
            "codigo": obra.codigo,
            "status": obra.status,
            "observacoes": obra.observacoes
        }
        
        obra_repository.remove(db, obra_id)
        
        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Obras",
            action="DELETE",
            description=f"Removeu a obra: {before_state['nome']}",
            object_changed="obras",
            object_id=str(obra_id),
            result="SUCESSO",
            before_state=json.dumps(before_state)
        )
        return {"detail": "Obra removida com sucesso."}

obra_controller = ObraController()
