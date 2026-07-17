from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.repositories.user import user_repository
from app.auth.oauth import verify_google_id_token
from app.auth.jwt import create_access_token, create_refresh_token
from app.config.settings import settings
from app.config.logging_config import app_logger

class AuthService:
    """
    Service layer for Authentication workflows.
    """

    def login_with_google(self, db: Session, id_token: str) -> Dict[str, Any]:
        # 1. Verify token with Google
        id_info = verify_google_id_token(id_token)
        if not id_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token do Google inválido ou expirado"
            )

        email = id_info.get("email")
        full_name = id_info.get("name", "")
        picture_url = id_info.get("picture")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail não fornecido pelo Google"
            )

        # 2. Retrieve user
        user = user_repository.get_by_email(db, email)

        if not user:
            # 3. Auto-registration
            app_logger.info(f"Auto-registering user: {email}")
            user = user_repository.create_pending_user(
                db=db,
                email=email,
                full_name=full_name,
                picture_url=picture_url
            )

        # 4. Enforce Active Status
        # We still generate the token so they can authenticate and hit `/api/v1/auth/me`
        # and receive a status "PENDENTE", which lets the frontend render the pending page correctly.
        roles = [r.name for r in user.roles]
        
        # Flatten permissions
        permissions = []
        for r in user.roles:
            permissions.extend([p.code for p in r.permissions])
        permissions = list(set(permissions))

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            roles=roles,
            permissions=permissions
        )
        refresh_token = create_refresh_token(user_id=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "picture_url": user.picture_url,
                "status": user.status,
                "roles": roles,
                "permissions": permissions
            }
        }

    def refresh_user_tokens(self, db: Session, refresh_token: str) -> Dict[str, str]:
        from app.auth.jwt import verify_token
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de atualização inválido ou expirado"
            )

        user_id = int(payload.get("sub"))
        user = user_repository.get(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou desativado"
            )

        roles = [r.name for r in user.roles]
        permissions = []
        for r in user.roles:
            permissions.extend([p.code for p in r.permissions])
        permissions = list(set(permissions))

        new_access = create_access_token(
            user_id=user.id,
            email=user.email,
            roles=roles,
            permissions=permissions
        )
        new_refresh = create_refresh_token(user_id=user.id)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }

auth_service = AuthService()
