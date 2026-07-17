from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.controllers.audit_controller import audit_controller
from app.schemas.audit import AuditLogResponse
from app.auth.rbac import RoleChecker

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])

@router.get("/", response_model=List[AuditLogResponse], dependencies=[Depends(RoleChecker(["Administrador"]))])
def search_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_email: Optional[str] = None,
    action: Optional[str] = None,
    module: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return audit_controller.get_logs(
        start_date=start_date,
        end_date=end_date,
        user_email=user_email,
        action=action,
        module=module,
        skip=skip,
        limit=limit,
        db=db
    )
