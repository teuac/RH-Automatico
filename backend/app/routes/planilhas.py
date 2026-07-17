from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.controllers.planilha_controller import planilha_controller
from app.schemas.planilha import PlanilhaCreate, PlanilhaUpdate, PlanilhaResponse
from app.auth.rbac import RoleChecker, get_active_user
from app.models.user import User

router = APIRouter(prefix="/planilhas", tags=["Planilhas"])

# Read accessibility for all profiles
@router.get("/", response_model=List[PlanilhaResponse], dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def list_spreadsheets(db: Session = Depends(get_db)):
    return planilha_controller.get_all(db)

@router.get("/{planilha_id}", response_model=PlanilhaResponse, dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_spreadsheet(planilha_id: int, db: Session = Depends(get_db)):
    return planilha_controller.get_by_id(planilha_id, db)

# Write modifications restricted to Administrador
@router.post("/", response_model=PlanilhaResponse, dependencies=[Depends(RoleChecker(["Administrador"]))])
def create_spreadsheet(request: Request, payload: PlanilhaCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    return planilha_controller.create(request, payload, db, current_user)

@router.put("/{planilha_id}", response_model=PlanilhaResponse, dependencies=[Depends(RoleChecker(["Administrador"]))])
def update_spreadsheet(planilha_id: int, request: Request, payload: PlanilhaUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    return planilha_controller.update(planilha_id, request, payload, db, current_user)

@router.delete("/{planilha_id}", dependencies=[Depends(RoleChecker(["Administrador"]))])
def delete_spreadsheet(planilha_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    return planilha_controller.delete(planilha_id, request, db, current_user)
