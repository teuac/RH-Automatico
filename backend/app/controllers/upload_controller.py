from fastapi import Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database.session import get_db
from app.services.upload_service import upload_service
from app.repositories.upload import upload_repository
from app.repositories.pending_record import pending_record_repository
from app.schemas.upload import UploadCommitRequest, UploadResponse
from app.auth.rbac import get_active_user
from app.models.user import User

class UploadController:
    @staticmethod
    async def preview(
        obra_id: int = Form(...),
        planilha_id: int = Form(...),
        override_date: Optional[str] = Form(None),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        file_bytes = await file.read()
        return upload_service.generate_preview(
            db=db,
            obra_id=obra_id,
            planilha_id=planilha_id,
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            override_date=override_date
        )

    @staticmethod
    def commit(
        request: Request,
        payload: UploadCommitRequest,
        db: Session,
        current_user: User
    ):
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Format the employees back to list of dicts for service call
        employees = [emp.model_dump() for emp in payload.funcionarios]
        
        return upload_service.commit_sync(
            db=db,
            user=current_user,
            ip_address=ip_address,
            user_agent=user_agent,
            obra_id=payload.obra_id,
            planilha_id=payload.planilha_id,
            date_str=payload.date,
            filename=payload.filename,
            funcionarios_data=employees
        )

    @staticmethod
    def get_history(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> List[UploadResponse]:
        return upload_repository.get_uploads_with_relations(db, skip, limit)

    @staticmethod
    def get_pending_records(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ):
        records = pending_record_repository.get_pending(db, skip, limit)
        return [
            {
                "id": rec.id,
                "upload_id": rec.upload_id,
                "obra_nome": rec.upload.obra.nome if rec.upload and rec.upload.obra else "Desconhecida",
                "employee_id": rec.employee_id,
                "employee_name": rec.employee_name,
                "date": rec.date,
                "times": rec.times,
                "status": rec.status,
                "reason": rec.reason,
                "created_at": rec.created_at
            }
            for rec in records
        ]

    @staticmethod
    def resolve_pending(
        record_id: int,
        status_action: str,  # 'RESOLVIDO' or 'IGNORADO'
        db: Session = Depends(get_db)
    ):
        """Resolves a pending presence record after administrator/RH takes action"""
        record = pending_record_repository.get(db, record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pendente não localizado.")
        
        record.status = status_action
        db.commit()
        return {"detail": f"Registro pendente marcado como {status_action}."}

upload_controller = UploadController()
