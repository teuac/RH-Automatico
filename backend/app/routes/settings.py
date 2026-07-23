import json
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.settings import system_settings_repository
from app.repositories.audit import audit_repository
from app.auth.rbac import RoleChecker

router = APIRouter(prefix="/settings", tags=["Configurações do Sistema"])

@router.get("/", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def get_settings(db: Session = Depends(get_db)):
    settings_list = system_settings_repository.get_multi(db)
    res = {s.key: s.value for s in settings_list}
    if "valor_diario_vt" not in res:
        res["valor_diario_vt"] = "12.00"
    if "ALLOWED_DOMAIN" not in res:
        res["ALLOWED_DOMAIN"] = "acengenharia.com.br"
    return res

@router.post("/", dependencies=[Depends(RoleChecker(["Administrador"]))])
def update_setting(
    request: Request,
    key: str,
    value: str,
    description: str = "",
    db: Session = Depends(get_db)
):
    current_user = request.state.user if hasattr(request.state, "user") else None
    
    # Check current value before edit
    existing = system_settings_repository.get_by_key(db, key)
    before_val = existing.value if existing else None
    
    # Save/Update setting
    setting = system_settings_repository.set_value(db, key, value, description)
    
    # Log Audit
    audit_repository.log(
        db=db,
        user_id=current_user.id if current_user else None,
        user_name=current_user.full_name if current_user else "Administrador",
        user_email=current_user.email if current_user else "admin",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        module="Configuracoes",
        screen="Configuracoes",
        action="UPDATE",
        description=f"Alterou configuração '{key}' de '{before_val}' para '{value}'",
        object_changed="settings",
        object_id=str(setting.id),
        result="SUCESSO",
        before_state=json.dumps({"value": before_val}),
        after_state=json.dumps({"value": value})
    )
    
    return {"key": key, "value": value}

@router.get("/google-sheets-status", dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_google_sheets_status():
    from app.google.sheets_service import google_sheets_service
    from app.config.settings import settings
    import os

    is_connected = google_sheets_service.is_configured()
    if is_connected:
        return {
            "status": "CONECTADO",
            "message": "Conta de serviço autenticada e conectada com sucesso."
        }
    else:
        has_info = bool(settings.GOOGLE_SERVICE_ACCOUNT_INFO)
        has_file = os.path.exists(settings.GOOGLE_SERVICE_ACCOUNT_FILE)
        if not has_info and not has_file:
            return {
                "status": "NAO_CONFIGURADO",
                "message": "Nenhuma credencial configurada no arquivo .env."
            }
        else:
            return {
                "status": "ERRO",
                "message": "Erro ao validar credenciais da conta de serviço. Verifique o formato do JSON ou permissões nos logs."
            }
