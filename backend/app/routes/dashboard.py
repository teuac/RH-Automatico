from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.controllers.dashboard_controller import dashboard_controller
from app.auth.rbac import RoleChecker

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", dependencies=[Depends(RoleChecker(["Administrador"]))])
def get_dashboard_statistics(db: Session = Depends(get_db)):
    return dashboard_controller.get_stats(db)
