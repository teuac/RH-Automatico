from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.controllers.upload_controller import upload_controller
from app.schemas.upload import UploadCommitRequest, UploadResponse
from app.auth.rbac import RoleChecker

router = APIRouter(prefix="/uploads", tags=["Uploads & Sincronização"])

@router.post("/preview", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
async def preview_upload(
    obra_id: int = Form(...),
    override_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await upload_controller.preview(
        obra_id=obra_id,
        override_date=override_date,
        file=file,
        db=db
    )

@router.post("/commit", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def commit_upload(
    request: Request,
    payload: UploadCommitRequest,
    db: Session = Depends(get_db)
):
    return upload_controller.commit(request, payload, db)

@router.get("/history", response_model=List[UploadResponse], dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_upload_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return upload_controller.get_history(skip, limit, db)

@router.get("/pending", dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_pending_entries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return upload_controller.get_pending_records(skip, limit, db)

@router.put("/pending/{record_id}/resolve", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def resolve_pending_entry(
    record_id: int,
    status_action: str = Form(...),  # 'RESOLVIDO' or 'IGNORADO'
    db: Session = Depends(get_db)
):
    return upload_controller.resolve_pending(record_id, status_action, db)
