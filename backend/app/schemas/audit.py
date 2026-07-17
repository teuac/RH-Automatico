from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action_date: str
    action_time: str
    module: str
    screen: str
    action: str
    description: Optional[str] = None
    object_changed: Optional[str] = None
    object_id: Optional[str] = None
    result: str
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
