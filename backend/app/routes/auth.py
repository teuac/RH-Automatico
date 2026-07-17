from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.controllers.auth_controller import auth_controller
from app.schemas.user import GoogleLoginRequest

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login")
def login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    return auth_controller.login(payload, db)

@router.post("/refresh")
def refresh(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    return auth_controller.refresh(refresh_token, db)

@router.get("/me")
def get_me(current_user = Depends(auth_controller.get_me)):
    return current_user

@router.get("/google-client-id")
def get_google_client_id():
    from app.config.settings import settings
    return {"client_id": settings.GOOGLE_CLIENT_ID}
