from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.controllers.obra_controller import obra_controller
from app.schemas.obra import ObraCreate, ObraUpdate, ObraResponse
from app.auth.rbac import RoleChecker, get_active_user
from app.models.user import User

router = APIRouter(prefix="/obras", tags=["Obras"])

# Read accessibility for all profiles
@router.get("/", response_model=List[ObraResponse], dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def list_obras(db: Session = Depends(get_db)):
    return obra_controller.get_all(db)

@router.get("/{obra_id}", response_model=ObraResponse, dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_obra(obra_id: int, db: Session = Depends(get_db)):
    return obra_controller.get_by_id(obra_id, db)

# Write modifications restricted to Administrador
@router.post("/", response_model=ObraResponse, dependencies=[Depends(RoleChecker(["Administrador"]))])
def create_obra(request: Request, payload: ObraCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    return obra_controller.create(request, payload, db, current_user)

@router.put("/{obra_id}", response_model=ObraResponse, dependencies=[Depends(RoleChecker(["Administrador"]))])
def update_obra(obra_id: int, request: Request, payload: ObraUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    return obra_controller.update(obra_id, request, payload, db, current_user)

@router.delete("/{obra_id}", dependencies=[Depends(RoleChecker(["Administrador"]))])
def delete_obra(obra_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    return obra_controller.delete(obra_id, request, db, current_user)
