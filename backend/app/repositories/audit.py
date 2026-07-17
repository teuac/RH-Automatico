from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from app.repositories.base import BaseRepository
from app.models.audit_log import AuditLog

class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)

    def log(
        self,
        db: Session,
        user_id: Optional[int],
        user_name: Optional[str],
        user_email: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        module: str,
        screen: str,
        action: str,
        description: Optional[str],
        object_changed: Optional[str] = None,
        object_id: Optional[str] = None,
        result: str = "SUCESSO",
        before_state: Optional[str] = None,
        after_state: Optional[str] = None
    ) -> AuditLog:
        now = datetime.datetime.utcnow()
        # Separate date and time formatting
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        db_log = AuditLog(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            action_date=date_str,
            action_time=time_str,
            module=module,
            screen=screen,
            action=action,
            description=description,
            object_changed=object_changed,
            object_id=object_id,
            result=result,
            before_state=before_state,
            after_state=after_state
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    def search_logs(
        self,
        db: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_email: Optional[str] = None,
        action: Optional[str] = None,
        module: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        query = db.query(AuditLog)
        
        if start_date:
            query = query.filter(AuditLog.action_date >= start_date)
        if end_date:
            query = query.filter(AuditLog.action_date <= end_date)
        if user_email:
            query = query.filter(AuditLog.user_email.ilike(f"%{user_email}%"))
        if action:
            query = query.filter(AuditLog.action == action)
        if module:
            query = query.filter(AuditLog.module == module)
            
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

audit_repository = AuditRepository()
