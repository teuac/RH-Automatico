from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import auth_service
from app.schemas.user import GoogleLoginRequest, UserResponse
from app.auth.rbac import get_current_user
from app.models.user import User

class AuthController:
    @staticmethod
    def login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
        return auth_service.login_with_google(db, payload.token)

    @staticmethod
    def refresh(refresh_token: str, db: Session = Depends(get_db)):
        return auth_service.refresh_user_tokens(db, refresh_token)

    @staticmethod
    def get_me(current_user: User = Depends(get_current_user)):
        roles = [r.name for r in current_user.roles]
        permissions = []
        for r in current_user.roles:
            permissions.extend([p.code for p in r.permissions])
        permissions = list(set(permissions))

        return {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "picture_url": current_user.picture_url,
            "status": current_user.status,
            "is_active": current_user.is_active,
            "roles": roles,
            "permissions": permissions
        }

auth_controller = AuthController()
