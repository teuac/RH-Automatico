from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.controllers.atestado_controller import atestado_controller
from app.schemas.atestado import AtestadoCreate, AtestadoUpdate, AtestadoResponse
from app.auth.rbac import RoleChecker, get_active_user
from app.models.user import User

router = APIRouter(prefix="/atestados", tags=["Atestados Médicos"])

@router.get("/", response_model=List[AtestadoResponse], dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_atestados(
    obra_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    return atestado_controller.get_all(db=db, obra_id=obra_id, status=status, current_user=current_user)

@router.get("/{atestado_id}", response_model=AtestadoResponse, dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_atestado_by_id(
    atestado_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    return atestado_controller.get_by_id(atestado_id=atestado_id, db=db, current_user=current_user)

@router.post("/", response_model=AtestadoResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def create_atestado(
    request: Request,
    payload: AtestadoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    return atestado_controller.create(request=request, payload=payload, db=db, current_user=current_user)

@router.post("/{atestado_id}/documento", response_model=AtestadoResponse, dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
async def upload_atestado_documento(
    atestado_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    return await atestado_controller.upload_documento(atestado_id=atestado_id, file=file, request=request, db=db, current_user=current_user)

@router.put("/{atestado_id}", response_model=AtestadoResponse, dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def update_atestado(
    atestado_id: int,
    request: Request,
    payload: AtestadoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    return atestado_controller.update(atestado_id=atestado_id, request=request, payload=payload, db=db, current_user=current_user)

@router.delete("/{atestado_id}", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def delete_atestado(
    atestado_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    return atestado_controller.delete(atestado_id=atestado_id, request=request, db=db, current_user=current_user)
