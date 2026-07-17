from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    picture_url: Optional[str] = None
    is_active: bool
    status: str
    created_at: datetime
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True

class UserUpdateStatus(BaseModel):
    status: str  # 'PENDENTE', 'ATIVO'

class UserUpdateRoles(BaseModel):
    roles: List[str]  # e.g., ['Administrador', 'RH']

class GoogleLoginRequest(BaseModel):
    token: str
