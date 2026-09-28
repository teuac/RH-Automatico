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
    
    # If the backend external URL changes, dynamically sync it in Evolution API
    if key == "BACKEND_EXTERNAL_URL" and value:
        try:
            from app.services.whatsapp_service import whatsapp_service
            whatsapp_service.configure_webhook(db, value)
        except Exception as e:
            pass

    
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
    return {
        "status": "DESATIVADO",
        "message": "A integração com o Google Sheets foi desativada e removida do sistema."
    }

@router.post("/test-whatsapp", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def test_whatsapp_connection(db: Session = Depends(get_db)):
    from app.services.whatsapp_service import whatsapp_service
    creds = whatsapp_service._get_credentials(db)
    if not creds["url"] or not creds["token"] or not creds["instance"]:
        return {"status": "ERROR", "message": "Credenciais não configuradas no banco de dados."}
    
    import requests
    url = f"{creds['url']}/instance/connectionState/{creds['instance']}"
    headers = {"apikey": creds["token"]}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 404:
            return {"status": "WARNING", "message": "Instância não encontrada na Evolution API. Crie-a no painel."}
        res.raise_for_status()
        data = res.json()
        state = data.get("instance", {}).get("state") or data.get("state") or (data.get("instance") if isinstance(data.get("instance"), str) else None)
        if state == "open" or data.get("instance", {}).get("connected") is True:
            return {"status": "SUCCESS", "message": "WhatsApp conectado com sucesso (Estado: OPEN)."}
        else:
            return {"status": "WARNING", "message": f"Instância existente mas não conectada. Estado: {state or 'DESCONECTADO'}"}
    except Exception as e:
        return {"status": "ERROR", "message": f"Erro de conexão com Evolution API: {str(e)}"}

