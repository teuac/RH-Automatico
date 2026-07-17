import json
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.repositories.user import user_repository
from app.repositories.audit import audit_repository
from app.schemas.user import UserResponse, UserUpdateStatus, UserUpdateRoles
from app.auth.rbac import get_active_user
from app.models.user import User

class UserController:
    @staticmethod
    def get_all(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> List[UserResponse]:
        return user_repository.get_users_with_roles(db)

    @staticmethod
    def update_status(
        user_id: int,
        request: Request,
        payload: UserUpdateStatus,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> UserResponse:
        target_user = user_repository.get(db, user_id)
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
            
        if target_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Você não pode alterar seu próprio status."
            )

        before_status = target_user.status
        user_repository.update_user_status(db, target_user, payload.status)
        
        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Usuarios",
            action="UPDATE",
            description=f"Alterou status do usuário '{target_user.email}' de '{before_status}' para '{payload.status}'",
            object_changed="users",
            object_id=str(target_user.id),
            result="SUCESSO",
            before_state=json.dumps({"status": before_status}),
            after_state=json.dumps({"status": payload.status})
        )
        return target_user

    @staticmethod
    def update_roles(
        user_id: int,
        request: Request,
        payload: UserUpdateRoles,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> UserResponse:
        target_user = user_repository.get(db, user_id)
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

        before_roles = [r.name for r in target_user.roles]
        user_repository.set_user_roles(db, target_user, payload.roles)
        
        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Usuarios",
            action="UPDATE",
            description=f"Alterou perfis do usuário '{target_user.email}' de {before_roles} para {payload.roles}",
            object_changed="users",
            object_id=str(target_user.id),
            result="SUCESSO",
            before_state=json.dumps({"roles": before_roles}),
            after_state=json.dumps({"roles": payload.roles})
        )
        return target_user

user_controller = UserController()
