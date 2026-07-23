import json
from datetime import datetime, date
from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.atestado import atestado_repository
from app.repositories.colaborador import colaborador_repository
from app.repositories.audit import audit_repository
from app.schemas.atestado import AtestadoCreate, AtestadoUpdate, AtestadoResponse
from app.auth.rbac import get_active_user
from app.models.user import User

class AtestadoController:
    @staticmethod
    def get_all(
        db: Session = Depends(get_db),
        obra_id: Optional[int] = None,
        status: Optional[str] = None,
        current_user: User = Depends(get_active_user)
    ) -> List[AtestadoResponse]:
        return atestado_repository.get_multi_with_relations(db, obra_id=obra_id, status=status)

    @staticmethod
    def get_by_id(
        atestado_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> AtestadoResponse:
        atestado = atestado_repository.get_with_relations(db, atestado_id)
        if not atestado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atestado não encontrado.")
        return atestado

    @staticmethod
    def create(
        request: Request,
        payload: AtestadoCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> AtestadoResponse:
        colaborador = colaborador_repository.get(db, payload.colaborador_id)
        if not colaborador:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colaborador não encontrado.")

        if payload.data_fim < payload.data_inicio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data final não pode ser anterior à data de início.")

        dias = (payload.data_fim - payload.data_inicio).days + 1
        data_dict = payload.model_dump()
        data_dict["dias"] = dias

        atestado = atestado_repository.create(db, data_dict)

        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Atestados",
            screen="Atestados",
            action="CREATE",
            description=f"Cadastrou atestado para {colaborador.nome} ({dias} dias: {payload.data_inicio} a {payload.data_fim})",
            object_changed="atestados",
            object_id=str(atestado.id),
            result="SUCESSO",
            after_state=json.dumps(payload.model_dump(), default=str)
        )
        return atestado_repository.get_with_relations(db, atestado.id)

    @staticmethod
    def update(
        atestado_id: int,
        request: Request,
        payload: AtestadoUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> AtestadoResponse:
        atestado = atestado_repository.get(db, atestado_id)
        if not atestado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atestado não encontrado.")

        data_dict = payload.model_dump(exclude_unset=True)
        start = data_dict.get("data_inicio", atestado.data_inicio)
        end = data_dict.get("data_fim", atestado.data_fim)

        if end < start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data final não pode ser anterior à data de início.")

        data_dict["dias"] = (end - start).days + 1

        before_state = {
            "colaborador_id": atestado.colaborador_id,
            "data_inicio": str(atestado.data_inicio),
            "data_fim": str(atestado.data_fim),
            "dias": atestado.dias,
            "status": atestado.status
        }

        updated_atestado = atestado_repository.update(db, atestado, data_dict)

        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Atestados",
            screen="Atestados",
            action="UPDATE",
            description=f"Atualizou atestado #{updated_atestado.id}",
            object_changed="atestados",
            object_id=str(updated_atestado.id),
            result="SUCESSO",
            before_state=json.dumps(before_state),
            after_state=json.dumps(data_dict, default=str)
        )
        return atestado_repository.get_with_relations(db, updated_atestado.id)

    @staticmethod
    def delete(
        atestado_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ):
        atestado = atestado_repository.get(db, atestado_id)
        if not atestado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atestado não encontrado.")

        before_state = {
            "colaborador_id": atestado.colaborador_id,
            "data_inicio": str(atestado.data_inicio),
            "data_fim": str(atestado.data_fim),
            "dias": atestado.dias,
            "status": atestado.status
        }

        atestado_repository.remove(db, atestado_id)

        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Atestados",
            screen="Atestados",
            action="DELETE",
            description=f"Removeu atestado #{atestado_id}",
            object_changed="atestados",
            object_id=str(atestado_id),
            result="SUCESSO",
            before_state=json.dumps(before_state)
        )
        return {"detail": "Atestado removido com sucesso."}

    @staticmethod
    async def upload_documento(
        atestado_id: int,
        file,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> AtestadoResponse:
        atestado = atestado_repository.get(db, atestado_id)
        if not atestado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atestado não encontrado.")

        ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else ""
        if ext not in ["pdf", "png", "jpg", "jpeg"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato não suportado. Envie PDF ou Imagem (PNG, JPG).")

        import os
        import time
        uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "atestados"))
        os.makedirs(uploads_dir, exist_ok=True)

        safe_filename = f"atestado_{atestado_id}_{int(time.time())}.{ext}"
        file_path = os.path.join(uploads_dir, safe_filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        doc_url = f"/uploads/atestados/{safe_filename}"
        updated = atestado_repository.update(db, atestado, {"documento_url": doc_url})

        return atestado_repository.get_with_relations(db, updated.id)

atestado_controller = AtestadoController()
