from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.controllers.user_controller import user_controller
from app.schemas.user import UserResponse, UserUpdateStatus, UserUpdateRoles
from app.auth.rbac import RoleChecker

router = APIRouter(prefix="/usuarios", tags=["Usuários (Admin)"])

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(RoleChecker(["Administrador"]))])
def list_users(db: Session = Depends(get_db)):
    return user_controller.get_all(db)

@router.put("/{user_id}/status", response_model=UserResponse, dependencies=[Depends(RoleChecker(["Administrador"]))])
def update_user_status(
    user_id: int,
    request: Request,
    payload: UserUpdateStatus,
    db: Session = Depends(get_db)
):
    return user_controller.update_status(user_id, request, payload, db)

@router.put("/{user_id}/roles", response_model=UserResponse, dependencies=[Depends(RoleChecker(["Administrador"]))])
def update_user_roles(
    user_id: int,
    request: Request,
    payload: UserUpdateRoles,
    db: Session = Depends(get_db)
):
    return user_controller.update_roles(user_id, request, payload, db)
