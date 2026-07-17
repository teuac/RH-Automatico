from fastapi import Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.repositories.audit import audit_repository
from app.schemas.audit import AuditLogResponse
from app.auth.rbac import get_active_user
from app.models.user import User

class AuditController:
    @staticmethod
    def get_logs(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_email: Optional[str] = None,
        action: Optional[str] = None,
        module: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> List[AuditLogResponse]:
        return audit_repository.search_logs(
            db=db,
            start_date=start_date,
            end_date=end_date,
            user_email=user_email,
            action=action,
            module=module,
            skip=skip,
            limit=limit
        )

audit_controller = AuditController()
