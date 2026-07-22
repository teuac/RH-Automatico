from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.auth.jwt import verify_token
from app.repositories.user import user_repository
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates token and extracts user.
    Allows PENDENTE users because they need to reach their profile/me page to view status.
    """
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Payload do token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = int(user_id_str)
    user = user_repository.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
        
    return user

def get_active_user(user: User = Depends(get_current_user)) -> User:
    """Verifies that the user has been activated by an administrator"""
    user_role_names = [role.name for role in user.roles]
    if user.status == "PENDENTE" and "Administrador" not in user_role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aguarde a liberação do administrador."
        )
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_active_user)) -> User:
        user_role_names = [role.name for role in user.roles]
        
        # 'Administrador' overrides all checks (superuser)
        if "Administrador" in user_role_names:
            return user
            
        # Check if user has any of the allowed roles
        if not any(role in self.allowed_roles for role in user_role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado para esta funcionalidade."
            )
            
        return user
