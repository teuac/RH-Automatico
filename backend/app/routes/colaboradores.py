from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.session import get_db
from app.controllers.colaborador_controller import colaborador_controller
from app.schemas.colaborador import ColaboradorCreate, ColaboradorUpdate, MigrarObraRequest
from app.auth.rbac import RoleChecker, get_active_user
from app.models.user import User

router = APIRouter(prefix="/colaboradores", tags=["Colaboradores"])

ADMIN_RH = ["Administrador", "RH"]
ALL_ROLES = ["Administrador", "RH", "Consulta"]


@router.get("/")
def list_colaboradores(
    skip: int = 0,
    limit: int = 500,
    obra_id: Optional[int] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(ALL_ROLES))
):
    from app.repositories.colaborador import colaborador_repository
    return colaborador_repository.get_multi(db, skip, limit, obra_id, search, status)


@router.get("/template")
def download_template(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(ADMIN_RH))
):
    return colaborador_controller.download_template(db, current_user)


@router.post("/import")
async def import_colaboradores(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(ADMIN_RH))
):
    return await colaborador_controller.import_excel(request, file, db, current_user)


@router.post("/migrar-obra")
def migrar_obra(
    request: Request,
    payload: MigrarObraRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(ADMIN_RH))
):
    return colaborador_controller.migrar_obra(request, payload, db, current_user)


@router.post("/")
def create_colaborador(
    request: Request,
    payload: ColaboradorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(ADMIN_RH))
):
    return colaborador_controller.create(request, payload, db, current_user)


@router.put("/{colaborador_id}")
def update_colaborador(
    colaborador_id: int,
    request: Request,
    payload: ColaboradorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(ADMIN_RH))
):
    return colaborador_controller.update(colaborador_id, request, payload, db, current_user)


@router.delete("/{colaborador_id}")
def delete_colaborador(
    colaborador_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(ADMIN_RH))
):
    return colaborador_controller.delete(colaborador_id, request, db, current_user)
